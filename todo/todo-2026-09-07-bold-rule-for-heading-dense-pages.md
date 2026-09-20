---
slug:              todo-2026-09-07-bold-rule-for-heading-dense-pages
kind:              analysis
domain:            content
severity:          null
status:            open
disposition:       wait
remind_on:         null
blocked_on:        "a session rooted in precedent-team-repo-maintenance (the practice's own set) to actually land the clause; this repository's sessions cannot push there."
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-07
closed:            null
---
## What

- <a id="bold-rule-for-heading-dense-pages"></a>~~**`bold-key-phrases` needs a weak
    counter-clause for heading-dense pages.**~~ **Done 2026-09-07**, in the team set,
    on branch `claude/bold-phrases-density-clause-mo6m33`. The clause went to
    `## Detail`, not `## Rule`: the practice is `tier: resident`, and a suggestion
    named deliberately weak does not earn text every session carries whether or not
    the occasion fires — the counterweight it qualifies ("emphasis is a budget", the
    two rough tests) was already in Detail, so the qualifier sits with what it
    qualifies. The resident block is unchanged at ≈248 tokens. No `checked_by`, for
    the reason this item gave. The Story carries the incident: the audit sweep was
    right for the page as it then stood, the page grew, the same emphasis stopped
    signalling — both halves kept, because the rule was right the first time and
    wrong the second on the same document.

    **The four-step runbook below was followed as written and every step held**,
    including the two the item could only predict: `add_repo` accepted both sibling
    `themorgan/*` sets from a session already holding one (the cross-tier rule keys
    on owner, as [AGENTS.md](../AGENTS.md)'s gotcha says), and a plain `git clone` of the
    public upstream needed no credentials. Kept unstruck as a working recipe for the
    next cross-set edit.

    **Follow-on, 2026-09-07: landing it in BOTH team sets made the resolver refuse.**
    `bold-key-phrases` now exists in `precedent-team-repo-maintenance` and
    `precedent-team-tms`, and so does `fail-gracefully` — two same-slug practices at
    the same level, landed the same day by two sessions each doing the obviously
    right thing. `precedent_resolve` raises `ResolveError` on a source list holding
    both: *"nothing orders two sources at the same level, so there is no answer to
    which one wins."* Any repository declaring both team sources fails to resolve
    entirely. Nothing is broken today (no repository declares both), and the
    question is filed at
    [`practice-consistency-across-team-repos`](todo-2026-09-07-practice-consistency-across-team-repos.md)
    with a recommendation. Morgan, 2026-09-07, on
    [documentation/WHY_PRECEDENT.md](../documentation/WHY_PRECEDENT.md):
    "this page has a lot of headings and short lists, so that would make it too
    bold". He asked for the one-line lead-in under each `##` to carry no bold
    at all — done that day — and named the rule himself as **a suggestion,
    deliberately weak**, not a gate.

    The page's own history is the evidence on both sides.
    [spec/PRELAUNCH_AUDIT.md](../spec/PRELAUNCH_AUDIT.md)'s round-three sweep
    found this exact document at 0.1 bold spans per 100 words against 0.8-1.9
    in every other outward-facing document and added seventeen, which was
    right at the time. The document has since grown from four groups to five
    and from twelve items to eighteen, and at that density a bold lead-in
    under every heading marks nothing — the structure is already doing the
    emphasis. **What to write:** an advisory clause on `bold-key-phrases`
    saying the density is judged against running prose, and that a page whose
    own structure carries the emphasis leaves its section lead-ins plain.
    **Deliberately no mechanical check:** a spans-per-100-words ratio cannot
    tell a heading-dense page from an under-emphasized one, which is the whole
    finding — a check here would re-flag the page Morgan just fixed.

    **Where it lives:** the TEAM set, `precedent-team-repo-maintenance`, at `tier:
    resident` — [spec/PRACTICE_ENGINE_PLAN.md](../spec/PRACTICE_ENGINE_PLAN.md)'s
    resolve run and [spec/PHASE5_DEEPCHECK.md](../spec/PHASE5_DEEPCHECK.md) both
    name it there alongside `nonblocking-questions` and `small-calls`. Being
    resident matters for the wording: it is carried in every session's context
    whether or not the occasion fires, so the clause has to be short.

    **Blocked on:** a session with that set on disk. This one does not have it
    ([tools/precedent_resolve.py](../tools/precedent_resolve.py): team source
    `../precedent-team-repo-maintenance` absent, no individual config — checked on
    disk rather than recalled, per
    [`migrated-practices-lost-their-stories`](todo-2026-09-06-migrated-practices-lost-their-stories.md)'s
    own correction about blockers taken from memory). Asked to attach it
    2026-09-07, `add_repo` refused for the reason
    [AGENTS.md](../AGENTS.md)'s gotcha already records — *"cross-tier adds are not
    supported in v1: requested themorgan/precedent-individual but session
    already has repos from owner(s) [alex137]"* — while `list_repos` shows all
    three private sets with `can_push: true`, so this is the session's shape,
    not the account's rights.

    **How to run it,** in this order — the order is the whole trick:

    1. Start a session whose **initial source** is
       `themorgan/precedent-team-repo-maintenance`. This is the only step that
       cannot be done from inside another session.
    2. `add_repo` `themorgan/precedent-individual` from there if you want
       it — same owner, so the cross-tier rule does not fire. **It is not
       part of this job.** `bold-key-phrases` is in
       `precedent-team-repo-maintenance` only, and team sets are siblings rather
       than a hierarchy, so nothing propagates between them. Sharpened
       2026-09-07 after Morgan asked whether this was one team set or all
       `precedent-team-*`. (`precedent-team-tms` was named here too until
       2026-09-10, when it was retired — it held one practice,
       `audience-register`, which moved to `precedent-team-working-style`.)

       **The consequence is worth seeing, and is a separate question:** the
       clause will not reach editorial document projects, which are the
       heading-dense prose pages it most describes. They do not carry
       `bold-key-phrases` at all —
       [templates/document-project/precedent.json](../templates/document-project/precedent.json)
       declares universal plus `precedent-team-writing` and
       `precedent-team-working-style`, not `-maintainers`.
       Wanting the rule there is a level decision (promote to universal, or
       copy to `-tms`), for Morgan, not something this item's clause does.
    3. Reach BestPractice with a plain `git clone` of
       `https://github.com/alex137/BestPractice` (branch
       `precedent-beta-v01`), **not** `add_repo` — the same cross-tier rule
       refuses it in that direction too, and this repo is public, so a clone
       needs no credentials.
    4. Edit `practices/bold-key-phrases.md` in the team set, follow that
       repo's own AGENTS.md for branch and checks, and push there.

    **What that session cannot do:** push to this repo. Its git credentials
    cover `themorgan/*` only, so striking this item through is a separate
    one-line follow-up from a BestPractice session, after the clause lands.

- ~~**`precedent_check.py` is not vendored into source sets, so a practice
  set enforces nothing of the universal catalogue.**~~ **Done 2026-09-07**, in
  the same day it was filed. It is the root cause behind two other items:
  `cite-the-incident`'s check never ran in the private sets, and neither did
  the status-contract check
  ([`convert-team-set-retired-statuses`](todo-2026-09-06-convert-team-set-retired-statuses.md)
  records the same shape). Both were assumed to be running. **A gap declared
  in a repo that cannot check for it is indistinguishable from one nobody
  declared** — which is how 34 empty Stories sat in a team source with its
  own gates green.
  **A correction to this item's own first draft, kept because the mistake is
  instructive:** it said the file was in *neither* `ENGINE_FILES` nor
  `CONSUMER_ENGINE_FILES`. That was wrong about consumers — it had been in
  `CONSUMER_ENGINE_FILES` all along — and right about sources. The conclusion
  survived because the repos that were actually broken are the three private
  *source* sets, not the consumers; but the supporting claim was overstated,
  and was asserted from reading one list rather than both.
  **What it took:** adding it to `ENGINE_FILES` (it reaches
  `CONSUMER_ENGINE_FILES` automatically, which is built from it), plus
  guarding the two imports that were still bare — `title_case` and, in
  `_source_naming`, `precedent_resolve`. A source set gets neither module,
  and an unguarded import turns a legitimately absent dependency into an
  ERRORED check, which reads as a broken tool rather than an absent one.
  `doc_lint` and `doc_sync` already degraded correctly.

## How It Closes

Not open until: a session rooted in precedent-team-repo-maintenance (the practice's own set) to actually land the clause; this repository's sessions cannot push there.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
