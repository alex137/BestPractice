"""cli.py -- run the bridge, invite a person, check the setup, test the scope line.

  python3 bridge/run.py check  --config ~/.config/chatbridge/config.json
  python3 bridge/run.py invite --config ... --handle morgan
  python3 bridge/run.py run    --config ...
  python3 bridge/run.py scope  --config ... --repo notes path/one.md tools/x.py
  python3 bridge/run.py cloud-config --out PATH   # a config from environment variables
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import urllib.request

from . import runner, transcribe
from .app import Bridge
from .store import Store
from .telegram import Telegram, TelegramError

DEFAULT_CONFIG = "~/.config/chatbridge/config.json"


def load_config(path):
    p = os.path.expanduser(path)
    with open(p, encoding="utf-8") as f:
        cfg = json.load(f)
    problems = []
    repos, people = cfg.get("repos") or {}, cfg.get("people") or {}
    if not repos:
        problems.append("no repos configured")
    for name, r in repos.items():
        for k in ("clone_url", "landing_branch"):
            if not r.get(k):
                problems.append(f"repo {name}: missing {k}")
    if not people:
        problems.append("no people configured")
    for h, pr in people.items():
        for r in pr.get("repos", []):
            if r not in repos:
                problems.append(f"person {h}: unknown repo {r}")
    if problems:
        raise SystemExit("config problems:\n  " + "\n  ".join(problems))
    return cfg


def telegram_from(cfg):
    token = os.environ.get(cfg.get("bot_token_env", "CHATBRIDGE_TELEGRAM_TOKEN"), "")
    return Telegram(token, cfg.get("telegram_base_url", "https://api.telegram.org"))


def store_from(cfg):
    return Store(cfg.get("state_dir", "~/.local/state/chatbridge"))


def cmd_run(cfg, a):
    tg = telegram_from(cfg)
    me = tg.me()
    print(f"chatbridge: serving @{me.get('username')} -- Ctrl-C to stop")
    bridge = Bridge(cfg, tg, store_from(cfg), transcribe.from_config(cfg.get("transcription")))
    try:
        bridge.serve_forever()
    except KeyboardInterrupt:
        print("stopping")
        bridge.stop_workers()


def cmd_invite(cfg, a):
    if a.handle not in cfg.get("people", {}):
        raise SystemExit(f"{a.handle} is not in the config's people")
    username = cfg.get("bot_username") or telegram_from(cfg).me()["username"]
    code = store_from(cfg).new_invite(a.handle, a.days)
    print(f"https://t.me/{username}?start={code}")
    print(f"(single use, expires in {a.days:g} days; send it to {a.handle} privately)")


def cmd_scope(cfg, a):
    from .gitops import Checkout
    from .scope import load_scope
    r = cfg["repos"][a.repo]
    path = a.checkout
    if not path:
        handle = next(iter(cfg["people"]))
        co = Checkout(os.path.join(os.path.expanduser(cfg.get("state_dir",
                      "~/.local/state/chatbridge")), "checkouts", a.repo, handle),
                      r["clone_url"], r["landing_branch"], f"chat/{handle}")
        co.ensure()
        path = str(co.path)
    s = load_scope(path, r.get("extra_owned_paths"), r.get("content_extensions"))
    for p in a.paths:
        ok, why = s.verdict(p)
        print(f"{'content  ' if ok else 'REFUSED  '}{p}  -- {why}")


def cmd_check(cfg, a):
    ok = True

    def row(good, what, detail=""):
        nonlocal ok
        ok = ok and good
        print(f"{'ok  ' if good else 'FIX '} {what}{(' -- ' + detail) if detail else ''}")

    env = cfg.get("bot_token_env", "CHATBRIDGE_TELEGRAM_TOKEN")
    if os.environ.get(env):
        try:
            me = telegram_from(cfg).me()
            row(True, f"Telegram bot @{me.get('username')} answers")
        except TelegramError as e:
            row(False, "Telegram bot token", str(e))
    else:
        row(False, "Telegram bot token", f"set the {env} environment variable")
    command = cfg.get("claude", {}).get("command", "claude")
    if shutil.which(command.split()[0]):
        flags = runner.supported_flags(command)
        row("--restricted" in flags or "--tools" in flags, "Claude Code is installed",
            "supports " + (", ".join(sorted(flags)) or "none of the lock-down flags -- update it"))
    else:
        row(False, "Claude Code is installed", f"'{command}' is not on PATH")
    try:
        t = transcribe.from_config(cfg.get("transcription"))
        if isinstance(t, transcribe.WhisperLocal):
            t.load()  # downloads the model on first run
            row(True, f"voice-note transcription (local Whisper '{t.model_name}' loaded)")
        else:
            row(t.available, "voice-note transcription",
                "" if t.available else "backend is 'none': voice notes will be refused")
    except transcribe.TranscriptionError as e:
        row(False, "voice-note transcription", str(e))
    for name, r in cfg["repos"].items():
        res = subprocess.run(["git", "ls-remote", "--heads", r["clone_url"], r["landing_branch"]],
                             capture_output=True, text=True, timeout=60,
                             env={**os.environ, "GIT_TERMINAL_PROMPT": "0"})
        row(res.returncode == 0 and bool(res.stdout.strip()), f"repo {name} reachable",
            f"branch {r['landing_branch']}" if res.returncode == 0 and res.stdout.strip()
            else (res.stderr.strip()[:200] or f"no branch {r['landing_branch']}"))
    denied = proxy_denials()
    if denied:
        row(False, "network", "this environment's network policy refused: " +
            ", ".join(denied) + " -- add them to the environment's allowed domains")
    return 0 if ok else 1


def proxy_denials():
    """Hosts a Claude Code cloud environment's egress proxy refused recently,
    read from its status page. Empty anywhere else."""
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy") or ""
    if not proxy.startswith("http://127.0.0.1"):
        return []
    try:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
        with opener.open(proxy.rstrip("/") + "/__agentproxy/status", timeout=5) as r:
            data = json.loads(r.read().decode())
    except Exception:
        return []
    hosts = []
    for f in data.get("recentRelayFailures") or []:
        h = (f.get("host") or "").rsplit(":", 1)[0]
        if h and h not in hosts and "403" in (f.get("detail") or ""):
            hosts.append(h)
    return hosts


def cloud_config():
    """A configuration built from environment variables, for a cloud session
    where nothing on disk survives. Nothing secret is in it: the bot token
    stays in its own environment variable."""
    e = os.environ.get
    repo = e("CHATBRIDGE_REPO", "")
    if repo.count("/") != 1:
        raise SystemExit("set CHATBRIDGE_REPO to owner/name, e.g. alex137/chat-test")
    name = repo.split("/")[1]
    handle = e("CHATBRIDGE_HANDLE", "me")

    def gitcfg(key):
        r = subprocess.run(["git", "config", "--global", key], capture_output=True, text=True)
        return r.stdout.strip() or None

    voice = e("CHATBRIDGE_VOICE", "whisper-local")
    transcription = {"backend": voice}
    if voice == "whisper-local":
        transcription.update(model=e("CHATBRIDGE_WHISPER_MODEL", "small"),
                             language=e("CHATBRIDGE_LANGUAGE") or None)
    elif voice == "openai":
        transcription.update(api_key_env="OPENAI_API_KEY",
                             language=e("CHATBRIDGE_LANGUAGE") or None)
    return {
        "bot_token_env": "CHATBRIDGE_TELEGRAM_TOKEN",
        "state_dir": e("CHATBRIDGE_STATE_DIR", "~/.local/state/chatbridge"),
        "claude": {"command": "claude", "restricted": True},
        "transcription": transcription,
        "reply": {"max_sentences": 3, "max_chars": 450, "batch_seconds": 4},
        "repos": {name: {"clone_url": f"https://github.com/{repo}.git",
                         "web_url": f"https://github.com/{repo}",
                         "landing_branch": e("CHATBRIDGE_LANDING", "main")}},
        "people": {handle: {"name": e("CHATBRIDGE_NAME", handle), "repos": [name],
                            "can_land": True,
                            "telegram_user_id": e("CHATBRIDGE_TELEGRAM_USER_ID") or None,
                            "git_name": e("CHATBRIDGE_GIT_NAME") or gitcfg("user.name"),
                            "git_email": e("CHATBRIDGE_GIT_EMAIL") or gitcfg("user.email")}},
    }


def main(argv=None):
    ap = argparse.ArgumentParser(prog="chatbridge")
    sub = ap.add_subparsers(dest="cmd", required=True)
    cc = sub.add_parser("cloud-config")
    cc.add_argument("--out", default=DEFAULT_CONFIG)
    for name in ("run", "invite", "check", "scope"):
        sp = sub.add_parser(name)
        sp.add_argument("--config", default=DEFAULT_CONFIG)
        if name == "invite":
            sp.add_argument("--handle", required=True)
            sp.add_argument("--days", type=float, default=7)
        if name == "scope":
            sp.add_argument("--repo", required=True)
            sp.add_argument("--checkout", help="an existing local checkout to read the line from")
            sp.add_argument("paths", nargs="+")
    a = ap.parse_args(argv)
    if a.cmd == "cloud-config":
        out = os.path.expanduser(a.out)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        with open(out, "w", encoding="utf-8") as f:
            json.dump(cloud_config(), f, indent=2)
        print(f"wrote {out}")
        return 0
    cfg = load_config(a.config)
    return {"run": cmd_run, "invite": cmd_invite, "check": cmd_check,
            "scope": cmd_scope}[a.cmd](cfg, a) or 0


if __name__ == "__main__":
    sys.exit(main())
