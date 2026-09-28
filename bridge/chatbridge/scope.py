"""scope.py -- which files a chat instruction may change: content, never machinery.

THE LINE. A repository's content is its documents, notes, decisions and open
items. Its machinery is everything that decides how the repository behaves:
the vendored engine, hooks, workflows, settings, instruction files and
practice text. An instruction that arrives through the chat bridge may change
content and may never change machinery, **whoever sends it -- the
repository's owner included**. The owner has a normal session for machinery;
the chat bridge is not one.

WHERE THE LINE COMES FROM -- the same registry GitHub enforces, so the bridge
and branch protection can never disagree about a path:

  1. a built-in floor (DEFAULT_OWNED) that no configuration can shrink;
  2. `owned_paths` in the target repository's precedent.json -- the registry
     tools/build_codeowners.py turns into CODEOWNERS;
  3. every pattern in the repository's CODEOWNERS, whoever owns it: a path
     somebody must review is not one a chat message may change alone;
  4. `extra_owned_paths` from the bridge's own configuration.

On top of that, a file counts as content only if its extension is on the
content list, and no path component may start with a dot (hidden files are
configuration everywhere).

A CODEOWNERS pattern the matcher cannot translate makes the whole scope
refuse every write, and says so. A boundary that is "probably" honoured is
the one that lets a change through (tools/precedent_owned_paths.py says the
same about its own matcher, which this module reuses).
"""
from __future__ import annotations

import json
import os
import pathlib
import sys

_TOOLS = pathlib.Path(__file__).resolve().parents[2] / "tools"
if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))
try:
    from precedent_owned_paths import (  # noqa: E402
        find_codeowners, parse_codeowners, pattern_to_regex)
except ImportError as exc:  # pragma: no cover - only when bridge/ is copied out alone
    raise SystemExit(
        "chatbridge needs tools/precedent_owned_paths.py from the same "
        f"repository checkout ({_TOOLS}); copy bridge/ together with tools/. "
        f"({exc})")

# The floor. Mirrors templates/document-project/precedent.json's
# owned_paths, plus the paths a chat must never reach in any repository.
DEFAULT_OWNED = [
    ("/.github/", "workflows and CODEOWNERS"),
    ("/.claude/", "session configuration and hooks"),
    ("/.git/", "git's own internals"),
    ("/.precedent/", "generated session state"),
    ("/tools/", "the vendored engine"),
    ("/precedent/", "the vendored practice catalogue"),
    ("/practices/", "practice text"),
    ("/local/", "repo-local practice text"),
    ("/templates/", "templates other repositories install"),
    ("/precedent.json", "the repository's own configuration"),
    ("/precedent-source.json", "the repository's own configuration"),
    ("/approvers.json", "who may land a practice"),
    ("/AGENTS.md", "the instructions every session loads"),
    ("/CLAUDE.md", "the instructions every session loads"),
    ("/GEMINI.md", "the instructions every session loads"),
    ("CODEOWNERS", "who reviews what"),
]

DEFAULT_CONTENT_EXTENSIONS = [".md", ".markdown", ".txt", ".csv", ".tsv"]


class Scope:
    """A decided content/machinery line for one repository checkout."""

    def __init__(self, owned, content_extensions, broken=None):
        # owned: list of (pattern, why)
        self.owned = list(owned)
        self.content_extensions = [e.lower() for e in content_extensions]
        self.broken = list(broken or [])  # untranslatable patterns
        self._compiled = [(pattern_to_regex(p), p, why) for p, why in self.owned]

    # -- the one question -------------------------------------------------
    def verdict(self, relpath: str):
        """-> (is_content, reason). `relpath` is repository-relative."""
        rel = normalize(relpath)
        if rel is None:
            return False, "outside the repository"
        if self.broken:
            return False, ("this repository's CODEOWNERS has a pattern the "
                           "bridge cannot read (" + ", ".join(self.broken) +
                           "), so every write is refused until it is fixed")
        parts = rel.split("/")
        if any(p.startswith(".") for p in parts):
            return False, "hidden files are configuration"
        hit = None
        for rx, pattern, why in self._compiled:
            if rx is not None and rx.match(rel):
                hit = (pattern, why)
        if hit:
            return False, f"{hit[0]} is repository machinery ({hit[1]})"
        ext = os.path.splitext(rel)[1].lower()
        if ext not in self.content_extensions:
            return False, (f"'{ext or 'no extension'}' is not a content file "
                           f"type here ({', '.join(self.content_extensions)})")
        return True, "content"

    def is_content(self, relpath: str) -> bool:
        return self.verdict(relpath)[0]

    def summary(self) -> str:
        """One line for the model's instructions."""
        pats = [p for p, _ in self.owned][:14]
        more = "" if len(self.owned) <= 14 else f", and {len(self.owned) - 14} more"
        return ("content files are " + ", ".join(self.content_extensions) +
                "; machinery (never editable from chat) includes " +
                ", ".join(pats) + more + ", and any hidden file")

    # -- persistence, so the tool-call guard sees the same line ------------
    def to_json(self) -> str:
        return json.dumps({"owned": self.owned,
                           "content_extensions": self.content_extensions,
                           "broken": self.broken}, indent=1)

    @classmethod
    def from_json(cls, text: str) -> "Scope":
        d = json.loads(text)
        return cls([tuple(x) for x in d["owned"]], d["content_extensions"],
                   d.get("broken"))


def normalize(relpath: str):
    """Repository-relative POSIX path, or None if it escapes the root."""
    p = relpath.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    if p.startswith("/") or not p:
        return None
    out = []
    for part in p.split("/"):
        if part in ("", "."):
            continue
        if part == "..":
            if not out:
                return None
            out.pop()
            continue
        out.append(part)
    return "/".join(out) if out else None


def load_scope(repo_root, extra_owned=None, content_extensions=None) -> Scope:
    """Build the scope for a checkout from every registry that names machinery."""
    root = pathlib.Path(repo_root)
    owned = list(DEFAULT_OWNED)
    broken = []
    cfg = root / "precedent.json"
    if cfg.is_file():
        try:
            data = json.loads(cfg.read_text(encoding="utf-8"))
        except ValueError:
            data = {}
            broken.append("precedent.json does not parse")
        for o in data.get("owned_paths") or []:
            if isinstance(o, dict) and o.get("path"):
                owned.append((o["path"], o.get("why") or "owned_paths"))
    co = find_codeowners(root)
    if co is not None:
        for pattern, _owners, _n in parse_codeowners(co.read_text(encoding="utf-8")):
            if pattern_to_regex(pattern) is None:
                broken.append(pattern)
            else:
                owned.append((pattern, "CODEOWNERS"))
    for p in extra_owned or []:
        owned.append((p, "the bridge's configuration"))
    return Scope(owned, content_extensions or DEFAULT_CONTENT_EXTENSIONS, broken)
