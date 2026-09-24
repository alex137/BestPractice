#!/usr/bin/env python3
"""practice_audit.py — audit the practice-export layer
(practice: practice-export-loop; practice: scrub-gate; practice: layered-practice-packs).

Runs from a dependent repo (script lives at process/upstream/tools/). A repo
may install several practice layers ("packs" -- (practice: layered-practice-packs)): the generic
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
     configured blocklist file that does not exist on disk FAILS — a
     configured-but-missing blocklist is a check that did not run, not a
     pass; only an explicit `scrub_blocklist: null` skips the check.

  2. DRIFT (baseline snapshots, practice: registry-source-of-truth). For each manifest entry with
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

  5. LOADER (the catalogue is actually in force). A repo that vendors the
     practice catalogue (process/upstream/practices/) must also run the
     loader over it: precedent.json declares a `level: "universal"` source,
     and the root instructions file carries the generated loader block.
     Either missing FAILS. Without both, every vendored practice is text on
     disk that no session ever reads -- no resident block, no occasion
     index, no gates -- while the install looks complete and this audit,
     until 2026-09-23, passed. That is the classic INSTALL.md section 1
     install, retired that day as an install path: a real consumer ran it
     for a day, took an update, and its sessions reported the rules as "a
     vendored copy of the upstream catalogue, not something this repo
     adopted". The remedy is the migration, never an exemption: there is
     deliberately no flag or manifest key that silences this check.

  6. DECLINED (a decline covers the text it was made against, practice:
     current-rule-governs). An entry with status "declined" records an
     upstream practice this repo chose not to take, with the sha256 of the
     upstream file as it stood then (declined_upstream_sha256) and the
     reason in notes. When the vendored upstream file has changed since, or
     is gone, the decline no longer covers the rule in force and this FAILS
     until somebody decides again: adopt it, or keep declining and record
     the new hash with --redecide NAME. --update-baseline never does that for
     you, because re-baselining a decline unread is the failure this check
     exists for. Incident, 2026-09-24: a consumer declined upstream's
     merge-keyword practice as a "duplicate" of a personal rule; upstream
     then replaced it with a broader one, two later syncs carried the
     decline forward unread, and a session refused a command the rule in
     force plainly authorized.

Run:  python3 process/upstream/tools/practice_audit.py                    # gate (all manifests)
      python3 process/upstream/tools/practice_audit.py --update-baseline  # re-record hashes
      python3 process/upstream/tools/practice_audit.py --manifest process/manifest.json  # one manifest
      python3 process/upstream/tools/practice_audit.py --loader-notice    # check 5 only, never fails
                                                    # (what tools/bootstrap.sh prints at session start)
      python3 process/upstream/tools/practice_audit.py --redecide NAME    # after re-deciding a decline:
                                                    # record the upstream file's current hash
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
    """-> ((patterns, exempt_prefixes) or None, reason). `path is None` is an explicit opt-out
    (`scrub_blocklist: null`) -- a deliberate choice, distinct from a
    configured path that simply doesn't exist on disk, which is a check
    that did not run, not a pass. Conflating the two (both used to return
    plain `None`) meant a manifest that never opted out, but whose
    blocklist file went missing -- a typo'd path, a file never committed --
    scrubbed nothing and reported success, same shape as the leak_gate.py
    bug this mirrors."""
    if path is None:
        return None, 'opt_out'
    if not path.exists():
        return None, 'missing'
    pats, exempt = [], []
    for i, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        # A leading "!" exempts a path prefix instead of adding a pattern.
        # Needed because a blocklist term can legitimately appear in the
        # vendored tree's own writing ABOUT that term -- upstream's decision
        # record explaining the leak-gate vocabulary quotes the very
        # identifiers it explains, and that arrived FROM upstream rather
        # than leaking TO it (2026-09-06, in a real consumer, where it was
        # the last thing standing between the repo and a clean gate). The
        # exemption sits in the blocklist because that is the one file a
        # consuming repo owns and reviews for exactly this question.
        if line.startswith('!'):
            exempt.append(line[1:].strip())
            continue
        try:
            pats.append(re.compile(line))
        except re.error as e:
            print(f"WARN: blocklist line {i} is not a valid regex ({e}): {line}")
    return (pats, tuple(exempt)), 'ok'

def scrub(tree, blocklist_path, fails, label):
    loaded, reason = load_blocklist(blocklist_path)
    pats, exempt = loaded if loaded else (None, ())
    if reason == 'missing':
        fails.append(f"SCRUB: [{label}] blocklist configured at "
                     f"{blocklist_path.relative_to(ROOT)} but the file does not "
                     f"exist — the scrub did not run, which is not a pass")
        print(f"scrub [{label}]: FAIL — configured blocklist "
              f"{blocklist_path.relative_to(ROOT)} is missing.")
        return
    if pats is None:
        print(f"scrub [{label}]: skipped — pack opted out (scrub_blocklist: null).")
        return
    hits = 0
    for path in sorted(tree.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXT:
            continue
        rel = path.relative_to(ROOT)
        if any(str(rel).replace('\\', '/').startswith(e) for e in exempt):
            continue
        for i, line in enumerate(path.read_text(encoding='utf-8', errors='ignore').splitlines(), 1):
            for pat in pats:
                if pat.search(line):
                    fails.append(f"SCRUB: {rel}:{i} matches blocklist /{pat.pattern}/: {line.strip()[:90]}")
                    hits += 1
                    break
    if not hits:
        extra = f", {len(exempt)} path exemption(s)" if exempt else ""
        print(f"scrub OK [{label}]: {tree.relative_to(ROOT)}/ clean against "
              f"{len(pats)} blocklist pattern(s){extra}.")

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

def _frontmatter(path):
    """-> {key: raw value} for a practice file's frontmatter, or {}. Kept
    to the flat `key: value` lines this check reads (status, in_force_at,
    slug, supersedes); a vendored tree may predate any shared reader."""
    try:
        text = path.read_text(encoding='utf-8', errors='replace')
    except OSError:
        return {}
    if not text.startswith('---'):
        return {}
    fm = {}
    for line in text.split('\n')[1:]:
        if line.strip() == '---':
            break
        m = re.match(r'^([a-z_]+):\s*(.*)$', line)
        if m:
            fm[m.group(1)] = m.group(2).strip().strip('"')
    return fm


def _successors(tree, slug):
    """Slugs of vendored practices that name `slug` in `supersedes:`."""
    out = []
    for f in sorted((tree / 'practices').glob('*.md')):
        sup = _frontmatter(f).get('supersedes', '')
        if re.search(r'["\s\[,]' + re.escape(slug) + r'["\s\],]', f' {sup} '):
            out.append(f.stem)
    return out


def stale_declines(manifest_path):
    """-> [(entry_name, sentence)] for every "declined" entry whose decision
    no longer covers the upstream file (practice: current-rule-governs).
    Shared with checkin.py so the update that moves the upstream file says
    so at once, instead of one audit later."""
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    label = manifest_path.stem.replace('manifest_', '').replace('manifest', 'upstream') or 'upstream'
    tree = ROOT / manifest.get('upstream', {}).get('vendored_at', 'process/upstream')
    out = []
    for e in manifest.get('entries', []):
        if e.get('status') != 'declined':
            continue
        name = f"{label}:{e.get('practice', '?')}"
        rel = e.get('upstream_path') or ''
        upstream = tree / rel
        if not rel:
            out.append((name, 'declined with no upstream_path, so nothing can tell '
                              'when the practice it declined has moved on'))
            continue
        if not upstream.is_file():
            out.append((name, f'declined {rel}, which is no longer in the vendored tree '
                              f'(renamed, merged or removed upstream) -- find what carries '
                              f'that rule now and decide again'))
            continue
        recorded = e.get('declined_upstream_sha256')
        if not recorded:
            out.append((name, f'declined {rel} with no declined_upstream_sha256, so '
                              f'nothing can tell whether the decision still covers it -- '
                              f'decide again against the current file, then --redecide '
                              f'{e.get("practice", "?")}'))
            continue
        if sha256(upstream) == recorded:
            continue
        fm = _frontmatter(upstream)
        now = []
        status = fm.get('status', '')
        if status and status != 'active':
            where = fm.get('in_force_at', '')
            now.append(f'it is now status: {status}'
                       + (f', in force at {where}' if where and where not in ('null', 'none') else ''))
        slug = fm.get('slug') or pathlib.Path(rel).stem
        succ = _successors(tree, slug)
        if succ:
            now.append('superseded by ' + ', '.join(succ))
        out.append((name, f'declined {rel}, and that file has changed upstream since'
                          + (f' ({"; ".join(now)})' if now else '')
                          + '. The decline covers the old text only: read the current '
                          f'rule, adopt it or decide again, then --redecide '
                          f'{e.get("practice", "?")} and update notes with the new reason'))
    return out


def redecide(manifest_paths, practice):
    """Record the current upstream hash on one declined entry. The person
    re-deciding is expected to have updated `notes` in the same change;
    this only stops the check firing on a decision somebody actually made."""
    hits = 0
    for mp in manifest_paths:
        manifest = json.loads(mp.read_text(encoding='utf-8'))
        tree = ROOT / manifest.get('upstream', {}).get('vendored_at', 'process/upstream')
        for e in manifest.get('entries', []):
            if e.get('practice') != practice or e.get('status') != 'declined':
                continue
            upstream = tree / (e.get('upstream_path') or '')
            if not upstream.is_file():
                print(f"practice_audit --redecide: {practice}'s upstream_path "
                      f"{e.get('upstream_path')!r} is not in the vendored tree; point "
                      f"the entry at what carries the rule now first.")
                return 1
            e['declined_upstream_sha256'] = sha256(upstream)
            mp.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + '\n',
                          encoding='utf-8')
            print(f"practice_audit --redecide: recorded the current hash of "
                  f"{e['upstream_path']} on {practice}. Make sure notes says why it "
                  f"is still declined against THIS version.")
            hits += 1
    if not hits:
        print(f"practice_audit --redecide: no entry with practice {practice!r} and "
              f"status 'declined'.")
        return 1
    return 0


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
        if e.get('status') == 'declined':
            # Check 6 handles these below. A decline has no local copy to
            # hash, and its notes are the only record of why.
            if not e.get('notes'):
                warns.append(f"[{name}] declined without notes — say why it was declined")
            continue
        # `or ''`, NOT a .get default: .get returns None for a key that is
        # PRESENT AND NULL, and `tree / None` raises TypeError rather than
        # failing the check -- so a manifest entry with no upstream
        # counterpart crashed the audit instead of being audited. Reported
        # 2026-09-21 by a consuming repo that added the first such entry
        # (a local-only action with nothing upstream to compare against)
        # and had to write "" rather than null to get past it. The manifest
        # is somebody else's file; it does not owe us a particular spelling
        # of absent.
        local = ROOT / (e.get('local_path') or '')
        upstream = tree / (e.get('upstream_path') or '')
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
                    # once masked a missed export for days. A 'diverged' entry is a
                    # deliberate, permanent "never export this" marker (practice:
                    # registry-source-of-truth) — a hash mismatch alone (which can be a
                    # stale baseline, not a new edit) is never grounds to infer the
                    # divergence is resolved, so status is re-baselined but left
                    # untouched here; flip it to 'synced' by hand once you have
                    # actually confirmed the divergence is gone.
                    print(f"  re-baselined [{name}] {e['local_path']}"
                          + ("  <-- was 'synced' and drifted: export the change to the vendored tree"
                             if status == 'synced' and e.get('local_sha256') else "")
                          + ("  <-- was 'diverged': status left as-is, hash only re-baselined; "
                             "flip to 'synced' by hand if the divergence is actually resolved"
                             if status == 'diverged' else ""))
                    e['local_sha256'] = cur
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

    # check 6 -- a decline covers the upstream text it was made against
    stale = stale_declines(manifest_path)
    for name, sentence in stale:
        fails.append(f"DECLINED: [{name}] {sentence}")
    n_declined = sum(1 for e in manifest.get('entries', []) if e.get('status') == 'declined')
    if n_declined and not stale:
        print(f"declined OK [{label}]: {n_declined} decline(s), each still made "
              f"against the current upstream file.")
    return len(manifest.get('entries', []))

LOADER_MARKER = '<!-- BEGIN GENERATED: precedent-loader -->'
MIGRATION_DOC = ('https://github.com/alex137/BestPractice/blob/precedent-beta-v01/'
                 'spec/MIGRATING_EXISTING_INSTALLS.md')


def loader_gaps(root):
    """What stops the vendored catalogue from being in force, as a list of
    plain sentences -- empty when it is in force, or when this repo vendors
    no catalogue at all (a pack-only layer has nothing for a loader to
    load). Shared with checkin.py, so the update that vendors the catalogue
    says the same thing this audit fails on."""
    if not (root / 'process' / 'upstream' / 'practices').is_dir():
        return []
    gaps = []
    try:
        cfg = json.loads((root / 'precedent.json').read_text(encoding='utf-8'))
    except (OSError, ValueError):
        cfg = None
    sources = cfg.get('sources', {}) if isinstance(cfg, dict) else {}
    if isinstance(sources, dict):
        sources = list(sources.values())
    if not any(isinstance(s, dict) and s.get('level') == 'universal'
               for s in sources or []):
        gaps.append('precedent.json declares no `level: "universal"` source, so '
                    'nothing resolves process/upstream/practices/')
    if not any(LOADER_MARKER in (root / n).read_text(encoding='utf-8', errors='replace')
               for n in ('AGENTS.md', 'CLAUDE.md') if (root / n).is_file()):
        gaps.append('neither AGENTS.md nor CLAUDE.md carries the generated '
                    'loader block, so no session is ever shown a practice')
    return gaps


def loader(fails):
    gaps = loader_gaps(ROOT)
    if not gaps:
        print("loader OK: the vendored catalogue is resolved and loaded "
              "(or no catalogue is vendored).")
        return
    fails.append(
        "LOADER: this repo vendors Precedent's practice catalogue but does not "
        "run it -- " + "; and ".join(gaps) + ". NONE of the vendored practices "
        "are in force in sessions here. This is the classic install "
        "(INSTALL.md section 1), retired 2026-09-23. Migrate the repo onto the "
        "loader, whole, in one change: " + MIGRATION_DOC)


def audit(update=False, only=None):
    fails, warns, pending = [], [], []
    if only:
        manifests = [ROOT / only]
    else:
        manifests = sorted((ROOT / 'process').glob('manifest*.json'))
    if not any(m.exists() for m in manifests):
        # Distinguish "this repo does not vendor anything" from "this repo
        # vendors something and lost its manifest". Both used to FAIL, so the
        # audit was permanently red in the upstream repo itself -- which is
        # not a dependent repo and has nothing to export from. A permanently
        # red gate stops being read, and then it is absent when a real
        # dependent repo drops its manifest.
        if not (ROOT / 'process').is_dir():
            print("practice_audit NOT APPLICABLE: this repo vendors no practice "
                  "layer (no process/ directory), so there is no export loop to "
                  "audit. This is the expected state in the upstream repo itself.")
            return 0
        print("practice_audit FAIL: process/ exists but there is no manifest at "
              "process/manifest*.json — a vendored tree with no manifest is "
              "unaudited (see process/upstream/INSTALL.md §5)")
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
    loader(fails)           # check 5 — the catalogue is actually in force

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
    # `--help` is what anyone types first; before 2026-09-06 this ran the
    # whole audit instead of answering. The module docstring is the usage.
    if any(a in ('--help', '-h') for a in args):
        print((__doc__ or '').strip())
        sys.exit(0)
    if '--loader-notice' in args:
        # Session start's copy of check 5: printed to stdout, where the
        # SessionStart hook puts it in front of the session, and exit 0
        # whatever it finds -- a bootstrap that blocks startup is worse
        # than what it reports.
        gaps = loader_gaps(ROOT)
        if gaps:
            print("PRECEDENT IS NOT RUNNING IN THIS REPO. It vendors the practice "
                  "catalogue under process/upstream/, but " + "; and ".join(gaps) +
                  ". None of those practices is in force in this session -- do not "
                  "tell anyone they are. Say so to the person first thing, and "
                  "offer the migration (the classic install was retired "
                  "2026-09-23): " + MIGRATION_DOC)
        sys.exit(0)
    only = None
    if '--manifest' in args:
        only = args[args.index('--manifest') + 1]
    if '--redecide' in args:
        i = args.index('--redecide')
        if i + 1 >= len(args):
            sys.exit('practice_audit: --redecide needs the entry\'s practice name')
        paths = [ROOT / only] if only else sorted((ROOT / 'process').glob('manifest*.json'))
        sys.exit(redecide(paths, args[i + 1]))
    sys.exit(audit(update='--update-baseline' in args, only=only))
