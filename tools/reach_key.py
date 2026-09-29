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

A class is followed the same way, one method at a time: reaching a class
hashes its shell (bases, decorators, class-level assignments and fields),
and a method is hashed only when reached code names an attribute of that
name (`row.price()`, `self.price`, `getattr(row, "price")`), since that is
the only way a method runs. Dunder methods are always hashed, because
operators and the interpreter call them without naming them. So an edit to a
pricing method re-keys a sizing solve only if the sizing code can call it.

Where it cannot follow, it widens rather than narrows:

* a module used as a bare value (passed to a function, aliased through a
  structure the resolver does not follow) is hashed whole;
* a reached definition that calls `getattr` on a module with a non-literal
  name, looks a name up through `globals()` or `vars()` (indexed, or with
  `.get`/`.pop`/`.setdefault`), or uses `exec`, `eval`, `__import__` or
  `importlib`, has its whole module hashed; copying a namespace whole
  (`module.__dict__.update(globals())`, the fork-pool registration idiom)
  is not a lookup, and neither is a module-level load by path
  (`importlib.util.spec_from_file_location(name, HERE / "engine.py")`,
  the host-shim idiom): that hashes the file it loads whole and follows
  the loader name by name, so a name added to a shim re-keys nothing that
  never reads it (a path its string constants do not spell falls back to
  hashing the loader whole);
* a `getattr`/`hasattr`/`setattr` with a non-literal name on anything but
  a module, or an `operator.attrgetter`/`methodcaller` with a non-literal
  name, hashes every method of every reached class;
* the attribute names used anywhere in a module hashed whole count as
  referenced, so a method it calls is hashed;
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

Early cutoff: `stop` names functions in the entry file whose code is not
followed, because the caller hashes what they RETURN into `extra` instead.
Use it where one memo feeds another: a solve that consumes another solve's
choice keys on the choice, so an edit that re-solves the first without
changing its answer does not re-solve the second.

    key = reach_key(path, ["wing_solve"], extra=repr(best_engines()).encode(),
                    stop=["best_engines"])

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


_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _class_shell(node):
    """A fresh copy of a class definition with its methods removed: what
    runs when the class is defined, without what runs only when a method
    is called."""
    c = ast.parse(ast.unparse(node)).body[0]
    body = []
    for b in c.body:
        if isinstance(b, _FUNCS):
            # the method's decorators run when the class is defined; its
            # body runs only when called, so a stub stands in for it
            b.body = [ast.Pass()]
            b.returns = None
        body.append(b)
    c.body = body or [ast.Pass()]
    return c


_PLAIN_DECORATORS = {"property", "staticmethod", "classmethod", "cached_property", "setter", "getter",
                     "deleter", "abstractmethod", "wraps", "lru_cache", "cache"}


def _registered_methods(node):
    """Methods under a decorator that is not one of the plain ones: such a
    decorator can hand the function to something that calls it by a name
    the code never writes (a registry keyed by name)."""
    out = set()
    for b in node.body:
        if isinstance(b, _FUNCS):
            for d in b.decorator_list:
                f = d.func if isinstance(d, ast.Call) else d
                name = f.attr if isinstance(f, ast.Attribute) else getattr(f, "id", "")
                if name not in _PLAIN_DECORATORS:
                    out.add(b.name)
    return out


def _class_body_names(node):
    """Names the class body uses outside its methods' bodies (class-level
    statements, method decorators): a method named there runs without being
    named as an attribute (`area = property(_area)`, `cost = price`)."""
    out = set()
    for b in node.body:
        parts = b.decorator_list if isinstance(b, _FUNCS) else [b]
        for part in parts:
            out |= {n.id for n in ast.walk(part) if isinstance(n, ast.Name)}
    return out


def _external_base(R, m, node):
    """A base class outside the repository (json.JSONEncoder, Thread, dict,
    Enum): its machinery calls methods by names the repository's code never
    writes (`default`, `run`, `_missing_`), so every method counts."""
    for b in node.bases:
        root = b
        while isinstance(root, ast.Attribute):
            root = root.value
        if isinstance(b, ast.Name) and b.id == "object":
            continue
        if isinstance(root, ast.Name) and (root.id in m.defs or R.module_alias(m, root.id)
                                            or (root.id in m.imports
                                                and R.find(m.imports[root.id][1], m.path.parent))):
            continue
        return True
    return False


def _methods(node, name):
    return [b for b in node.body if isinstance(b, _FUNCS) and b.name == name]


def _dunder(name):
    return name.startswith("__") and name.endswith("__")


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
        self.dumps = {}
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


