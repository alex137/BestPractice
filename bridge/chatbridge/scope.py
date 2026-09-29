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
import re
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
    # Instruction files are machinery wherever they sit: a CLAUDE.md in a
    # subfolder is loaded by the next session that works there.
    ("CLAUDE.md", "an instructions file sessions load"),
    ("CLAUDE.local.md", "an instructions file sessions load"),
    ("AGENTS.md", "an instructions file sessions load"),
    ("AGENTS.override.md", "an instructions file sessions load"),
    ("GEMINI.md", "an instructions file sessions load"),
    ("SKILL.md", "a skill sessions load"),
]

# Markdown only by default. `.txt` and `.csv` are opt-in per repository,
# because `requirements.txt` or `CMakeLists.txt` are build inputs, not prose.
DEFAULT_CONTENT_EXTENSIONS = [".md", ".markdown"]

# Build and dependency files with a content-looking extension, refused even
# where a repository opts `.txt` in.
BUILD_BASENAMES = ("requirements", "constraints", "cmakelists", "robots", "llms")


class Scope:
    """A decided content/machinery line for one repository checkout."""

    def __init__(self, owned, content_extensions, broken=None, read_only=False):
        # owned: list of (pattern, why)
        self.read_only = bool(read_only)  # a person allowed to ask, not to change
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
        if self.read_only:
            return False, "this person has read-only access through the chat"
        if self.broken:
            return False, ("this repository names machinery with a pattern the "
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
        base = parts[-1].lower()
        if any(base.startswith(b) for b in BUILD_BASENAMES) and ext != ".md":
            return False, f"{parts[-1]} is a build or dependency file"
        if ext not in self.content_extensions:
            return False, (f"'{ext or 'no extension'}' is not a content file "
                           f"type here ({', '.join(self.content_extensions)})")
        return True, "content"

    def is_content(self, relpath: str) -> bool:
        return self.verdict(relpath)[0]

    def summary(self) -> str:
        """One line for the model's instructions."""
        if self.read_only:
            return ("READ-ONLY: this person may ask about the repository but not "
                    "change any file, content included")
        pats = [p for p, _ in self.owned][:14]
        more = "" if len(self.owned) <= 14 else f", and {len(self.owned) - 14} more"
        return ("content files are " + ", ".join(self.content_extensions) +
                "; machinery (never editable from chat) includes " +
                ", ".join(pats) + more + ", and any hidden file")

    # -- persistence, so the tool-call guard sees the same line ------------
    def to_json(self) -> str:
        return json.dumps({"owned": self.owned,
                           "content_extensions": self.content_extensions,
                           "broken": self.broken, "read_only": self.read_only}, indent=1)

    @classmethod
    def from_json(cls, text: str) -> "Scope":
        d = json.loads(text)
        return cls([tuple(x) for x in d["owned"]], d["content_extensions"],
                   d.get("broken"), d.get("read_only", False))


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
    # Files the root instruction files pull in with @path are instructions too.
    for top in ("CLAUDE.md", "AGENTS.md"):
        f = root / top
        if f.is_file():
            for m in re.finditer(r"(?:^|\s)@([\w./-]+)", f.read_text(encoding="utf-8",
                                                                     errors="replace")):
                target = normalize(m.group(1))
                if target and not target.startswith("."):
                    owned.append(("/" + target, f"imported by {top}"))
    # Submodules are other repositories: never content.
    gm = root / ".gitmodules"
    if gm.is_file():
        for m in re.finditer(r"(?m)^\s*path\s*=\s*(\S+)", gm.read_text(encoding="utf-8")):
            owned.append(("/" + m.group(1).strip("/") + "/", "a git submodule"))
            owned.append(("/" + m.group(1).strip("/"), "a git submodule"))
    co = find_codeowners(root)
    if co is not None:
        for pattern, _owners, _n in parse_codeowners(co.read_text(encoding="utf-8")):
            if pattern_to_regex(pattern) is None:
                broken.append(pattern)
            else:
                owned.append((pattern, "CODEOWNERS"))
    for p in extra_owned or []:
        owned.append((p, "the bridge's configuration"))
    # Any machinery pattern the matcher can't translate fails closed, whichever
    # registry it came from -- dropping it would let its paths through.
    for p, _why in owned:
        if pattern_to_regex(p) is None and p not in broken:
            broken.append(p)
    return Scope(owned, content_extensions or DEFAULT_CONTENT_EXTENSIONS, broken)
