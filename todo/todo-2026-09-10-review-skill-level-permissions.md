---
slug:              todo-2026-09-10-review-skill-level-permissions
kind:              manual
domain:            null
severity:          null
status:            open
disposition:       ask
remind_on:         "2026-09-10"
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-10
closed:            null
---
## What

- <a id="review-skill-level-permissions"></a>**Review the whole
   technical/non-technical permission split, now that the pieces are in
   three separate places.** Asked for by Morgan on 2026-09-10, closing the
   thread that produced the split: *"note a TODO to review the 'technical vs
   nontechnical' permissions later."*

   **ANSWERED 2026-09-11, in the part that was actually blocked on him.**
   Morgan drew the line himself: *"The dividing line I wanted to make is
   between whether they can make practices (no, only suggest them) or other
   'technical' changes (update vendored files, etc)"* — and, on the model the
   item describes below, *"I think the Nontechnical users still need to
   contribute. This is an alternative to google docs, they need to write and
   create hand in hand with AI."* The line is now keyed to **paths and to
   `approvers.json`, not to a kind of person**, so the two open bullets below
   are moot rather than decided: there is no per-person restriction left for a
   mis-set role to be a backstop against, and no forgettable per-person deny
   list, because the boundary is `.github/CODEOWNERS` plus branch protection.
   [spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md) is the rewrite.
   **What stays open is smaller and is named there**: the three unverified
   GitHub behaviours (item 14 carries them), and whether the
   identity-resolving guardrail in its "What this does not cover" section is
   worth building at all. `strength: decided` for the line; `assented` for the
   CODEOWNERS mechanism, which was this session's proposal.

   **What the split used to be.** A non-technical contributor was restricted by
   their GitHub collaborator role (Triage or Read, never Write), which GitHub
   enforces server-side, and by their own session or environment
   configuration — a dedicated `environment_id`, per-session settings, or an
   untracked `.claude/settings.local.json`. Nothing restricting them lived in
   a tracked file any more:
   [templates/document-project/](../templates/document-project/)'s
   `.claude/settings.json` denies `rm` alone, which is not role-specific.
   [spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md)
   Step 3 is the specification;
   [practices/technical-describes-people.md](../practices/technical-describes-people.md)
   is the rule that keeps a per-person restriction out of a shared file.

   **What is worth reviewing, and why it is a review rather than a fix.**
   Three things came up while the split was being made and none was decided:

   - **The tracked deny list was an accidental backstop against a mis-set
     GitHub role**, and removing it means instantiation step 5's role
     assignment now carries that weight alone. Nothing checks it.
   - **The per-person layer is a manual README step** (instantiation step 6),
     so it can simply be forgotten. The contributor is still blocked by their
     role if it is — they just get a worse error — but nobody has decided
     whether that is acceptable or whether the step should be mechanical.
   - ~~**The spec file still carries the project-vs-person slippage in its
     own filename.**~~ **Fixed 2026-09-10**, together with two documentation
     guides named for their readers' skill level, after Morgan restated the
     point directly: *"WE SHOULD NOT MAKE A DIFFERENCE BETWEEN TECHNICAL OR
     NONTECHNICAL PROJECTS/DOCUMENTS."* `NONTECHNICAL_TEAM_PRACTICE_CAPTURE`
     → [spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md](../spec/DOCUMENT_WORK_PRACTICE_CAPTURE.md),
     `HOW_TO_USE_THIS_TECHNICAL` →
     [documentation/FOR_DEVELOPERS.md](../documentation/FOR_DEVELOPERS.md),
     `HOW_TO_USE_THIS_NONTECHNICAL` →
     [documentation/FOR_EVERYONE_ELSE.md](../documentation/FOR_EVERYONE_ELSE.md).
     [spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md)
     is correct as it stands — it names a contributor, who is a person, and
     the practice's own check exempts exactly that form.

   **blocked-on:** nothing, for the policy call — answered above on
   2026-09-11. What the original entry said, kept because it is why this sat
   for a day: every open question here is a policy call about
   how much protection a forgettable manual step may carry, not something a
   session can settle by reading the tree. He named the reason it waits
   rather than the reason it is hard: *"it requires deeper thought of mine
   and I can't do it now because I still have a dozen claude tabs open and I
   want to wrap up the repo_add issues, the voice issues etc first."* So the
   blocker is his attention, and the queue ahead of it is real work he has
   already named.

   ~~**Remind:** still pending on Morgan; surface it again on 2026-09-15 as a
   line in this list, not as a trigger phrase — he asked for the reminder to
   be the note itself (2026-09-14, Morgan)~~ **Answered 2026-09-14, a day
   early, by Morgan asking for it himself**: the review is
   [spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md)'s "Review,
   2026-09-14" section, and what it left open is the items it names. The
   "worse error" bullet above has a proposed mechanism now
   ([`pre-pr-ownership-guardrail`](#pre-pr-ownership-guardrail)).
   **Disposition:** wait (2026-09-14; the ask was answered, the follow-ups
   carry their own)

## How It Closes

(not yet stated by the migration -- a session filling this in should read ## What and say what has to be true for `status` to become `done`.)

## Notes

2026-09-16: migrated from TODO.md by tools/todo_migrate.py.
