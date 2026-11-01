#!/usr/bin/env python3
"""Split the one-file harness into a runner and one file per area

split_verify_harness.py -- the move that turned tools/verify_harness.py
(about 98,000 lines, every test in one file) into the runner and shared
fixtures, left in tools/verify_harness.py, plus one file per area,
tools/harness/vh_<area>.py (2026-10-31; todo-2026-10-31-root-issues-from-the-very-deep-
check-session, "Calls for Morgan"). Sessions and helpers had been colliding on
the one file every day.

It is a script, not a hand edit, so it can be re-run on a fresh staging if the
file moves underneath it, and so what it did can be checked:

    python3 tools/split_verify_harness.py --report   # the plan, writes nothing
    python3 tools/split_verify_harness.py --write    # do it
    python3 tools/split_verify_harness.py --verify ORIGINAL
            # the split tree defines exactly what ORIGINAL (the one-file
            # verify_harness.py, e.g. from `git show origin/staging:...`)
            # defined: the same names, and every function the same code

What moves and what stays:
  - every top-level `def check_*` moves to its area's file, with the
    decorators and the comment lines above it;
  - a helper `def` or `class` moves with them only when every use of its
    name is in that one area's checks or helpers; one used anywhere else
    stays in the runner;
  - every other statement -- imports, constants, the environment setup, the
    runner, main() -- stays in tools/verify_harness.py, in its order.

A check's area is the tool it exercises most (the AREAS table below), else
a word in its name, else `misc`. Nothing about how a check runs depends on
its area: verify_harness.py executes every part into its own namespace
(harness_parts.py), so names, order and globals are what they were.
"""
import ast
import collections
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
TOOLS = ROOT / 'tools'
sys.path.insert(0, str(TOOLS))
import harness_parts  # noqa: E402

HARNESS = ROOT / harness_parts.HARNESS
PARTS = ROOT / harness_parts.PARTS_DIR

