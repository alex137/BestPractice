---
slug:        very-deep-check
title:       The very deep check — a whole-repo coherence review, on request only
tier:        on-demand
severity:    advisory
applies_to:  ["**"]
occasion:    "a person explicitly asks for a \"very deep check\" across the whole repo, or after work that invites drift"
gates:       []
index_clause: "read the whole repo against itself for drift; never a routine gate"
checked_by:  null
defines:     ["very deep check"]
status:      active
supersedes:  []
overrides:   null
added:       null
approved_by: "pending review; revised 2026-09-05, Morgan F, to require every
  declared team/individual source actually be in the session before the check
  runs, and to add a stale-branch sweep across every repo the check touches;
  revised again same day, Morgan F, to add a cross-source-staleness check"
---
## Rule
When a person explicitly asks for a "very deep check", or after work that
invites drift (a batch of practices added or reordered, a practice that
changed shape, an install into a new repo, a merge that resolved conflicts
across several shared files), run
[tools/very_deep_check.py](tools/very_deep_check.py): it enumerates this
checkout's own top-level documents and deliverable content, plus the
`practices/*.md` tree of every source in force (resolved the same way
[tools/precedent_resolve.py](tools/precedent_resolve.py) does for ordinary
loading), and hands the invoking session a fixed checklist of drift
categories to read that scope against. Never wired into a commit, push, or
merge gate — the mechanical audits and `routing-audit` already cover what
can be checked cheaply and often; this covers what can only be judged, and
is deliberately rare because the judging is expensive.

**Before the tool runs, every declared team and individual source must
actually be present in this session, not merely resolvable in theory.** The
ordinary loader tolerates a missing personal source and says so on stderr —
that degradation is the right call for routine loading, where one operator's
absent individual set is expected and tolerable. It is the wrong call here:
a very deep check is explicitly asked for, and scoped to the whole set of
repos in force, so a source silently dropped defeats the reason it was
asked. `tools/very_deep_check.py` now fails loudly instead of degrading
when a declared team or individual source isn't actually there — this was a
real gap, not a hypothetical one: nothing before this revision made a
session go get the sibling clones a very deep check needs, so a session
that ran it in a fresh checkout with no siblings present quietly checked
this repo alone and called it done. On that failure, attach or clone the
missing source into the session (this harness's own repo-attachment
mechanism, or a plain `git clone` of the source's repo, whichever this
session has) and re-run — never re-run with `--allow-missing-sources` just
to make the failure go away; that flag is for the rare case where proceeding
without the source is actually the intent (e.g. auditing a repo that
deliberately has no team set yet).

