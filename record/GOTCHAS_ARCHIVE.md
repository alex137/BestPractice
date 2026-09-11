---
title:         Build-environment Gotchas — the Full Text
kind:          record
status:        live
opened:        2026-09-08
closed:        null
superseded_by: null
supersedes:    []
audience:      session
summary:       Every gotcha whose live entry was shortened or removed, preserved verbatim, with the verdict that put it here.
---

# Build-environment Gotchas — the Full Text

**Nothing was deleted.** Every entry below is the verbatim text that stood in
[AGENTS.md](../AGENTS.md)'s gotchas section before the 2026-09-08 pass. An
entry is here because a session no longer needs all of it *before* it starts
work — not because any of it stopped being true.

**Why an archive and not a deletion.** A gotcha's payload is the **story of
what failed**, and [environment-gotchas](../practices/environment-gotchas.md)
says so: a fix with no failure attached is a fact you cannot judge, and the
next session undoes it the moment it looks wrong. Deleting the settled
entries would leave a live section of unexplained rules. So the stories stay,
in full, one link away — **only the loading changed.**

**Three verdicts.** `archived` — the trap cannot fire any more, verified
against the tree rather than taken from the entry's own claim; no live entry
remains. `compressed` — the trap is live and a shorter entry stands in
AGENTS.md; the history that made the original long is here. `rewritten` — the
entry had grown into a self-contradiction; **read its verdict before any
paragraph of it.**

**If you are here because a symptom matched:** for a `compressed` entry, the
live half in AGENTS.md is the authority on what to do now, and this is
background. For an `archived` one, check the dates against the tree before
acting on anything.

**Four entries are not here at all** — they were short and wholly live, so
they stand in AGENTS.md unchanged.

**Later passes append rather than rewrite this file**, so the paragraphs above
describe the 2026-09-08 pass that started it and not the whole of what is
here. Entries are numbered in the order they arrived; a gap in the numbering
is an entry that was never archived, not one that went missing. The most
recent pass is 2026-09-11, which moved six entries — the three largest in the
section among them — after verifying each against the tree rather than against
its own claim about itself.

**Link targets in an archived entry are repointed** from the repo root to
`../`, so they resolve from this directory
([rename-updates-links](../practices/rename-updates-links.md)). Nothing else
about the text is touched: that is the only edit an entry gets on its way
here.


## 2. A git helper that returns stdout and drops the exit code will hand you a

**Verdict: `compressed`.** Live, and the most-repeated bug in the project -- it fired twice on 2026-09-08 alone. The live entry now states both shapes of it; the inventory of the five tools the same one-liner was found in is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A git helper that returns stdout and drops the exit code will hand you a
  ref *name* where a commit hash belongs.** `git rev-parse <missing-ref>` exits
  non-zero but *prints the ref you asked for* on stdout, so
  `_git(...'rev-parse', ref) or <fallback>` never falls back: it binds the
  truthy string `origin/precedent-beta-v01` and carries it forward as a hash.
  Reached continuous integration on 2026-09-06 as `precedent-beta-v01 @ origin/prece has no
  tools/build_views.py` — a 12-char truncation of a ref name. Use
  `rev-parse --verify --quiet` (silent, exit 1) whenever a ref may be absent.
  Note the trigger: a *non-repo* prints nothing, so the plain form looks fine
  for years — it only echoes on an **unborn `HEAD`** (a repo with no commits) or
  a missing ref, which is why this survived so long. Audited across
  [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) on
  2026-09-06 and found twice more: `status()` reported a clone that simply has
  no `SOURCE_BRANCH` as *"upstream has moved — run `refresh`"*, a false alarm
  wired to what was then a destructive remedy; and `seed()` recorded
  `source_commit: "HEAD"` into `ENGINE_MANIFEST.json`, after which every later
  comparison read as "moved" forever. A sweep found the same one-liner in
  [tools/routing_audit.py](../tools/routing_audit.py), where it was persisting a
  review record at commit `"HEAD"`.
  The same swallowed exit code hid a failing `git checkout` in a dirty tree
  during the very session that fixed this, making a broken negative control
  look like a passing test — so treat "the command reported nothing" as no
  evidence at all.

</details>

## 3. A repository attached mid-session clones single-branch, so every

**Verdict: `compressed`.** Live for any repo attached mid-session. The verification detail behind the self-applying refspec repair is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A repository attached mid-session clones single-branch, so every
  branch you create there reads as "unpushed" forever — including to a
  Stop hook that then blocks the turn.** `add_repo` hands you a
  `git clone --depth 1` whose only refspec is
  `+refs/heads/main:refs/remotes/origin/main`. Push a feature branch and
  the push genuinely succeeds, but no `origin/<branch>` ref is ever
  written, so `git rev-list origin/<branch>..HEAD` cannot resolve and every
  freshness check reports the branch as having unpushed commits with no
  remote counterpart. 2026-09-06: this fired on both consumer repos after
  their work was already safely on GitHub, and the honest-looking remedy —
  push again — changes nothing, because the push was never the problem.
  A second trap sits on top of it: `add_repo`'s clone URL is lowercased
  (the owner and repo name lowercased), so GitHub answers with
  `remote: This repository moved`, which reads like the cause and is not.
  Confirm with `git ls-remote origin refs/heads/<branch>` — that talks to
  the server and ignores local refs entirely — then repair the clone rather
  than re-pushing:
  `git config --unset-all remote.origin.fetch`,
  `git config --add remote.origin.fetch '+refs/heads/*:refs/remotes/origin/*'`,
  a bounded `git fetch --depth=50 origin <branch>`, and
  `git branch --set-upstream-to=origin/<branch>`. Setting the remote URL to
  the canonical capitalization at the same time stops the misleading
  redirect notice.
  **The refspec half of that repair now applies itself** — 2026-09-06,
  [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh) here and
  [templates/bootstrap.sh](../templates/bootstrap.sh) for dependent repos both
  widen `remote.origin.fetch` at session start when it carries no
  `refs/heads/*` mapping, before the freshness block runs. It is local
  config only, idempotent, and announced on stderr rather than done
  silently. Verified against a real `--single-branch` clone: pushing a
  feature branch from one left `git rev-list origin/feature..HEAD` unable
  to resolve at all, and the repair plus one fetch made it answer `0`. The
  clone-URL capitalization half is *not* automated — nothing local knows
  the canonical spelling — so that stays a manual `git remote set-url`.

</details>

## 4. A tool handed a clone as a *source* can still check that clone out from

**Verdict: `archived`.** Fixed 2026-09-06, verified 2026-09-08: checkin.py contains no live `git checkout` call at all -- every remaining occurrence is prose in a comment. update() reads the source ref with `git archive`, asserted in verify_harness.py with negative controls. The tool can no longer move a caller's checkout.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A tool handed a clone as a *source* can still check that clone out from
  under you.** `process/upstream/tools/checkin.py update <bestpractice-clone>`,
  run from a consuming repo, opened with `git checkout <default-branch>` and
  `git pull` **inside the clone you passed it**. On 2026-09-06 that silently
  moved a session's BestPractice checkout off `precedent-beta-v01` onto
  `main`, mid-session — and the command had already FAILED its own guard by
  then, so the mutation was pure collateral. The session noticed only because
  `templates/practice-set-*/` and thirty tools had vanished from a tree it had
  just been working in, and briefly read that as another session having deleted
  real work. `git status` was clean and `git log` looked sane, because nothing
  was damaged: it was simply a different branch. **If files you were just
  using disappear, check `git rev-parse --abbrev-ref HEAD` before concluding
  anything was lost** — and on a dirty tree the checkout would have failed and
  left the pull half-applied instead, which is worse. Fixed forward the same
  day: `update()` now reads the source ref with `git archive` (no checkout, no
  pull, no HEAD movement — the guarantee
  [tools/precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) already
  made explicitly), and mirrors the branch the consumer's own
  `process/manifest.json` records rather than the clone's configured default —
  every consumer tracks `precedent-beta-v01` while `main` is still the
  default, so the old code would have mirrored `main` over a beta-vendored
  tree, a wholesale revert dressed as an update. Both properties are asserted
  in [tools/verify_harness.py](../tools/verify_harness.py) with negative
  controls.

</details>

## 5. A stale container is indistinguishable from missing work; the freshness

