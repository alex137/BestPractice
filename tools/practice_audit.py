#!/usr/bin/env python3
"""practice_audit.py — audit the practice-export layer (BestPractice 14 & 15).

Runs from a dependent repo (script lives at process/upstream/tools/). Three
checks, in order — any FAIL exits non-zero:

  1. SCRUB (the proprietary gate). Every text file under process/upstream/ is
     scanned against process/scrub_blocklist.txt (one regex per line, `#`
     comments). Any hit FAILS: the vendored tree is destined for a public
     repo and must be public-safe at all times, not just at check-in. If no
     blocklist exists, the check is skipped with a notice (a public dependent
     repo needs none).

  2. DRIFT (baseline snapshots, practice 7). For each manifest entry with
     granularity "file": the local file's sha256 is compared to the recorded
     local_sha256 baseline. Changed while status is "synced" → FAIL — the
     local improvement must be exported to process/upstream/ and re-baselined
     (--update-baseline), or the entry deliberately flipped to "diverged"
     (then it is listed as pending export, not failed). This exists because
     "copy changes back" as a prose rule is exactly the kind of convention
     that gets skipped under pressure.

  3. INTEGRITY. Manifest and upstream paths exist; "section"-granularity
     entries' section_marker still occurs in local_path (warn-only — section
     tracking is approximate by design); "local-only" entries carry notes.

Run:  python3 process/upstream/tools/practice_audit.py                    # gate
      python3 process/upstream/tools/practice_audit.py --update-baseline  # re-record hashes
"""
import hashlib, json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve()
_top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=HERE.parent,
                      capture_output=True, text=True).stdout.strip()
ROOT = pathlib.Path(_top) if _top else HERE.parents[3]
UPSTREAM = ROOT / 'process' / 'upstream'
MANIFEST = ROOT / 'process' / 'manifest.json'
BLOCKLIST = ROOT / 'process' / 'scrub_blocklist.txt'

TEXT_EXT = {'.md', '.py', '.sh', '.json', '.txt', '.yml', '.yaml', '.toml', '.template'}

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_blocklist():
    if not BLOCKLIST.exists():
        return None
    pats = []
    for i, line in enumerate(BLOCKLIST.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            pats.append(re.compile(line))
        except re.error as e:
            print(f"WARN: blocklist line {i} is not a valid regex ({e}): {line}")
    return pats

def scrub(fails):
    pats = load_blocklist()
    if pats is None:
        print("scrub: no process/scrub_blocklist.txt — skipped (public dependent repo?).")
        return
    hits = 0
    for path in sorted(UPSTREAM.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXT:
            continue
        rel = path.relative_to(ROOT)
        for i, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
            for pat in pats:
                if pat.search(line):
                    fails.append(f"SCRUB: {rel}:{i} matches blocklist /{pat.pattern}/: {line.strip()[:90]}")
                    hits += 1
                    break
    if not hits:
        print(f"scrub OK: process/upstream/ clean against {len(pats)} blocklist pattern(s).")

def audit(update=False):
    fails, warns, pending = [], [], []
    if not MANIFEST.exists():
        print(f"practice_audit FAIL: no manifest at {MANIFEST.relative_to(ROOT)} "
              f"(see process/upstream/INSTALL.md §5)")
        return 1
    manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))

    scrub(fails)  # check 1 — always first: it guards the public tree

    changed = False
    for e in manifest.get('entries', []):
        name = e.get('practice', '?')
        local = ROOT / e.get('local_path', '')
        upstream = UPSTREAM / e.get('upstream_path', '')
        if not local.exists():
            fails.append(f"INTEGRITY: [{name}] local_path missing: {e.get('local_path')}")
            continue
        if e.get('upstream_path') and not upstream.exists():
            fails.append(f"INTEGRITY: [{name}] upstream_path missing: {e.get('upstream_path')}")
        status = e.get('status', 'synced')
        if status == 'local-only' and not e.get('notes'):
            warns.append(f"[{name}] local-only without notes — say why it stays local")
        gran = e.get('granularity', 'file')
        if gran == 'file':
            cur = sha256(local)
            if update:
                if e.get('local_sha256') != cur:
                    e['local_sha256'] = cur
                    if status == 'diverged':
                        e['status'] = 'synced'
                    changed = True
            elif not e.get('local_sha256'):
                warns.append(f"[{name}] no baseline hash — run --update-baseline")
            elif cur != e['local_sha256']:
                if status == 'synced':
                    fails.append(f"DRIFT: [{name}] {e['local_path']} changed since baseline while "
                                 f"status='synced' — export the change to process/upstream/ and "
                                 f"--update-baseline, or flip the entry to 'diverged'")
                else:
                    pending.append(f"[{name}] {e['local_path']} (status={status}) — pending export")
        elif gran == 'section':
            marker = e.get('section_marker', '')
            if marker and marker not in local.read_text(encoding='utf-8', errors='ignore'):
                warns.append(f"[{name}] section_marker not found in {e['local_path']}: '{marker}'")

    if update and changed:
        MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print("practice_audit: baselines updated.")

    for p in pending:
        print(f"pending: {p}")
    for w in warns:
        print(f"WARN: {w}")
    for f in fails:
        print(f"FAIL: {f}")
    if fails:
        print(f"\npractice_audit FAIL — {len(fails)} error(s).")
        return 1
    print(f"practice_audit OK: {len(manifest.get('entries', []))} entries; "
          f"{len(pending)} pending export; {len(warns)} warning(s).")
    return 0

if __name__ == '__main__':
    sys.exit(audit(update='--update-baseline' in sys.argv))