**The check also sweeps every repo it touches for its own stale branches.**
For the checkout itself and for every team/individual source that is its own
git checkout (a repo-local source living inside the parent checkout shares
its parent's branches and isn't swept separately), `tools/very_deep_check.py`
reports every branch that is fully merged into that repo's integration
branch and still not deleted — a mechanical, offline fact (`git merge-base
--is-ancestor`), true regardless of whether GitHub's own "merged" flag is
set (a repo that lands each pull request (PR) by direct push rather than GitHub's merge button
never sets it, which is exactly the case in these repos). A branch the scan
cannot mechanically prove merged is still worth a look — it may be closed
because a later PR superseded it — but that call needs the branch's PR
history, which an offline git check has no access to; see Install for why
that half stays a session step rather than a second mechanical check. Either
way, apply the branch-cleanup method an individual practice set may already
give a session for its own commits (Morgan's own, as one example, names
this in [`next-steps-after-commit`](https://github.com/themorgan/precedent-individual/blob/main/practices/next-steps-after-commit.md)) —
identify by who opened or drove the PR (the invoking person's own GitHub
login, never a branch someone else created), skip the repo's default branch
and its protected integration branch, and report each remaining one with a
direct link to its most recent PR's page — the same one-click **Delete
branch** link GitHub already shows there. That kind of personal practice
may decline to do this retroactive, whole-repo sweep on its own ("a
separate, one-off task, done only when asked for directly") — a very deep
check is exactly that direct ask, so this is the one place the sweep
belongs as a standing step rather than a one-off.

## Detail
**This is not `full-practice-audit` under another name — the two ask
different questions.** `full-practice-audit` asks, practice by practice,
"is this specific practice's Rule satisfied?" — a closed question against
one Rule at a time. The very deep check asks a question no single
practice's Rule can be checked against: "does the repo's own writing still
hold together?" A contradiction between two documents, a stale
cross-reference, a rule restated in three places, a heading that drifted to
the wrong capitalization scheme — none of these is a violation of any one
practice's Rule text; each is a property of the documents *as a set*, which
is exactly what a per-practice sweep cannot see no matter how many times it
runs.

**What to look for — a starting point, not a specification. Report
anything that makes the repo harder to trust or follow, whether or not a
bullet below names it:**

- **Contradictions** — two rules, or two documents, that can't both be
  followed; a rule whose own carve-outs have eaten it.
- **Stale references** — a slug, practice number, filename, heading, or
  click-path pointing at something moved or gone; a positional number cited
  as if it were a name; numbering that skips, repeats, or runs out of order;
  an orphaned name a rename elsewhere left behind in this repo's own prose.
- **Fragments** — a sentence, note, or heading left behind by an earlier
  edit: a "temporary" caveat whose occasion has passed, a note about a
  reorganization that already happened.
- **Needless repetition** — the same rule stated in full in several places,
  where one statement plus pointers would do.
- **Disproportion** — paragraphs of detail on a minor point, prose that
  emphasizes an aside more than the point it supports, a rule grouped where
  it no longer fits.
- **Process-cost disproportion** — a rule that's minor in the scheme of
  things but costs a disproportionate amount of tokens, time, or friction
  each time it applies, especially one re-researched from scratch on every
  occurrence instead of following a written-down answer.
- **Formatting and spacing drift** — inconsistent heading levels and
  capitalization, a bullet missing the blank line its neighbors have, mixed
  list markers, a ragged table, stray blank lines or trailing whitespace, a
  stale "last updated" header.
- **Self-application** — a rule this repo asks of every project it's
  installed into that this repo doesn't yet follow itself.
- **Cross-source staleness** — a check, tool, or convention this repo
  changed that an attached team or individual source's own tooling,
  vendored engine copy, or written practice still assumes the old form of.
  Update the source in the same pass (per
  [cross-source-rollout](cross-source-rollout.md)) if it's attached; if a
  `blocked-on` TODO for it already exists, confirm it's still accurate
  rather than adding a second one.
- **Backlog drift** — a `TODO.md` (or equivalent open-items document) entry
  already done, no longer relevant, or never actually decided.
- **Anything else the read turns up** — if something is wrong and none of
  the categories above name it, it is still a finding; if it is the kind of
  thing that will recur, add a bullet here so the next very deep check looks
  for it deliberately.

Fix what the review turns up in the same pass — these are almost always
small — then re-run the mechanical audits, since the fixes themselves can
break a link. Anything deliberately left alone gets a line in `TODO.md`
saying so, rather than being silently dropped.

Two more things this check reports, distinct from the drift categories
above since neither is a property of the documents themselves:

- **Missing sources, fixed before reading anything.** If the team or
  individual source is declared but not present in this session, that is a
  blocking failure, not a finding to note and read around — go attach or
  clone it (see Rule) and only then start the coherence read.
- **Stale branches, one list per repo actually in scope.** Every branch the
  mechanical scan can prove merged into its repo's integration branch, plus
  any closed-and-superseded branch the session's own judgment turns up,
  named with a direct link to its most recent PR's page.

## Why
The mechanical audits (`doc_lint.py`, `leak_gate.py`, `precedent_check.py`,
`doc_sync.py`) catch broken links, bad syntax, and enforcement drift; the
routing audit catches a practice that should have fired and didn't. None of
them reads a document's own argument for whether it still makes sense —
that's a judgment call by design, not a gap any of them is meant to close,
which is exactly why this stays a separate, on-demand mechanism rather than
folded into one of the three.

**Read this before trusting the result, the same caution
`full-practice-audit` states for itself.**
[spec/ATTENTION_CEILING.md](spec/ATTENTION_CEILING.md)'s review-arm result
(54% recall on a whole-catalogue judgment pass, worse than no review at all)
was measured against practice-compliance judging, not document-coherence
reading — a different task, so that figure does not transfer here directly
— but nothing has evaluated this specific mechanism's own reliability
either. Treat it the same way: a backstop for what enforcement cannot
reach, not a substitute for enforcement, until it has its own evaluation.

## Story
Named in [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s v28 amendment
(2026-09-01) as "the inherited RepoPersonalPreferences (RPP) audit list ...
heavier than any of [light check, deep check, routing audit] ... not yet
inventoried here (RPP is a separate private repo); enumerate and wire it as
an on-demand tool when phase 5 or later actually needs it" — tracked nowhere
else, the same
structural gap [spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md)
found `routing-audit` fell into, and logged there as `TODO.md` item 17.

Enumerating it turned up something the v28 amendment's own author could not
have known: earlier that same day, the phase-3 private-set migration
(v27) had already carried this exact list into
[`precedent-team-maintainers`](https://github.com/themorgan/precedent-team-maintainers)
as its own `deep-check` practice, generalized (RPP's own vendored-tree
language dropped, since Precedent's private sets aren't vendored the way
RPP's `process/` tree was) but otherwise the same enumeration as here. So
the list was never actually missing — it just wasn't recognized as the
fulfillment of this commitment, and it existed only as prose in a private
team practice with no companion engine, one repo away from where a
Precedent user without access to that private team set could reach it. This
practice and its tool are the universal version: available to any repo
running Precedent, not only Morgan and Alex's. Whether
`precedent-team-maintainers`' own `deep-check` should now point at this one
via `overrides:`, or stay a separate team-level statement of the same rule,
is the team's own call — noted, not decided, here.

Revised 2026-09-05, on Morgan's direct request, adding the two gaps above.
Both were real, reproduced, not hypothetical: this repo's own team source
(`../precedent-team-maintainers`) is declared in
[precedent.json](precedent.json), yet nothing before this revision made a
session go get that sibling clone before running the check, so a session
starting in a fresh checkout with no siblings present would run the tool,
see the source reported "missing" on stderr, and call the result a very
deep check anyway. And a request in the same conversation to actually run
the newly-added sweep surfaced real, currently-undeleted stale branches
across every repo in force in that session — this repo, its team source,
and the session's own individual source — every one of them a branch whose
PR had closed (several merged by direct push, with GitHub's own `merged`
flag still `false` for that reason, confirming the Rule's note above is not
a hypothetical either) with nobody ever going back to delete it.

Revised again the same day, same conversation, to add the checklist's
cross-source-staleness bullet: a change to how this repo itself checks,
resolves, or merges is not finished at this repo's own commit if an
attached team or individual source's own tooling or written conventions
now assume the old form of it. The standing prevention side of that same
gap is [cross-source-rollout](cross-source-rollout.md), raised in the same
request — this bullet is its detection-side backstop, for whatever a
session's own rollout at merge time still misses.

## Install
[tools/very_deep_check.py](tools/very_deep_check.py) enumerates the scope
(this checkout's own top-level documents plus every active source's
`practices/*.md` tree, reusing `tools/precedent_resolve.py`'s own source
resolution) and prints the checklist above for the invoking session to
apply. No mechanical `checked_by` exists for this practice's own Rule, and
can't: what it asks for is a session's judgment applied to a scope the tool
enumerates, the same class of resistant-to-automation practice
`full-practice-audit` and `mistakes-become-rules` already name. See
[full-practice-audit](full-practice-audit.md) for the narrower,
already-built sibling this one deliberately does not replace, and
[spec/UNBUILT_PLAN_ITEMS.md](spec/UNBUILT_PLAN_ITEMS.md) for the decision
record this practice's own build closes out.

The two additions above *are* mechanically checked, as far as a mechanical
check can reach (`checkable-gets-checked`): a missing declared team or
individual source is a hard, non-zero-exit failure by default (pass
`--allow-missing-sources` only when proceeding without it is actually
intended), and the merged half of the branch sweep is a real git check
(`merge-base --is-ancestor` against each repo's own `origin/HEAD`, or an
explicit `--target` for this checkout when its own integration branch isn't
its default one — this repo's own `precedent-beta-v01` being exactly that
case). What stays a session step, deliberately, is the other half: turning
a mechanically-merged branch into a *reported* one requires knowing which
PR it came from, who drove that PR, and that PR's URL — none of which an
offline `git` check can see, the same reason a person-level practice
covering the identical lookup for a session's own commits has no
`checked_by` of its own either. A closed-but-not-provably-
merged branch is the same story one layer further out: only the session,
reading that branch's own PR thread, can tell "superseded" from "abandoned,
still someone's open question" — the very thing this whole practice exists
to hand to a session's judgment rather than force into a script.