_PARSED = {}                      # path -> (content hash, _Module): parsed once per process per content


def _parsed(path):
    sig = hashlib.sha256(path.read_bytes()).digest()
    hit = _PARSED.get(path)
    if hit is None or hit[0] != sig:
        hit = (sig, _Module(path))
        _PARSED[path] = hit
    return hit[1]


def _digest(m, kind, sym, node):
    """The hashed form of one definition, memoised on its parsed module (a
    caller keying many entry points in one process re-parses nothing)."""
    k = (kind, sym, id(node))
    d = m.dumps.get(k)
    if d is None:
        if kind in ("assign",):
            d = _dump(ast.parse(ast.unparse(node)))
        else:
            d = _dump(_strip_docstrings(ast.parse(ast.unparse(node))))
        m.dumps[k] = d
    return d


class _Resolver:
    def __init__(self, entry, search_dirs, root):
        self.root = Path(root) if root else None
        self.dirs = [Path(d) for d in search_dirs]
        self.mods = {}
        self.entry = self.load(Path(entry).resolve())

    def load(self, path):
        if path not in self.mods:
            self.mods[path] = _parsed(path)
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


# A session shares work across many keys computed over unchanged files (a
# gate keying hundreds of blocks in one process): what each definition
# names, and where each import resolves, is worked out once. Opt-in, and
# only valid while no file changes -- begin_session() / end_session().
_SESSION = None


def begin_session():
    global _SESSION
    _SESSION = {}


def end_session():
    global _SESSION
    _SESSION = None


def _refs_record(R, m, node, dynamic):
    """What one definition names: (work, whole, attrs, widen) -- the
    definitions and statements to follow, the modules to hash whole, the
    attribute names used, and whether an attribute is looked up by a
    computed name."""
    work, whole, attrs, widen = [], set(), set(), [False]
    loads, loaded = _path_loads(R, m, node)
    whole |= loaded
    loads |= _param_loader_names(node)       # a helper that loads the path its caller names
    for n in ast.walk(node):
        # a call to such a helper: the file its caller names is what loads
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in m.defs \
                and _param_loader_names(m.defs[n.func.id]):
            hit = _resolve_rel(R, m, n.args[0]) if n.args else None
            whole.add(hit if hit is not None else _EVERY_MODULE)
    local = _locals(node)            # a name bound in a function is local throughout it
    outer = _outer_scope_ids(node)   # defaults, decorators, annotations: evaluated outside it

    def is_local(name, nid):
        return name in local and nid not in outer
    lazy = _lazy_imports(R, m, node)  # `import x as q` inside the function: q is module x

    def attr_ref(chain, nid=None):
        """Follow base.a1.a2... through module aliases; queue the first
        non-module attribute, or hash a module reached as a bare value."""
        if chain[0] in lazy and not is_local(chain[0], nid):
            mod = lazy[chain[0]]
            if isinstance(mod, tuple):           # `from x import name`, then name.attr
                work.append(mod)
                return
        else:
            mod = None if is_local(chain[0], nid) else R.module_alias(m, chain[0])
        if not mod:
            if is_local(chain[0], nid):
                return
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
        if isinstance(n, ast.Attribute):
            attrs.add(n.attr)
        if isinstance(n, ast.Call):
            fname = n.func.id if isinstance(n.func, ast.Name) else \
                n.func.attr if isinstance(n.func, ast.Attribute) else ""
            if fname in ("attrgetter", "methodcaller"):
                lits = [a.value for a in n.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
                attrs.update(x for lit in lits for x in lit.split("."))
                if fname == "attrgetter" and len(lits) < len(n.args) or fname == "methodcaller" and not (
                        n.args and isinstance(n.args[0], ast.Constant)):
                    widen[0] = True
            if isinstance(n.func, ast.Name) and n.func.id in ("getattr", "hasattr", "setattr") \
                    and len(n.args) >= 2:
                literal = isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str)
                if literal:
                    attrs.add(n.args[1].value)
                elif not (isinstance(n.args[0], ast.Name) and not is_local(n.args[0].id, id(n.args[0]))
                          and R.module_alias(m, n.args[0].id)):
                    widen[0] = True          # an object's attribute by computed name: any method may run
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id in ("getattr", "hasattr", "setattr") and len(n.args) >= 2 \
                and isinstance(n.args[0], ast.Name):
            if isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                attr_ref([n.args[0].id, n.args[1].value], id(n.args[0]))
                consumed.add(id(n.args[0]))
            elif dynamic and not is_local(n.args[0].id, id(n.args[0])):
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
                attr_ref([cur.id, *reversed(chain)], id(cur))
        for c in ast.iter_child_nodes(n):
            if isinstance(n, ast.Attribute) and isinstance(c, ast.Attribute):
                c._parent_attr = n
    for n in ast.walk(node):
        if isinstance(n, ast.Name) and id(n) not in consumed and n.id in lazy and not is_local(n.id, id(n)):
            target = lazy[n.id]
            if isinstance(target, tuple):
                work.append(target)
            else:
                whole.add(target)            # the lazily imported module used as a bare value
            continue
        if isinstance(n, ast.Name) and id(n) not in consumed and is_local(n.id, id(n)):
            continue
        if isinstance(n, ast.Name) and id(n) not in consumed:
            modp = R.module_alias(m, n.id)
            if modp:
                whole.add(modp)
            elif n.id in m.defs or n.id in m.assigns or n.id in m.imports:
                work.append((m.path, n.id))
        elif dynamic and isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                and n.func.id in _DYNAMIC_CALLS and lookup(n):
            whole.add(m.path)
        elif isinstance(n, ast.Name) and n.id == "importlib" and id(n) not in loads:
            whole.add(m.path)
            whole.add(_EVERY_MODULE)     # it may load a file the text does not name
    return work, whole, attrs, widen[0]