# area -> (what it covers, the tools whose tests go there). A tool not named
# here falls back to the name rules below, then to `misc`.
AREAS = {
    'practice_checks': ('precedent_check.py, the practice audit and the '
                        'practice-file rules it enforces', [
        'precedent_check', 'practice_audit', 'precedent_practice_refs',
        'practice_standing', 'title_case', 'precedent_close_detect',
        'precedent_candidate', 'precedent_paths', 'parse_check',
        'behavioral_replay']),
    'conversion': ('the BestPractice-to-Precedent conversion: the catalogue '
                   'split into practice files, and nothing lost or invented', [
        'split_practices', 'catalogue_stats']),
    'update_vendors': ('Update Vendors in a consuming repository', [
        'precedent_update', 'precedent_update_all', 'precedent_merge_vendors',
        'precedent_local_edits', 'precedent_consumer_shape',
        'precedent_update_driver']),
    'vendor_engine': ('the engine a consumer vendors, and installing it', [
        'precedent_vendor_engine', 'precedent_engine_freshness',
        'precedent_materialize', 'precedent_install', 'precedent_regenerate']),
    'checkin': ('check-in pull requests from dependent repositories', [
        'checkin']),
    'very_deep_check': ('the very deep check and the fleet audit', [
        'very_deep_check', 'ci_fleet_audit']),
    'sources': ('practice sources: resolving, loading and showing them', [
        'precedent_resolve', 'precedent_session_practices', 'precedent_show',
        'precedent_vocabulary', 'precedent_source_names',
        'precedent_source_home', 'precedent_loader']),
    'source_setup': ('attaching, refreshing and moving practice sources', [
        'precedent_refresh_sources', 'precedent_source_bootstrap',
        'precedent_bootstrap_source', 'precedent_source_credentials',
        'precedent_move', 'precedent_access_check',
        'precedent_individual_bootstrap']),
    'views_and_docs': ('generated views, the doc tools and the todo index', [
        'build_views', 'precedent_sync_views', 'doc_lint', 'doc_html',
        'doc_sync', 'doc_lint_gate', 'build_todo_index', 'build_codeowners',
        'build_gotcha_index', 'todo_migrate', 'precedent_migrate_views',
        'precedent_review_page', 'precedent_whats_new', 'typography',
        'todo_disposition', 'build_where_things_are']),
    'branches_and_landing': ('branches, landing, merging and main\'s test', [
        'precedent_branches', 'precedent_land', 'precedent_stale_branches',
        'precedent_branch_name', 'precedent_merge_check', 'merge_check_gate',
        'precedent_ci_verified', 'close_main_test_issue', 'landing_pr_guard',
        'open_failures', 'precedent_boundary_check', 'lease_board']),
    'gates': ('the reply check and the hook gates', [
        'precedent_reply_check', 'reply_gate', 'precedent_gate',
        'artifact_publish_gate', 'answer_first_gate', 'stop_git_check',
        'stop_reply_check', 'wait_loop_gate', 'repo_attach_gate',
        'precedent_paths_hook']),
    'leak_and_privacy': ('the leak gate and outbound privacy', [
        'leak_gate', 'outbound_privacy_scan', 'outbound_privacy_gate',
        'our_language']),
    'push_check': ('the push check, test reach, test review and load budgets', [
        'precedent_push_check', 'push_check_gate', 'harness_reach',
        'harness_reach_hook', 'test_review', 'session_load_trend',
        'harness_times_merge', 'light_check']),
    'session_start': ('session start: bootstrap, hooks, Python, freshness', [
        'bootstrap', 'session_start', 'precedent_python',
        'precedent_session_check', 'precedent_hooks', 'freshness_guard',
        'precedent_container_safe', 'precedent_run_session_hooks',
        'maintainer_heartbeat', 'precedent_heartbeat', 'precedent_hooks']),
    'identity_and_time': ('commit identity, authorship and the clock', [
        'commit_identity', 'check_commit_author', 'precedent_identity',
        'precedent_time', 'check_commit_dates', 'check_session_trailer',
        'commit_identity_push_gate']),
    'migrations': ('migrations and decommissioning', [
        'migration_retire_pre_staging', 'precedent_migrate_status',
        'precedent_decommission', 'doc_lifecycle']),
}
# Checks placed by name, ahead of every other rule. The planted-case suite
# is one function of about 4,300 lines that every enforced practice adds a
# case to; on 2026-10-31 a helper could not add five owed cases because
# another held the one file, so it gets a file of its own.
EXPLICIT = {'check_precedent_check_fires': 'planted_cases'}
# Name rules, for a check that names no tool: first match wins.
NAME_RULES = [
    ('very_deep_check', 'very_deep_check'),
    ('update_vendors', 'update_vendors'),
    ('commit_identity', 'identity_and_time'),
    ('merge_check', 'branches_and_landing'),
    ('main_test', 'branches_and_landing'),
    ('push_', 'push_check'),
    ('changed_files', 'push_check'),
    ('new_test', 'push_check'),
    ('load_ceiling', 'push_check'),
    ('as_ci', 'harness_self'), ('harness', 'harness_self'),
    ('isolated', 'harness_self'), ('tempdir', 'harness_self'),
    ('fixture', 'harness_self'), ('seed_cache', 'harness_self'),
    ('failure_detail', 'harness_self'), ('bare_all', 'harness_self'),
    ('answer_first', 'gates'), ('archive_check', 'gates'),
    ('session_check', 'session_start'), ('session_share', 'sources'),
    ('brought_set', 'sources'), ('sync_', 'views_and_docs'),
    ('todo_index', 'views_and_docs'), ('decommission', 'migrations'),
    ('migration', 'migrations'), ('leftover_pack', 'migrations'),
    ('refresh', 'source_setup'), ('individual', 'source_setup'),
    ('installer', 'vendor_engine'), ('install_', 'vendor_engine'),
    ('update_', 'update_vendors'), ('practice_change', 'practice_checks'),
    ('no_duplication', 'practice_checks'), ('set_refuses', 'sources'),
    ('source_', 'sources'), ('content_preserved', 'conversion'),
    ('no_lost_content', 'conversion'), ('no_invented_content', 'conversion'),
    ('list_structure', 'conversion'), ('section_source_order', 'conversion'),
    ('duplicate_runs', 'conversion'), ('github_ci', 'branches_and_landing'),
    ('conflict_markers', 'practice_checks'),
]
AREA_DOCS = dict({a: d for a, (d, _t) in AREAS.items()},
                 harness_self='the harness itself: the runner, --as-ci, its '
                              'fixtures and their isolation',
                 planted_cases='the planted cases: one per enforced practice '
                               'check, each with its clean control '
                               '(check_precedent_check_fires)',
                 misc='checks that fit no one area')
