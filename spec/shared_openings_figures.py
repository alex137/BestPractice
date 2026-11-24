#!/usr/bin/env python3
"""The figures spec/SHARED_OPENINGS.md cites, computed, never typed.

Inputs, and nothing else:
  - the size of each always-loaded file here, measured the way the
    session-load budget measures it (tools/build_views.py, _approx_tokens);
  - the ceiling in tools/session_load_budgets.json (session_load_tokens);
  - Anthropic's published cache multipliers, each quoted with its page in
    spec/shared-openings-sources/anthropic-api-prompt-caching.txt.

A "token-equivalent" is one input token at the model's ordinary input price.
Run: python3 spec/shared_openings_figures.py
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import build_views  # noqa: E402

# Sourced: "Cache write tokens with a 5-minute TTL are 1.25 times the base
# input tokens price." / "...1-hour TTL are 2 times..." / "Cache read tokens
# are 0.1 times the base input tokens price" (footnotes: 0.05x and 0.025x on
# the newest models).
WRITE_5M, WRITE_1H = 1.25, 2.0
READS = (0.1, 0.05, 0.025)


def measure():
    t = build_views._approx_tokens
    agents = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
    b = agents.index('<!-- BEGIN GENERATED: precedent-loader -->')
    e = agents.index('<!-- END GENERATED')
    block = agents[b:e]
    i = block.index('## Occasion index')
    parts = [('AGENTS.md, hand-written lines before the practice block', t(agents[:b])),
             ('AGENTS.md, resident rules', t(block[:i])),
             ('AGENTS.md, occasion index and standing instruction', t(block[i:])),
             ('AGENTS.md, hand-written lines after the practice block', t(agents[e:])),
             ('CLAUDE.md', t((ROOT / 'CLAUDE.md').read_text(encoding='utf-8')))]
    sp = ROOT / '.precedent' / 'SESSION_PRACTICES.md'
    session = t(sp.read_text(encoding='utf-8')) if sp.is_file() else None
    return parts, session


def main():
    parts, session = measure()
    tracked = sum(n for _, n in parts)
    ceiling = json.loads((ROOT / 'tools' / 'session_load_budgets.json')
                         .read_text(encoding='utf-8'))['session_load_tokens']
    assert tracked > 0 and ceiling >= tracked, (tracked, ceiling)
    assert WRITE_5M > max(READS) and WRITE_1H > WRITE_5M
    print('| Part | Tokens (rough) |\n|---|---|')
    for name, n in parts:
        print(f'| {name} | {n:,} |')
    print(f'| **Tracked files, same for everyone on this commit** | **{tracked:,}** |')
    if session is None:
        print('| Session practices file | not on this machine |')
    else:
        print(f'| Session practices file, written at session start | {session:,} |')
        print(f'| **Whole opening Precedent adds** | **{tracked + session:,}** |')
    print(f'| Ceiling a repository may reach | {ceiling:,} |')
    print()
    print('| Case | Token-equivalents, first request of a session |\n|---|---|')
    for label, n in (('tracked files', tracked), ('at the ceiling', ceiling)):
        print(f'| {label}: nothing warm, 5-minute write | {n * WRITE_5M:,.0f} |')
        print(f'| {label}: nothing warm, 1-hour write | {n * WRITE_1H:,.0f} |')
        for r in READS:
            print(f'| {label}: already warm, read at {r}x | {n * r:,.0f} |')
        lo = n * (WRITE_5M - max(READS))
        hi = n * (WRITE_1H - min(READS))
        print(f'| **{label}: the most a warm opening can save** | '
              f'**{lo:,.0f} to {hi:,.0f}** |')


if __name__ == '__main__':
    main()
