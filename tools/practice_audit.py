#!/usr/bin/env python3
"""practice_audit.py — audit the practice-export layer (BestPractice 14, 15 & 23).

Runs from a dependent repo (script lives at process/upstream/tools/). A repo
may install several practice layers ("packs", practice 23): the generic
upstream at process/upstream/ tracked by process/manifest.json, plus any
domain packs vendored at process/<pack>/ tracked by process/manifest_<pack>.json.
This audit discovers every process/manifest*.json and runs the same three
checks against each manifest's own vendored tree — any FAIL exits non-zero:

  1. SCRUB (the leakage gate). Every text file under the manifest's
     upstream.vendored_at tree is scanned against that manifest's blocklist:
     upstream.scrub_blocklist if the key is present (a JSON null explicitly
     opts the pack out, with a notice), else the default
     process/scrub_blocklist.txt. Any hit FAILS: a vendored tree destined
     for another repo must be clean at all times, not just at check-in. A
     missing blocklist file skips the check with a notice.

  2. DRIFT (baseline snapshots, practice 7). For each manifest entry with
     granularity "file": the local file's sha256 is compared to the recorded
     local_sha256 baseline. Changed while status is "synced" → FAIL — the
     local improvement must be exported to the vendored tree and re-baselined
     (--update-baseline), or the entry deliberately flipped to "diverged"
     (then it is listed as pending export, not failed). This exists because
     "copy changes back" as a prose rule is exactly the kind of convention
     that gets skipped under pressure.

  3. INTEGRITY. Manifest and upstream paths exist; "section"-granularity
     entries' section_marker still occurs in local_path (warn-only — section
     tracking is approximate by design); "local-only" entries carry notes.

  4. LAYOUT (root hygiene). Upstream-internal docs (INSTALL.md,
     PRACTICES.md, SETUP.md, ...) must not sit at the dependent repo's
     root — they belong only inside a vendored tree such as
     process/upstream/. A contributor browsing the root should see the
     project's own subject matter plus the instantiated files, nothing
     about BestPractice internals. A root file with one of these names
     FAILS unless a manifest records it as this repo's own document (an
     entry with that local_path). Runs once per audit, with exceptions
     collected across all manifests.

Run:  python3 process/upstream/tools/practice_audit.py                    # gate (all manifests)
      python3 process/upstream/tools/practice_audit.py --update-baseline  # re-record hashes
      python3 process/upstream/tools/practice_audit.py --manifest process/manifest.json  # one manifest
"""
import hashlib, json, pathlib, re, subprocess, sys

HERE = pathlib.Path(__file__).resolve()
_top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=HERE.parent,
                      capture_output=True, text=True).stdout.strip()
ROOT = pathlib.Path(_top) if _top else HERE.parents[3]
DEFAULT_BLOCKLIST = 'process/scrub_blocklist.txt'

TEXT_EXT = {'.md', '.py', '.sh', '.json', '.txt', '.yml', '.yaml', '.toml', '.template'}

# Docs that exist ONLY inside the vendored tree; finding one at the
# dependent repo's root means the install scattered files it should have
# contained (INSTALL.md §1, "root hygiene").
UPSTREAM_ONLY_DOCS = ['INSTALL.md', 'PRACTICES.md', 'SETUP.md', 'GITHUB_ACTIONS.md',
                      'MOBILE.md', 'METHOD.md', 'GIT.md']

def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load_blocklist(path):
    if path is None or not path.exists():
        return None
    pats = []
    for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        try:
            pats.append(re.compile(line))
        except re.error as e:
            print(f"WARN: blocklist line {i} is not a valid regex ({e}): {line}")
    return pats

def scrub(tree, blocklist_path, fails, label):
    pats = load_blocklist(blocklist_path)
    if pats is None:
        why = "pack opted out (scrub_blocklist: null)" if blocklist_path is None else \
              f"no blocklist at {blocklist_path.relative_to(ROOT)}"
        print(f"scrub [{label}]: skipped — {why}.")
        return
    hits = 0
    for path in sorted(tree.rglob('*')):
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
        print(f"scrub OK [{label}]: {tree.relative_to(ROOT)}/ clean against {len(pats)} blocklist pattern(s).")