TOOL_AREA = {t: a for a, (_d, tools) in AREAS.items() for t in tools}
PART_HEADER = """\
# {title}
#
# tools/harness/vh_{name}.py -- part of the verification harness:
# {doc}.
#
# Not run on its own and not imported: tools/verify_harness.py executes every
# file in this directory into its own namespace, so the helpers, constants and
# imports it defines are in scope here, and a check here is called, filtered,
# timed and reported exactly as one in verify_harness.py is
# (tools/harness_parts.py). Run one with the harness:
#     PRECEDENT_CHECK_ONLY=check_name python3 tools/verify_harness.py
# A new check goes in the file for the tool it exercises. No docstring up
# here: one would replace verify_harness.py's own __doc__ when executed.
"""


def _tool_stems():
    return {p.stem.replace('-', '_') for p in TOOLS.glob('*.py')} | \
           {p.stem.replace('-', '_') for p in TOOLS.glob('*.sh')}


def _aliases(src):
    out = {}
    for m in re.finditer(r'^\s*import (\w+) as (\w+)', src, re.M):
        out[m.group(2)] = m.group(1)
    for m in re.finditer(r'^\s*(\w+) = _?load\w*\(\s*[\'"](\w+)', src, re.M):
        out.setdefault(m.group(1), m.group(2))
    return out


def area_of(name, body, stems, aliases):
    if name in EXPLICIT:
        return EXPLICIT[name]
    refs = collections.Counter()
    for m in re.findall(r"([A-Za-z_][\w\-]*)\.(?:py|sh)\b", body):
        m = m.replace('-', '_')
        if m in stems and m != 'verify_harness':
            refs[m] += 1
    for m in re.findall(r"\b(\w+)\.\w+\(", body):
        if m in aliases and aliases[m] in stems:
            refs[aliases[m]] += 1
        elif m in stems:
            refs[m] += 1
    for tool, _n in refs.most_common():
        if tool in TOOL_AREA:
            return TOOL_AREA[tool]
        break
    short = name[len('check_'):]
    for word, area in NAME_RULES:
        if word in short:
            return area
    for tool, _n in refs.most_common():
        if tool in TOOL_AREA:
            return TOOL_AREA[tool]
    return 'misc'


class Chunk:
    __slots__ = ('start', 'end', 'node', 'name', 'kind', 'area')

    def __init__(self, start, end, node):
        self.start, self.end, self.node = start, end, node
        self.name = getattr(node, 'name', None)
        self.kind = ('check' if isinstance(node, ast.FunctionDef)
                     and node.name.startswith('check_') else
                     'def' if isinstance(node, (ast.FunctionDef,
                                                ast.AsyncFunctionDef,
                                                ast.ClassDef)) else 'stmt')
        self.area = None


def chunks(src):
    """-> the file as consecutive Chunks covering every line exactly once:
    each top-level statement with the comment and blank lines above it."""
    tree = ast.parse(src)
    lines = src.splitlines(keepends=True)
    out, prev_end = [], 0
    for node in tree.body:
        out.append(Chunk(prev_end, node.end_lineno, node))
        prev_end = node.end_lineno
    if prev_end < len(lines):
        out[-1].end = len(lines)
    # The comment block directly above a def belongs to it, but a blank-line
    # separated block above that belongs to the statement before (it is the
    # previous section's trailer or a free-standing banner).
    for i in range(1, len(out)):
        c = out[i]
        if c.kind == 'stmt':
            continue
        first = min([c.node.lineno] + [d.lineno for d in
                                       getattr(c.node, 'decorator_list', [])])
        k = first - 1                      # 1-based line above the def
        while k > c.start and lines[k - 1].lstrip().startswith('#'):
            k -= 1
        # lines c.start+1 .. k stay with the previous chunk
        if k > c.start:
            out[i - 1].end = k
            c.start = k
    return out, lines