**Verdict: `compressed`.** The guard repairs now rather than warning. What stays live is the part no guard covers -- it does not run for an attached sibling, or when the session was rooted above the repo. The three incidents and the guard's design history are here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A stale container is indistinguishable from missing work; the freshness
  guard can be the thing that's lying; and the guard cannot save the very
  containers that most need it.** Three incidents, each one level deeper than
  the last. 2026-09-01: a session's local branch shared ZERO commits with
  origin, 51 merged commits invisible. 2026-09-06: a session started on a
  5-day-old shallow clone, 207 commits behind `precedent-beta-v01`, and
  concluded that [tools/precedent_check.py](../tools/precedent_check.py) and
  [.github/workflows/deep-check.yml](../.github/workflows/deep-check.yml) "did
  not exist" — they had landed days earlier;
  [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh) stayed
  silent because its `git fetch` failed and it then compared the local commit
  against an unrefreshed remote-tracking ref: both were equally old, so
  nothing looked behind. Fixed then to warn when the fetch itself fails.
  **2026-09-06, the one that ended warning as a strategy:** a session came up
  366 commits behind, and the hardened freshness block *did run and could not
  help* — the container's copy of the hook was built 2026-08-31 and predated
  the block by six days. **A guard shipped inside the checkout it guards is
  missing from precisely the containers stale enough to need it.** The
  documentation failed identically: the AGENTS.md that session was handed had
  no gotchas section at all, so every entry here — including this one — was
  invisible to it. Warning was never going to be enough, because by the time
  a session could act on a warning the harness has already handed it a stale
  instructions file. The guard therefore **repairs**: on a clean tree that
  is strictly behind, it fast-forwards and says so, which makes the harness
  re-read the instruction files. Diverged, no-shared-history, and dirty-tree
  states still only warn — a hook that discards work is worse than any stale
  checkout. **That logic lives in
  [.claude/hooks/freshness-guard.sh](../.claude/hooks/freshness-guard.sh), and
  only there** — it briefly also sat inline in
  [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh), where the
  two ran back to back at every startup, fetching twice and racing to
  fast-forward the same branch; the inline copy is gone rather than kept in
  sync by hand. The guard is wired three times, because one firing point
  cannot cover the others: `SessionStart` (once, at the start),
  `PreToolUse` (once, before the session's first write) and
  `UserPromptSubmit` (the long-open-tab case — a tab open for hours that has
  already made its first edit is otherwise never rechecked). The
  `UserPromptSubmit` mode is throttled on a stamp file's mtime, so it costs
  ≈17ms and prints nothing inside its interval (default 600s,
  `git config precedent.freshness.intervalSeconds`); nothing polls and
  nothing runs between prompts. Its first version built the stamp path from
  `git rev-parse --git-dir`, which answers *relative* to the repo, so every
  write landed in the wrong directory, the throttle never engaged, and it
  re-checked on every prompt while printing a path error — use
  `--absolute-git-dir` for any path a hook will use from an unknown working
  directory. Two further fixes fell out of testing it: the freshness block was
  gated behind `CLAUDE_CODE_REMOTE=true` along with the `pip install`, so on a
  local machine it **never ran at all** (verified: total silence on all six
  test cases, including a failed fetch); and the old remedy it printed —
  `git checkout -B <branch> origin/<branch>` — was printed for a *diverged*
  branch too, where following it silently discards the local commits, because
  the check never distinguished "behind" from "behind and ahead". Before
  concluding that anything is missing or unfinished, still run
  `git fetch origin <branch>` and `git rev-list --count HEAD..origin/<branch>`
  yourself: the hook does not run for a repo attached mid-session (see the
  `add_repo` entry below).

</details>

## 8. A `scope: 'tree'` check in `tools/precedent_check.py` can silently

**Verdict: `compressed`.** Live. The live entry keeps the lesson (an empty result reads as clean, not as couldn't-check); the LEDGER.md specifics of the 2026-09-05 instance are here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A `scope: 'tree'` check in `tools/precedent_check.py` can silently
  report a false *pass* on an under-fetched local clone, not just degrade
  loudly like the two entries above.** `parallel-artifact-ledger` walks
  `git log --no-merges -- <member-dir>` for each harness-adapter directory
  and fails on any commit whose hash isn't in `templates/harness/LEDGER.md`.
  2026-09-05: a local run reported `0 violated`, but GitHub Actions' own
  checkout of the exact same commit reported a real violation (twice) —
  `templates/harness/LEDGER.md` was missing a row for a commit from
  five weeks before the ledger file existed. The local clone's history
  simply didn't reach back far enough for `git log` to find that commit at
  all, so the check had nothing to flag — an empty result read as "clean,"
  not as "couldn't check." `git fetch --depth=1000 origin <branch>` (or
  deeper — this check needs the *entire* history of the directories it
  walks, not just enough for the current branch's own diff) before
  trusting a clean local run of any `scope: 'tree'` check.

</details>

## 10. A session's local checkout can be stale enough to look complete while

**Verdict: `archived`.** Merged into the compressed freshness entry -- the same trap recorded twice, with an identical live instruction: fetch and count before concluding anything is missing.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A session's local checkout can be stale enough to look complete while
  missing real, merged work — with no error.** A session opened here on
  2026-09-01 had a local `precedent-beta-v01` that shared **zero** commits
  with origin's tip: phases 1.5 through 4, every `spec/*.md` brief, and
  `CHANGES_TO_TELL_ALEX.md` simply did not exist locally. `git status`
  reported "up to date with origin" because that check runs against
  whatever the remote-tracking ref happened to be at last fetch, and no
  fetch had happened yet. Reading the tree, running the harness, anything
  short of `git fetch` first would have silently analyzed or built on a
  months-stale snapshot. [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh)
  now fetches the current branch and warns loudly (never fails the
  session — a git failure here must not block startup) if local `HEAD`
  differs from origin's, distinguishing "behind" from "shares no history
  at all" (a force-push or rewrite, the worse case). If you see that
  warning, and your working tree is clean: `git checkout -B <branch>
  origin/<branch>`.

</details>

## 11. On a shallow clone, `git merge-base` between two *different* branches

**Verdict: `compressed`.** Live. The live entry keeps the conclusion; the per-branch merge-base readings that isolated it are here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **On a shallow clone, `git merge-base` between two *different* branches
  can exit 1 ("no common ancestor") even when the branches genuinely share
  history — and that false negative reads exactly like a destructive
  force-push.** On 2026-09-06, comparing `precedent-beta-v01` against an
  older feature branch this way returned exit 1, which looked like proof
  the two had disjoint, independently-rewritten histories; the session
  nearly asked the user to confirm a branch rewrite that had never
  happened. `git merge-base <A> origin/main` and `git merge-base <B>
  origin/main` each resolved fine in the meantime — the shallow fetch
  simply didn't reach far enough back to contain the real common ancestor
  of `<A>` and `<B>` themselves, even though each one individually had a
  shorter path back to `main`. `git merge-base` exiting 1 is not by itself
  evidence of a rewritten or discarded branch: `git fetch --unshallow
  origin` (or a deep enough bounded `git fetch --depth=<N> origin
  <branch>`, per the entries above) and recheck before concluding
  anything about two branches' relationship.

</details>

## 12. Inherited audits that have nothing to inspect say so, rather than

**Verdict: `archived`.** Informational and self-correcting: the three tools say NOT APPLICABLE with a reason, and precedent_check.py reports that as skipped rather than passed. Nothing here can mislead a session into wasted work.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **Inherited audits that have nothing to inspect say so, rather than
  passing or failing.** [tools/practice_audit.py](../tools/practice_audit.py)
  wants a `process/manifest*.json` this repo does not have, because this
  repo is the upstream it audits a *dependent* repo against. It used to
  exit non-zero for that reason — permanently red, so nobody ran it — and
  [tools/doc_sync.py](../tools/doc_sync.py) and
  [tools/model_audit.py](../tools/model_audit.py), whose `PAIRS` and
  `INSTRUMENTED` lists were then empty, printed `OK` on having inspected
  nothing: a confident all-clear from a scan that never ran. All three now
  say NOT APPLICABLE with the reason, and
  [tools/precedent_check.py](../tools/precedent_check.py) reports that as
  skipped rather than passed. (`PAIRS` and `INSTRUMENTED` have both since
  been filled in here — two documents and one script — so only
  `practice_audit.py` is still NOT APPLICABLE in this repo. Corrected
  2026-09-06; the entry had gone on asserting all three were empty.)

</details>

## 13. `git log --format=%P` silently reports no parents at all for a commit

**Verdict: `compressed`.** Live. The live entry keeps the remedy (`git cat-file -p`); the reproduction detail is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **`git log --format=%P` silently reports no parents at all for a commit
  sitting at a shallow clone's boundary, even when it really has two.** Writing a mechanical check for `precedent-team-maintainers`
  (a `checked_by` script that needed to tell a merge commit apart from an
  ordinary one, to exempt merges from a per-commit rule) used `%P` and
  worked perfectly against a full clone, then silently misclassified the
  exact commit sitting at the shallow boundary as parentless the moment the
  same script ran against a fresh `--depth 1` clone of the same repo —
  reproduced directly, not just suspected. Git's pretty-printers respect
  the shallow graft for traversal purposes even though the commit object's
  own header still genuinely records both parents. `git cat-file -p <sha>`
  reads that header directly and is unaffected — count lines starting with
  `parent ` instead of parsing `%P`, anywhere a check needs to know a
  shallow-clone-safe parent count or parent list.

</details>

## 14. A consuming repo's own mechanical check against materialized

**Verdict: `compressed`.** Live architectural guidance. The live entry keeps the rule and the reason; the full incident is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A consuming repo's own mechanical check against materialized
  `tools/checks/`/`practices/` output cannot just call
  `precedent_resolve.load_config()` and trust every source it lists.** A
  repo-local (or team, or individual) source's own check script belongs
  under that source's own declared `path` (`local/tools/checks/` for a
  source declared `path: "local"`), never directly in the consuming
  repo's own `tools/checks/` — that is `precedent_materialize.py`'s own
  *output* directory, deleted and rewritten from every declared source on
  every `precedent_sync_views.py` run, so a hand-added file there
  survives only until the next sync. A dependent repo built exactly this
  mechanical check (verify every materialized `check_*.py` has a
  byte-identical twin in its source) and shipped a first version that
  resolved sources live to decide what counts as reachable — it passed
  locally, then failed the repo's own CI on the very next push, on `main`
  itself, flagging every check script sourced from its team and
  individual sources. A team source is a live sibling clone outside the
  repo; an individual source resolves only via a private, non-repo
  user-level config — neither exists in a bare CI checkout, and never
  will, so "this source didn't resolve here" is not evidence of an
  orphaned file. The fix: attribute by the *committed* `MANIFEST.json`'s
  own `checks` list (already written by `precedent_materialize.py`,
  recording exactly which source produced each file) instead of by live
  resolution — a file with no entry there at all is the real signature of
  a hand-dropped orphan and always fails; a recorded file whose source
  simply is not reachable in the current environment is skipped, never
  failed.

</details>

## 15. A repo attached mid-session never runs its own SessionStart hook, so

**Verdict: `compressed`.** Live, and hit constantly. The live entry keeps the symptom and the one-line fix; the full 2026-09-06 diagnosis is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A repo attached mid-session never runs its own SessionStart hook, so
  every environment guarantee that hook provides is silently absent while
  you work in it.** SessionStart hooks fire for the session's *primary*
  repo only. A sibling attached with `add_repo` — which is how this repo
  is present whenever a dependent repo's session needs it for a vendor
  refresh or a check-in — is just a directory on disk: its
  [.claude/hooks/session-start.sh](../.claude/hooks/session-start.sh) is
  never executed, no matter that it is committed, executable, and correct.
  2026-09-06, working here from a dependent repo's session:
  `python3 tools/verify_harness.py` reported `FAIL: every tool answers
  --help with exit 0 ... doc_html.py exited 1`, and separately
  `N/A: rendered documents are current -- tools/doc_html.py could not be
  imported (No module named 'markdown') -- not a pass`. Both were the same
  missing module, which this repo's own hook installs on line 13 and has
  installed since 2026-09-04 — it simply had not run. The failure reads
  like a broken tool and is an unrun hook, so the reflex to go debug
  `doc_html.py` is wasted. `pip install cmarkgfm markdown` by hand once
  per session you work in an attached sibling, then re-run the gate: the
  harness went from `1 failed` to `0 failed` with no code change at all.
  The same reasoning covers the refspec repair and the freshness warning
  further down that hook — none of them ran either, so treat every entry
  in this section that says "the session-start hook does this" as *not*
  done when you arrived here as a sibling.

</details>

## 16. Something can move this checkout off your working branch mid-session,

**Verdict: `compressed`.** Live and explicitly unresolved. The live entry keeps the symptom, the ruled-out suspects and the recovery; the full reflog account is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **Something can move this checkout off your working branch mid-session,
  and the cause is NOT known — treat a silently-vanished edit as this
  before you re-derive it.** 2026-09-08, three minutes after a commit on
  `claude/deep-review-…`, the reflog recorded
  `checkout: moving from claude/deep-review-… to precedent-beta-v01`
  followed by `pull origin precedent-beta-v01: Fast-forward`. Nobody asked
  for either. The commit survived on the abandoned branch, but the next
  twenty minutes of edits were made on `precedent-beta-v01`, and the only
  symptom was **a function that had silently stopped existing** — a check
  written earlier in the session was simply not in the file any more, which
  reads exactly like a bad edit and is really a branch switch. `git status`
  was clean throughout, as it always is for a checkout.
  **Three obvious suspects are ruled out, by replay rather than reasoning**:
  `precedent_vendor_engine.py seed`,
  `precedent_refresh_sources.py --apply` and `checkin.py fresh` were each
  run against a throwaway clone sitting on a feature branch, and none of
  them moved `HEAD`. So this is not the `checkin.py update` incident above
  returning; whatever does it is outside this repo's own tools, and the
  next session should not assume it has been fixed.
  **Detection is the whole remedy available.**
  [tools/precedent_session_check.py](../tools/precedent_session_check.py)
  stamps the branch on its first run of a session and compares on every
  later one, so the drift is one command away instead of an archaeology
  problem. When it fires: the work is **not lost** — `git reflog` still
  lists the commit, `git checkout <the branch it names>` returns to it, and
  anything committed after the move is recovered with `git cherry-pick`.
  Check `git rev-parse --abbrev-ref HEAD` before concluding an edit was
  bad, and re-verify with `git reflog` rather than trusting that a clean
  tree means nothing happened.

</details>

## 17. The session's PRIMARY repo does not run its SessionStart hooks either,

**Verdict: `compressed`.** Live -- this project's own required layout causes it. The full inventory of what was absent that day is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The session's PRIMARY repo does not run its SessionStart hooks either,
  when the harness rooted the session one directory ABOVE it — and this
  project's own required layout is what causes that.** The entry above is
  about an attached sibling; this is its mirror image and reads as the
  opposite, because here the repository *is* the one you are working in,
  its hooks are committed, executable and correctly wired, and they still
  never fire. 2026-09-08, a session opened with four Precedent repos side
  by side under `/home/user` — the layout a team source requires, since it
  resolves as a *sibling clone* — and the harness set the session root to
  that parent. Every hook in
  [.claude/settings.json](../.claude/settings.json) is written as
  `$CLAUDE_PROJECT_DIR/.claude/hooks/…`, `/home/user` has no `.claude/`,
  so every one of them resolved to nothing. Silently: a hook whose path
  does not exist is not an error anybody sees.
  What was absent, all at once: the commit identity (so `user.email` was
  still `noreply@anthropic.com`, and every commit would have been a
  wrong-author commit this repo's own check refuses), the global commit
  backstop, the freshness guard, the `pip install`, the path-trigger
  channel, the Stop-time git check — and
  `.precedent/SESSION_PRACTICES.md`, which is the ONLY route by which the
  private team and individual practices reach a session at all. That file
  did not exist, so **53 practices that bind work here were silently not
  in force**, including `audience-register`, which governs how every reply
  in the session is written. AGENTS.md's own Standing Instruction told the
  session to read a file that was never generated.
  **Do not diagnose this from `env`** — `CLAUDE_PROJECT_DIR` is usually
  not set in a tool shell at all, so reading it proves nothing either way.
  Test the *effects*:
  [tools/precedent_session_check.py](../tools/precedent_session_check.py)
  checks each guarantee by what
  it left behind (does `.precedent/SESSION_PRACTICES.md` exist, is
  `user.email` a person, is `core.hooksPath` set, do `cmarkgfm` and
  `markdown` import, does `remote.origin.fetch` carry `refs/heads/*`, is
  the checkout behind origin) and `--apply` runs the three SessionStart
  hooks by hand. It cannot itself be a hook, for the obvious reason: the
  failure *is* that hooks do not run, so anything waiting to be triggered
  is the one thing guaranteed not to fire — the same shape as the
  freshness guard that shipped inside the checkout it guarded.

</details>

## 18. The three private practice sets cannot be attached from a session

**Verdict: `rewritten`.** READ THIS BEFORE ANY PARAGRAPH BELOW. This entry had grown into a contradiction: a restriction asserted, falsified by a six-repository session, re-measured as holding in both directions, ending 'now unexplained'. A session on 2026-09-08 again held all four repositories and pushed to three. The live entry now says only what is measured and tells a session to call `add_repo` and read the answer. Nothing below is the current state.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The three private practice sets cannot be attached from a session
  rooted in this repo, and it is a session-shape rule, not a permissions
  problem — so do not go hunting for the permission.** As of 2026-09-06,
  asked to attach `themorgan/precedent-team-maintainers`,
  `themorgan/precedent-individual` and `themorgan/precedent-team-tms` while
  working in `alex137/BestPractice`, `add_repo` refuses outright:
  *"cross-tier adds are not supported in v1: requested
  themorgan/precedent-team-maintainers but session already has repos from
  owner(s) [alex137]"*. Everything about the surrounding evidence argues the
  other way and is misleading: `list_repos` returns all three, private, with
  `can_push: true` for this account, so access genuinely exists — it is the
  *session's* composition that is refused, not the account's rights. The
  obvious fallback fails too, differently enough to look like a second
  problem: a plain `git ls-remote https://github.com/themorgan/...` answers
  *"could not read Username for 'https://github.com': terminal prompts
  disabled"*, because this session's git credentials cover `alex137/*` only.
  Nothing done from inside such a session closes this. The remedy is a
  session whose **initial source** is the private repo
  ([TODO.md](../TODO.md)'s `attach-private-sources` item, which also lists what
  to run once there); BestPractice is public, so that session clones it
  directly with no second `add_repo`. The failure this entry prevents is
  spending the attempt at all: the fact was already recorded in
  [TODO.md](../TODO.md), [spec/PHASE6_BRIEF.md](../spec/PHASE6_BRIEF.md) and
  [decisions/2026-09-01-relax-private-repo-isolation.md](../decisions/2026-09-01-relax-private-repo-isolation.md),
  and a session on 2026-09-06 rediscovered it by trying both calls anyway,
  because this section — the one place written to stop rediscovery — did not
  carry it.
  **NO LONGER TRUE as written, 2026-09-07.** A session that day held
  `alex137/bestpractice` and five `themorgan/*` repositories at once —
  including all three private sets, worked in and pushed to — and `add_repo`
  accepted a sixth (a private consumer repo under the same owner)
  mid-session. Mixed owners
  in one session is precisely what this entry says is refused.
  **The open half is now measured, 2026-09-07: a fresh session rooted here
  still refuses on its FIRST cross-owner add.** `add_repo` for
  `themorgan/precedent-individual`, called as the session's first tool call
  exactly as the banner at the top of this file instructs, answered with the
  same v1 message word for word.
  **The symmetric half, measured 2026-09-07: rooting in the private repo
  does not buy the add either.** A session rooted in
  `themorgan/precedent-individual` asked for `alex137/bestpractice` and was
  refused in the same words with the owners swapped — *"cross-tier adds are
  not supported in v1: requested alex137/bestpractice but session already
  has repos from owner(s) [themorgan]"*. So the refusal runs in BOTH
  directions. The clause this replaces — that a session rooted in a
  `themorgan/*` repo "keeps adding freely" because BestPractice is a public
  add — was an INFERENCE drawn from the mixed-set session above, never a
  measurement, and it is now falsified: public-vs-private is not the axis,
  and the first cross-owner add loses whichever owner you start from. **So
  how that mixed-set session reached six repositories across two owners is
  now unexplained** — the only explanation on offer has just been ruled out.
  Do not build on it, and do not repeat the attempt expecting the earlier
  result. The remedy stands unchanged and is the only one, but state it
  accurately: root the session in the repo you must PUSH to, and expect the
  other owner's repositories to be unattachable from it for the whole
  session. That is not a workaround to route around — it is why work
  spanning both owners is split across two sessions, each rooted where it
  writes.
  What it costs when you skip it is not abstract. That 2026-09-07 session
  ran with `individual` and `team` both unresolved, which means the
  `go-merge` keyword's own definition was unreadable while the user was
  using it — the one thing `.precedent/SESSION_PRACTICES.md` says out loud
  and nothing else in the tree does.

</details>

## 19. A harness run that overlaps a write to the tree fails on a change

**Verdict: `compressed`.** Live. The live entry keeps the rule and the tell; the run-by-run account is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A harness run that overlaps a write to the tree fails on a change
  belonging to no commit, and the count alone cannot tell you that.**
  [tools/verify_harness.py](../tools/verify_harness.py) reads the tree as it
  goes, over more than a hundred checks and several minutes. On 2026-09-07 a
  run came back `1 failed` because a negative-control test — for a fix being
  made in that same session — had briefly planted a failing check into
  `verify_harness.py` while the run was still in progress. The failure was
  real, reproducible on demand, and belonged to no commit. Two earlier runs
  and four later ones on the identical tree were clean, which is what a
  genuine intermittent looks like too: `1 failed` renders identically
  whether it is self-inflicted, a real flake, or a real bug. Run the harness
  to completion before editing anything it reads, including its own control
  tests, and never run two at once. Since 2026-09-07 the run recaps every
  failure BY NAME immediately before the summary line, so `tail -5` is
  enough to tell these apart — before that it printed only the count, and a
  failure hundreds of lines up was lost the moment anyone re-ran.

</details>

## 20. Setting `git config precedent.requireVocabulary true` to satisfy the leak

**Verdict: `compressed`.** Live, and used on every deep check. The live entry keeps the two commands; the failure text of both gates is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **Setting `git config precedent.requireVocabulary true` to satisfy the leak
  gate makes `verify_harness.py` fail two of its own leak-gate checks.** The
  two gates want opposite environments and neither says so. 2026-09-07,
  running the full deep check before a push: `leak_gate.py` refused with
  *"this clone has declared that it HAS a private-term blocklist ... and
  PRECEDENT_LEAK_BLOCKLIST is not set"*, which the gotcha above tells you to
  fix by setting both. With both set, `verify_harness.py` then reported
  `2 failed` — *"the default blocklist is applied with no environment
  variable set"* and *"a clean tree now reports OK rather than PARTIAL"* —
  because those cases assert the gate's behaviour for a clone that has
  declared nothing. Neither failure is a real defect and neither is caused by
  whatever you are changing, which is exactly why it costs a session an hour.
  Run them in different environments: `python3 tools/leak_gate.py` with
  `PRECEDENT_LEAK_BLOCKLIST` exported, and
  `env -u PRECEDENT_LEAK_BLOCKLIST python3 tools/verify_harness.py` with the
  git config unset. Unset the config when you are done rather than leaving it
  on the clone — a later session running the harness will hit this again with
  no idea why.

</details>

## 21. A test fixture that asserts on commit identity must OWN that identity,

**Verdict: `archived`.** Fixed 2026-09-07 at module scope in verify_harness.py (verified 2026-09-08 -- the pop is still there), and the general rule is now the universal practice `fixture-owns-its-state`, which reaches every session through the occasion index. A story with both a fix and a practice behind it does not belong in front of every session.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A test fixture that asserts on commit identity must OWN that identity,
  or the session's environment silently becomes part of the test.** FIXED
  2026-09-07 in [verify_harness.py](../tools/verify_harness.py) and recorded
  here for the story, not for a workaround -- if you hit it, your checkout
  predates the fix. `check_identity_reaches_a_repo_that_did_not_exist_yet`
  built its fixture by copying `os.environ`, pointing `HOME` at a temporary
  directory, setting a global identity inside it and asserting that commits
  there used it. It popped `PRECEDENT_ALLOW_ANY_AUTHOR`,
  `PRECEDENT_COMMIT_EMAIL` and `PRECEDENT_COMMIT_TZ`, but NOT the
  `GIT_AUTHOR_*` variables -- and those outrank `git config --global
  user.*`. So in a session that exports them (the individual practice set's
  `.claude/settings.json` does) every fixture commit was authored by the
  real person, and **4 of that check's 11 stated cases failed, none of them
  real**: *a repo created AFTER the hook commits as the person*, *a
  bot-authored commit is refused there*, *and the refusal names itself as
  the global backstop*, *a correct commit is not blocked*. **Three of the
  four failed in the direction that wastes the hour** -- a bot identity the
  fixture plants in LOCAL config was never the author any more, so the
  refusal each case waits for correctly did not fire, and a working backstop
  read as broken in a check whose name is *"the commit identity reaches a
  repo attached after the hook ran"*. That is the wrong-author incident this
  check exists to catch, so the failure impersonates the bug. Measured
  2026-09-07, same tree, no code change: `1 failed` with the variables
  exported, `0 failed` under `env -u`. **The fix drops the author trio once
  at module scope**, beside the `PRECEDENT_ALLOW_ANY_AUTHOR` line that
  solved the mirror-image problem, rather than in the one fixture that
  happened to notice -- a fixture written later would inherit the same
  invisible dependency. `GIT_AUTHOR_DATE` goes too (the same check asserts
  on the author-date offset); `GIT_COMMITTER_*` deliberately does not,
  because nothing here or in
  [commit-identity.sh](../.claude/hooks/commit-identity.sh) reads the
  committer. Verified against the hostile case: with all three exported,
  `GIT_AUTHOR_DATE` set to a `+0000` that would independently have broken
  the timezone case, the run is `0 failed`. The reusable half is the first
  sentence -- this is the second time an ambient variable turned a green
  gate red here, after the `requireVocabulary` entry above, and both cost an
  hour to the same shape: two mechanisms wanting opposite environments,
  neither saying so.

</details>

## 22. The individual source resolves to a clone you are probably not editing,

**Verdict: `compressed`.** Live -- it fired again on 2026-09-08 with the config-named clone three commits behind. The live entry keeps the check command and the preference; the recorded per-machine states are here, because a fix outside the repository cannot be recorded inside it as a state.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The individual source resolves to a clone you are probably not editing,
  and it can be many commits stale.** `~/.config/precedent/config.json`
  names an absolute path, and on 2026-09-07 that path was
  `/root/precedent-individual` while every repo this session had attached,
  edited and pushed lived under `/home/user/`. Two clones of the same
  repository, and **everything that resolves the individual source at
  runtime reads the one in the config** — which was 6 commits behind, so it
  did not carry work committed and pushed an hour earlier from the other.
  It cost two separate confusions before the cause was found: a harness
  fixture that failed intermittently because it was reading that clone's
  freshness (not its own), and a SessionStart hook that installed one of the
  two commit hooks it should have, because the script it executed was the
  stale copy. Neither symptom pointed at a path. Check
  `python3 -c "import json,pathlib;print(json.load(open(pathlib.Path('~/.config/precedent/config.json').expanduser()))['individual']['path'])"`
  against where you are actually working, before concluding a tool is
  broken — and `git -C <that path> rev-list --count HEAD..origin/main` before
  trusting anything it produced. **The rule that resolves it, 2026-09-07:
  the config-named clone is `git pull --ff-only`ed from origin at every
  session start, so it can only ever be BEHIND — an attached sibling clone
  beside the repo you are working in is what a session actually edits and
  pushes from, and is the better evidence of what the source says.**
  [tools/verify_harness.py](../tools/verify_harness.py)'s
  `check_commit_identity_copies_are_identical` encodes exactly that
  preference; its first run reported drift against an uncommitted edit three
  directories away, which is the trap in miniature. **Do not read the next sentence as
  done everywhere.** A session on 2026-09-07 repointed the config at
  `/home/user/precedent-individual` and recorded that here as "resolved for
  this machine" -- but `~/.config/precedent/config.json` is a per-container
  file that no repository can carry, so a *different* container reading this
  paragraph still had `/root/precedent-individual` in its config, and the
  same paragraph's "nothing reads it now" was false there: everything reads
  exactly it. A fix that lives outside the repository cannot be recorded
  inside the repository as a state; only as a thing to check. **So check
  it**, with the command above, rather than trusting this. The saving grace
  when you find `/root/`: `precedent-individual-bootstrap.sh` pulls that
  clone `--ff-only` at every session start, so it is normally current in
  content even when it is the wrong path -- verified 2026-09-07, both clones
  at the same commit. What it will not have is uncommitted work in progress
  from the attached sibling, which is the case the preference above exists
  for.

</details>

## 23. A sibling clone that was current when you took it can rot while you

**Verdict: `compressed`.** Live. The live entry keeps the direction-of-mistake warning and the confirming command; the full instance is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A sibling clone that was current when you took it can rot while you
  work, and a "these copies do not match" failure will blame the code
  rather than your clone.** The entry above is about a clone that is
  behind when a session *starts*; this is the same trap arriving later,
  and it is the shape that will keep recurring now that several sessions
  routinely work these repositories at the same time. 2026-09-07:
  `verify_harness.py` came back `1 failed` on
  *"every reachable copy of commit-identity.sh is byte-identical (3 copies
  found)"*, listing this repo's two copies in agreement and the copy in
  the attached `precedent-team-maintainers` clone differing. The check was
  correct that the files differed and wrong about what that meant: the
  clone had been taken hours earlier, another session had pushed to that
  repository twice since, and it was **2 commits behind**. A single
  `git -C <clone> pull --ff-only` made all three hashes agree, and the
  re-run was `0 failed` with no change to any file here.
  **So before believing any cross-copy mismatch: refresh every attached
  sibling clone and run it again.** The reason this is worth a rule rather
  than a shrug is the direction the mistake runs — the failure reads as
  "this repo's file is wrong", and the obvious remedy is to copy the
  clone's older version over the newer one, which silently reverts
  somebody else's just-landed work. Confirm which side is stale before
  editing either: `git -C <clone> fetch && git -C <clone> rev-list --count
  HEAD..origin/<branch>` answers it in one line.
  The same reasoning applies to the check itself when it is the new thing:
  this one had landed minutes before it fired, so "a check that has never
  been green here" was also on the table, and ruling that out meant
  running it against the untouched branch tip first. A failure in a check
  younger than your branch is worth locating before it is worth fixing.

</details>

## 24. `HEAD == origin/<branch>` and a clean tree is NOT evidence that your

**Verdict: `compressed`.** Live. The live entry keeps both habits and the recovery; the full sequence is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **`HEAD == origin/<branch>` and a clean tree is NOT evidence that your
  work landed — it is the exact reading you get when your commit has been
  thrown away.** 2026-09-07: a session edited `TODO.md` while sitting on
  local `precedent-beta-v01`, committed there, then ran its usual
  push-and-merge sequence — `git push origin <feature-branch>` (which
  reported *"Everything up-to-date"*, correctly, because the feature branch
  had not moved), then
  `git checkout -B precedent-beta-v01 origin/precedent-beta-v01`, which
  **silently discarded the commit it had just made**. Its verification step
  then printed `HEAD=a7e503c beta=a7e503c dirty=0` and read as success:
  every ref matched, nothing was uncommitted, and the change was in neither
  the local tree nor the remote. A concurrent session's own push to the
  same branch made the hashes advance, which made the output look *more*
  convincing, not less.
  Two habits close it. **Commit on the working branch, never on the branch
  you are about to reset** — `git checkout -B` is a reset, and a
  scripted push-then-checkout sequence will run it whether or not you have
  uncommitted history there. And **verify the CONTENT, not the refs**:
  `git show origin/<branch>:<file> | grep <a phrase from your change>`
  answers the question `verify-postcondition` actually asks, where ref
  equality only answers a proxy for it. The first grep written that day
  matched a coincidental phrase already present elsewhere in the file and
  briefly confirmed the wrong thing — so grep for a phrase distinctive to
  your own edit, not a common one.
  Recovery, when it happens: the commit is not gone, it is unreferenced.
  `git reflog` still lists it (`commit: <your message>`), and
  `git cherry-pick <that hash>` onto the working branch restores it.

</details>

## 25. The commit backstop is GLOBAL now (`core.hooksPath`), so it reaches

**Verdict: `compressed`.** Live. The live entry keeps the fixture rule and the `--absolute-git-dir` warning; the full account is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The commit backstop is GLOBAL now (`core.hooksPath`), so it reaches
  throwaway fixture repositories too — and refused them.** 2026-09-07, the
  third wrong-author incident in two days forced the scope up: a repo
  attached mid-session inherits the container's *global* identity (measured:
  `noreply@anthropic.com`), so a per-checkout SessionStart fix cannot cover
  it even in principle. Setting the identity globally, plus a backstop at
  `core.hooksPath`, is what reaches a repository that does not exist yet.
  The cost landed immediately: `verify_harness.py` builds dozens of
  temporary repos and commits in them without `TZ`, and the backstop
  refused the first one — `RuntimeError: git commit -qm base: commit
  refused: author-date offset is '+0000'`, the whole run down, in a
  mechanism that had nothing to do with what was being tested. **A fixture
  commit is not a person's commit**: the harness now sets
  `PRECEDENT_ALLOW_ANY_AUTHOR=1` once for every subprocess it spawns (the
  two checks that exercise the refusals pop it back out, so coverage is
  intact). Any other tool that creates scratch repositories and commits in
  them needs the same, and the symptom will not look like an identity
  problem.
  `core.hooksPath` also makes git look THERE AND NOWHERE ELSE, so the global
  hooks chain to each repository's own `.git/hooks/<name>` first — without
  that, every repo's own gates vanish silently. Resolve that path with
  `rev-parse --absolute-git-dir`, never `rev-parse --git-path hooks`: the
  latter *respects* `core.hooksPath` and so names the global directory,
  which made the chain look broken when it worked and a fixture look
  correct when it was planting its hook in the wrong place.

</details>

## 26. The timezone half of that backstop was refusing a wrong offset it could

**Verdict: `compressed`.** Live only as a diagnosis shortcut -- the mechanism works. The derivation is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **The timezone half of that backstop was refusing a wrong offset it could
  have prevented — the container's clock is the lever, and a hook can move
  it.** 2026-09-07: every commit here needed a `TZ="…" git commit` prefix
  and the merge commits that forgot it were refused, correctly, for
  `+0000`. Three mechanisms existed and every one of them acts *after* git
  has resolved an offset: `pre-commit` refuses, `prepare-commit-msg`
  refuses the merge, and the `.claude/settings.local.json` derivation
  applies only from the NEXT session, because the harness reads environment
  before hooks run. Measured rather than reasoned: `/etc/localtime` was
  `Etc/UTC`, `TZ` was unset in every tool shell (`echo "${TZ:-<unset>}"`),
  and `settings.local.json` already carried the right zone and was inert.
  git falls back to the SYSTEM zone when `TZ` is unset, and the system zone
  is the one lever a hook can move mid-session that every later shell,
  tool, and `git merge` picks up without cooperating — so
  [.claude/hooks/commit-identity.sh](../.claude/hooks/commit-identity.sh)
  repoints it, for a **declared** zone only. Verified end to end: a fresh
  `git init` with no prefix and no local config committed at `-0300`.
  `PRECEDENT_LOCALTIME` overrides the target so this is testable — and the
  older `check_commit_identity_derives_declared_timezone` fixture, which
  declares Europe/Berlin, now sets it too; without that the harness itself
  would have put the container on Berlin time and every later commit in the
  session would have been refused for an offset the harness caused.
  **If you suspect a timezone problem, check `date` and
  `ls -l .git/hooks/pre-commit`, not the `env` block** — that block is
  inert here and reading it sent two earlier diagnoses down the wrong path.

</details>

## 27. "no individual source resolved" is not noise — it means every personal

**Verdict: `compressed`.** Live, and among the most expensive to miss. The live entry keeps the signal, the cost and the remedy; the full account is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **"no individual source resolved" is not noise — it means every personal
  and team practice is silently absent, and the session will confidently
  apply the wrong rules.** 2026-09-07: a session ran most of a long working
  day in this repository with none of the account owner's personal
  practices loaded.
  `tools/precedent_resolve.py` printed the reason on *every single run* —
  *"no individual source resolved … which usually means its clone could
  not be fetched (a private repository this session was never granted)"* —
  and the session read past it every time as startup chatter, because the
  checks it prefixes all reported `0 violated` and the line sits directly
  above the summary a session is reading the output *for*. (The counts in
  an earlier draft of this entry -- "twenty turns", "fifteen times" --
  were impressions written as figures and neither was counted; the
  frequency is *every run*, which is the part that matters and the part
  that is checkable.)
  The cost is invisible while it is happening, which is what makes it
  worth an entry: the practices that did not load included
  `audience-register`, the owner's standing rule about how replies to him
  are written, so every reply that session was pitched by guesswork while
  a rule saying exactly what to do sat unread in a repository nobody had
  fetched. He had asked for that register repeatedly across days, and the
  session's own diagnosis each time was "I keep forgetting" — a
  misdiagnosis, since the rule was never in front of it.
  **When you see that line, stop and fix it before doing anything that
  depends on the rules:** call `add_repo` for the private sources (the
  banner at the top of this file), then re-run
  `python3 tools/precedent_resolve.py --repo .` and confirm the count says
  `individual` and `team` rather than universal alone. A single-digit
  source count where you expected four is the same signal in a different
  shape.

</details>

## 28. A private repo name reaches a public tree by nobody having predicted

**Verdict: `compressed`.** Live. The live entry keeps the allowlist rule, the URL-form trap and the short-form lesson; the measurement behind each pattern stem is here.

<details>
<summary>The full entry as it stood before 2026-09-08</summary>

- **A private repo name reaches a public tree by nobody having predicted
  it, so repo references are an ALLOWLIST now, not a blocklist.** The
  vocabulary layer blocks the literal strings somebody typed, which failed in
  both directions on 2026-09-07: it missed a private repository nobody had
  listed, and it blocked two names that had become public, forcing 88 hits
  clearable only by deleting content about public files. Declare an owner
  private-by-default in the private blocklist file
  (`# visibility-audit: private-owner <account> -- reason`) and every
  `owner/name` mention is refused unless an `allow` line gives a reason. It
  caught an abandoned private fork on its first run, plus its own manual's
  example, which had used a real account name. The set of names you may
  mention is small and known; the set of repos you might create is unbounded.
  **The URL form is the case that matters and is easy to miss**: the
  lookbehind keeping `a/acct/x` from matching also rejects
  `github.com/acct/x`, because the character before the owner is `/` there
  too — a stated test case caught that, reading it did not.
  [tools/very_deep_check.py](../tools/very_deep_check.py) does the other half on
  request, asking the GitHub API whether each referenced repo is actually
  private and whether a blocklisted name has since gone public; the push gate
  cannot, because it must work offline and in continuous integration (CI).
  Its reach is limited to repos the session can see — `/user/repos` answers
  *"sessions are bound to their configured repositories"* — so it reports how
  many it could NOT determine rather than counting those as passes.

  **A blocklist entry catches the name somebody typed, never the SHORT form
  of it.** The 2026-09-07 sweep scrubbed a private consumer repo's name from
  this tree, `d167ada` caught four stragglers at 17:12 — and two hits of
  `<that repo>-local` survived both, in
  [spec/SOURCE_NAMING.md](../spec/SOURCE_NAMING.md) and [TODO.md](../TODO.md),
  written at 07:02 and not removed until 21:17, all on the same public
  branch and the same day. That string was the name its repo-local practice
  source carried before `source-naming` renamed it to `local`, so it was
  written by sessions describing a *rename*, in exactly the documents that
  exist to explain the convention. The repo-reference allowlist could not see
  it at all — that layer only matches `owner/name`.

  **The vocabulary layer's miss is the instructive half, and the obvious
  reading of it is wrong.** The suffix was never the problem: a `\bFullName\b`
  pattern DOES match `FullName-local`, because a hyphen is a word boundary.
  What defeated it is that the leak used the repo's short form — a head the
  full-name pattern does not begin to cover. So the fix that matters is
  **truncating each pattern to a distinctive stem**, and a trailing `[\w-]*`
  is belt-and-braces on top of it, not the mechanism. Landed 2026-09-07 in the
  individual practice set, seven patterns, with the evidence recorded beside
  them: each stem was cut only as far as its measured hit count against this
  tree stayed at zero (the shorter cuts of the same names score in the tens to
  the low thousands here, which is why "just truncate harder" is not the
  rule), and two further cuts that scored zero were still rejected as
  fragments an ordinary camelCase identifier could produce. Positive control,
  replayed over the two commits that actually carried the leak: the old
  full-name list reports the tree clean, the stems report three hits.
  A private repo leaks through what is named AFTER it — a practice source, a
  branch, a directory, a tag, a check — long after the repo's own name is
  gone, and it leaks under the short name people actually type.

</details>
## 29. A fresh container does not see `PRECEDENT_GIT_TOKEN` either

**Verdict: `archived`.** The trap as written cannot fire: the variables do arrive, verified 2026-09-10 in a brand-new container that came up with all four private sources already cloned. What the three measurements below actually found was **two environments with the same name** — the values were set on one and the sessions ran in the other. Every measurement here is accurate; the conclusion each draws from it is not. **Read the verdict before any paragraph of it**, and see [AGENTS.md](../AGENTS.md)'s live entry for the half that is still worth knowing.

**Why it stayed wrong for three days.** Each measurement correctly ruled out the explanation before it — "you set it after the container started" died to a container 40 seconds old, and "`PRECEDENT_*` is being filtered" died to a dump showing no user-defined variable of any kind. The remaining candidate was always "the platform does not pass them through", because **nobody thought to ask how many environments the account had.** `list_environments` answered it in one call: two, both named `Default`, identical descriptions, created 100 ms apart.

<details>
<summary>The full entry as it stood before 2026-09-10</summary>

  **First half of that report, 2026-09-09, and it is not about the token
  being wrong: setting the variable does not reach a session that is already
  running.** Morgan set `PRECEDENT_GIT_TOKEN` and, in the same conversation,
  a RESUMED session in the container that predated it measured **zero**
  `PRECEDENT_*` variables in its environment — not an empty token, not a
  rejected one, the whole family absent. So the credential path was neither
  confirmed nor disproved; it was never exercised. **The tool's `MISSING`
  line is indistinguishable in the two cases** — "you did not set it" and
  "you set it after this container started" print identically, which is
  exactly how a correct configuration gets read as a broken one.
  **Start a NEW session to test an environment change, and check
  `env | grep -c PRECEDENT` before concluding anything about the token
  itself.** Whether a valid token then works is still unmeasured; whoever
  gets one into a fresh session should record it here.

  **Second half, 2026-09-09, and it removes the comfortable explanation: a
  session in a BRAND-NEW container measured `env | grep -c PRECEDENT` as
  **0** as well.** `uptime` read `up 0 min`, the container's own init
  process was 40 seconds old at the first tool call, and Morgan had set
  `PRECEDENT_GIT_TOKEN` before that
  container existed — so "you set it after this container started" does not
  cover it, and neither does "start a new session", which is what the
  paragraph above tells you to do. **A fresh container does not see the
  variable either.** Where it stops is unmeasured: the environment
  configuration may not have saved it, or the runner may not pass
  `PRECEDENT_*` through to the session at all. **Go read the environment
  configuration itself before touching the token, the credential helper or
  `add_repo`** — all three are downstream of a variable that is not arriving.
  The session-start hook reported the whole downstream cost in the same
  breath: four private sources unresolved, universal catalogue alone.

  **Third measurement, 2026-09-09, and it is now two containers: a session
  rooted at a DIFFERENT repository, in its own brand-new container on the
  same environment, also measured zero.** Dumping every variable NAME (values
  stripped, so nothing secret is printed) showed only harness-provided ones —
  `CLAUDE_*`, `CCR_*`, the proxy and certificate-bundle settings,
  `GITHUB_TOKEN` — and **not one user-defined variable of any kind**. So this
  is not `PRECEDENT_*` being filtered out; nothing set in the environment
  configuration is arriving at all. **To tell "the variables do not arrive"
  from "the token specifically did not save", put a throwaway
  `PRECEDENT_PING=1` beside the token and start a NEW session.** If that
  throwaway variable is absent too, the fault is upstream of everything in this repository, and no
  amount of work on the token, the credential helper or `add_repo` will move
  it.

</details>


## 30. A `BLOCKED by freshness-guard` on your first tool call can mean your branch has no counterpart on origin yet

**Verdict: `archived`.** The trap cannot fire any more. Fixed 2026-09-11 in
both copies of the guard -- [.claude/hooks/freshness-guard.sh](../.claude/hooks/freshness-guard.sh)
and [templates/harness/claude-code/hooks/freshness-guard.sh](../templates/harness/claude-code/hooks/freshness-guard.sh):
`pre-write` and `session-start` now ask
`git ls-remote --exit-code --heads origin <branch>` before deciding what a
failed fetch meant, and wave through only exit 2 -- origin answered and does
not have the ref. Asserted in both directions in
[tools/verify_harness.py](../tools/verify_harness.py), including the negative
controls that an unreachable origin still exits 2 and still blocks, and that a
branch absent from origin is still refused when its base has moved. The live
entry in [AGENTS.md](../AGENTS.md) keeps only the lesson that survives the
fix: a refusal naming a remedy that cannot work is a question about what the
guard measured, never a reason to set `precedent.freshness.override`.

**Read the fix date against the tree before acting on the workaround below.**
Pushing an empty branch to give the guard a counterpart was the right move on
2026-09-09 and is unnecessary now.

<details>
<summary>The full entry as it stood before 2026-09-11</summary>

- **A `BLOCKED by freshness-guard` on your first tool call can mean your
  BRANCH has no counterpart on origin yet, not that your checkout is stale —
  and the override the message offers switches the guard off for the whole
  checkout.** Reported 2026-09-09 by a session working in one of the private
  practice-set repositories: its first command was refused because the branch
  it had been told to work on did not exist on origin, so there was nothing
  for the guard to fetch or compare against. **The remedy the refusal names
  is the wrong one here.** `git config precedent.freshness.override true`
  buys past a branch-shaped inconvenience by disabling freshness checking for
  the rest of the session — trading the guard that catches the single most
  expensive failure class in this file for the smallest possible convenience.
  **Push the branch instead.** It gives the guard a counterpart to fetch,
  costs nothing (the branch carries no commits beyond its base yet), and
  leaves every later check running. That session did exactly that, after
  confirming by hand that its HEAD matched `origin/main` on a clean tree.
  **Not established from here:** which of the guard's paths produced the
  refusal, or whether that set's copy is the older build named two entries
  above — that repository is under another owner and cannot be attached to a
  session rooted here, per the cross-owner entry below.

</details>

## 31. If you suspect a timezone problem, check `date` and `ls -l .git/hooks/pre-commit`, not the `env` block

**Verdict: `archived` (superseded), 2026-09-11.** Removed from
[AGENTS.md](../AGENTS.md) because its central claim had become **false**, not
because it had become quiet. It said the `env` block in
`.claude/settings.local.json` is **inert**. The commit-identity entry that now
stands in the live section says the opposite, from a measurement taken the
same day: the harness reads that block *before* hooks run, **so an explicit
`TZ` there beats `/etc/localtime` outright**, and one credential-less session
writing `TZ=America/New_York` into that untracked file poisons every later
session in the clone. Its instruction is therefore to **read that file first**
— exactly what this entry told a session not to bother doing.

Everything else it carried is in that entry too, in more detail: `TZ` unset in
tool shells so git falls back to the system zone, `commit-identity.sh`
repointing `/etc/localtime` for a declared zone, and `PRECEDENT_LOCALTIME`
existing so the repoint is testable. So nothing was lost by removing it, and a
contradiction between two adjacent entries went with it — which is the kind of
thing a reader resolves by trusting whichever one they read first.

The two diagnoses it was written about are entry 26 above; that derivation is
unaffected and stands.

<details>
<summary>The full entry as it stood until 2026-09-11</summary>

- **If you suspect a timezone problem, check `date` and
  `ls -l .git/hooks/pre-commit`, not the `env` block.** The block in
  `.claude/settings.local.json` is inert — the harness reads environment
  before hooks run — and reading it sent two diagnoses down the wrong path.
  `TZ` is unset in every tool shell, so git falls back to the SYSTEM zone;
  [.claude/hooks/commit-identity.sh](../.claude/hooks/commit-identity.sh)
  repoints `/etc/localtime` for a **declared** zone, which is the one lever a
  hook can move mid-session that every later shell and `git merge` picks up.
  `PRECEDENT_LOCALTIME` overrides the target so this is testable. The
  derivation is in the archive.

</details>


## 32. Your commits are authored by the bot because the harness sets that identity in git's GLOBAL config AND in every clone's LOCAL config

**Verdict: `compressed`.** Live where `PRECEDENT_COMMIT_*` is not set on the environment, and that is
still every fresh container nobody has configured -- so a live entry stands.
What moved here is the forensics of the two things that kept UNDOING the
repair, because both are now closed at the cause. `PRECEDENT_COMMIT_NAME`,
`_EMAIL` and `_TZ` in the environment are rung 1 of the hook's ladder: they
need no clone, no private source and no credential, so the fallback rung that
repointed `/etc/localtime` and wrote `TZ=America/New_York` into
`.claude/settings.local.json` is never reached. Verified 2026-09-11 by
controlled test -- a throwaway repo with an empty HOME, the two credential
variables scrubbed, and the bot identity preloaded as the harness sets it: the
hook resolved at rung 1, set the person, the global identity and the declared
-0300, and installed the backstop. The Stop-hook trap stayed in the live
entry; it is harness behaviour nothing here controls.

**Verbatim, as it stood in [AGENTS.md](../AGENTS.md) before the 2026-09-11 currency pass:**

- **Your commits are authored by the bot because the harness sets that
  identity in git's GLOBAL config AND in every clone's LOCAL config — so a
  global-only fix is silently overridden, and the Stop hook will tell you to
  put the bot back.** Measured 2026-09-11: `user.name=Claude`,
  `user.email=noreply@anthropic.com` in `--global` and in both clones'
  `--local`, `TZ` unset so the system clock reads **-0400** rather than the
  declared -0300, and no global backstop installed to refuse any of it.
  `git var GIT_AUTHOR_IDENT` returned the bot with no env override in sight.
  The cause is the entry above — a session rooted one directory up, so
  `commit-identity.sh` never ran — but the SYMPTOM reads as a git-config
  problem, and the config it reads as is one somebody already set on purpose.
  **The cost is that a wrong-author commit cannot be repaired after it
  merges** without rewriting `main`, which is why `fab8d42` and two entries in
  the individual set's `grandfathered_commit_shas` are permanent.
  **The remedy is one line, and it is not `git config`:**
  ```
  bash .claude/hooks/commit-identity.sh
  ```
  It sets the local identity, the GLOBAL one (so a clone attached later
  inherits a person), repoints `/etc/localtime` so later shells and
  `git merge` get the right offset without a `TZ=` prefix, and installs the
  global `core.hooksPath` backstop that refuses a bot-authored commit
  everywhere.
  **Running it once is not enough, and there are TWO separate things that
  undo it. Both were reproduced 2026-09-11; neither was guessed.**
  **First, and this is the one that kept coming back:
  `python3 tools/verify_harness.py` used to repoint the REAL container's
  `/etc/localtime`.** Its fixtures run `commit-identity.sh`, where no identity
  resolves, so the hook falls to its last rung -- this repo's declared
  `fallback_timezone`, `America/New_York` -- and moved the machine's own
  symlink to it. Controlled before/after: Buenos_Aires in, New_York out,
  across one harness run, with the session's clock left wrong afterwards.
  **The cost lands nowhere near the harness**: the NEXT commit is refused with
  `author-date offset is '-0400'` while the author is already correct, which
  reads as a fresh identity problem and is really this. Fixed by setting
  `PRECEDENT_LOCALTIME` once for the whole run, the same way the harness
  already sets `PRECEDENT_ALLOW_ANY_AUTHOR` for fixture commits -- the
  identical bug, one field over. If a stale harness is around, run it as
  `PRECEDENT_LOCALTIME=/tmp/x python3 tools/verify_harness.py`.
  **Second, a slower one that survives the session.** The same fallback rung,
  reached in a real session because the credential was missing, ALSO writes
  `TZ=America/New_York` into `.claude/settings.local.json` -- **untracked and
  gitignored**, so it shows in no diff and no review, and the harness reads
  that `env` block BEFORE hooks run, where an explicit `TZ` beats
  `/etc/localtime` outright. One credential-less session therefore poisons
  every later session in that clone, invisibly. **So read that file before
  touching any `git config`:**
  `python3 -c "import json;print(json.load(open('.claude/settings.local.json'))['env'])"`.
  Between them these explain why repairing the identity never held: after the
  first repair the identity was never wrong again, and the offset was arriving
  from a fixture that moved the machine's clock or from a variable a previous
  session had written. **Note the asymmetry** that hid it: an individual
  practice source carries a TRACKED `settings.json` env block naming its
  owner's zone, so work rooted THERE is immune; a shared repository
  deliberately names nobody, depends entirely on the hook, and is the one that
  gets poisoned.
  **The durable answer is `PRECEDENT_COMMIT_TZ` in the environment** -- on
  EVERY environment sharing a name, per the twin-environment trap above -- so
  the fallback rung is never reached at all. It needs `PRECEDENT_COMMIT_*` in the environment or a resolvable
  `identity.json`; with the variables present it needs no private repo at all.
  **Verify by effect, never by reading the config you just wrote:**
  `env -u GIT_AUTHOR_NAME -u GIT_AUTHOR_EMAIL -u TZ git var GIT_AUTHOR_IDENT`
  must name the person and the declared offset.
  **The second trap is the one that wastes the time.** The harness's own Stop
  hook flags commits whose committer is not `noreply@anthropic.com` and asks
  you to `--amend --reset-author` onto exactly the bot account the individual
  set's own `commit-author` practice refuses and its own mechanical check
  fails on — the account that practice's Rule calls never a person. Neither
  file is in this repository, which is why neither is linked here. Following it recreates the violation
  this repository spent a day fixing. **The repository's gate wins over
  generic harness guidance**; say so and leave the commit alone.



## 33. A `verify_harness.py` fixture that builds a "no credential" scenario inherits the container's real credential

**Verdict: `archived`.** The bug is fixed at the head of
[tools/verify_harness.py](../tools/verify_harness.py) -- all three variables
are scrubbed once, for every fixture, rather than in the fixture that happened
to notice -- and `check_fixtures_own_the_credential_environment` holds it
there as a control rather than a restatement: it plants the variables in a
subprocess, imports the module, and asserts they come back gone. Verified
present in the tree 2026-09-11, not taken from the entry's own claim. A short
live entry survives carrying only the diagnostic tell, because the failure
still reads as a missing credential when it happens and that reading sends a
session to fix access it already has.

**Verbatim, as it stood in [AGENTS.md](../AGENTS.md) before the 2026-09-11 currency pass:**

- **A `verify_harness.py` fixture that builds a "no credential" scenario
  inherits the container's real credential, so it asserts the opposite of
  what it ran — and it only fails once the environment starts carrying
  one.** 2026-09-11: four harness failures were reported to a person as
  "the absent `PRECEDENT_GIT_TOKEN`". The token was **present**
  (`env | grep -c PRECEDENT` said 6), and two of the four failed *because*
  of that. `check_source_credentials` and
  `check_individual_source_bootstrap_self_heals` each spawn subprocesses
  with `{**os.environ, ...}`; the cases asserting *"with no base url the
  team source is named as NOT in force"* and *"that hook degrades quietly
  when nothing else supplies one"* therefore ran against a real
  `PRECEDENT_SOURCE_BASE_URL`, tried to clone from github.com, and failed on
  `could not read Username` — which reads exactly like a missing credential
  and is a present one.
  **The diagnosis is backwards in the expensive direction**: it sends you to
  go fix access you already have. Separate the two by running
  `env -u PRECEDENT_GIT_TOKEN -u PRECEDENT_SOURCE_BASE_URL python3
  tools/verify_harness.py` — if failures *disappear*, the fixture is
  inheriting, not missing.
  One fixture's own comment said *"Run here with a HOME that has nothing and
  no git credentials"* while inheriting both, which is the tell: **a premise
  stated in a comment is not a premise the fixture established**
  ([fixture-owns-its-state](../practices/fixture-owns-its-state.md)). Both
  `run()` helpers and all four hook subprocesses now pop the two variables,
  so a case that wants either supplies it explicitly. Before that the whole
  harness's result depended on which container it ran in, and nothing said
  so.
  **The per-fixture pops are not the whole fix, because the next fixture
  will not have read them.** That practice's own Rule says to clear the
  ambient inputs at the top, once, rather than in the fixture that happened
  to notice — so the scrub also sits at the head of
  [tools/verify_harness.py](../tools/verify_harness.py), beside the
  `GIT_AUTHOR_*` one that was the identical shape four days earlier, and
  `check_fixtures_own_the_credential_environment` holds it there: it plants
  both variables in a subprocess, imports the module, and asserts they come
  back gone. Neutering the scrub turns three of its four cases red, the
  planted one included — so it is a control, not a restatement.
  **Third instance, 2026-09-11, `PRECEDENT_FRESHNESS_ALSO`** — it names
  OTHER repositories the freshness guard checks, so a guard fixture inheriting
  it walked out of its own temporary clone into this container's real attached
  sets, could not fetch a private one, and blocked. Both guard copies reported
  *"pre-write does not block a branch absent from origin (exit 2)"*, red on any
  machine with the variable and green everywhere else. **The tell is a block
  naming a repo or branch the fixture never created.** Scrubbed at the head of
  [tools/verify_harness.py](../tools/verify_harness.py) with the other two, and
  planted-and-asserted by `check_fixtures_own_the_credential_environment`.

  **The generalization is worth more than the fix: an ABSENCE is state
  too.** A fixture constructing "no credential is available" owns that
  absence exactly as much as it owns a file it wrote, and owning it means
  scrubbing the environment rather than merely declining to set anything.
  Same shape as the fixture whose `HOME` got a clone written into it, one
  level out — that one owned its scenario and not the environment the
  scenario was read from.



## 34. Attaching the private practice sets is a session-shape question, and what is measured about it does not add up

**Verdict: `compressed`.** The credential route made the `add_repo` question secondary rather than
primary: with `PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL` on the
environment the SessionStart hook clones every source before the first turn,
verified end to end on fresh containers 2026-09-10 and again 2026-09-11. So
the long 2026-09-09 measurement sequence -- the authenticated HTTPS probe, the
ambient-credential test, the credential-helper test that established that
route -- has done its work and is history. The live entry keeps the
contradiction in one paragraph (it is still true that nobody can explain it,
and a session may still need the fallback) and keeps the twin-environment trap
in full, which is the only half that still costs days.

**Verbatim, as it stood in [AGENTS.md](../AGENTS.md) before the 2026-09-11 currency pass:**

- **Attaching the private practice sets is a session-shape question, and what
  is measured about it does not add up — so measure, do not reason.** Three
  separate 2026-09-07 measurements had `add_repo` refusing a cross-owner add
  in BOTH directions with *"cross-tier adds are not supported in v1"*,
  including as a session's very first tool call. Two other sessions —
  2026-09-07 and 2026-09-08 — held `alex137/bestpractice` and four or more
  `themorgan/*` repositories at once, worked in and pushed to all of them.
  **Nobody has an explanation that fits both.** Do not build on either
  outcome and do not repeat an attempt expecting a remembered result: call
  `add_repo`, read what it says, and proceed from that.
  What is NOT in doubt is the cost of skipping it, and it is the entry above:
  a session with `individual` and `team` unresolved applies the wrong rules
  all day and cannot tell. If the adds are refused, **root the session in the
  repo you must PUSH to** and expect the other owner's repositories to be
  unattachable for its whole life — that is why work spanning both owners is
  split across two sessions. The full contradictory sequence is in the
  archive; read the verdict there before any single paragraph of it.

  **2026-09-09 adds one measurement that is not contradictory, and one route
  that does not depend on `add_repo` at all.** The refusal was reproduced as
  a session's very FIRST tool call, rooted at `alex137/bestpractice` — so
  "call it before anything else" is not a remedy: the initial repository
  already counts as *"session already has repos from owner(s)"*. Three other
  things were measured in the same container. An authenticated HTTPS request
  to github.com **reaches GitHub's own authentication** rather than a proxy
  error. There is **no ambient credential** for a private repo (a bare
  `git ls-remote` on one asks for a username; the same call on a public repo
  succeeds). And the credential helper in
  [tools/precedent_source_credentials.py](../tools/precedent_source_credentials.py)
  **does deliver** a token to git — with a deliberately invalid one, git sent
  it and GitHub rejected it rather than prompting. **So set
  `PRECEDENT_GIT_TOKEN` and `PRECEDENT_SOURCE_BASE_URL` in the environment
  ([INSTALL.md](../INSTALL.md) §8) and the SessionStart hook clones the sources
  before the first turn, where no ordering rule can reach it.** **Verified end to end
  2026-09-10**: a real read-scoped token in the environment, and a brand-new
  container came up with all four private sources cloned before the first
  turn — [tools/precedent_resolve.py](../tools/precedent_resolve.py) reported 146 practices
  from 6 sources (41 team, 13 individual) in a repo that had been resolving
  89 from 1. That tool prints `MISSING` when no credential is set and `SET`
  when one is set and a clone still failed, and the session check, the
  session-start source report and every vendor update print the same line.

  **The trap that made this look impossible for three days, and the only
  live half left: an account can hold TWO environments with the SAME NAME,
  and the selector gives you no way to tell them apart.** Measured 2026-09-09
  and 2026-09-10 — three sessions across two fresh containers reported
  `env | grep -c PRECEDENT` as **0**, with not one user-defined variable of
  any kind in a full name dump. That reads exactly like "the runner does not
  pass them through", and it is not that: `list_environments` showed **two
  environments both named `Default`**, same description, created 100 ms
  apart. The variables were set on one; the sessions ran in the other.
  Setting the same values on both fixed it in a single session. **Not
  established:** whether the twin was the whole cause or the first save had
  also failed — both fit what was measured, and nobody re-ran it to find out.
  **So: give your environments distinct names**, and put a throwaway
  `PRECEDENT_PING=1` beside the token — the ping separates "the variables do
  not arrive" from "the token is wrong", which print identically otherwise.
  An environment change never reaches a session already running, so test in a
  NEW one. The three-day sequence, including two readings that were right
  about the measurement and wrong about the cause, is entry 29 in
  [record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md).



## 35. A `BLOCKED by freshness-guard` on your first tool call is no longer the new-branch false positive it was until 2026-09-11

**Verdict: `archived`.** The mechanism is fixed in both copies of the guard and verified in the tree
2026-09-11: `git ls-remote --exit-code --heads origin <branch>` separates
"origin has no such branch" from "origin could not be reached". What the entry
had beyond the mechanism was a general lesson, and a general lesson does not
need 278 tokens in a file every session reads -- a one-line survivor carries
it, since the override is still offered in every block message and so the
shape can recur in some other guard.

**Verbatim, as it stood in [AGENTS.md](../AGENTS.md) before the 2026-09-11 currency pass:**

- **A `BLOCKED by freshness-guard` on your first tool call is no longer the
  new-branch false positive it was until 2026-09-11 — so read what it
  actually says before reaching for the override.** The guard used to treat
  "origin has no such branch" and "origin could not be reached" as the same
  failure, and refused the first write of every newly created branch; the
  remedy it named, `git fetch origin <branch>`, could not succeed against a
  ref that does not exist, so the only way forward a session found was
  `git config precedent.freshness.override true` — which switches freshness
  checking off for that checkout permanently, including the stale-base check
  that catches the single most expensive failure class in this file. Fixed in
  both copies here: `git ls-remote --exit-code --heads origin <branch>`
  separates the two, and only the branch-absent case is waved through — with
  the base-branch check still running on it. **What stays true is the shape
  of the trap**, since the override is still on offer in every block message:
  a refusal naming a remedy that cannot work is the moment to ask what the
  guard actually measured, not to disable it. **An unreachable origin still
  blocks, deliberately.** The 2026-09-09 incident, and the push-the-branch
  workaround it had to use, are entry 30 in
  [record/GOTCHAS_ARCHIVE.md](../record/GOTCHAS_ARCHIVE.md).



## 36. `git clone` with no `--branch` asks the SERVER which branch to check out

**Verdict: `compressed`.** Pinned since 2026-09-10 and verified in the tree 2026-09-11:
[tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
clones with an explicit branch and puts an existing clone back on it before
pulling, refusing rather than moving one with uncommitted work, and
[tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
reports a clone sitting off its branch at session start. The live entry keeps
the incident in short form and the lesson in full -- **when a rule forbids
asking a question, check whether something else is asking it for you** -- for
the reason the entry gives itself: the guard reads Python and could not see a
`git clone` making the same inference on our behalf, so the class is open even
though this instance is shut.

**Verbatim, as it stood in [AGENTS.md](../AGENTS.md) before the 2026-09-11 currency pass:**

- **`git clone` with no `--branch` asks the SERVER which branch to check out,
  and the answer is a setting on a web page that nothing in this repository
  can see.** The remote's `HEAD` symref is whatever the repository's default
  branch is set to, and git follows it silently. 2026-09-09, measured from a
  consuming repo: two practice-source repositories had that setting pointed at
  a feature branch, so every session-start clone of those sources landed on an
  older tree. `precedent_sync_views.py --check` then reported the CONSUMER as
  drifted, and a plain sync would have written the older text over newer
  committed text — deleting a practice's whole `## Story` block and a clause
  of its Rule, with no warning and exit 0. **The consuming repo had never been
  stale; the clone had been pointed somewhere else.**
  **The second half is what made it persist**: `git pull --ff-only` pulls
  whatever branch the checkout is already on, so a clone that landed wrong
  once stayed wrong every session afterwards.
  **The trap for a reader is that this repository already forbids exactly this
  inference and the guard could not see it.** `precedent_check.py --only
  declared-base-branch` fails any tool resolving `refs/remotes/origin/HEAD`
  without reading a DECLARED branch first — six tools carried that bug and two
  were actively wrong. It reads Python, so it never saw a `git clone` making
  the same inference implicitly, on our behalf. **When a rule forbids asking a
  question, check whether something else is asking it for you.**
  Pinned since 2026-09-10:
  [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
  clones with an explicit branch and puts an existing clone back on it before
  pulling — declared `base_branch` if the source declares one, else `main`,
  never the remote's HEAD. It **refuses** rather than moving a clone that is on
  the wrong branch with uncommitted work in it, because that is somebody's
  working copy. And
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  reports an attached clone sitting off its branch at session start, since a
  pin only takes effect the next time something clones or pulls.



## 37. The absence of `.claude/hooks/` is NOT evidence that a repo's hooks are missing

**Verdict: `compressed`.** Both halves are mechanical and both were verified passing 2026-09-11
(`precedent_check.py --only declared-hooks-exist`, and
[tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)'s
per-source pass). The misreading is still available to a session that reasons
from a directory listing instead of running the check, so a live entry stands;
what moved here is the detail of which set it was and how the first repair
attempt would itself have installed the second copy that set exists to
prevent.

**Verbatim, as it stood in [AGENTS.md](../AGENTS.md) before the 2026-09-11 currency pass:**

- **The absence of `.claude/hooks/` is NOT evidence that a repo's hooks are
  missing. Resolve the paths its settings.json actually declares — a
  directory listing cannot answer the question.** 2026-09-09: a session
  measured that an individual practice source had a `.claude/settings.json`
  and no `.claude/hooks/` directory at all, and concluded from that pair
  alone that the set's freshness guard and commit-identity backstop had been
  declared and silently off for its whole life. **They had not been.** That
  set wires four hooks to its own tracked `bootstrap/` directory, on purpose,
  so that one copy exists and nothing can drift from it; all four resolve,
  exist, and are executable. A path-resolving check across all five private
  sets then found every declared hook present and executable in every one.
  The wrong reading was easy because it names a real failure — a hook whose
  path does not exist really is silent, per the two entries above — and the
  two states look identical from a listing.
  **Both halves are mechanical now.**
  `python3 tools/precedent_check.py --only declared-hooks-exist` resolves
  every `$CLAUDE_PROJECT_DIR` hook path a settings.json declares and fails on
  one that is missing or not executable, in any repository the engine is
  vendored into.
  [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
  does the same per attached source and **refuses to "repair" a hook declared
  outside `.claude/hooks/`**: its own first version assumed the standard
  layout, and against that individual set would have installed exactly the
  second copy its comment exists to prevent.

