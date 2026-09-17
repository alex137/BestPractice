#!/usr/bin/env python3
"""move_paths.py -- move tracked files or directories and repoint every
reference to them in the same change (practice: rename-updates-links).

  python3 move_paths.py --map MAP.json [--dry-run] [--check-imports]

MAP.json is {"old/path": "new/path", ...}, paths relative to the repository
root. A directory entry moves the whole tracked subtree. The tool

  1. expands directories to their tracked files, refuses a source that is
     not tracked or a destination that already exists;
  2. scans every tracked text file for path-like tokens -- relative
     markdown-link targets, repo-relative path strings in code and
     registries, glob patterns with a moved directory prefix, and absolute
     GitHub blob/tree URLs -- resolves each against the file's OWN old
     location, then the repository root, then the configured EXTRA_BASES,
     and rewrites it to the same target's new location relative to the
     file's NEW location. A moved file's outbound links and every inbound
     link are handled by the same rule, so nothing is special-cased;
  3. reports, without touching them, the references inside EXCLUDED files
     (as-filed artifacts, sent copies, vendored trees -- anything a host
     declares immutable) that will dangle after the move, so the person
     who moves knows exactly what they left behind;
  4. `git mv`s each file and writes the rewritten contents.

Optional `--check-imports`: after the move, list Python files that import a
sibling module by bare name (`import foo` / `from foo import ...` where
foo.py lives in the repository) and no longer sit in the same directory as
it, unless a `sys.path.insert(...)` line in the file names that directory.
A moved model's importers are the reference the token scan cannot see.

A host configures it by setting, before calling main():
  ROOT          repository root (default: the git toplevel of the cwd)
  EXCLUDE       fnmatch patterns (repo-relative) never rewritten -- scanned
                and reported only
  EXTRA_BASES   directories tried as resolution bases after the file's own
                directory and the repository root (a registry that records
                paths relative to a subtree names that subtree here)
  TEXT_EXTS     extensions of files that are scanned
  URL_RE        regex whose group 1 is a repository URL prefix ending in
                "/blob/<ref>/" or "/tree/<ref>/" and group 2 the path part
  POST_MOVE     callable(expanded_file_map, dry_run) run after the move --
                a host records the moves in whatever registry it keeps

Exit 0 on a completed move (or a completed dry run), 1 on a refusal with
the reason on stderr and nothing written.

Story. The first mass move this served was a repository reshaping itself
along product boundaries ahead of a split: fifty files in the first
tranche, eight hundred references to them, and a rule that as-filed
artifacts are never rewritten. Moving by hand and fixing links by grep had
already cost sessions on smaller renames; the failure it prevents is the
one where the link fix lands a day after the move.
"""
import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys

ROOT = None
EXCLUDE = []
EXTRA_BASES = []
TEXT_EXTS = {".md", ".py", ".sh", ".json", ".txt", ".yml", ".yaml", ".html",
             ".svg", ".css", ".template", ".toml", ".cfg", ".ini"}
DOTFILES = {".gitignore", ".gitattributes"}
URL_RE = re.compile(r"(https?://github\.com/[^/\s)]+/[^/\s)]+/(?:blob|tree)/[^/\s)]+/)"
                    r"([A-Za-z0-9_./*-]+)")
POST_MOVE = None

FILE_EXT_ALT = (r"md|py|svg|png|jpg|jpeg|gif|html|json|txt|csv|xlsx|sh|yml|yaml"
                r"|pdf|docx|mp4|css|template|toml")
# A path-like token: something with a slash (relative or repo-relative,
# optionally ending in a glob or a trailing slash), or a bare filename with
# a known extension. Bounded so it never eats a word or a URL scheme.
TOKEN_RE = re.compile(
    r"(?<![A-Za-z0-9_@:/.\\-])("
    r"(?:\.\.?/)+(?:[A-Za-z0-9_.-]+/)*[A-Za-z0-9_*.-]*"
    r"|(?:[A-Za-z0-9_.-]+/)+[A-Za-z0-9_*.-]*"
    r"|[A-Za-z0-9_-]+\.(?:" + FILE_EXT_ALT + r")"
    r")(?![A-Za-z0-9_])")


