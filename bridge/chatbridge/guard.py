"""guard.py -- the PreToolUse hook every chat turn runs under.

Claude Code calls this before each tool use and passes the call as JSON on
stdin. It allows reads inside the repository checkout, allows edits to
content files inside it, and denies everything else with a reason the model
sees -- so a turn that tries to touch machinery is told why at once, instead
of finding out when the bridge refuses to commit.

It is the SECOND of three locks, not the boundary:
  1. the tool set the bridge starts Claude Code with (file tools only);
  2. this hook;
  3. the bridge's own check of `git status` after the turn, which decides
     what is committed. That one does not depend on the model or on Claude
     Code honouring a hook, so it is the one that holds.

Run by Claude Code as:
  python3 guard.py --root <checkout> --scope <scope.json>
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from chatbridge.scope import Scope  # noqa: E402

READ_TOOLS = {"Read": "file_path", "Glob": "path", "Grep": "path", "LS": "path"}
WRITE_TOOLS = {"Edit": "file_path", "Write": "file_path", "MultiEdit": "file_path",
               "NotebookEdit": "notebook_path"}
# Tools with no file effect that are harmless to allow.
INERT_TOOLS = {"TodoWrite"}


def _inside(root: str, path: str):
    """-> repository-relative path if `path` resolves inside `root`, else None.
    Symlinks are resolved, so a link pointing out of the checkout is outside."""
    root_real = os.path.realpath(root)
    target = path if os.path.isabs(path) else os.path.join(root_real, path)
    real = os.path.realpath(target)
    if real == root_real:
        return ""
    if real.startswith(root_real + os.sep):
        return os.path.relpath(real, root_real).replace(os.sep, "/")
    return None


def decide(call: dict, root: str, scope: Scope):
    """-> None to allow, or a reason string to deny."""
    tool = call.get("tool_name") or ""
    args = call.get("tool_input") or {}
    if tool in INERT_TOOLS:
        return None
    if tool in READ_TOOLS:
        pat = args.get("pattern") if tool == "Glob" else None
        if pat and (os.path.isabs(pat) or pat.startswith("~") or ".." in pat.split("/")):
            return "Searching outside this repository isn't available through the chat bridge."
        p = args.get(READ_TOOLS[tool])
        if not p:
            return None  # defaults to the working directory, the checkout
        rel = _inside(root, p)
        if rel is None:
            return "Reading outside this repository isn't available through the chat bridge."
        if rel == ".git" or rel.startswith(".git/"):
            return "Git's own files aren't available through the chat bridge."
        return None
    if tool in WRITE_TOOLS:
        p = args.get(WRITE_TOOLS[tool])
        if not p:
            return "No file path given."
        rel = _inside(root, p)
        if rel is None or rel == "":
            return "Writing outside this repository isn't available through the chat bridge."
        ok, why = scope.verdict(rel)
        if not ok:
            return (f"'{rel}' can't be changed from chat: {why}. Chat instructions "
                    "are limited to content, for everyone, the owner included. Tell "
                    "the person it needs a normal session.")
        return None
    return (f"The {tool} tool isn't available through the chat bridge: chat "
            "instructions are limited to reading and editing content files.")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--scope", required=True)
    a = ap.parse_args(argv)
    try:
        call = json.load(sys.stdin)
        with open(a.scope, encoding="utf-8") as f:
            scope = Scope.from_json(f.read())
        reason = decide(call, a.root, scope)
    except Exception as exc:  # fail closed
        reason = f"The chat bridge's guard could not check this call ({exc}); refused."
    if reason:
        json.dump({"hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason}}, sys.stdout)
    return 0


if __name__ == "__main__":
    sys.exit(main())
