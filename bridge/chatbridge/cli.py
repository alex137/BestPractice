"""cli.py -- run the bridge, invite a person, check the setup, test the scope line.

  python3 bridge/run.py check  --config ~/.config/chatbridge/config.json
  python3 bridge/run.py invite --config ... --handle morgan
  python3 bridge/run.py run    --config ...
  python3 bridge/run.py scope  --config ... --repo notes path/one.md tools/x.py
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys

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
    return 0 if ok else 1


def main(argv=None):
    ap = argparse.ArgumentParser(prog="chatbridge")
    sub = ap.add_subparsers(dest="cmd", required=True)
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
    cfg = load_config(a.config)
    return {"run": cmd_run, "invite": cmd_invite, "check": cmd_check,
            "scope": cmd_scope}[a.cmd](cfg, a) or 0


if __name__ == "__main__":
    sys.exit(main())
