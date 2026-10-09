#!/usr/bin/env python3
"""Hash a set of inputs now and say later whether they still hold and which moved, under frozen schemes: the hashing shared by the fact ledger and any drift check

Content record: hash a set of inputs now, and say later whether they still
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
  p   a path as a stat sees it: missing, a directory, a file with its
      executable bits, or a symbolic link and its target
  v   an environment variable, with each temporary directory's own name
      blanked (a fixture made fresh each run is the same input every run)
  w   the whole environment, blanked as v, leaving out ENV_VOLATILE and
      the comma-separated names the input's name lists
  q   what a read-only git query answers: its exit status and output, run
      again where it ran (the name is JSON: [directory, argv, variables set,
      variables unset], "{root}" standing for the root), with the root's own
      path and each temporary directory's name blanked in the answer

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
import re
import stat
import subprocess
import sys
import tempfile
from pathlib import Path

VERSION = "1"
SCHEMES = ("raw", "rstrip")
# Variables a shell rewrites on its own (kind w never counts them).
ENV_VOLATILE = ("OLDPWD", "PWD", "SHLVL", "_")


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


def _temp_blanked(value):
    """`value` with every `<temp dir>/<one name>` turned into `<tmp>`: the
    name tempfile chose this run, which no input of the work can be."""
    out = value
    for base in sorted({tempfile.gettempdir(), os.path.realpath(tempfile.gettempdir())},
                       key=len, reverse=True):
        out = re.sub(re.escape(base.rstrip(os.sep)) + r"/[^/:\s]+", "<tmp>", out)
    return out


def _probe(p):
    try:
        st = os.lstat(p)
    except (OSError, ValueError):
        return "missing"
    if stat.S_ISLNK(st.st_mode):
        try:
            return "link:" + os.readlink(p)
        except OSError:
            return "link:?"
    if stat.S_ISDIR(st.st_mode):
        return "dir"
    return "file:" + oct(st.st_mode & 0o111)


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

    def _query(self, name):
        import json
        try:
            where, argv, put, drop = json.loads(name)
        except (ValueError, TypeError):
            return "unreadable"
        root = str(self.root)
        argv = [str(a).replace("{root}", root) for a in argv]
        if not argv or os.path.basename(argv[0]) != "git":
            return "not a git query"
        env = dict(os.environ)
        env.update({k: str(v).replace("{root}", root) for k, v in put.items()})
        for k in drop:
            env.pop(k, None)
        cwd = where.replace("{root}", root) if where.startswith("{root}") else str(self.root / where)
        try:
            r = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=120)
        except (OSError, subprocess.TimeoutExpired) as e:
            return "failed:" + type(e).__name__
        text = (f"{r.returncode}\0".encode() + r.stdout + b"\0" + r.stderr).decode("utf-8", "surrogateescape")
        for base in sorted({root, os.path.realpath(root)}, key=len, reverse=True):
            text = text.replace(base, "{root}")
        return digest(_temp_blanked(text).encode("utf-8", "surrogateescape"), self.length)

    def sig(self, kind, name):
        if kind == "e":
            v = os.environ.get(name)
            return digest("\0unset" if v is None else v, self.length)
        if kind == "v":
            v = os.environ.get(name)
            return digest("\0unset" if v is None else _temp_blanked(v), self.length)
        if kind == "w":
            left_out = set(ENV_VOLATILE) | set(filter(None, name.split(",")))
            return digest("\0".join(f"{k}={_temp_blanked(v)}" for k, v in sorted(os.environ.items())
                                     if k not in left_out), self.length)
        p = self.root / name
        if kind == "x":
            return "dir" if p.is_dir() else ("file" if os.path.lexists(p) else "missing")
        if kind == "p":
            return _probe(p)
        if kind == "q":
            return self._query(name)
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
        # p: a probe sees the type, a file's executable bits and a link's target
        (root / "run.sh").write_text("")
        before = Reader(root).sig("p", "run.sh")
        os.chmod(root / "run.sh", 0o755)
        if Reader(root).sig("p", "run.sh") == before or before != "file:0o0":
            bad.append(f"a probe does not see a file's executable bits: {before}")
        os.symlink("d", root / "ln")
        if Reader(root).sig("p", "ln") != "link:d" or Reader(root).sig("p", "gone2") != "missing":
            bad.append("a probe does not tell a link and a missing path apart")
        # q: a git query answers the same until what it reads moves
        subprocess.run(["git", "init", "-q", str(root)], capture_output=True)
        q = '[".", ["git", "ls-files", "--others"], {}, []]'
        before_q = Reader(root).sig("q", q)
        if before_q != Reader(root).sig("q", q) or len(before_q) != 16:
            bad.append("a git query does not answer the same twice")
        (root / "new.txt").write_text("")
        if Reader(root).sig("q", q) == before_q:
            bad.append("a git query's answer does not move with what it reads")
        if Reader(root).sig("q", '[".", ["rm", "-rf", "."], {}, []]') != "not a git query":
            bad.append("a query that is not git is run")
        # v and w: a temporary directory's own name is blanked, nothing else is
        os.environ["CONTENT_RECORD_T"] = str(Path(tempfile.gettempdir()) / "tmpAAAA" / "home")
        pwd = os.environ.get("PWD")
        try:
            a = Reader(root).sig("v", "CONTENT_RECORD_T")
            wa = Reader(root).sig("w", "")
            os.environ["CONTENT_RECORD_T"] = str(Path(tempfile.gettempdir()) / "tmpBBBB" / "home")
            if Reader(root).sig("v", "CONTENT_RECORD_T") != a or Reader(root).sig("w", "") != wa:
                bad.append("a temporary directory's own name is not blanked")
            os.environ["CONTENT_RECORD_T"] = str(Path(tempfile.gettempdir()) / "tmpBBBB" / "work")
            if Reader(root).sig("v", "CONTENT_RECORD_T") == a or Reader(root).sig("w", "") == wa:
                bad.append("a change under a temporary directory is blanked too")
            if Reader(root).sig("w", "CONTENT_RECORD_T") == wa:
                bad.append("w does not leave out the names it lists")
            pwd, w_before = os.environ.get("PWD"), Reader(root).sig("w", "")
            os.environ["PWD"] = (pwd or "") + "-moved"
            if Reader(root).sig("w", "") != w_before:
                bad.append("w counts a variable the shell rewrites on its own")
        finally:
            os.environ.pop("CONTENT_RECORD_T", None)
            if pwd is None:
                os.environ.pop("PWD", None)
            else:
                os.environ["PWD"] = pwd
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
