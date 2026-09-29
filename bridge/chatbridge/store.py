"""store.py -- the bridge's own state, kept outside every repository.

Telegram user identifiers, invite codes and Claude session identifiers are
credentials by another name, and a repository is forever, so none of it is
ever written into a checkout (spec/SPECULATIVE_WHATSAPP_BRIDGE.md, "Phone
numbers never enter the repository"). It lives in `state_dir`, one JSON file
plus one file per full answer.
"""
from __future__ import annotations

import json
import os
import pathlib
import secrets
import tempfile
import threading
import time


class Store:
    def __init__(self, state_dir):
        self.dir = pathlib.Path(os.path.expanduser(str(state_dir)))
        self.dir.mkdir(parents=True, exist_ok=True)
        os.chmod(self.dir, 0o700)
        (self.dir / "answers").mkdir(exist_ok=True)
        self.path = self.dir / "state.json"
        self.lock = threading.RLock()
        self.data = {"offset": 0, "bindings": {}, "invites": {}, "people": {},
                     "messages": {}}
        if self.path.is_file():
            self.data.update(json.loads(self.path.read_text(encoding="utf-8")))

    def save(self):
        with self.lock:
            fd, tmp = tempfile.mkstemp(dir=self.dir, prefix=".state-")
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=1, sort_keys=True)
            os.chmod(tmp, 0o600)
            os.replace(tmp, self.path)

    # -- who is who --------------------------------------------------------
    def handle_for(self, user_id: int):
        return self.data["bindings"].get(str(user_id))

    def bind(self, user_id: int, handle: str):
        with self.lock:
            self.data["bindings"][str(user_id)] = handle
            self.save()

    # Invites live in their own file, read fresh each time: `invite` runs as a
    # separate process while the bridge is serving, and the bridge rewrites
    # state.json on every poll, which would otherwise erase the new invite.
    def _invites(self):
        p = self.dir / "invites.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else {}

    def _save_invites(self, inv):
        fd, tmp = tempfile.mkstemp(dir=self.dir, prefix=".invites-")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(inv, f)
        os.chmod(tmp, 0o600)
        os.replace(tmp, self.dir / "invites.json")

    def new_invite(self, handle: str, days: float = 7) -> str:
        code = secrets.token_urlsafe(18)  # 24 chars of [A-Za-z0-9_-]
        with self.lock:
            inv = self._invites()
            inv[code] = {"handle": handle, "expires": time.time() + days * 86400}
            self._save_invites(inv)
        return code

    def redeem(self, code: str):
        """-> handle, once. An invite is single-use and expires."""
        with self.lock:
            inv = self._invites()
            found = inv.pop(code, None)
            self._save_invites(inv)
        if not found or found["expires"] < time.time():
            return None
        return found["handle"]

    # -- per-person conversation state ------------------------------------
    def person(self, handle: str) -> dict:
        with self.lock:
            return self.data["people"].setdefault(handle, {"current_repo": None,
                                                           "sessions": {}})

    def set_current_repo(self, handle, repo):
        with self.lock:
            self.person(handle)["current_repo"] = repo
            self.save()

    def session(self, handle, repo):
        return self.person(handle)["sessions"].get(repo)

    def set_session(self, handle, repo, session_id):
        with self.lock:
            s = self.person(handle)["sessions"]
            if session_id:
                s[repo] = session_id
            else:
                s.pop(repo, None)
            self.save()

    # -- bot messages -> which repo/answer they belong to ------------------
    def remember_message(self, chat_id, message_id, repo, answer_id=None):
        with self.lock:
            self.data["messages"][f"{chat_id}:{message_id}"] = {"repo": repo,
                                                                "answer": answer_id}
            # Keep the map bounded; old replies route to the current repo.
            if len(self.data["messages"]) > 2000:
                for k in list(self.data["messages"])[:500]:
                    del self.data["messages"][k]
            self.save()

    def message_info(self, chat_id, message_id):
        return self.data["messages"].get(f"{chat_id}:{message_id}")

    # -- full answers --------------------------------------------------------
    def save_answer(self, text: str) -> str:
        aid = secrets.token_hex(6)
        p = self.dir / "answers" / f"{aid}.md"
        p.write_text(text, encoding="utf-8")
        os.chmod(p, 0o600)
        return aid

    def answer(self, aid: str):
        if not aid or not aid.isalnum():
            return None
        p = self.dir / "answers" / f"{aid}.md"
        return p.read_text(encoding="utf-8") if p.is_file() else None

    def set_offset(self, offset: int):
        with self.lock:
            self.data["offset"] = offset
            self.save()