def _git(*args):
    return subprocess.run(["git", "-C", ROOT, *args], capture_output=True, text=True)


def _tracked():
    r = _git("ls-files")
    if r.returncode:
        sys.exit(f"move_paths: git ls-files failed: {r.stderr.strip()}")
    return [l for l in r.stdout.splitlines() if l]


def _excluded(rel):
    return any(fnmatch.fnmatch(rel, p) or rel.startswith(p.rstrip("*"))
               for p in EXCLUDE)


def _is_text(rel):
    base = os.path.basename(rel)
    return base in DOTFILES or os.path.splitext(rel)[1].lower() in TEXT_EXTS


def expand_map(raw, tracked):
    """{old: new} with directories expanded to their tracked files.
    Returns (file_map, dir_map)."""
    tset = set(tracked)
    file_map, dir_map = {}, {}
    for old, new in raw.items():
        old = old.rstrip("/"); new = new.rstrip("/")
        if old in tset:
            file_map[old] = new
            continue
        under = [t for t in tracked if t.startswith(old + "/")]
        if not under:
            sys.exit(f"move_paths: {old!r} is not a tracked file or directory")
        dir_map[old] = new
        for t in under:
            file_map[t] = new + t[len(old):]
    for old, new in file_map.items():
        if new in tset and new not in file_map:
            sys.exit(f"move_paths: destination {new!r} already exists")
        if os.path.exists(os.path.join(ROOT, new)) and new != old:
            sys.exit(f"move_paths: destination {new!r} exists on disk")
    dups = {}
    for old, new in file_map.items():
        dups.setdefault(new, []).append(old)
    for new, olds in dups.items():
        if len(olds) > 1:
            sys.exit(f"move_paths: {olds} would all land on {new!r}")
    return file_map, dir_map


def _norm(p):
    p = os.path.normpath(p)
    return "" if p == "." else p


def _retarget(rel, file_map, dir_map):
    """The new repo-relative path of an old one, or None if it did not move."""
    if rel in file_map:
        return file_map[rel]
    for od, nd in dir_map.items():
        if rel == od:
            return nd
        if rel.startswith(od + "/"):
            return nd + rel[len(od):]
    return None


def rewrite(text, old_rel, new_rel, file_map, dir_map, tracked_set, dir_set):
    """Rewrite path tokens in `text` (a file at old_rel moving to new_rel).
    Returns (new_text, n_changes, dangling_targets)."""
    old_dir = _norm(os.path.dirname(old_rel))
    new_dir = _norm(os.path.dirname(new_rel))
    bases = [(old_dir, new_dir), ("", "")] + [(b, b) for b in EXTRA_BASES]
    changes = 0
    dangling = []

    def resolve(token):
        """-> (base_index, resolved_old_path, kind) or None."""
        t = token
        glob = "*" in t
        trailing = t.endswith("/")
        core = t.rstrip("/")
        if glob:
            core = os.path.dirname(core)
        for i, (b, _nb) in enumerate(bases):
            cand = _norm(os.path.join(b, core)) if core else b
            if cand.startswith(".."):
                continue
            if cand in tracked_set or cand in dir_set:
                return i, cand, ("glob" if glob else "dir" if trailing or cand in dir_set else "file")
        return None

    def sub(m):
        nonlocal changes
        token = m.group(1)
        # Sentence punctuation glued to a path ("under docs/.", "x.md.") is
        # not part of it.
        tail = ""
        while token.endswith(".") and not token.endswith("/.."):
            token, tail = token[:-1], token[-1] + tail
        if token.endswith("/.") :
            token, tail = token[:-1], "." + tail
        if not token or token in ("/", "./", "../"):
            return m.group(0)
        # A bare filename (no slash) is prose or an identifier unless it is
        # a markdown link target; only the target is a path to repoint.
        if "/" not in token and m.string[max(0, m.start(1) - 2):m.start(1)] != "](":
            return m.group(0)
        r = resolve(token)
        if r is None:
            return m.group(0)
        i, cand, kind = r
        target = _retarget(cand, file_map, dir_map) or cand
        base_old, base_new = bases[i]
        # Nothing to do unless the target moved, or this file moved and the
        # token was relative to it.
        if target == cand and (i != 0 or old_rel == new_rel):
            return m.group(0)
        if base_new:
            new_tok = os.path.relpath(target, base_new) if target != base_new else "."
        else:
            new_tok = target
        # Restore the token's own shape: glob tail, trailing slash, ./ prefix.
        if kind == "glob":
            new_tok = new_tok + "/" + os.path.basename(token) if new_tok != "." else os.path.basename(token)
        elif kind == "dir" and token.endswith("/"):
            new_tok += "/"
        if token.startswith("./") and not new_tok.startswith("."):
            new_tok = "./" + new_tok
        if new_tok == token:
            return m.group(0)
        changes += 1
        return (m.group(0)[: m.start(1) - m.start(0)] + new_tok + tail
                + m.group(0)[m.end(1) - m.start(0):])

    def sub_url(m):
        nonlocal changes
        path = m.group(2).rstrip("/")
        glob = "*" in path
        core = os.path.dirname(path) if glob else path
        if core not in tracked_set and core not in dir_set:
            return m.group(0)
        target = _retarget(core, file_map, dir_map)
        if not target:
            return m.group(0)
        if glob:
            target = target + "/" + os.path.basename(path)
        changes += 1
        return m.group(1) + target + ("/" if m.group(2).endswith("/") else "")

    out = URL_RE.sub(sub_url, text)
    out = TOKEN_RE.sub(sub, out)
    return out, changes, dangling


