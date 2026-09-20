---
slug:              todo-2026-09-09-source-hook-drift
kind:              decision
domain:            null
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "those other threads first, then a session rooted under the sets' own owner to carry it out — this repository's sessions cannot push there, re-confirmed 2026-09-09 by `add_repo` refusing at `access: \"push\"`. It carries no disposition, so it is `wait` ([open-item-disposition](practices/open-item-dispo"
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-09
closed:            null
---
## What

- <a id="source-hook-drift"></a>**Decide whether a drifted-but-present session hook in a practice-set
   source gets brought up to canonical automatically.** Measured 2026-09-09
   across the five private sets: every declared hook exists and is
   executable, so nothing is broken — but one set's `freshness-guard.sh` is
   an older, shorter build supporting only `session-start` and `pre-write`
   (its settings.json wires no `UserPromptSubmit` to match, so it is
   self-consistent, not damaged), and `commit-identity.sh` is one version
   behind in all five, which is the signature of canonical moving on after
   installation.
   [tools/precedent_refresh_sources.py](../tools/precedent_refresh_sources.py)
   restores a hook that is declared and *missing*; it deliberately does not
   touch one that is present, because overwriting a working guard changes
   what blocks a session, and a set may be sitting on an older build for a
   reason. The question is whether hook content should join the vendored
   engine as something `--apply` keeps current, with the same
   review-and-publish rules, or stay a per-set decision.
   **Approved 2026-09-09, `strength: assented`.** Morgan: *"Okay let's
   follow your advice. Make the changes you recommended in all the repos you
   recommended"*, and, in the same message, *"Except don't yet update the
   vendored-in versions; we'll make some changes in some other threads
   first."* Both halves are authorized — refresh `commit-identity.sh` across
   all five sets, and bring the older `freshness-guard.sh` up to canonical
   including the `UserPromptSubmit` wiring it currently lacks — and **none of
   it is carried into the sets until those other threads land.** Recorded
   `assented` rather than `decided` because it is agreement to this session's
   own proposal, not him choosing it independently
   ([decision-strength](../practices/decision-strength.md)).
   **The `commit-identity.sh` half is NOT done, and the line below claiming
   it was is wrong.** It read: *"the same `BOOTSTRAP DRIFT` check that found
   it, re-run against all four sets brought current, reports no
   `commit-identity.sh` difference in any of them."* Measured again
   2026-09-11, later the same day, by `verify_harness.py`'s byte-identical
   copy check with all four sources attached: `precedent-individual` matches
   canonical, and **all three team sets still differ**. Whatever that earlier
   re-run covered, it was not these three.

   **What differs is two lines and neither of them executes**, which is why
   this is housekeeping rather than a live defect. The team sets carry
   `DEFAULT_TZ="America/Argentina/Buenos_Aires"` and its matching comment;
   canonical carries `America/New_York`. `DEFAULT_TZ` is the hook's
   last-resort rung, reached only when the repository declares no
   `fallback_timezone` — and all three declare one, so the line is
   unreachable in every repo that has it. No commit's offset has ever come
   from it.

   **It is staleness, not a hand-edit.** The sets were refreshed to canonical
   on 2026-09-09 (`c0d0bcb`); canonical then moved that literal in `4abb73b`
   on 2026-09-10, *"Move the engine's last-resort timezone off one person's
   zone"*. The sets are simply pre-`4abb73b`.

   **Their `precedent.json` must not be touched while fixing this.** All
   three declare `fallback_timezone: America/New_York`, decided in `9ad7ff0`
   on 2026-09-10 — a team set is shared by level, so an unidentified
   committer there could be anyone, and Buenos Aires is Morgan's own zone and
   belongs in his individual source. The refresh is about not drifting from
   canonical; the value that actually fires is already right.

   **Blocked-on:** a session rooted under the sets' own owner. Measured
   2026-09-11 from here — `git push --dry-run` into a team set returns *"not
   in this session's authorized repository set, so the proxy will not inject
   a credential"*, HTTP 403.

   **The `freshness-guard.sh` half is DONE too, landed 2026-09-11 here.** The
   direction was upstream, as the 2026-09-11 reading below predicted: the
   set's copy carried two mechanisms canonical did not. **One of them was
   already being fixed in parallel** — `e572e9e` landed
   `_branch_absent_from_origin` the same day, from the incident rather than
   from the set — so only the other was carried, and canonical KEPT its own
   version of the first.

   - **The absent-branch split: not carried, upstream's shape kept.** Both
     ask `git ls-remote --exit-code`. The set's `_remote_branch_state`
     returns a three-way state and is called BEFORE the fetch; canonical's
     `_branch_absent_from_origin` returns a boolean and is called only AFTER
     a fetch has already failed, so the common case costs one round trip
     instead of two. Same behaviour in all three cases, and canonical's is
     cheaper for a hook that runs at every session start and first write.
   - **`PRECEDENT_FRESHNESS_ALSO`: carried.** A `;`-separated
     `<path>=<base branch>` list of repositories the session merely has
     ATTACHED, with the per-repo split (`_session_start_one`,
     `_pre_write_one`, `_also_entries`, `_also_resolve`) that makes both
     modes walk them. Generic: a hook fires for the project dir and nothing
     else, so a sibling clone a team source resolves to runs none of its own
     freshness checking — that is Precedent architecture, not one person's
     layout. Unset, it changes nothing.

   `check_freshness_guard_checks_attached_repositories` in
   [tools/verify_harness.py](../tools/verify_harness.py) runs both copies of the
   real hook against real repositories and asserts the guard's own words, with
   a control requiring the same stale attached repo to pass silently when the
   variable is unset
   ([control-asserts-which-failure](../practices/control-asserts-which-failure.md)).

   **What the set and canonical still differ on, so the remainder is
   explained rather than open.** Four comment differences, each deliberate:
   its own `bootstrap/` install path (that set wires hooks from a tracked
   directory on purpose, one copy with nothing to drift from it, and
   canonical must describe the layout an adopter gets); a citation of one of
   that set's private practices, which an adopter cannot read; and two places
   naming this repository where canonical needs the generic case. Plus the
   one real code difference above — the two shapes of the absent-branch
   check.

   **Blocked-on, and it needs a session rooted under the sets' own owner:**
   the set should take canonical's `_branch_absent_from_origin` in place of
   its own `_remote_branch_state`, which is the cheaper shape and ends the
   divergence; and a later `--apply` that brings hooks up to canonical wants
   those four comment differences reconciled deliberately rather than
   silently overwritten, since two of them are that set's own layout being
   correct about itself. This repository's sessions cannot push there
   (re-confirmed 2026-09-09 by `add_repo` refusing at `access: "push"`).

   **Also blocked-on, and smaller:** in `pre-write` the per-repo messages do
   not name WHICH repository they are about — `fast-forwarded 'main'` reads as
   the project dir even when the also-list found it in an attached one (the
   `session-start` half does print `also checking attached repository
   <path>`). Left as-is deliberately: changing those strings would diverge
   the two files' executable content again, and that set's own mutation test
   asserts them, so the fix has to land in both at once.

   **Confirmed independently 2026-09-11**, by the very deep check's new
   `BOOTSTRAP DRIFT` section on its first real run: regenerating each set
   with today's generator and diffing it found `commit-identity.sh`
   differing from canonical in every set it could see, and
   `freshness-guard.sh` differing in `precedent-individual`. Two mechanisms
   that share no code now say the same thing, so the measurement above is
   not an artifact of how it was taken.
   **Blocked-on:** those other threads first, then a session rooted under the
   sets' own owner to carry it out — this repository's sessions cannot push
   there, re-confirmed 2026-09-09 by `add_repo` refusing at `access: "push"`.
   It carries no disposition, so it is `wait`
   ([open-item-disposition](../practices/open-item-disposition.md)).

   **Still open, and now measured against a hook that MATTERS: 2026-09-14,
   all four sets carry a `freshness-guard.sh` with no `_deepen_if_shallow`.**
   That is the shallow-clone phantom-divergence fix
   ([record/GOTCHAS.md#g37](../record/GOTCHAS.md#g37)), so a session rooted in
   any of the four meets the full trap — the guard refuses to update a
   checkout that is merely behind, and the session then works from a stale
   tree without knowing. The same day's engine refresh across all four sets
   did not carry it, which is the point of this item: the engine has a repair
   path and the hooks do not. This raises the stake on the question above
   without answering it — "a set may be sitting on an older build for a
   reason" is still true, and is now weighed against a guard that misreports
   staleness.

   **Morgan authorized the carry the same day, and a BestPractice-rooted
   session cannot perform it — established, not assumed.** 2026-09-14, asked
   to push the guard out to the four sets, a session here copied canonical
   into each set at the path that set's own `settings.json` declares
   (`bootstrap/freshness-guard.sh` in the individual set, `.claude/hooks/` in
   the three team sets — [record/GOTCHAS.md#g19](../record/GOTCHAS.md#g19)),
   committed all four on `precedent/carry-deepen-fix`, and got HTTP 403 on
   every push: *"not in this session's authorized repository set, so the
   proxy will not inject a credential"*. `add_repo` at `access: "push"` then
   refused with a different message than the one this item already records —
   *"cross-tier adds are not supported in v1"*, naming the owner mismatch
   directly. **Those four commits died with that container**, which is the
   part worth knowing: the work is a verbatim copy of a file in a public
   repository, so a session rooted in the sets reproduces it in one command
   rather than needing anything transported.
   **The carry itself no longer needs a decision** — it is the `assented`
   authorization above, now narrowed to one hook and one reason. What stays
   open is the general question: whether `--apply` should keep hook content
   current by default.

   **The general question now has an answer on the CONSUMER side, 2026-09-15,
   which is directly relevant precedent here even though it does not close
   this item.** `precedent_vendor_engine.py` now vendors `.claude/hooks/*.sh`
   the same way it vendors `tools/` — tracked in `ENGINE_MANIFEST.json`
   (`hook_files`/`hooks_sha256`), refreshed by `refresh`, refused on
   hand-edit unless `--force`, scoped to what a repo's own `settings.json`
   actually wires (`_wired_hook_names`, added after a first version vendored
   everything unconditionally and planted an orphan hook in every plain
   consumer install — caught by `hooks-on-disk-are-reachable` before it
   shipped). That answers "should hook content join the vendored engine as
   something kept current" for a consumer repo: yes, drift-checked, never
   silent. **It does not answer it for an attached practice-set source** —
   `precedent_refresh_sources.py` is a different tool, a different
   destination shape (a sibling clone, not a vendored copy), and this item's
   own blocked-on (a session rooted under the sets' own owner) still holds.
   Whoever picks this item up should read `_wired_hook_names`'s docstring in
   `tools/precedent_vendor_engine.py` before designing the source-side
   answer — the orphan-hook failure mode it describes applies just as much
   to a set's `bootstrap/` layout as to a consumer's `.claude/hooks/`.

## How It Closes

Not open until: those other threads first, then a session rooted under the sets' own owner to carry it out — this repository's sessions cannot push there, re-confirmed 2026-09-09 by `add_repo` refusing at `access: "push"`. It carries no disposition, so it is `wait` ([open-item-disposition](practices/open-item-dispo

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
