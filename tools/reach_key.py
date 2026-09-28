"""A memo key over the code a solve actually reaches (practice
`slow-steps-report-and-cache`: a heavy solve caches to disk, keyed on what
can change its result; companion of `shared-result-cache`).

A memo keyed on the whole import closure of the file that makes it is
correct and wasteful: any edit to any imported file re-keys it, so an edit
that cannot change one number the solve produces (a new cache hook, a
reworded emitter, a function the solve never calls) still costs a cold
solve. `reach_key` keys the memo on what the solve can execute instead:
starting from the entry functions, it follows every name and every
`module.attr` reference, across the repository's modules, and hashes the
syntax trees of the definitions and the constants reached, plus the
import-time side effects of every repository module the entry file imports
(a monkeypatch at import time changes behaviour whether or not a function
names it). Syntax trees, not text: a comment or a docstring edit re-keys
nothing.

Where it cannot follow, it widens rather than narrows:

* a module used as a bare value (passed to a function, aliased through a
  structure the resolver does not follow) is hashed whole;
* a reached definition that calls `getattr` on a module with a non-literal
  name, looks a name up through `globals()` or `vars()` (indexed, or with
  `.get`/`.pop`/`.setdefault`), or uses `exec`, `eval`, `__import__` or
  `importlib`, has its whole module hashed; copying a namespace whole
  (`module.__dict__.update(globals())`, the fork-pool registration idiom)
  is not a lookup;
* external modules (the standard library, installed packages) are not
  followed; the interpreter's major.minor version is in the key.

Two things are left out on purpose, both named in the code they touch:

* top-level statements that only edit `sys.path`, which decide where
  modules are found, not what they compute;
* a definition whose `def` line carries `# reach-key: io` -- memo loaders
  and writers, whose only effect is to fetch or store the result of the
  function the key covers. Mark nothing else: a marked function's body is
  never hashed.

    key = reach_key(path, ["solve_rows"], search_dirs=[...], extra=b"v2")

`search_dirs` are the directories a bare `import name` may resolve to after
the importing file's own directory, in the order the program puts them on
`sys.path`. The result is a 16-hex-digit string.
"""
import ast
import hashlib
import sys
from pathlib import Path

IO_MARK = "# reach-key: io"
_DYNAMIC_CALLS = {"globals", "vars", "exec", "eval", "__import__"}


def _strip_docstrings(node):
    """A copy-free pass that blanks docstrings in place on a parsed tree
    the caller owns (every tree here is parsed fresh for hashing)."""
    for n in ast.walk(node):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)):
            b = n.body
            if b and isinstance(b[0], ast.Expr) and isinstance(getattr(b[0], "value", None), ast.Constant) \
                    and isinstance(b[0].value.value, str):
                b[0] = ast.Pass()
    return node


def _dump(node):
    return ast.dump(node, include_attributes=False)


def _path_only(stmt, src):
    """A top-level statement whose only work is editing sys.path (with its
    helper names)."""
    seg = ast.get_source_segment(src, stmt) or ""
    if "path.insert" not in seg and "path.append" not in seg:
        return False
    for n in ast.walk(stmt):
        if isinstance(n, (ast.Assign, ast.AugAssign, ast.AnnAssign)):
            ts = n.targets if isinstance(n, ast.Assign) else [n.target]
            for t in ts:
                for x in ast.walk(t):
                    if isinstance(x, ast.Name) and not x.id.startswith("_"):
                        return False
        if isinstance(n, ast.Call):
            f = n.func
            chain = []
            while isinstance(f, ast.Attribute):
                chain.append(f.attr)
                f = f.value
            if chain and chain[0] in ("insert", "append") and len(chain) > 1 and chain[1] == "path":
                continue
            if "path" in chain:            # os.path.dirname / abspath / join
                continue
            if isinstance(f, ast.Name) and f.id in ("str", "Path"):
                continue
            return False
    return True


def _main_guard(stmt):
    if not isinstance(stmt, ast.If):
        return False
    t = stmt.test
    return (isinstance(t, ast.Compare) and isinstance(t.left, ast.Name) and t.left.id == "__name__")


