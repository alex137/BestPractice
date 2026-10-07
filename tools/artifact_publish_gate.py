#!/usr/bin/env python3
"""The publish gate: a page reaches a link only as a fresh render of a
registered document (practice: docs-track-models, "Published pages").

Run by templates/harness/claude-code/hooks/artifact-publish-gate.sh as a
PreToolUse hook on the Artifact tool. On a publish of an .html or .md page
(`file_path`, and any .html source among `files`), the file's bytes must
equal the on-disk render of a document the repo's renderer registers, and
that render must be newer than its source. A session publishes a copy of
the render it just made, which is byte-identical, so the normal route
passes; a page written by hand -- a review draft with its figures typed in
-- is refused, because no check that reads the repository can ever compare
it with a model.

THE INCIDENT (2026-10-05, a consumer). A deck's review page was hand-built
in a scratch folder with its figures typed in and published straight to a
link, so its contents could be agreed before the real build. Every check on
script-derived figures -- the generated blocks, the model audit, the lint --
reads files in the repository, so nothing compared the page with a model.
The model moved; the page did not; nobody saw it for nine days.

THE REGISTRY. The registered renders are the DOCS (source .md, title) and
COMPOSITE_RENDERS (.html -> {"sources": [...]}) of the repo's renderer
module: tools/doc_html.py by default, or the host shim named by
tools/artifact_publish_gate_host.json as {"registry": "path/to/shim.py"} --
the same engine-plus-host-shim split doc_lint uses.

WHAT IT DOES NOT CHECK. Where a page came from, not whether its generated
blocks are current: that is doc_sync at commit and `doc_html.py --stale`
for renders. Asset uploads, reads, lists and creating from an Artifact type
are not publishes of a page and pass. A page that is not a deliverable (an
index, an explainer) is refused too: write it as markdown, register it and
render it.

ENGINE-REGISTERED GENERATORS (2026-10-07). Some pages have no document
behind them: the branch-cleanup page that the ladder set's
stale-branch-cleanup practice puts in a session's closing summary is
written by tools/precedent_stale_branches.py --html from the live branch
list. The gate refused it, so two rules in force contradicted each other and
a session fell back to pasting links into chat. A tool named in GENERATORS
calls record_generated() on every page it writes, which notes the page's
sha256 in a ledger outside any repository (GENERATED_LEDGER); a page whose
bytes match an entry from the last FRESH_SECONDS passes, the same
copy-of-a-fresh-render test a registered document gets. Edit one byte of it
and it is a hand-made page again, refused. The gate exists so typed-in
figures cannot drift from a model; a generator has no model to drift from,
only its own output.

FAIL-OPEN ON THE PLUMBING (practice: fail-gracefully). An unparseable
payload, or a registry that will not load, lets the call through with a
line on stderr: a gate that breaks a session over its own missing
dependency is a gate somebody disables.

Exit 0 lets the call through; exit 2 refuses it with the reason on stderr.
`--self-check` runs the two-direction test on a throwaway tree.
"""
import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(os.environ.get('CLAUDE_PROJECT_DIR')
            or Path(__file__).resolve().parents[1])
HOST_FILE = 'tools/artifact_publish_gate_host.json'
DEFAULT_REGISTRY = 'tools/doc_html.py'
# The engine's own page generators: a page one of these wrote, unedited and
# recent, may be published. Only an engine change adds one.
GENERATORS = ('precedent_stale_branches.py',)
FRESH_SECONDS = 3600
LEDGER_KEEP = 50
PRACTICE_NOTE = '(practice: docs-track-models, "Published pages")'


def generated_ledger():
    """Where generated pages are noted: per person, outside any repository,
    because the gate's project and the generator's repository need not be
    the same one."""
    env = os.environ.get('PRECEDENT_GENERATED_PAGES')
    if env:
        return Path(env)
    base = os.environ.get('XDG_CACHE_HOME') or str(Path.home() / '.cache')
    return Path(base) / 'precedent' / 'generated_pages.json'


def _read_ledger():
    try:
        data = json.loads(generated_ledger().read_text(encoding='utf-8'))
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def record_generated(path, generator, now=None):
    """Note that `generator` (a GENERATORS name) just wrote `path`. Never
    raises: a ledger that cannot be written only means the page will be
    refused, and the refusal says why."""
    import time
    try:
        data = _read_ledger()
        data[_sha(path)] = {'generator': generator, 'path': str(path),
                            'at': int(now if now is not None else time.time())}
        keep = sorted(data.items(), key=lambda kv: kv[1].get('at', 0))[-LEDGER_KEEP:]
        out = generated_ledger()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(dict(keep), indent=1), encoding='utf-8')
        return True
    except OSError:
        return False