def layout(fails, claimed):
    stray = [n for n in UPSTREAM_ONLY_DOCS if (ROOT / n).exists() and n not in claimed]
    if stray:
        fails.append(
            "LAYOUT: upstream-internal doc(s) at the repo root: " + ", ".join(stray) +
            " — these belong only under process/upstream/. The root gets ONLY the"
            " instantiated files (AGENTS.md + harness pointer, MAP.md, TODO.md,"
            " GLOSSARY.md, GETTING_STARTED.md, the README entry block) — see"
            " process/upstream/INSTALL.md §1 'root hygiene'. Delete the strays (their"
            " content lives in process/upstream/); if one is genuinely this repo's own"
            " document, record it as a manifest entry with that local_path.")
    else:
        print("layout OK: no upstream-internal docs at the repo root.")

def audit_manifest(manifest_path, update, fails, warns, pending):
    label = manifest_path.stem.replace('manifest_', '').replace('manifest', 'upstream') or 'upstream'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    up = manifest.get('upstream', {})
    tree = ROOT / up.get('vendored_at', 'process/upstream')
    if not tree.is_dir():
        fails.append(f"INTEGRITY: [{label}] vendored tree missing: {up.get('vendored_at')}")
        return 0
    if 'scrub_blocklist' in up:
        bl = None if up['scrub_blocklist'] is None else ROOT / up['scrub_blocklist']
    else:
        bl = ROOT / DEFAULT_BLOCKLIST
    scrub(tree, bl, fails, label)  # check 1 — always first: it guards the outbound tree

    changed = False
    for e in manifest.get('entries', []):
        name = f"{label}:{e.get('practice', '?')}"
        local = ROOT / e.get('local_path', '')
        upstream = tree / e.get('upstream_path', '')
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
                    # Name every re-baselined entry: a 'synced' entry re-baselining
                    # here means its drift was never exported — silent absorption
                    # once masked a missed export for days.
                    print(f"  re-baselined [{name}] {e['local_path']}"
                          + ("  <-- was 'synced' and drifted: export the change to the vendored tree"
                             if status == 'synced' and e.get('local_sha256') else ""))
                    e['local_sha256'] = cur
                    if status == 'diverged':
                        e['status'] = 'synced'
                    changed = True
            elif not e.get('local_sha256'):
                warns.append(f"[{name}] no baseline hash — run --update-baseline")
            elif cur != e['local_sha256']:
                if status == 'synced':
                    fails.append(f"DRIFT: [{name}] {e['local_path']} changed since baseline while "
                                 f"status='synced' — export the change to {up.get('vendored_at', 'the vendored tree')} "
                                 f"and --update-baseline, or flip the entry to 'diverged'")
                else:
                    pending.append(f"[{name}] {e['local_path']} (status={status}) — pending export")
        elif gran == 'section':
            marker = e.get('section_marker', '')
            if marker and marker not in local.read_text(encoding='utf-8', errors='ignore'):
                warns.append(f"[{name}] section_marker not found in {e['local_path']}: '{marker}'")

    if update and changed:
        manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f"practice_audit [{label}]: baselines updated.")
    return len(manifest.get('entries', []))

def audit(update=False, only=None):
    fails, warns, pending = [], [], []
    if only:
        manifests = [ROOT / only]
    else:
        manifests = sorted((ROOT / 'process').glob('manifest*.json'))
    if not any(m.exists() for m in manifests):
        print("practice_audit FAIL: no manifest at process/manifest*.json "
              "(see process/upstream/INSTALL.md §5)")
        return 1
    n = 0
    claimed = set()
    for m in manifests:
        if not m.exists():
            print(f"practice_audit FAIL: no manifest at {m}")
            return 1
        n += audit_manifest(m, update, fails, warns, pending)
        claimed |= {e.get('local_path')
                    for e in json.loads(m.read_text(encoding='utf-8')).get('entries', [])}
    layout(fails, claimed)  # check 4 — root hygiene, once per audit

    for p in pending:
        print(f"pending: {p}")
    for w in warns:
        print(f"WARN: {w}")
    for f in fails:
        print(f"FAIL: {f}")
    if fails:
        print(f"\npractice_audit FAIL — {len(fails)} error(s).")
        return 1
    print(f"practice_audit OK: {len(manifests)} manifest(s), {n} entries; "
          f"{len(pending)} pending export; {len(warns)} warning(s).")
    return 0

if __name__ == '__main__':
    args = sys.argv[1:]
    only = None
    if '--manifest' in args:
        only = args[args.index('--manifest') + 1]
    sys.exit(audit(update='--update-baseline' in args, only=only))
