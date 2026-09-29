#!/usr/bin/env python3
"""routing_reasons -- every practice's routing choice on one page, read
from the practice files themselves.

    python3 tools/routing_reasons.py                # print the table
    python3 tools/routing_reasons.py --emit table   # the page's block

WHY A GENERATED PAGE (2026-09-29). tools/routing_scope.json used to hold
every routing reason in one hand-kept list, which is what let the
2026-08-31 routing pass apply one rule to all its candidates side by side.
The reasons moved into each practice's own applies_to_why, so they cannot
drift from the globs, and the side-by-side view is rebuilt from them here:
a view, not a second copy (practices: registry-source-of-truth,
upstream-fix). spec/ROUTING_REASONS.md carries it as a doc_sync block.
"""

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
import split_practices as sp  # noqa: E402


def _decode(raw):
    raw = (raw or '').strip()
    if raw.startswith('"'):
        try:
            return json.loads(raw)
        except ValueError:
            return raw.strip('"')
    return raw


def rows(practices_dir=ROOT / 'practices'):
    """-> [(slug, applies_to, gates, why)] for every active on-demand
    practice, alphabetically by slug."""
    out = []
    for f in sorted(Path(practices_dir).glob('*.md')):
        try:
            fm, _ = sp._read_practice_file(f)
        except sp.PracticeFileError:
            continue
        if (fm.get('tier') or '').strip() != 'on-demand':
            continue
        if (fm.get('status', 'active') or 'active').strip().strip('"') != 'active':
            continue
        why = _decode(fm.get('applies_to_why'))
        gates_why = _decode(fm.get('gates_why'))
        if gates_why:
            why = f'{why} **Gate:** {gates_why}'
        out.append((fm.get('slug', f.stem).strip(),
                    (fm.get('applies_to') or '').strip(),
                    (fm.get('gates') or '[]').strip(), why))
    return out


def emit_table(practices_dir=ROOT / 'practices'):
    def cell(s):
        return s.replace('|', '\\|').replace('\n', ' ')
    lines = ['| Practice | Files (`applies_to`) | Gates | Why |', '|---|---|---|---|']
    for slug, globs, gates, why in rows(practices_dir):
        lines.append(f'| [{slug}](../practices/{slug}.md) | `{cell(globs)}` '
                     f'| `{cell(gates)}` | {cell(why)} |')
    return '\n'.join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--emit', metavar='NAME',
                    help="print a generated block for doc_sync ('table')")
    args = ap.parse_args(argv)
    if args.emit and args.emit != 'table':
        sys.exit(f'routing_reasons: no block named {args.emit!r}')
    print(emit_table())
    return 0


if __name__ == '__main__':
    sys.exit(main())
