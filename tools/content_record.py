#!/usr/bin/env python3
"""Content record: hash a set of inputs now, and say later whether they still
hold and which moved.

Practice `judgment-check-or-tool` (spec/SHARED_ENGINES_PLAN.md, section 2).
Several tools asked the same question in their own words -- a gate's
ledger of verified facts (`fact_ledger.py`), a drift check against content
recorded at a release, the manifest stamped on a built package -- and each
kept its own hashing. This module is that hashing, once.

An input is (kind, name). The kinds a Reader knows:

  f   a file's content              d   a directory's listing (names)
  x   whether a path exists          e   an environment variable
  g   a git repository's state (HEAD, refs, the working tree by content)

A signature is a sha256 hex digest, truncated to `length` characters when
the caller keeps short ones (the fact ledger keeps 16). Two text schemes for
a file, both frozen -- a stored record made under one must reproduce under
it forever, so neither is ever changed, only added beside:

  raw      the bytes as they are
  rstrip   UTF-8 text with each line's trailing whitespace dropped and the
           whole stripped: insensitive to line endings and trailing blanks

A Record is the stored form: [[kind, name, signature], ...]. `holds()`
re-reads every input and returns (True, []) or (False, [what moved]).
`digest()` is one short code over the whole record.

  python3 content_record.py --self-check
"""
import hashlib
import os
import subprocess
import sys
from pathlib import Path

VERSION = "1"
SCHEMES = ("raw", "rstrip")


def digest(data, length=None):
    """sha256 hex of `data` (str as UTF-8), cut to `length` characters."""
    h = hashlib.sha256(data.encode() if isinstance(data, str) else data).hexdigest()
    return h[:length] if length else h


def text_rstrip(text):
    """The `rstrip` scheme's normalization (frozen)."""
    return "\n".join(line.rstrip() for line in text.split("\n")).strip()


def file_hash(path, scheme="raw", length=None):
    """The signature of a file's content under `scheme`. Raises OSError for
    a missing file; a caller that wants "missing" uses Reader.sig."""
    if scheme == "raw":
        with open(path, "rb") as f:
            return digest(f.read(), length)
    if scheme == "rstrip":
        with open(path, encoding="utf-8") as f:
            return digest(text_rstrip(f.read()), length)
    raise ValueError(f"unknown scheme {scheme!r}; known: {', '.join(SCHEMES)}")


class Reader:
    """Signatures of inputs under one root, with the repository states
    computed once per reader (a run does not change them)."""

    def __init__(self, root, length=16, scheme="raw"):
        self.root = Path(root)
        self.length = length
        self.scheme = scheme
        self._repo = {}

    def repo_state(self, path):
        key = str(path)
        if key not in self._repo:
            def git(*a):
                r = subprocess.run(["git", "-C", key, *a], capture_output=True)
                return r.stdout if r.returncode == 0 else b"?"
            h = hashlib.sha256()
            for part in (git("rev-parse", "HEAD"), git("for-each-ref", "--format=%(refname) %(objectname)"),
                         git("diff", "HEAD", "--binary"), git("status", "--porcelain=v1", "-uall", "-z")):
                h.update(part + b"\0")
            for name in git("ls-files", "--others", "--exclude-standard", "-z").split(b"\0"):
                f = Path(key) / name.decode(errors="replace")
                if name and f.is_file():
                    h.update(name + b"\0" + f.read_bytes())
            self._repo[key] = h.hexdigest()[:self.length] if self.length else h.hexdigest()
        return self._repo[key]

    def sig(self, kind, name):
        if kind == "e":
            v = os.environ.get(name)
            return digest("\0unset" if v is None else v, self.length)
        p = self.root / name
        if kind == "x":
            return "dir" if p.is_dir() else ("file" if os.path.lexists(p) else "missing")
        if kind == "g":
            return self.repo_state(p)
        try:
            if kind == "d":
                return digest("\n".join(sorted(x.name for x in p.iterdir())), self.length)
            return file_hash(p, self.scheme, self.length)
        except (OSError, UnicodeDecodeError):
            return "missing"


class Record:
    """A set of (kind, name, signature) taken at one moment."""

    def __init__(self, inputs):
        self.inputs = [tuple(i) for i in inputs]

    @classmethod
    def of(cls, reader, keys):
        """A record of `keys` ((kind, name) pairs) as they are now."""
        return cls(sorted((k, n, reader.sig(k, n)) for k, n in set(map(tuple, keys))))

    def holds(self, reader, ignore=()):
        """(True, []) when every input still has its signature, else
        (False, [(kind, name), ...] that moved). Names in `ignore` never
        count."""
        ignore = set(ignore)
        moved = [(k, n) for k, n, s in self.inputs
                 if n not in ignore and reader.sig(k, n) != s]
        return (not moved, moved)

    def digest(self, length=16):
        return digest("\n".join("\t".join(i) for i in sorted(self.inputs)), length)

    def to_list(self):
        return [list(i) for i in sorted(self.inputs)]


# ------------------------------------------------------------ self-check --
def self_check():
    import tempfile
    bad = []
    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        (root / "a.txt").write_text("one  \r\ntwo\n\n")
        (root / "d").mkdir()
        (root / "d" / "x").write_text("")
        r = Reader(root)
        # schemes are frozen: these literals are the contract
        if file_hash(root / "a.txt", "rstrip") != digest("one\ntwo"):
            bad.append("rstrip scheme does not hash the normalized text")
        if text_rstrip("one  \r\ntwo\n\n") != "one\ntwo":
            bad.append("rstrip normalization changed")
        if digest("abc") != "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad":
            bad.append("digest is not sha256")
        rec = Record.of(r, [("f", "a.txt"), ("d", "d"), ("x", "gone"), ("e", "CONTENT_RECORD_T")])
        if rec.holds(Reader(root)) != (True, []):
            bad.append("a fresh record does not hold")
        (root / "a.txt").write_text("changed\n")
        (root / "d" / "y").write_text("")
        (root / "gone").write_text("")
        os.environ["CONTENT_RECORD_T"] = "set"
        try:
            ok, moved = rec.holds(Reader(root))
        finally:
            os.environ.pop("CONTENT_RECORD_T", None)
        if ok or sorted(moved) != sorted([("f", "a.txt"), ("d", "d"), ("x", "gone"), ("e", "CONTENT_RECORD_T")]):
            bad.append(f"moved inputs not all reported: {moved}")
        if rec.holds(Reader(root), ignore={"a.txt", "d", "gone", "CONTENT_RECORD_T"})[0] is not True:
            bad.append("ignored names still counted")
        if Record(rec.to_list()).digest() != rec.digest():
            bad.append("a record does not round-trip through its stored form")
        (root / "a.txt").unlink()
        if Reader(root).sig("f", "a.txt") != "missing":
            bad.append("a missing file is not 'missing'")
    return bad


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ["--self-check"]:
        bad = self_check()
        for b in bad:
            print(f"content_record self-check FAIL: {b}")
        if not bad:
            print("content_record self-check OK")
        return 1 if bad else 0
    print(__doc__)
    return 0


if __name__ == "__main__":
    sys.exit(main())