class _Module:
    def __init__(self, path):
        self.path = path
        self.src = path.read_text(errors="replace")
        self.lines = self.src.splitlines()
        self.tree = ast.parse(self.src)
        self.defs, self.assigns, self.imports, self.effects, self.io = {}, {}, {}, [], set()
        for stmt in self.tree.body:
            self._classify(stmt, top=True)

    def _collect_imports(self, stmt):
        for n in ast.walk(stmt):
            if IO_MARK in self.lines[n.lineno - 1] if hasattr(n, "lineno") else False:
                continue                             # a cache or I/O hook: not part of what is computed
            if isinstance(n, ast.Import):
                for a in n.names:
                    self.imports[a.asname or a.name.split(".")[0]] = ("mod", a.name.split(".")[0] if not a.asname else a.name)
            elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                for a in n.names:
                    self.imports[a.asname or a.name] = ("from", n.module.split(".")[0], a.name)

    def _classify(self, stmt, top):
        if isinstance(stmt, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            self.defs[stmt.name] = stmt
            if IO_MARK in self.lines[stmt.lineno - 1]:
                self.io.add(stmt.name)
            return
        if isinstance(stmt, (ast.Import, ast.ImportFrom)):
            self._collect_imports(stmt)
            return
        if isinstance(stmt, (ast.Assign, ast.AnnAssign, ast.AugAssign)):
            targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
            names = [x.id for t in targets for x in ast.walk(t) if isinstance(x, ast.Name)]
            plain = all(isinstance(t, (ast.Name, ast.Tuple, ast.List)) for t in targets)
            if plain and names:                      # reached only when a name is referenced
                for nm in names:
                    self.assigns.setdefault(nm, []).append(stmt)
                return
        if isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant):
            return                                   # the module docstring or a bare string
        if _main_guard(stmt):
            return
        self._collect_imports(stmt)
        if _path_only(stmt, self.src):
            return
        self.effects.append(stmt)


class _Resolver:
    def __init__(self, entry, search_dirs, root):
        self.root = Path(root) if root else None
        self.dirs = [Path(d) for d in search_dirs]
        self.mods = {}
        self.entry = self.load(Path(entry).resolve())

    def load(self, path):
        if path not in self.mods:
            self.mods[path] = _Module(path)
        return self.mods[path]

    def find(self, modname, from_dir):
        for d in [from_dir, *self.dirs]:
            c = (d / f"{modname}.py")
            if c.is_file():
                return c.resolve()
        return None

    def module_alias(self, m, name, seen=None):
        """The repo module a module-level name in m stands for, or None."""
        seen = seen or set()
        if (m.path, name) in seen:
            return None
        seen.add((m.path, name))
        imp = m.imports.get(name)
        if imp:
            if imp[0] == "mod":
                return self.find(imp[1], m.path.parent)
            p = self.find(imp[1], m.path.parent)
            if p:                               # from pkg import submodule-as-attr
                return self.module_alias(self.load(p), imp[2], seen)
            return None
        for stmt in m.assigns.get(name, []):
            if not isinstance(stmt, ast.Assign):
                continue
            for t in stmt.targets:
                pairs = []
                if isinstance(t, ast.Name):
                    pairs = [(t, stmt.value)]
                elif isinstance(t, (ast.Tuple, ast.List)) and isinstance(stmt.value, (ast.Tuple, ast.List)) \
                        and len(t.elts) == len(stmt.value.elts):
                    pairs = list(zip(t.elts, stmt.value.elts))
                for tgt, val in pairs:
                    if isinstance(tgt, ast.Name) and tgt.id == name and isinstance(val, ast.Attribute) \
                            and isinstance(val.value, ast.Name):
                        base = self.module_alias(m, val.value.id, seen)
                        if base:
                            return self.module_alias(self.load(base), val.attr, seen)
        return None