def generated_problem(sha, page, now=None):
    """-> None when `sha` is a fresh page a registered generator wrote; a
    refusal line when it was one but is too old; '' when no generator wrote
    it (the caller's registered-document test then decides)."""
    import time
    entry = _read_ledger().get(sha)
    if not entry or entry.get('generator') not in GENERATORS:
        return ''
    age = int(now if now is not None else time.time()) - int(entry.get('at', 0))
    if age <= FRESH_SECONDS:
        return None
    return (f'{page}: {entry["generator"]} wrote this page {age // 60} minutes '
            f'ago, longer than {FRESH_SECONDS // 60} allow; run it again and '
            f'publish the new page.')


def registry_module_path(root=ROOT):
    """The module whose DOCS and COMPOSITE_RENDERS list the renders."""
    host = root / HOST_FILE
    if host.is_file():
        rel = (json.loads(host.read_text(encoding='utf-8')) or {}).get('registry')
        if rel:
            return root / rel
    return root / DEFAULT_REGISTRY


def load_registry(root=ROOT):
    """[(source paths, render path)], repo-relative."""
    path = registry_module_path(root)
    if not path.is_file():
        raise FileNotFoundError(f'{path.relative_to(root)} does not exist')
    spec = importlib.util.spec_from_file_location('publish_gate_registry', path)
    mod = importlib.util.module_from_spec(spec)
    argv, sys.argv = sys.argv, [str(path)]
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.argv = argv
    out = [([d[0]], str(Path(d[0]).with_suffix('.html')))
           for d in getattr(mod, 'DOCS', [])]
    for html, spec_ in (getattr(mod, 'COMPOSITE_RENDERS', {}) or {}).items():
        out.append((list((spec_ or {}).get('sources') or []), html))
    return out


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pages_in(tool_input):
    """The page files this call would publish."""
    if (tool_input.get('action') or 'publish') != 'publish':
        return []
    if tool_input.get('asset'):
        return []
    out = []
    fp = tool_input.get('file_path')
    if isinstance(fp, str) and fp.lower().endswith(('.html', '.htm', '.md')):
        out.append(fp)
    files = tool_input.get('files') or {}
    for src in (files.values() if isinstance(files, dict) else []):
        if isinstance(src, dict):
            src = src.get('from')
        if isinstance(src, str) and src.lower().endswith(('.html', '.htm')):
            out.append(src)
    return out


def check(pages, registry, root=ROOT, now=None):
    """The refusal lines; empty means every page is a fresh render."""
    renders = {}
    for sources, html in registry:
        p = root / html
        if p.is_file():
            renders.setdefault(_sha(p), []).append((sources, p))
    problems = []
    for page in pages:
        p = Path(page)
        if not p.is_absolute():
            p = root / p
        if not p.is_file():
            continue   # the tool reports a missing file itself
        sha = _sha(p)
        hits = renders.get(sha)
        if not hits:
            gen = generated_problem(sha, page, now)
            if gen is None:
                continue
            if gen:
                problems.append(gen)
                continue
            problems.append(
                f'{page}: not a render of any registered document. Only a '
                f'copy of what the renderer produced from a registered source '
                f'may be published -- nothing typed by hand reaches a link. '
                f'Write it as markdown with its figures in generated blocks, '
                f'register it, render it, and publish a copy of the render. '
                f'A page an engine generator writes ({", ".join(GENERATORS)}) '
                f'passes when published unedited within the hour.')
            continue
        sources, html = hits[0]
        newer = [s for s in sources if (root / s).is_file()
                 and (root / s).stat().st_mtime > html.stat().st_mtime]
        if newer:
            problems.append(
                f'{page}: the render is older than {", ".join(newer)}; render '
                f'it again and publish the new copy.')
    return problems


def main():
    try:
        payload = json.loads(sys.stdin.read() or '{}')
    except ValueError:
        return 0
    name = payload.get('tool_name') or ''
    if name != 'Artifact' and not name.endswith('__Artifact'):
        return 0
    pages = pages_in(payload.get('tool_input') or {})
    if not pages:
        return 0
    try:
        registry = load_registry()
    except Exception as exc:  # noqa: BLE001 -- fail open, and say so
        print(f'artifact_publish_gate: the render registry did not load '
              f'({exc}); this publish is not checked', file=sys.stderr)
        return 0
    problems = check(pages, registry)
    if problems:
        # The practice pointer is said here, not in the hook, so rewording
        # it never touches a hook file (see doc_lint.py's hook_reason).
        print('artifact publish refused:\n  ' + '\n  '.join(problems)
              + f'\n\n{PRACTICE_NOTE}', file=sys.stderr)
        return 2
    return 0