def plan(src):
    cs, lines = chunks(src)
    stems, aliases = _tool_stems(), _aliases(src)
    text = {id(c): ''.join(lines[c.start:c.end]) for c in cs}
    for c in cs:
        c.area = area_of(c.name, text[id(c)], stems, aliases) \
            if c.kind == 'check' else None
    # Which chunks mention each top-level def's name (a word match, strings
    # and comments included, so a doubtful use keeps the def in the runner).
    names = {c.name for c in cs if c.kind == 'def'}
    word = re.compile(r'\b(' + '|'.join(sorted(map(re.escape, names), key=len,
                                               reverse=True)) + r')\b')
    users = collections.defaultdict(set)
    for c in cs:
        for m in set(word.findall(text[id(c)])):
            if m != c.name:
                users[m].add(id(c))
    # The runner's main() and everything after the last check must keep
    # what they use; a helper moves only while all its users sit in one area.
    by_id = {id(c): c for c in cs}
    changed = True
    while changed:
        changed = False
        for c in cs:
            if c.kind != 'def' or c.area:
                continue
            areas = {by_id[u].area for u in users[c.name]}
            if len(areas) == 1 and None not in areas:
                c.area = areas.pop()
                changed = True
    return cs, lines


def render(cs, lines):
    """-> (runner_text, {area: part_text})."""
    runner, parts = [], collections.defaultdict(list)
    loader_at = None
    for c in cs:
        seg = ''.join(lines[c.start:c.end])
        if c.area:
            parts[c.area].append(seg)
        else:
            if loader_at is None and c.kind == 'stmt' and isinstance(c.node, ast.If) \
                    and '__main__' in ast.unparse(c.node.test):
                loader_at = len(runner)
            runner.append(seg)
    if loader_at is None:
        raise SystemExit('split_verify_harness: no `if __name__ == "__main__"` '
                         'block to load the parts before')
    runner.insert(loader_at, LOADER)
    out = {}
    for area, segs in parts.items():
        doc = AREA_DOCS[area]
        body = ''.join(segs).lstrip('\n')
        out[area] = PART_HEADER.format(
            title=f'The harness tests for {doc.split(":")[0].split(",")[0]}',
            name=area, doc=doc) + '\n\n' + body
        if not out[area].endswith('\n'):
            out[area] += '\n'
    return ''.join(runner), out


LOADER = r'''

# THE TESTS LIVE IN tools/harness/, ONE FILE PER AREA (2026-10-31). This file
# keeps the runner and the shared fixtures; every check moved into the area it
# exercises, so sessions stop colliding on one 98,000-line file. Each part is
# executed into THIS namespace, not imported: a check there sees every name
# defined above exactly as when it lived here, and the filter, the timing, the
# reach recording and main() find it in globals() as before. Compiled under its
# own path, so a traceback and the reach ledger name the real file.
# tools/split_verify_harness.py made the split; tools/harness_parts.py is the
# one answer to "which files are the harness" for every tool that reads it.
import harness_parts  # noqa: E402


def _load_harness_parts():
    # One namespace means a second `def` of a name already defined -- here or
    # in another part -- would replace the first without a word, and which
    # one wins would hang on file order. Refused instead, naming both.
    seen = {}
    for _part in harness_parts.part_paths(ROOT):
        _src = _part.read_text(encoding='utf-8')
        for _name in re.findall(r'^(?:def|class) (\w+)', _src, re.M):
            where = seen.get(_name) or ('tools/verify_harness.py'
                                        if _name in globals() else None)
            if where:
                raise SystemExit(f'verify_harness: {_name} is defined in '
                                 f'{where} and again in tools/harness/'
                                 f'{_part.name} -- one name, one definition')
            seen[_name] = f'tools/harness/{_part.name}'
        exec(compile(_src, str(_part), 'exec'), globals())


_load_harness_parts()

'''


def report(cs):
    size = collections.Counter()
    count = collections.Counter()
    for c in cs:
        a = c.area or '(runner)'
        size[a] += c.end - c.start
        if c.kind == 'check':
            count[a] += 1
    for a, n in size.most_common():
        print(f'{n:7d} lines  {count[a]:4d} checks  {a}')
    print(f'{sum(size.values()):7d} lines  {sum(count.values()):4d} checks  total')


# -- --verify ------------------------------------------------------------------
def _top_level(src, drop_loader=False):
    """-> Counter of ast.dump(node) for each top-level statement of `src`,
    line numbers left out: what the code is, not where it sits."""
    nodes = ast.parse(src).body
    if drop_loader:
        loader = {ast.dump(n) for n in ast.parse(LOADER).body}
        nodes = [n for n in nodes if ast.dump(n) not in loader]
    return collections.Counter(ast.dump(n) for n in nodes)