def find_dangling(text, rel, file_map, dir_map, tracked_set, dir_set):
    """References in an immutable file that will no longer resolve after the
    move. A reference from a file that moves too, to a target that moves
    with it, is not dangling when the relative form is unchanged (a sibling
    link inside a directory that moves as a block)."""
    new_rel = file_map.get(rel, rel)
    old_dir = _norm(os.path.dirname(rel))
    new_dir = _norm(os.path.dirname(new_rel))
    found = []
    for m in TOKEN_RE.finditer(text):
        token = m.group(1).rstrip(".")
        if "/" not in token and m.string[max(0, m.start(1) - 2):m.start(1)] != "](":
            continue
        core = token.rstrip("/")
        if "*" in core:
            core = os.path.dirname(core)
        for i, b in enumerate([old_dir, ""] + list(EXTRA_BASES)):
            cand = _norm(os.path.join(b, core)) if core else b
            if cand.startswith(".."):
                continue
            if cand not in tracked_set and cand not in dir_set:
                continue
            target = _retarget(cand, file_map, dir_map) or cand
            base_new = new_dir if i == 0 else b
            still = (_norm(os.path.join(base_new, core)) if core else base_new) == target
            if not still:
                found.append(token)
            break
    for m in URL_RE.finditer(text):
        path = m.group(2).rstrip("/")
        if _retarget(path, file_map, dir_map):
            found.append(m.group(0))
    return found