def _locals(node):
    """The names local to a function: its parameters and every name it
    binds (assignment, loop target, `with ... as`, `except ... as`,
    nested def or class), less those it declares global or nonlocal. A
    name bound by an import inside the function is left out: it is a
    module, and the resolver follows it as one. Python makes such a name local throughout the function, so
    a local that happens to share a module alias's name (`bp = dict(...)`
    beside `import battery_pod as bp`) is not the module. Nested functions
    and comprehensions keep their own scopes and are not counted here."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        return frozenset()
    names, declared = set(), set()
    a = node.args
    for arg in a.posonlyargs + a.args + a.kwonlyargs + [x for x in (a.vararg, a.kwarg) if x]:
        names.add(arg.arg)
    body = node.body if isinstance(node.body, list) else [node.body]
    stack = list(body)
    while stack:
        n = stack.pop()
        if isinstance(n, (ast.Global, ast.Nonlocal)):
            declared.update(n.names)
        elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.add(n.name)
            stack.extend(n.decorator_list)
            continue                  # its body is its own scope
        elif isinstance(n, (ast.Lambda, ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
            continue
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            names.add(n.id)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            names.add(n.name)
        elif isinstance(n, ast.NamedExpr) and isinstance(n.target, ast.Name):
            names.add(n.target.id)
        stack.extend(ast.iter_child_nodes(n))
    # a name a nested function declares global is the module's there, and the
    # outer set filters the whole tree: never treat it as local (over-broad)
    declared |= {x for n in ast.walk(node) if isinstance(n, (ast.Global, ast.Nonlocal)) for x in n.names}
    return frozenset(names - declared)


def _outer_scope_ids(node):
    """ids of the Name nodes a function evaluates in its enclosing scope:
    its parameter defaults, decorators and annotations. A parameter named
    like a module constant (`def drag(q, S=S)`) is local inside the body,
    and the module's `S` in the default."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
        return frozenset()
    a = node.args
    parts = list(a.defaults) + [d for d in a.kw_defaults if d is not None]
    if not isinstance(node, ast.Lambda):
        parts += list(node.decorator_list) + ([node.returns] if node.returns else [])
        parts += [x.annotation for x in a.posonlyargs + a.args + a.kwonlyargs + [y for y in (a.vararg, a.kwarg) if y]
                  if x.annotation is not None]
    return frozenset(id(n) for part in parts for n in ast.walk(part) if isinstance(n, ast.Name))


