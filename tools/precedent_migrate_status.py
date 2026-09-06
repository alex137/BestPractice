#!/usr/bin/env python3
"""precedent_migrate_status.py — classify practices carrying the OLD status
vocabulary, where `retired` meant two different things. Reports by default;
writes only what it was explicitly told to write.

WHY THIS EXISTS. Before `in_force_at:` (2026-09-06,
decisions/2026-09-06-deduplication-not-retirement.md), `status: retired` was
the only way to record that a practice stopped applying in a source, and it
covered BOTH:

  - a redundant COPY, where the rule is fully in force from another source
    -- the common case, and every correct use of the old status;
  - a rule withdrawn everywhere -- the rare case, and the one attempt at it
    was the mistake that dropped a live per-commit check for a day.

A legacy record does not say which. That is not a detail to paper over: the
whole point of the new vocabulary is that "deduplicated safely" and "dropped
and forgotten" stop being indistinguishable, and a migration that GUESSED
would re-introduce exactly the resemblance-based reasoning the rename
removes. So this tool proposes, shows its evidence, and refuses to decide
the undetermined cases by itself.

WHY IT IS IN THE VENDORED ENGINE. The legacy records are in the private
practice sets, not here -- BestPractice's own catalogue never had one. A
migration that only exists upstream cannot reach the repos that need it, so
this ships in precedent_vendor_engine.py's ENGINE_FILES and runs inside each
set, against that set's own files.

WHAT IT PROPOSES, AND WHAT IT WILL NOT.

  same-slug match     A practice with the SAME slug resolves active in one
                      of the --against sources. Proposed as
                      `deduplicated` + `in_force_at: <slug>`. High
                      confidence: the identical rule is in force elsewhere.
  no match            Reported as UNDETERMINED, with the practice's own
                      `## Story` printed as evidence, because the old
                      convention put the forwarding address there in prose.
                      NOT parsed -- a regex over prose is a guess wearing a
                      mechanism's clothes. A person reads it and decides.

A renamed successor (precedent-team-maintainers' `header-caps`, whose rule
is in force at universal as `headline-capitalization`) is UNDETERMINED by
construction, and correctly so: nothing mechanical connects the two names.
Name it with --set.

Usage:
  # report only -- always start here
  precedent_migrate_status.py --repo . --against ../precedent-individual,..

  # then write the decisions, one flag per practice
  precedent_migrate_status.py --repo . --against .. \\
      --set bestpractice-sync=bestpractice-sync \\
      --set header-caps=headline-capitalization --apply

  --set SLUG=TARGET   TARGET is another practice's slug, or `engine` (the
                      mechanism absorbed the rule), or `none` (withdrawn
                      everywhere -- requires a non-empty ## Story, and is
                      refused without one).

Exit 0 when nothing is left to migrate; 1 while any legacy record remains,
so this doubles as the compliance check a source set otherwise has no way to
run (verify_harness.py is not vendored).

`--apply` writes one file at a time, so an interrupted run leaves a PARTIAL
migration. That is deliberate rather than all-or-nothing: each rewrite is
independent, and re-running simply continues with whatever is still
unmigrated -- a half-applied run is recoverable by running again, and every
record it already converted is correct. Check `git status` after an
interrupted run rather than assuming nothing was written.
"""
import pathlib
import re
import sys

_ENGINE_DIR = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(_ENGINE_DIR))
import split_practices as sp        # noqa: E402
import build_views as bv            # noqa: E402


def legacy_records(practices_dir):
    """-> [(path, fm, sections)] for every practice carrying a non-active
    status with no `in_force_at:`. A record that HAS the field was written
    or migrated under the new vocabulary and is left alone, whatever it
    says -- validating those is status_contract_violation's job, not this
    tool's."""
    out = []
    for f in sorted(pathlib.Path(practices_dir).glob('*.md')):
        try:
            fm, sections = sp._read_practice_file(f)
        except sp.PracticeFileError:
            continue
        if bv.is_in_force(fm):
            continue
        if bv._json_str(fm.get('in_force_at', '')):
            continue
        out.append((f, fm, sections))
    return out


def active_slugs(against_paths):
    """Every slug that is ACTIVE in one of the named sources, with where it
    was found. Active rather than merely present: a surviving copy that is
    itself dropped is not a surviving copy, which is the deduplication that
    silently loses a rule."""
    found = {}
    for p in against_paths:
        d = pathlib.Path(p) / 'practices'
        if not d.is_dir():
            continue
        for f in sorted(d.glob('*.md')):
            try:
                fm, _sections = sp._read_practice_file(f)
            except sp.PracticeFileError:
                continue
            if bv.is_in_force(fm):
                found.setdefault(fm.get('slug', f.stem), str(p))
    return found