def reach_key(path, entries, search_dirs=(), extra=b"", root=None, trace=None):
    """The key: see the module docstring. `trace`, a list, receives what
    was hashed as (file, kind, symbol, digest) for inspection."""
    R = _Resolver(path, search_dirs, root)
    items, whole, done = [], set(), set()
    work = [(R.entry.path, e) for e in entries]

    # every repo module the entry file imports, transitively: their
    # import-time side effects run whatever the solve reaches
    closure, todo = set(), [R.entry.path]
    while todo:
        p = todo.pop()
        if p in closure:
            continue
        closure.add(p)
        m = R.load(p)
        for imp in m.imports.values():
            q = R.find(imp[1], p.parent)
            if q and q not in closure:
                todo.append(q)
    for p in sorted(closure):
        m = R.load(p)
        for i, st in enumerate(m.effects):
            items.append((p, "effect", str(i), _dump(_strip_docstrings(ast.parse(ast.unparse(st))))))
            work.append((p, ("__stmt__", st)))

    def attr_ref(m, chain):
        """Follow base.a1.a2... through module aliases; queue the first
        non-module attribute, or hash a module reached as a bare value."""
        mod = R.module_alias(m, chain[0])
        if not mod:
            if chain[0] in m.defs or chain[0] in m.assigns or chain[0] in m.imports:
                work.append((m.path, chain[0]))
            return
        for a in chain[1:]:
            nxt = R.module_alias(R.load(mod), a)
            if not nxt:
                work.append((mod, a))
                return
            mod = nxt
        whole.add(mod)

    def refs(m, node, dynamic=True):
        consumed = set()                 # Name nodes already handled as a chain base or a literal getattr
        parent = {id(c): n for n in ast.walk(node) for c in ast.iter_child_nodes(n)}

        def lookup(call):
            """globals()/vars() used to look a name up (indexed, .get,
            .pop, .setdefault), as against copied whole (the fork-pool
            registration idiom `module.__dict__.update(globals())`)."""
            if call.func.id not in ("globals", "vars"):
                return True                  # exec, eval, __import__: always dynamic
            p = parent.get(id(call))
            return (isinstance(p, ast.Subscript) and p.value is call) or \
                (isinstance(p, ast.Attribute) and p.value is call
                 and p.attr in ("get", "pop", "setdefault", "__getitem__"))
        for n in ast.walk(node):
            if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                    and n.func.id in ("getattr", "hasattr", "setattr") and len(n.args) >= 2 \
                    and isinstance(n.args[0], ast.Name):
                if isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                    attr_ref(m, [n.args[0].id, n.args[1].value])
                    consumed.add(id(n.args[0]))
                elif dynamic:
                    modp = R.module_alias(m, n.args[0].id)
                    if modp:
                        whole.add(modp)
                        consumed.add(id(n.args[0]))
            if isinstance(n, ast.Attribute) and not isinstance(getattr(n, "_parent_attr", None), ast.Attribute):
                chain, cur = [], n
                while isinstance(cur, ast.Attribute):
                    chain.append(cur.attr)
                    cur = cur.value
                if isinstance(cur, ast.Name):
                    consumed.add(id(cur))
                    attr_ref(m, [cur.id, *reversed(chain)])
            for c in ast.iter_child_nodes(n):
                if isinstance(n, ast.Attribute) and isinstance(c, ast.Attribute):
                    c._parent_attr = n
        for n in ast.walk(node):
            if isinstance(n, ast.Name) and id(n) not in consumed:
                modp = R.module_alias(m, n.id)
                if modp:
                    whole.add(modp)
                elif n.id in m.defs or n.id in m.assigns or n.id in m.imports:
                    work.append((m.path, n.id))
            elif dynamic and isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                    and n.func.id in _DYNAMIC_CALLS and lookup(n):
                whole.add(m.path)
            elif isinstance(n, ast.Name) and n.id == "importlib":
                whole.add(m.path)

    while work:
        p, sym = work.pop()
        if isinstance(sym, tuple):                 # an import-time statement: follow what it names; the
            refs(R.load(p), sym[1], dynamic=False)  # statement itself is hashed, so its globals() use is seen
            continue
        if (p, sym) in done:
            continue
        done.add((p, sym))
        m = R.load(p)
        if sym in m.io:
            continue
        if sym in m.defs:
            node = m.defs[sym]
            items.append((p, "def", sym, _dump(_strip_docstrings(ast.parse(ast.unparse(node))))))
            refs(m, node)
        elif sym in m.assigns:
            for st in m.assigns[sym]:
                items.append((p, "assign", sym, _dump(ast.parse(ast.unparse(st)))))
                refs(m, st)
        elif sym in m.imports:
            imp = m.imports[sym]
            q = R.find(imp[1], p.parent)
            if q:
                if imp[0] == "mod":
                    whole.add(q)
                else:
                    work.append((q, imp[2]))
    for p in sorted(whole):
        m = R.load(p)
        items.append((p, "whole", "", _dump(_strip_docstrings(ast.parse(m.src)))))

    h = hashlib.sha256(f"py{sys.version_info[0]}.{sys.version_info[1]}".encode())
    base = Path(root).resolve() if root else None
    for p, kind, sym, d in sorted(set(items)):
        rel = str(p.relative_to(base)) if base and base in p.parents else p.name
        if trace is not None:
            trace.append((rel, kind, sym, hashlib.sha256(d.encode()).hexdigest()[:8]))
        h.update(f"\0{rel}\0{kind}\0{sym}\0".encode())
        h.update(d.encode())
    h.update(b"\0extra\0" + (extra if isinstance(extra, bytes) else str(extra).encode()))
    return h.hexdigest()[:16]


