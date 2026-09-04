<!-- Last updated: 2026-09-04 (Buenos Aires) by the session that closed the "I have nothing yet" onboarding gap -->

# Bootstrapping a Brand-New Individual or Team Set

This is the generalized, repeatable procedure for the case
[the guided-install conversation](../SETUP.md) step 2 and
[INSTALL.md](../INSTALL.md) step 9 both used to leave as a dead end: an
adopter with **no** individual practice repo and **no** team practice repo
yet, who wants one. It exists because every other piece of documentation
about individual/team sources — this document included until now —
assumed the repo already existed.

**This is a different document from
[PRIVATE_SETS_BRIEF.md](PRIVATE_SETS_BRIEF.md), on purpose.** That brief
records how `themorgan/precedent-individual` and
`themorgan/precedent-team-maintainers` were actually populated: bespoke,
one-off work, done from a session opened directly against those two
already-*existing* private repos, carrying RepoPersonalPreferences' (RPP)
real 46 rules across.
It is a historical record of this project's own phase-3 work, not a
procedure anyone else should follow. This document is the opposite: no
private content, no existing repo assumed, meant to be followed by any
adopter, any number of times.

## What the tool does, and does not do

[`tools/precedent_bootstrap_source.py`](../tools/precedent_bootstrap_source.py)
mechanizes everything that does not require credentials this tool can't
assume a session has:

- Copies [`templates/practice-set-individual/`](../templates/practice-set-individual/)
  or [`templates/practice-set-team/`](../templates/practice-set-team/) into
  a target directory, filling in the owner's name (and, for a team, its
  first approver's name and GitHub handle) wherever the skeleton names a
  placeholder.
- Refuses to write into a non-empty destination without `--force true`.
- Prints — or, opted in with `--write-user-config true` /
  `--write-repo-config PATH`, writes — the exact wiring the next step
  needs: the `~/.config/precedent/config.json` `individual` block, or the
  consuming project's `precedent.json` `"sources"` entry.

**It never touches a git remote or any hosting API.** Creating the actual
repository — `gh repo create`, or a few clicks on GitHub — needs
credentials or a platform capability this tool can't assume any given
session has, and guessing wrong there is worse than asking. That step
stays explicit, below.

## The procedure

### For an individual set

1. Pick a name (by convention, `<your-name>-individual` or similar — see
   [PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md#what-morgan-needs-to-do)'s
   naming convention for the pattern this project itself used).
2. Create a **private** repository under the person's own account. If the
   session has the access to do this itself (a GitHub App/token scoped for
   repo creation), do it directly; otherwise hand the person the exact
   command (`gh repo create <name> --private`) or the exact click-path
   (github.com → **New repository** → private → no template).
3. Run:
   ```
   python3 tools/precedent_bootstrap_source.py --level individual \
       --name <name> --dest <local clone path>
   ```
4. `cd` into the destination, `git init` (if step 2's repo creation didn't
   already leave a clone), commit everything, add the remote from step 2,
   push.
5. Either pass `--write-user-config true` on the bootstrap command (step 3)
   to write `~/.config/precedent/config.json` directly, or copy the printed
   snippet there by hand. **Never** write this into any shared project's
   own tracked files — see `precedent_resolve.py`'s own header for why
   that's refused outright, not just discouraged.
6. Fill in `leak-blocklist.txt` with the person's own private terms, then
   `export PRECEDENT_LEAK_BLOCKLIST=<path>` and
   `git config precedent.requireVocabulary true` in every shared project
   they work in.
7. Delete `practices/example-starter.md` once a real first practice
   replaces it.

### For a team set

Same shape, with two differences: the repo is created once per team (not
per person), and it needs at least one approver at creation time.

1. Pick a name (by convention, `<team-name>-maintainers` or similar).
2. Create a **private** repository, shared with the team's members as
   collaborators. Same access caveat as step 2 above.
3. Run:
   ```
   python3 tools/precedent_bootstrap_source.py --level team \
       --name <name> --dest <local clone path> \
       --approver "Full Name:github-handle"
   ```
   (Comma-separate multiple `name:handle` pairs to seed more than one
   approver at creation — still fine per
   [PRACTICE_ENGINE_PLAN.md's Stage 4](../PRACTICE_ENGINE_PLAN.md#stage-4--approval-by-level):
   "whoever creates a team set is its first approver. No ceremony.")
4. `cd` into the destination, `git init`/commit/push, same as the
   individual case.
5. Wire it into the **consuming project's own tracked `precedent.json`**
   (this one *is* meant to be shared — everyone on the project reads it):
   either pass `--write-repo-config <project root>` on the bootstrap
   command, or add the printed `"sources"` entry by hand, per
   [INSTALL.md step 9](../INSTALL.md#9-ask-about-team-and-individual-practice-sources).
6. On a hosted/ephemeral session where nothing under the project's git
   checkout persists between sessions, wire the sibling-checkout access
   the same way [spec/MIGRATING_EXISTING_INSTALLS.md](MIGRATING_EXISTING_INSTALLS.md)'s
   step 4 already documents for an existing team source — this is the
   identical gap, not a new one.
7. Fill in `leak-blocklist.txt` and `approvers.json` for real, delete
   `practices/example-starter.md` once a real first practice replaces it.

## What this does not close

- **Repo creation itself stays a human/session step**, per the "what the
  tool does not do" section above — this document does not pretend
  otherwise.
- **This is not [`spec/PHASE6_BRIEF.md`](PHASE6_BRIEF.md) item 2** (wiring
  the full candidate/proposal pipeline — `precedent_candidate.py`,
  `precedent_promote.py`, `precedent_land.py` — into a consuming repo).
  That item is about *proposing new practices upward* once a set already
  exists; this document is about the set existing in the first place. A
  freshly bootstrapped set works today with direct edits (as
  `examples/practice-set/` already shows) — the creation-pipeline tooling
  is a separate, still-open piece of work.
- **Not rehearsed against a real, brand-new external adopter yet** — the
  harness check (`check_bootstrap_source_produces_resolvable_set` in
  `tools/verify_harness.py`) proves the tool's *output* resolves cleanly
  against a synthetic consumer repo; it does not prove the full
  human-in-the-loop procedure above reads well to someone who has never
  seen Precedent before. Worth a real rehearsal the same way
  [spec/PHASE6_BRIEF.md](PHASE6_BRIEF.md) item 4 flags for the loader
  install path generally.
