<!-- Last updated: 2026-09-04 by the session that drafted this plan, from a
     brainstorm conversation with Morgan. Not yet executed against a real
     repo or a real person — see "Status" below. -->

# Plan: a locked-down access pattern for non-technical contributors

**Status: drafted, not executed.** This is a self-contained implementation
plan, written so a fresh session (with no memory of the conversation that
produced it) can pick it up and carry it out. It has not been run against a
real employee or a real repo yet — doing so for the first time doubles as
[spec/PHASE6_BRIEF.md](PHASE6_BRIEF.md)'s still-open item 4 (the end-to-end
rehearsal of [INSTALL.md §0](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using),
which that brief already flagged as "not yet rehearsed end to end against a
real project" and "the biggest and least certain piece of work"). Treat any
friction this plan hits as a finding for that item, not just a one-off fix.

## The problem this solves

Morgan wants to bring people who work at a Google-Docs level of technical
skill — never touching GitHub, never seeing git or mechanical-rule
vocabulary — into a repo that vendors this Precedent loader, so their
plain-language observations and ideas can become real practice candidates.
They must not be able to break the repo, and must never be put in a
position to approve or even notice anything technical (a merge, a mechanical
check, a resident-budget tradeoff). Two things have to be true at once:
structurally safe, and legible to someone who has never used git.

## The model (two independent layers — both required)

1. **GitHub's own collaborator role on the person's repo — the actual,
   platform-enforced boundary.** Set to **Triage** (can comment on and
   manage Issues — enough to participate in candidate threads — but cannot
   push, merge, or touch protected files) or **Read** (view only, no Issue
   comments) if even that is too much. This is enforced by GitHub itself,
   independent of anything Claude does or is told — a push attempt is
   rejected at the API level, not talked out of.
   - **This only binds anything if the person authenticates to GitHub as
     themselves.** If their Claude Code session instead rides a shared
     org-wide GitHub connection with broader rights, their individual
     collaborator role is never actually checked. Confirm which model
     applies before relying on this layer — see "Prerequisites," item 2.
2. **Claude Code session/environment configuration — the UX and
   defense-in-depth layer.** A restricted `permission_mode` (never
   `bypassPermissions`) and a tool allowlist with no push/merge/arbitrary-shell
   entries, plus a plain-language persona instruction, so the person is
   never even offered a technical option, let alone asked to approve one —
   and so trouble that doesn't route through GitHub at all (e.g. shell
   commands) is also blocked. This is enforced by the harness's own
   configuration, not by GitHub, and doesn't depend on the answer to (1).

Neither layer alone is sufficient: GitHub roles don't stop confusing or
costly tool use that never reaches GitHub; session config alone is only as
strong as Claude's cooperation, not a hard platform boundary.

## Prerequisites — decide/do before starting (some need Morgan directly)

1. **Which repo, and does it exist yet?** The plan below assumes a project
   repo for this person that will vendor the Precedent loader per
   [INSTALL.md §0](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using).
   If it doesn't exist, create it first (private, per this repo's own
   working style) — `mcp__github__create_repository` if the implementing
   session has that tool, otherwise Morgan creates it directly.
2. **Confirm the GitHub auth-binding model** (blocks layer 1 entirely if
   wrong). Does this person's Claude Code session connect *her own* GitHub
   login, or does it ride a shared connection? This is a platform detail
   the implementing session should verify empirically rather than assume —
   e.g. have her attempt something her role should forbid (a direct push)
   once set up, and confirm GitHub actually rejects it under her identity,
   not just that Claude declined to try. If the answer is "shared
   connection," layer 1 does nothing and the plan is *session-config-only*
   until that's fixed — say so plainly rather than reporting the setup as
   safe.
3. **Add her as a repo collaborator — Morgan (or an org admin) does this
   by hand.** No tool in this session's GitHub toolset creates a
   collaborator invite (confirmed absent from the available `mcp__github__*`
   tools while drafting this plan — only listing collaborators is exposed,
   not adding one). GitHub UI: repo → **Settings → Collaborators and teams
   → Add people** → her account → role **Triage** (recommended default —
   lets her comment on candidate Issues) or **Read** if even that's too
   much. This mirrors
   [templates/AGENTS.md.loader.template](../templates/AGENTS.md.loader.template)'s
   existing "Add project members" administrator flow, which today only
   names Read/Write as the choice — extending it with a Triage-for-limited-
   contributors option is part of this plan's step 4 below, not a
   prerequisite to redo by hand each time.
4. **Decide Triage vs. Read.** Triage is the right default if she should be
   able to comment on her own raised candidates and see responses — closest
   to the "Google Docs commenting" experience Morgan described. Read only
   if even Issue participation should route entirely through Claude instead
   of her ever opening GitHub's Issues tab herself (she may never open
   GitHub at all either way — this only matters if she ever does).

## Implementation sequence

### Step 1 — Install the Precedent loader into her repo