def _rewrite(path, status, target):
    """Set `status:` and `in_force_at:` in the frontmatter, in place,
    preserving the file's own column alignment and touching nothing else.
    `in_force_at:` is inserted directly after `status:` when the field is
    absent, which is where every emitter in this engine writes it.

    Operates ONLY between the opening `---` and the closing one: a practice
    body can legitimately contain a line beginning `status:` (several of
    this catalogue's own do, quoting frontmatter in prose), and a
    whole-file replace would corrupt it."""
    text = path.read_text(encoding='utf-8')
    if not text.startswith('---\n'):
        raise sp.PracticeFileError(f"{path}: no opening frontmatter fence.")
    end = text.index('\n---\n', 4)
    head, fm_text, tail = text[:4], text[4:end], text[end:]

    lines = fm_text.split('\n')
    status_at = next((i for i, l in enumerate(lines) if l.startswith('status:')), None)
    if status_at is None:
        raise sp.PracticeFileError(f"{path}: frontmatter has no `status:` field.")
    pad = re.match(r'status:(\s*)', lines[status_at]).group(1) or ' '
    lines[status_at] = f"status:{pad}{status}"

    target_at = next((i for i, l in enumerate(lines) if l.startswith('in_force_at:')), None)
    if target_at is None:
        lines.insert(status_at + 1, f"in_force_at: {target}")
    else:
        lines[target_at] = f"in_force_at: {target}"

    path.write_text(head + '\n'.join(lines) + tail, encoding='utf-8')


def report(repo, against_paths, decisions, apply_):
    practices_dir = pathlib.Path(repo) / 'practices'
    if not practices_dir.is_dir():
        sys.exit(f"precedent_migrate_status FAIL: no practices/ under {repo}")
    records = legacy_records(practices_dir)
    if not records:
        print("precedent_migrate_status: no legacy status records -- "
              "every non-active practice carries an in_force_at:.")
        return 0

    live = active_slugs(against_paths)
    if not against_paths:
        print("NOTE: no --against sources given, so nothing can be verified as "
              "in force. Proposals below are shape only.\n")

    determined, undetermined, written = [], [], []
    for path, fm, sections in records:
        slug = fm.get('slug', path.stem)
        old = bv.practice_status(fm)
        chosen = decisions.get(slug)

        if chosen is None and slug in live:
            chosen, why = slug, f"same slug is active in {live[slug]}"
        elif chosen is not None:
            why = "named with --set"
        else:
            why = None

        if chosen is None:
            undetermined.append((path, slug, old, sections.get('story', '')))
            continue

        if chosen == bv.IN_FORCE_AT_NOWHERE:
            new_status = bv.RETIRED_STATUS
            if not sections.get('story', '').strip():
                undetermined.append(
                    (path, slug, old,
                     "REFUSED: --set ...=none needs a ## Story saying why nobody "
                     "wants this rule anywhere. Retirement is the one status no "
                     "mechanism can verify for you."))
                continue
        else:
            new_status = bv.DEDUPLICATED_STATUS
            if chosen != bv.IN_FORCE_AT_ENGINE and against_paths and chosen not in live:
                undetermined.append(
                    (path, slug, old,
                     f"REFUSED: in_force_at: {chosen!r} is not active in any "
                     f"--against source. A surviving copy that is itself gone "
                     f"is not a surviving copy."))
                continue

        determined.append((path, slug, old, new_status, chosen, why))

    for _path, slug, old, new_status, target, why in determined:
        print(f"{slug}: status: {old} -> {new_status}, in_force_at: {target}   ({why})")
    for path, slug, old, story in undetermined:
        print(f"\nUNDETERMINED  {slug} (status: {old}) — {path}")
        if story.startswith('REFUSED'):
            print(f"  {story}")
        else:
            print("  Nothing mechanical connects it to a surviving practice. The old "
                  "convention put the forwarding address in ## Story; it is printed "
                  "below as evidence, NOT parsed. Decide, then pass "
                  f"--set {slug}=<slug|engine|none>.")
            body = story.strip() or '(## Story is empty — there is no recorded reason.)'
            for line in body.split('\n')[:12]:
                print(f"  | {line}")

    if apply_:
        for path, slug, _old, new_status, target, _why in determined:
            _rewrite(path, new_status, target)
            written.append(slug)
        print(f"\napplied: {len(written)} practice(s) rewritten "
              f"({', '.join(written) if written else 'none'}).")
    elif determined:
        print(f"\n{len(determined)} determined, not written — re-run with --apply.")

    remaining = len(undetermined) + (0 if apply_ else len(determined))
    if remaining:
        print(f"{remaining} record(s) still carrying the old vocabulary.")
    return 1 if remaining else 0


def _parse_args(argv):
    if any(a in ('--help', '-h') for a in argv):
        print((__doc__ or '').strip())
        raise SystemExit(0)
    repo, against, decisions, apply_ = '.', [], {}, False
    i = 0
    while i < len(argv):
        tok = argv[i]
        if tok == '--apply':
            apply_ = True
            i += 1
            continue
        if i + 1 >= len(argv):
            sys.exit(f"precedent_migrate_status FAIL: {tok!r} needs a value.")
        val = argv[i + 1]
        if tok == '--repo':
            repo = val
        elif tok == '--against':
            against = [p for p in val.split(',') if p]
        elif tok == '--set':
            if '=' not in val:
                sys.exit(f"precedent_migrate_status FAIL: --set wants SLUG=TARGET, got {val!r}")
            k, v = val.split('=', 1)
            decisions[k] = v
        else:
            sys.exit(f"precedent_migrate_status FAIL: unknown flag {tok!r}")
        i += 2
    return repo, against, decisions, apply_


def main():
    return report(*_parse_args(sys.argv[1:]))


if __name__ == '__main__':
    sys.exit(main())