def self_check():
    """Two directions, on a tree this test builds and owns: a copy of a
    fresh render passes; a hand-built page and a stale render are refused;
    a composite render is recognised; calls that publish no page pass."""
    import shutil
    import tempfile
    cases = []
    cases.append(('a read publishes nothing',
                  pages_in({'action': 'read', 'file_path': 'x.html'}) == []))
    cases.append(('an asset upload publishes no page',
                  pages_in({'asset': True, 'file_path': 'x.html', 'url': 'u'}) == []))
    cases.append(('a data file is not a page', pages_in({'file_path': 'x.json'}) == []))
    cases.append(('an .html among files is a page',
                  pages_in({'file_path': 'a.html',
                            'files': {'b.html': {'from': 'c.html'}}}) == ['a.html', 'c.html']))
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / 'tools').mkdir()
        (root / 'tools' / 'shim.py').write_text(
            "DOCS = [('doc.md', 'Doc')]\n"
            "COMPOSITE_RENDERS = {'both.html': {'sources': ['doc.md', 'other.md']}}\n",
            encoding='utf-8')
        (root / HOST_FILE).write_text('{"registry": "tools/shim.py"}', encoding='utf-8')
        for name, body in (('doc.md', '# Doc\n'), ('other.md', '# Other\n'),
                           ('doc.html', '<h1>Doc</h1>'), ('both.html', '<h1>Both</h1>')):
            (root / name).write_text(body, encoding='utf-8')
        for name, t in (('doc.md', 1e6), ('other.md', 1e6),
                        ('doc.html', 2e6), ('both.html', 2e6)):
            os.utime(root / name, (t, t))
        registry = load_registry(root)
        cases.append(('the host file names the registry',
                      (['doc.md'], 'doc.html') in registry))
        copy = root / 'scratch_copy.html'
        shutil.copyfile(root / 'doc.html', copy)
        composite = root / 'scratch_both.html'
        shutil.copyfile(root / 'both.html', composite)
        hand = root / 'hand_built.html'
        hand.write_text('<h1>typed by hand</h1>', encoding='utf-8')
        cases.append(('a copy of a fresh render passes',
                      not check([str(copy)], registry, root)))
        cases.append(('a copy of a fresh composite render passes',
                      not check([str(composite)], registry, root)))
        cases.append(('a hand-built page is refused',
                      bool(check([str(hand)], registry, root))))
        os.utime(root / 'other.md', (3e6, 3e6))
        cases.append(('a composite older than one of its sources is refused',
                      bool(check([str(composite)], registry, root))))
        os.utime(root / 'doc.md', (3e6, 3e6))
        cases.append(('a render older than its source is refused',
                      bool(check([str(copy)], registry, root))))
        saved = os.environ.get('PRECEDENT_GENERATED_PAGES')
        os.environ['PRECEDENT_GENERATED_PAGES'] = str(root / 'ledger.json')
        try:
            page = root / 'branch-cleanup.html'
            page.write_text('<h1>91 branches</h1>', encoding='utf-8')
            cases.append(('a generator page nobody recorded is refused',
                          bool(check([str(page)], registry, root, now=5000))))
            record_generated(page, 'precedent_stale_branches.py', now=5000)
            cases.append(('a fresh unedited generator page passes',
                          not check([str(page)], registry, root, now=5000 + 60)))
            cases.append(('...and an hour and more later it is refused',
                          'run it again' in ' '.join(check(
                              [str(page)], registry, root, now=5000 + FRESH_SECONDS + 1))))
            page.write_text('<h1>91 branches, edited</h1>', encoding='utf-8')
            cases.append(('one edited byte makes it a hand-made page, refused',
                          'not a render' in ' '.join(check(
                              [str(page)], registry, root, now=5000 + 60))))
            record_generated(page, 'some_other_tool.py', now=5000)
            cases.append(('a tool not in GENERATORS cannot vouch for a page',
                          bool(check([str(page)], registry, root, now=5000 + 60))))
        finally:
            if saved is None:
                os.environ.pop('PRECEDENT_GENERATED_PAGES', None)
            else:
                os.environ['PRECEDENT_GENERATED_PAGES'] = saved
    failed = [n for n, ok in cases if not ok]
    if failed:
        print('artifact_publish_gate self-check FAIL: ' + '; '.join(failed))
        return 1
    print(f'artifact_publish_gate self-check OK ({len(cases)} cases)')
    return 0


if __name__ == '__main__':
    if '--help' in sys.argv or '-h' in sys.argv:
        print(__doc__)
        sys.exit(0)
    if '--self-check' in sys.argv:
        sys.exit(self_check())
    sys.exit(main())