def self_check():
    """The properties the key must hold, on synthetic modules: a change the
    solve can see re-keys it, one it cannot see does not. Returns the
    failures (empty when all hold)."""
    import tempfile
    fails = []
    lib = (
        'import helper as h\n'
        'SCALE = 3\n'
        'UNUSED = 9\n'
        'h.PATCHED = 1\n'
        'def solve(x):\n'
        '    """Doc."""\n'
        '    return h.twice(x) * SCALE + getattr(h, "BIAS")\n'
        'def emit():\n'
        '    return str(solve(1))\n'
        'def load():  ' + IO_MARK + '\n'
        '    return None\n'
    )
    helper = (
        'BIAS = 1\n'
        'def twice(x):\n'
        '    return 2 * x\n'
        'def unrelated():\n'
        '    return 0\n'
    )
    variants = [
        ("a comment in the solve", "lib", lambda s: s.replace("return h.twice", "# note\n    return h.twice"), False),
        ("a docstring in the solve", "lib", lambda s: s.replace('"""Doc."""', '"""Other."""'), False),
        ("an emitter the solve never calls", "lib", lambda s: s.replace("str(solve(1))", "str(solve(2))"), False),
        ("an unused constant", "lib", lambda s: s.replace("UNUSED = 9", "UNUSED = 8"), False),
        ("an I/O-marked loader", "lib", lambda s: s.replace("return None", "return 1"), False),
        ("a function the solve never calls, in another module", "helper", lambda s: s.replace("return 0", "return 1"), False),
        ("a constant the solve reads", "lib", lambda s: s.replace("SCALE = 3", "SCALE = 4"), True),
        ("a function the solve calls, in another module", "helper", lambda s: s.replace("2 * x", "3 * x"), True),
        ("a constant read through getattr with a literal name", "helper", lambda s: s.replace("BIAS = 1", "BIAS = 2"), True),
        ("an import-time patch", "lib", lambda s: s.replace("h.PATCHED = 1", "h.PATCHED = 2"), True),
    ]
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        def key(files):
            for n, src in files.items():
                (d / f"{n}.py").write_text(src)
            return reach_key(d / "lib.py", ["solve"], [str(d)])
        base = key({"lib": lib, "helper": helper})
        for what, mod, edit, should in variants:
            files = {"lib": lib, "helper": helper}
            files[mod] = edit(files[mod])
            if files[mod] == {"lib": lib, "helper": helper}[mod]:
                fails.append(f"test edit did not apply: {what}")
                continue
            moved = key(files) != base
            if moved != should:
                fails.append(f"{what}: the key {'moved' if moved else 'held'}, it should have "
                             f"{'moved' if should else 'held'}")
        if key({"lib": lib, "helper": helper}) != base:
            fails.append("the key is not reproducible")
    return fails


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser(description="Print the reach key of entry functions in a file.")
    ap.add_argument("path")
    ap.add_argument("entries", nargs="+")
    ap.add_argument("--dir", action="append", default=[], help="a search directory (repeatable)")
    ap.add_argument("--trace", action="store_true", help="list what is hashed")
    if sys.argv[1:] == ["--self-check"]:
        f = self_check()
        print(f"self_check: {'PASS' if not f else f}")
        sys.exit(1 if f else 0)
    a = ap.parse_args()
    tr = [] if a.trace else None
    print(reach_key(a.path, a.entries, a.dir, trace=tr))
    for t in tr or []:
        print("  ", *t)