def _lazy_imports(R, m, node):
    """Imports inside a function: local name -> the repository module it
    binds (`import x as q`), or -> (module, name) for `from x import name`.
    Module-level imports are the resolver's; these would otherwise not be
    followed at all, and a solve that imports a model lazily would not
    re-key when that model changed."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return {}
    out = {}
    for n in ast.walk(node):
        if IO_MARK in m.lines[n.lineno - 1] if hasattr(n, "lineno") and n.lineno <= len(m.lines) else False:
            continue
        if isinstance(n, ast.Import):
            for a in n.names:
                p = R.find(a.name.split(".")[0] if not a.asname else a.name, m.path.parent)
                if p:
                    out[a.asname or a.name.split(".")[0]] = p
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            p = R.find(n.module.split(".")[0], m.path.parent)
            if p:
                for a in n.names:
                    out[a.asname or a.name] = (p, a.name)   # x is a flat module: name is in it
    return out


def _all_imports(R, m):
    """Every repository module m imports, at module level or inside a
    function: a lazily imported module's import-time effects run when the
    function that imports it does."""
    out = set()
    for imp in m.imports.values():
        q = R.find(imp[1], m.path.parent)
        if q:
            out.add(q)
    for n in ast.walk(m.tree):
        if hasattr(n, "lineno") and n.lineno <= len(m.lines) and IO_MARK in m.lines[n.lineno - 1]:
            continue
        if isinstance(n, ast.Import):
            for a in n.names:
                q = R.find(a.name.split(".")[0], m.path.parent)
                if q:
                    out.add(q)
        elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
            q = R.find(n.module.split(".")[0], m.path.parent)
            if q:
                out.add(q)
    return out


def _is_path_load_exec(st):
    """`spec.loader.exec_module(module)`: the statement that runs a module
    loaded by path (the host-shim idiom). It runs that file into the module
    object it names and nothing else, so it is not counted as an import-time
    effect of the loader: the loaded file is hashed when reached code uses
    the name it was bound to (see _path_loads). A file that patches other
    modules as it loads would escape this; the host shims do not."""
    return (isinstance(st, ast.Expr) and isinstance(st.value, ast.Call)
            and isinstance(st.value.func, ast.Attribute) and st.value.func.attr == "exec_module"
            and isinstance(st.value.func.value, ast.Attribute) and st.value.func.value.attr == "loader"
            and len(st.value.args) == 1 and isinstance(st.value.args[0], ast.Name))


_EVERY_MODULE = Path("/__every_repository_module__")


def _param_loader_names(node):
    """For a function that loads, by spec_from_file_location, a path built
    from one of its own parameters (`def _load(rel): ... ROOT / rel`): the
    importlib Name nodes of that load, which its call sites resolve. Empty
    for anything else."""
    if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return set()
    a = node.args
    params = {x.arg for x in a.posonlyargs + a.args + a.kwonlyargs}
    out = set()
    for n in ast.walk(node):
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr in ("spec_from_file_location", "module_from_spec"):
            base = n.func.value
            while isinstance(base, ast.Attribute):
                base = base.value
            if not (isinstance(base, ast.Name) and base.id == "importlib"):
                continue
            if n.func.attr == "spec_from_file_location" and not (
                    len(n.args) >= 2 and any(isinstance(x, ast.Name) and x.id in params
                                             for x in ast.walk(n.args[1]))):
                return set()                 # a load its callers do not name
            out.add(id(base))
    return out


def _resolve_rel(R, m, arg):
    """A repository file named by a string constant, relative to the root,
    the module's directory or one of its parents; None when it is not a
    constant or names no file."""
    if not (isinstance(arg, ast.Constant) and isinstance(arg.value, str) and arg.value.endswith(".py")):
        return None
    rel = Path(arg.value)
    for b in ([R.root] if R.root else []) + [m.path.parent] + list(m.path.parents):
        if (b / rel).is_file():
            return (b / rel).resolve()
    return None


def _spelled_tail(expr):
    """The part of a spelled path whose constants name the file: the whole
    `BASE / "a" / "b.py"`, or the constant arguments of an os.path.join."""
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr == "join":
        return ast.Tuple(elts=list(expr.args[1:]), ctx=ast.Load())
    return expr


def _path_spelled(expr):
    """A path whose every segment after its base is a string constant:
    `BASE / "a" / "b.py"` (the base may be anything: ROOT, HERE,
    Path(__file__).parent). A variable segment anywhere else means the file
    cannot be named from the text."""
    if isinstance(expr, ast.Call) and isinstance(expr.func, ast.Attribute) and expr.func.attr == "join":
        # os.path.join(BASE, "a", "b.py"): every argument after the base a constant
        return len(expr.args) >= 2 and all(isinstance(x, ast.Constant) and isinstance(x.value, str)
                                           for x in expr.args[1:])
    base = expr
    while isinstance(base, ast.BinOp) and isinstance(base.op, ast.Div):
        if not (isinstance(base.right, ast.Constant) and isinstance(base.right.value, str)):
            return isinstance(expr, ast.Constant) and isinstance(expr.value, str)
        base = base.left
    return base is not expr or (isinstance(expr, ast.Constant) and isinstance(expr.value, str))


def _path_loads(R, m, node):
    """A module-level statement that loads a repository file by path
    (`importlib.util.spec_from_file_location(name, ROOT / "a" / "b.py")`,
    or `module_from_spec` on such a spec) is a load, not a lookup: it can
    run only the file it names. Returns (the importlib Name nodes it
    accounts for, the files to hash whole). A path that cannot be resolved
    from its string constants is left to the caller, who hashes the module
    whole as before."""
    if isinstance(node, ast.ClassDef):
        return set(), set()
    names, files = set(), set()
    for n in ast.walk(node):
        if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr in ("spec_from_file_location", "module_from_spec", "import_module")):
            continue
        base = n.func.value
        while isinstance(base, ast.Attribute):
            base = base.value
        if not (isinstance(base, ast.Name) and base.id == "importlib"):
            continue
        if n.func.attr == "import_module":
            arg = n.args[0] if n.args else None
            hit = R.find(arg.value, m.path.parent) if isinstance(arg, ast.Constant) and isinstance(arg.value, str) \
                and "." not in arg.value else None
            if hit is None:
                continue
            files.add(hit.resolve())
        elif n.func.attr == "spec_from_file_location":
            if len(n.args) < 2:
                continue
            expr = n.args[1]
            if isinstance(expr, ast.Name):
                # the path held in a local the function assigns once
                bound = [st.value for st in ast.walk(node) if isinstance(st, ast.Assign)
                         and len(st.targets) == 1 and isinstance(st.targets[0], ast.Name)
                         and st.targets[0].id == expr.id]
                if len(bound) != 1:
                    continue
                expr = bound[0]
            if not _path_spelled(expr):
                continue
            parts = [c.value for c in sorted(
                (c for c in ast.walk(_spelled_tail(expr)) if isinstance(c, ast.Constant) and isinstance(c.value, str)),
                key=lambda c: (c.lineno, c.col_offset))]              # source order, not walk order
            if not parts or not parts[-1].endswith(".py"):
                continue
            rel = Path(*[q for part in parts for q in part.split("/") if q])
            bases = ([R.root] if R.root else []) + list(m.path.parents)
            hit = next((b / rel for b in bases if (b / rel).is_file()), None)
            if hit is None:
                continue
            files.add(hit.resolve())
        names.add(id(base))
    return names, files


def reach_key(path, entries, search_dirs=(), extra=b"", root=None, trace=None, stop=(), files=None):
    """The key: see the module docstring. `trace`, a list, receives what
    was hashed as (file, kind, symbol, digest) for inspection. `files`, a
    set, receives every repository module the key accounts for: the static
    import closure (whatever of it can run is hashed, and the rest cannot
    change a result) plus every module hashed in part or whole."""
    R = _Resolver(path, search_dirs, root)
    items, whole, done = [], set(), {(R.entry.path, s) for s in stop}
    classes, attrs, widen = [], set(), [False]   # reached classes; attribute names used; dynamic attribute access seen
    work = [(R.entry.path, e) for e in entries]
    dirs_key = tuple(str(d) for d in R.dirs) + (str(R.root),)

    # every repo module the entry file imports, transitively: their
    # import-time side effects run whatever the solve reaches
    ck = ("closure", R.entry.path, dirs_key)
    closure = _SESSION.get(ck) if _SESSION is not None else None
    if closure is None:
        closure, todo = set(), [R.entry.path]
        while todo:
            p = todo.pop()
            if p in closure:
                continue
            closure.add(p)
            m = R.load(p)
            for q in _all_imports(R, m):
                if q not in closure:
                    todo.append(q)
        if _SESSION is not None:
            _SESSION[ck] = closure
    for p in sorted(closure):
        m = R.load(p)
        for i, st in enumerate(m.effects):
            if _is_path_load_exec(st):
                continue          # followed through the name it binds, when that is reached
            items.append((p, "effect", str(i), _digest(m, "effect", str(i), st)))
            work.append((p, ("__stmt__", st)))

    def used_attrs(tree):
        """The attribute names a module hashed whole can use, without
        following it: enough to hash the methods it can call."""
        for n in ast.walk(tree):
            if isinstance(n, ast.Attribute):
                attrs.add(n.attr)
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Name) \
                    and n.func.id in ("getattr", "hasattr", "setattr") and len(n.args) >= 2:
                if isinstance(n.args[1], ast.Constant) and isinstance(n.args[1].value, str):
                    attrs.add(n.args[1].value)
                else:
                    widen[0] = True

    def refs(m, node, dynamic=True):
        k = (m, id(node), dynamic, dirs_key)
        rec = _SESSION.get(k) if _SESSION is not None else None
        if rec is None:
            rec = _refs_record(R, m, node, dynamic)
            if _SESSION is not None:
                _SESSION[k] = rec
        work.extend(rec[0])
        whole.update(rec[1])
        if _EVERY_MODULE in whole:
            # a load the text does not name: every module it could be counts
            whole.discard(_EVERY_MODULE)
            for d in R.dirs:
                whole.update(q.resolve() for q in Path(d).rglob("*.py") if "__pycache__" not in q.parts)
        attrs.update(rec[2])
        if rec[3]:
            widen[0] = True

    def drain():
        while work:
            p, sym = work.pop()
            if isinstance(sym, tuple) and sym[0] == "__method__":
                _, cls, name = sym
                if (p, f"{cls}.{name}") in done:
                    continue
                done.add((p, f"{cls}.{name}"))
                m = R.load(p)
                for node in _methods(m.defs[cls], name):
                    items.append((p, "method", f"{cls}.{name}", _digest(m, "method", f"{cls}.{name}", node)))
                    refs(m, node)
                continue
            if isinstance(sym, tuple):                 # an import-time statement: follow what it names; the
                refs(R.load(p), sym[1], dynamic=False)  # statement itself is hashed, so its globals() use is seen
                continue
            if (p, sym) in done:
                continue
            done.add((p, sym))
            m = R.load(p)
            if sym in m.io:
                continue
            if sym in m.defs and isinstance(m.defs[sym], ast.ClassDef):
                shell = m.dumps.get(("shell", sym))
                if shell is None:
                    shell = m.dumps[("shell", sym)] = _strip_docstrings(_class_shell(m.defs[sym]))
                items.append((p, "class", sym, _digest(m, "class", sym, shell)))
                refs(m, shell)
                classes.append((p, sym))
            elif sym in m.defs:
                node = m.defs[sym]
                items.append((p, "def", sym, _digest(m, "def", sym, node)))
                refs(m, node)
            elif sym in m.assigns:
                for st in m.assigns[sym]:
                    items.append((p, "assign", sym, _digest(m, "assign", sym, st)))
                    refs(m, st)
            elif sym in m.imports:
                imp = m.imports[sym]
                q = R.find(imp[1], p.parent)
                if q:
                    if imp[0] == "mod":
                        whole.add(q)
                    else:
                        work.append((q, imp[2]))

    # a method runs only when something names it, so the reached classes'
    # methods are added to a fixed point: each hashed method can name more
    seen_whole = set()
    while True:
        drain()
        for p in sorted(whole - seen_whole):        # names used in a module hashed whole count too
            seen_whole.add(p)
            used_attrs(R.load(p).tree)
        more = False
        for p, cls in classes:
            cnode = R.load(p).defs[cls]
            named = _class_body_names(cnode) | _registered_methods(cnode)
            external = _external_base(R, R.load(p), cnode)
            for b in cnode.body:
                if isinstance(b, _FUNCS) and (p, f"{cls}.{b.name}") not in done \
                        and (widen[0] or external or _dunder(b.name) or b.name in attrs or b.name in named):
                    work.append((p, ("__method__", cls, b.name)))
                    more = True
        if not more and not work:
            break
    for p in sorted(whole):
        m = R.load(p)
        items.append((p, "whole", "", _digest(m, "whole", "", m.tree)))

    h = hashlib.sha256(f"py{sys.version_info[0]}.{sys.version_info[1]}".encode())
    base = Path(root).resolve() if root else None
    if files is not None:
        for p in set(closure) | {i[0] for i in items} | set(whole):
            files.add(str(p.relative_to(base)) if base and base in p.parents else p.name)
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

    # classes: a method is hashed only when reached code can call it
    rows = (
        'class Row:\n'
        '    SPAN = 2\n'
        '    def __init__(self, m):\n'
        '        self.m = m\n'
        '    def size(self):\n'
        '        return self.m * self.SPAN + self.helper()\n'
        '    def helper(self):\n'
        '        return 1\n'
        '    def price(self):\n'
        '        return self.m * 10\n'
        'def sizing():\n'
        '    return Row(3).size()\n'
        'def pricing(col):\n'
        '    return getattr(Row(3), col)()\n'
    )
    cases = [
        ("a method the solve never names", "sizing", lambda s: s.replace("self.m * 10", "self.m * 11"), False),
        ("a method the solve calls", "sizing", lambda s: s.replace("self.m * self.SPAN", "self.m * self.SPAN * 2"), True),
        ("a method reached through another method", "sizing", lambda s: s.replace("return 1", "return 2"), True),
        ("a class-level constant", "sizing", lambda s: s.replace("SPAN = 2", "SPAN = 3"), True),
        ("the constructor", "sizing", lambda s: s.replace("self.m = m", "self.m = m + 1"), True),
        ("any method, under an attribute looked up by computed name", "pricing",
         lambda s: s.replace("self.m * 10", "self.m * 11"), True),
    ]
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        def ckey(src, entry):
            (d / "rows.py").write_text(src)
            return reach_key(d / "rows.py", [entry], [str(d)])
        # early cutoff: a stopped function's code is left to the caller, who hashes its result
        (d / "rows.py").write_text(rows)
        a = reach_key(d / "rows.py", ["sizing"], [str(d)], stop=["Row"])
        (d / "rows.py").write_text(rows.replace("SPAN = 2", "SPAN = 3"))
        if reach_key(d / "rows.py", ["sizing"], [str(d)], stop=["Row"]) != a:
            fails.append("stop: an edit inside a stopped name moved the key")
        for what, entry, edit, should in cases:
            moved = ckey(edit(rows), entry) != ckey(rows, entry)
            if moved != should:
                fails.append(f"class, {what}: the key {'moved' if moved else 'held'}, it should have "
                             f"{'moved' if should else 'held'}")
    # the review's cases (2026-09-29): each edit is one the solve can see
    H = "def twice(x):\n    return 2 * x\ndef deco(f):\n    return f\n"
    must_move = [
        ("a parameter default names a module constant (S=S)",
         {"lib.py": "S = 2.0\ndef drag(q, S=S):\n    return q * S\ndef solve():\n    return drag(3)\n"},
         "lib.py", ("lib.py", "S = 2.0", "S = 3.0")),
        ("a decorator names a module a parameter shadows",
         {"helper.py": H.replace("return f", "return lambda *a: f(*a)"),
          "lib.py": "import helper as h\n@h.deco\ndef solve(h):\n    return h\n"},
         "lib.py", ("helper.py", "lambda *a: f(*a)", "lambda *a: 0")),
        ("a computed getattr on a local named like a module",
         {"helper.py": H, "lib.py": "import helper as h\nclass Row:\n    def price(self):\n        return 1\n"
                                    "def solve(col):\n    h = Row()\n    return getattr(h, col)()\n"},
         "lib.py", ("lib.py", "return 1", "return 2")),
        ("a method reached through property()",
         {"lib.py": "class Row:\n    def _area(self):\n        return 1\n    area = property(_area)\n"
                    "def solve():\n    return Row().area\n"},
         "lib.py", ("lib.py", "return 1", "return 2")),
        ("a method a standard-library base calls (JSONEncoder.default)",
         {"lib.py": "import json\nclass Enc(json.JSONEncoder):\n    def default(self, o):\n        return 1\n"
                    "def solve():\n    return json.dumps(object(), cls=Enc)\n"},
         "lib.py", ("lib.py", "return 1", "return 2")),
        ("a method a registering decorator hands out",
         {"lib.py": "REG = {}\ndef reg(f):\n    REG[f.__name__] = f\n    return f\nclass Row:\n    @reg\n"
                    "    def price(self):\n        return 1\ndef solve():\n    return REG['price'](Row())\n"},
         "lib.py", ("lib.py", "return 1\ndef solve", "return 2\ndef solve")),
        ("a lazily imported module's import-time effects",
         {"tab.py": "T = {}\nfor i in range(3):\n    T[i] = i * 2\n",
          "lib.py": "def solve():\n    import tab\n    return tab.T[2]\n"},
         "lib.py", ("tab.py", "i * 2", "i * 3")),
        ("a nested function's global against an outer local",
         {"helper.py": H, "lib.py": "import helper as h\ndef solve(x):\n    h = 1\n    def g():\n        global h\n"
                                    "        return h.twice(x)\n    return g()\n"},
         "lib.py", ("helper.py", "2 * x", "3 * x")),
        ("a load by path with a variable segment",
         {"v2/eng.py": "def f():\n    return 1\n",
          "lib.py": "import importlib.util\nfrom pathlib import Path\nV = 'v2'\n"
                    "_s = importlib.util.spec_from_file_location('e', Path(__file__).parent / V / 'eng.py')\n"
                    "E = importlib.util.module_from_spec(_s)\n_s.loader.exec_module(E)\n"
                    "def solve():\n    return E.f()\n"},
         "lib.py", ("v2/eng.py", "return 1", "return 2")),
        ("a loader helper called with a constant path",
         {"eng.py": "def f():\n    return 1\n",
          "lib.py": "import importlib.util\nfrom pathlib import Path\nROOT = Path(__file__).parent\n"
                    "def _load(rel):\n    s = importlib.util.spec_from_file_location('x', ROOT / rel)\n"
                    "    m = importlib.util.module_from_spec(s)\n    s.loader.exec_module(m)\n    return m\n"
                    "E = _load('eng.py')\ndef solve():\n    return E.f()\n"},
         "lib.py", ("eng.py", "return 1", "return 2")),
        ("a path held in a local, built with os.path.join",
         {"eng.py": "def f():\n    return 1\n",
          "lib.py": "import importlib.util, os\ndef solve():\n"
                    "    path = os.path.join(os.path.dirname(__file__), 'eng.py')\n"
                    "    s = importlib.util.spec_from_file_location('x', path)\n"
                    "    m = importlib.util.module_from_spec(s)\n    s.loader.exec_module(m)\n    return m.f()\n"},
         "lib.py", ("eng.py", "return 1", "return 2")),
    ]
    for what, files, entry, (fn, old_t, new_t) in must_move:
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            for n, t in files.items():
                (d / n).parent.mkdir(parents=True, exist_ok=True)
                (d / n).write_text(t)
            a = reach_key(d / entry, ["solve"], [str(d)], root=d)
            (d / fn).write_text((d / fn).read_text().replace(old_t, new_t))
            if reach_key(d / entry, ["solve"], [str(d)], root=d) == a:
                fails.append(f"{what}: an edit the solve can see held the key")
    with tempfile.TemporaryDirectory() as td:
        # a local that shares a module alias's name is the local, not the
        # module: an edit to the module's unreached code holds the key, and
        # a lazy import inside a function is still followed
        d = Path(td)
        (d / "pod.py").write_text("def mass():\n    return 3\ndef price():\n    return 9\n")
        solver = ("import pod as bp\n"
                  "def solve(x):\n    bp = {'m': x}\n    return bp['m']\n"
                  "def lazy():\n    import pod as q\n    return q.mass()\n")
        (d / "solver.py").write_text(solver)
        a = reach_key(d / "solver.py", ["solve"], [str(d)], root=d)
        b = reach_key(d / "solver.py", ["lazy"], [str(d)], root=d)
        (d / "pod.py").write_text("def mass():\n    return 4\ndef price():\n    return 9\n")
        if reach_key(d / "solver.py", ["solve"], [str(d)], root=d) != a:
            fails.append("a local named like a module alias hashed the module")
        if reach_key(d / "solver.py", ["lazy"], [str(d)], root=d) == b:
            fails.append("a lazy import inside a function was not followed")
    with tempfile.TemporaryDirectory() as td:
        # a shim that loads its engine by path: the shim is followed name by
        # name and the engine hashed whole, so a new name in the shim that
        # the solve never reads leaves the key alone
        d = Path(td)
        (d / "eng").mkdir()
        (d / "eng" / "fmt_engine.py").write_text("class Qty:\n    def __call__(self, v):\n        return str(v)\n")
        shim = ('import importlib.util\nfrom pathlib import Path\nHERE = Path(__file__).resolve().parent\n'
                '_spec = importlib.util.spec_from_file_location("fe", HERE / "eng" / "fmt_engine.py")\n'
                'engine = importlib.util.module_from_spec(_spec)\n_spec.loader.exec_module(engine)\n'
                'KW = engine.Qty()\n')
        (d / "fmt.py").write_text(shim)
        (d / "solver.py").write_text("import fmt\ndef solve(x):\n    return fmt.KW(x)\n")
        a = reach_key(d / "solver.py", ["solve"], [str(d)], root=d)
        (d / "fmt.py").write_text(shim + "NEW = engine.Qty()\n")
        if reach_key(d / "solver.py", ["solve"], [str(d)], root=d) != a:
            fails.append("load by path: a name added to the loader, never read, moved the key")
        (d / "other.py").write_text("import fmt\ndef solve(x):\n    return x + 1\n")
        c = reach_key(d / "other.py", ["solve"], [str(d)], root=d)
        (d / "eng" / "fmt_engine.py").write_text("class Qty:\n    def __call__(self, v):\n        return repr(v)\n")
        if reach_key(d / "solver.py", ["solve"], [str(d)], root=d) == a:
            fails.append("load by path: an edit to the loaded file held the key")
        if reach_key(d / "other.py", ["solve"], [str(d)], root=d) != c:
            fails.append("load by path: a solve that imports the loader but uses none of it re-keyed "
                         "when the loaded file changed")
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