_LOAD_PROBE = r"""
import json, pathlib, re, sys, types
path, src_file = sys.argv[1], sys.argv[2]
sys.path.insert(0, str(pathlib.Path(path).parent))
g = {'__name__': 'verify_harness_under_test', '__file__': path}
exec(compile(pathlib.Path(src_file).read_text(encoding='utf-8'), path, 'exec'), g)
def shape(v):
    if isinstance(v, types.FunctionType):
        return ['function', v.__name__, v.__code__.co_firstlineno > 0]
    if isinstance(v, type):
        return ['class', v.__name__]
    if isinstance(v, types.ModuleType):
        return ['module', v.__name__]
    if isinstance(v, re.Pattern):
        return ['re', v.pattern, v.flags]
    if isinstance(v, (str, int, float, bool, type(None), tuple, list, dict,
                      frozenset, set, pathlib.PurePath)):
        try:
            return ['value', repr(sorted(map(repr, v)) if isinstance(v, (set, frozenset)) else v)]
        except Exception:
            return ['value', type(v).__name__]
    return ['object', type(v).__name__]
skip = {'__builtins__', '__file__', '_EMPTY_GITCONFIG_DIR'}
print(json.dumps({k: shape(v) for k, v in g.items() if k not in skip}))
"""


def _loaded(src_file):
    import json
    import subprocess
    r = subprocess.run([sys.executable, '-c', _LOAD_PROBE, str(HARNESS),
                        str(src_file)], capture_output=True, text=True,
                       cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit(f'split_verify_harness: {src_file} does not load:\n'
                         + r.stderr[-3000:])
    return json.loads(r.stdout.strip().splitlines()[-1])


def verify(original_path):
    """The split tree is the original, moved: (1) the same top-level
    statements, compared parsed, each exactly once across the runner and
    the parts; (2) loaded, each in a fresh process, the same names with the
    same values, and the same checks."""
    original = pathlib.Path(original_path).read_text(encoding='utf-8')
    before = _top_level(original)
    after = _top_level(HARNESS.read_text(encoding='utf-8'), drop_loader=True)
    for p in harness_parts.part_paths(ROOT):
        after += _top_level(p.read_text(encoding='utf-8'))
    code_ok = before == after
    print(f'top-level statements before: {sum(before.values())}  after: '
          f'{sum(after.values())}  identical: {code_ok}')
    if not code_ok:
        print(f'  only before: {sum((before - after).values())}, only after: '
              f'{sum((after - before).values())}')
        for d in list((before - after) | (after - before))[:5]:
            print('   ', d[:200])
    a, b = _loaded(original_path), _loaded(HARNESS)
    extra = {'harness_parts', '_load_harness_parts', '_part'}
    lost = sorted(set(a) - set(b))
    added = sorted(set(b) - set(a) - extra)
    diff = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    ca = sorted(k for k in a if k.startswith('check_'))
    cb = sorted(k for k in b if k.startswith('check_'))
    print(f'checks before: {len(ca)}  after: {len(cb)}  identical list: {ca == cb}')
    print(f'names before: {len(a)}  after: {len(b)}')
    for label, xs in (('lost', lost), ('added', added), ('different', diff)):
        if xs:
            print(f'{label}: {len(xs)}: ' + ', '.join(xs[:40]))
    ok = code_ok and ca == cb and not lost and not added and not diff
    print('VERIFIED: same statements, same names, same values' if ok
          else 'NOT VERIFIED')
    return 0 if ok else 1


def main(argv):
    if argv[:1] in (['-h'], ['--help']):
        print(__doc__)
        return 0
    if '--verify' in argv:
        return verify(argv[argv.index('--verify') + 1])
    src = HARNESS.read_text(encoding='utf-8')
    if harness_parts.part_paths(ROOT):
        raise SystemExit(f'split_verify_harness: {harness_parts.PARTS_DIR}/ '
                         'already has parts -- run it on a one-file harness')
    cs, lines = plan(src)
    if '--write' not in argv:
        report(cs)
        return 0
    runner, parts = render(cs, lines)
    # Lossless: every line of the original is in exactly one output, once.
    moved = sum(c.end - c.start for c in cs if c.area)
    assert moved + (len(runner.splitlines()) - len(LOADER.splitlines())) \
        == len(lines), 'the split lost or duplicated lines'
    PARTS.mkdir(exist_ok=True)
    for area, text in sorted(parts.items()):
        (PARTS / f'vh_{area}.py').write_text(text, encoding='utf-8')
    HARNESS.write_text(runner, encoding='utf-8')
    report(cs)
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