def check_imports(tracked_after):
    """Python files importing a repo module by bare name from another
    directory without a sys.path line naming that directory."""
    stems = {}
    for t in tracked_after:
        if t.endswith(".py"):
            stems.setdefault(os.path.splitext(os.path.basename(t))[0], []).append(t)
    imp_re = re.compile(r"^(?:import|from)\s+([A-Za-z_][A-Za-z0-9_]*)\b", re.M)
    problems = []
    for t in tracked_after:
        if not t.endswith(".py"):
            continue
        try:
            src = open(os.path.join(ROOT, t), encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        here = os.path.dirname(t)
        for mod in set(imp_re.findall(src)):
            if mod not in stems:
                continue
            dirs = {os.path.dirname(p) for p in stems[mod]}
            if here in dirs:
                continue
            # A sys.path line naming the module's directory (by its last
            # component) counts as reaching it.
            named = any(os.path.basename(d) and os.path.basename(d) in src for d in dirs)
            if not named:
                problems.append(f"{t}: imports {mod} (in {sorted(dirs)}) from another "
                                f"directory with no sys.path line naming it")
    return problems


def main(argv=None):
    global ROOT
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--map", required=True, help="JSON {old: new}, repo-relative")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--check-imports", action="store_true")
    ap.add_argument("--verbose", action="store_true")
    ap.add_argument("--show", action="append", default=[], metavar="PATH",
                    help="print the unified diff the rewrite would make to PATH "
                         "(repo-relative, old path); repeatable; works in a dry run")
    args = ap.parse_args(argv)
    if ROOT is None:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        ROOT = r.stdout.strip()
    raw = json.load(open(args.map, encoding="utf-8"))
    tracked = _tracked()
    file_map, dir_map = expand_map(raw, tracked)
    tracked_set = set(tracked)
    dir_set = set()
    for t in tracked:
        d = os.path.dirname(t)
        while d:
            dir_set.add(d)
            d = os.path.dirname(d)
    dir_set |= set(dir_map)

    rewritten = {}
    dangling = {}
    for rel in tracked:
        if not _is_text(rel):
            continue
        path = os.path.join(ROOT, rel)
        try:
            text = open(path, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        if _excluded(rel):
            d = find_dangling(text, rel, file_map, dir_map, tracked_set, dir_set)
            if d:
                dangling[rel] = d
            continue
        new_rel = file_map.get(rel, rel)
        out, n, _ = rewrite(text, rel, new_rel, file_map, dir_map, tracked_set, dir_set)
        if n:
            rewritten[rel] = (new_rel, out, n)

    print(f"move_paths: {len(file_map)} file(s) to move ({len(dir_map)} directory rule(s)); "
          f"{len(rewritten)} file(s) with references to rewrite "
          f"({sum(v[2] for v in rewritten.values())} replacement(s))")
    if args.verbose:
        for rel, (new_rel, _o, n) in sorted(rewritten.items()):
            print(f"  rewrite {rel}: {n}")
    if args.show:
        import difflib
        for rel in args.show:
            if rel not in rewritten:
                print(f"--- {rel}: no rewrite")
                continue
            new_rel, out, _n = rewritten[rel]
            old = open(os.path.join(ROOT, rel), encoding="utf-8").read()
            sys.stdout.writelines(difflib.unified_diff(
                old.splitlines(True), out.splitlines(True), rel, new_rel, n=0))
    if dangling:
        print(f"DANGLING after move -- {sum(len(v) for v in dangling.values())} reference(s) in "
              f"{len(dangling)} excluded (immutable) file(s), left as they are:")
        for rel, toks in sorted(dangling.items()):
            print(f"  {rel}: {sorted(set(toks))}")
    if args.dry_run:
        print("dry run: nothing moved, nothing written")
        return 0

    # Move first (git mv keeps history detectable), then write contents.
    for old, new in sorted(file_map.items()):
        os.makedirs(os.path.join(ROOT, os.path.dirname(new)) or ROOT, exist_ok=True)
        r = _git("mv", old, new)
        if r.returncode:
            sys.exit(f"move_paths: git mv {old} {new} failed: {r.stderr.strip()}")
    for rel, (new_rel, out, _n) in rewritten.items():
        with open(os.path.join(ROOT, new_rel), "w", encoding="utf-8") as f:
            f.write(out)
    # Drop directories emptied by the move.
    for od in sorted(dir_map, reverse=True):
        p = os.path.join(ROOT, od)
        while p and p != ROOT and os.path.isdir(p) and not os.listdir(p):
            os.rmdir(p)
            p = os.path.dirname(p)
    print(f"moved {len(file_map)} file(s); rewrote {len(rewritten)} file(s)")
    if POST_MOVE:
        POST_MOVE(file_map, False)
    if args.check_imports:
        after = _tracked()
        probs = check_imports(after)
        if probs:
            print(f"IMPORT CHECK -- {len(probs)} cross-directory bare import(s) to fix:")
            for p in probs:
                print("  " + p)
        else:
            print("import check OK: every bare sibling import is reachable")
    return 0


if __name__ == "__main__":
    sys.exit(main())