Follow [INSTALL.md §0](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)
exactly: vendor `practices/` and the whole `tools/` directory from this
repo (`precedent-beta-v01` today — see this repo's own
`environment-gotchas` entry on that name), write `precedent.json`,
instantiate [templates/AGENTS.md.loader.template](../templates/AGENTS.md.loader.template)
as her repo's `AGENTS.md`, run [tools/precedent_sync_views.py](../tools/precedent_sync_views.py). §0 has not
been rehearsed end to end before this — expect to hit gaps; record them
(see "Closing the loop," below) rather than silently working around them.

### Step 2 — Wire the candidate pipeline for real use, not the placeholder

[tools/precedent_candidate.py](../tools/precedent_candidate.py) gets vendored by step 1 (it's part of
`tools/`), but the loader template's merge-runbook step 0b currently
carries a placeholder — a plain pull request (PR) against the upstream repo — because, per
that template's own comment, "the candidate/promotion pipeline ... is not
wired into a fresh install as of this writing"
([spec/PHASE6_BRIEF.md](PHASE6_BRIEF.md) tracks this as open item 2). That
gap is about *exporting to this upstream repo*; it does not block her
repo's own local candidates. Add an explicit instruction to her repo's
`AGENTS.md` (a new bullet, near the "Administrator requests" section) that
when she raises a practice idea in plain language, Claude:

1. Restates it back to her in her own words to confirm before acting.
2. Drafts a candidate with [tools/precedent_candidate.py](../tools/precedent_candidate.py) at whatever level
   fits (individual, if it's just her working style; team/universal via
   `--as-issue true` if it should become a GitHub Issue others can see and
   comment on — see [spec/CANDIDATE_FORMAT.md](CANDIDATE_FORMAT.md)'s
   "Which one for team" for the exact rule on when a file is enough versus
   when it needs to be an Issue).
3. Never mentions promotion, resident budgets, `checked_by`, or any other
   mechanical-rule vocabulary to her — that's Morgan's or a technical
   session's business, not hers.

### Step 3 — Restrict her Claude Code session/environment

- If a dedicated `environment_id` is available for her, configure it (or
  her per-session settings) with `permission_mode` never set to
  `bypassPermissions`, and exclude `git push`, `git merge`, and any raw
  shell tool from the allowlist — contrast with
  [templates/harness/claude-code/settings.json](../templates/harness/claude-code/settings.json)'s
  stock allowlist, which includes `git push -u origin *` by default; hers
  should not.
- Give her repo's `.claude/settings.json` (or her session's system-prompt
  addendum) the plain-language persona instruction: no git/GitHub jargon,
  no mechanical-rule talk, restate her ideas before acting on them, route
  everything through step 2's candidate flow.

### Step 4 — Generalize the "Add project members" flow (small, do it now)

Since this is the first time a Triage-level, non-technical contributor
pattern is needed, fold it back into
[templates/AGENTS.md.loader.template](../templates/AGENTS.md.loader.template)'s
existing "Add project members" administrator flow (currently only
distinguishes Read vs. Write) so the next repo doesn't have to re-derive
this plan from scratch — add a third option naming Triage and when to
choose it, and the persona-instruction step. Small, bounded, and this
plan's own step 3 already worked out the wording — do it in the same
session rather than filing it as a follow-up.

### Step 5 — Verify, don't just report success

Per this repo's own `verify-postcondition` practice: name the actual state
wanted, then test it independently of what any command printed.

- **"She cannot push or merge."** Have her session attempt a direct push
  (to a throwaway branch is fine) and confirm GitHub itself rejects it
  under her identity — not that Claude simply didn't try.
- **"Her session never offers a push/merge/shell tool."** Check her
  session's actual configured tool list, not just the persona instruction
  text.
- **"A plain-language idea she raises produces a real candidate."** Run one
  end-to-end example: have her describe an observation in her own words,
  confirm a candidate file or Issue is actually created (per step 2), and
  that no git/mechanical vocabulary appeared in her conversation.
- **"The GitHub-auth-binding assumption from Prerequisites item 2 holds."**
  Re-confirm explicitly, in writing, in the record this step produces —
  don't let it stay an assumption once it's actually been tested.

## Closing the loop

Once run for real, write up what happened — what INSTALL.md §0 got right
or missed, what step 2/4's wiring actually looked like once tested, and the
verification results from step 5 — as an update or a new spec brief in the
same style as [spec/PHASE6_BRIEF.md](PHASE6_BRIEF.md), and link it from
that brief's own "real work still ahead" item 4. This is the first real
rehearsal that brief has been waiting on; its findings belong there, not
only in this plan.

## What this plan does not cover

- Team- or universal-level candidate promotion once she's raised one — that
  still needs a listed approver (Morgan, or whoever `approvers.json` names)
  to run [precedent_promote.py](../tools/precedent_promote.py)/[precedent_land.py](../tools/precedent_land.py); nothing here changes
  who can land a practice.
- What happens if her repo needs a `team` source too (a second private
  set shared with other technical contributors) — same mechanics, not
  addressed here since it wasn't part of the original scenario.
- Non-GitHub hosts (see [TODO.md](../TODO.md) item 8) — this plan assumes
  GitHub throughout, since that's what her repo and this loader use today.
