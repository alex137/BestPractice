---
slug:              todo-2026-09-11-team-maintainers-is-a-roster-name
kind:              decision
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          "\"go ahead and rename the set too\" -- Morgan approved renaming precedent-team-repo-maintenance for its subject rather than its roster."
decision_strength: decided
waiting_on:        null
noted:             2026-09-11
closed:            2026-09-11
---
## What

- <a id="team-maintainers-is-a-roster-name"></a>**Rename `precedent-team-repo-maintenance` for its subject.** Raised 2026-09-11,
  reviewing what was left in that set after the subject split. Of its 21
  active practices, 19 were about one subject — running a repository that
  vendors a practice layer: install, the two sync workflows, the drift and
  freshness notices, the light and deep checks, branch setup, the backlog
  gate, how a rule is placed and scoped in the catalogue. **The set is
  already subject-scoped; what is stale is its name.** "Maintainers" names a
  group of people, which is exactly what
  [source-naming](../practices/source-naming.md) says goes stale the moment a
  third person joins, and that rule's own table records that no check can
  see it — `precedent-team-repo-maintenance` and `precedent-team-morgan-alex` are
  indistinguishable to a scanner. The other two of the 21 were retired
  outright on 2026-09-11 (`llm-neutral`, `match-parsed-id-not-prefix`);
  neither was about maintaining a repository and no subject set exists for
  engineering craft. `precedent-team-repo-maintenance` is the obvious
  candidate name.

  **Not done, deliberately, and this is a judgment call rather than a
  blocker.** A source's name is not a filename: it is the GitHub repository
  name, the sibling clone path every `precedent.json` names, and what the
  session-start hook clones from `PRECEDENT_SOURCE_BASE_URL`. Renaming it
  moves all three at once, in every consumer, and a consumer whose
  `precedent.json` still names the old path resolves *nothing* from the set
  rather than failing loudly. Two team sources claiming one slug is a hard
  refusal, so it has to be a move, not a copy.

  **DONE 2026-09-11**, the same day it was raised, on Morgan's instruction —
  *"go ahead and rename the set too"*, `strength: decided`. The set is
  `precedent-team-repo-maintenance`.

  The blocker this item named was taken the other way round rather than
  waited out: the subject-split patch in that set's
  `handoff/2026-09-09-BESTPRACTICE_SUBJECT_SPLIT.md` is still unapplied and
  still edits the same `sources` block, so the patch file was **deliberately
  left carrying the old name** — rewriting strings inside a patch is how you
  get one that applies cleanly and means something else — and its handoff
  note now says which single hunk will conflict and how to resolve it.

  **References were rewritten in the same change**, 182 of them across 61
  files in three repositories, with two deliberate exceptions: the patch
  above, and each set's **vendored engine** under `tools/`, which is
  BestPractice's text and travels on its own refresh. Places worth knowing
  about because nothing would have pointed at them:

  - **`precedent-individual`'s leak blocklist.** Its repo-reference
    allowlist had an `allow themorgan/precedent-team-maintainers` line, and
    that allowlist is default-refuse for the whole account. Missed, every
    reference to the new name in this public tree reads as an undeclared
    private repository and the gate goes red on the next push. The old name
    keeps a line of its own, because this item and that set's README record
    the lineage on purpose.
  - **`approvers.json`'s `team:` field**, which feeds the generated
    `CODEOWNERS` through a content hash — so `build_codeowners.py --check`
    failed until it was regenerated, in a file nobody would think to look at
    for a rename.
  - **`PRECEDENT_FRESHNESS_ALSO`** in the environment, which is not in any
    repository and so could not be changed from here. See the next item.

  **One consuming repo was missed, and it went unnoticed for three days.**
  A consuming repo's own `precedent.json` still declared
  `precedent-team-maintainers`, at `../precedent-team-maintainers`, until
  2026-09-14. "Three repositories" above counted the practice sets; the
  repo that CONSUMES them was not among them, and nothing in the rewrite
  pass would have pointed at it, because the rename was driven from the
  sets outward. The consequence is worse than a stale string: the
  session-start clone lands a set under its CURRENT name, so that sibling
  path resolved to nothing on disk and the repo silently ran without
  twenty-one team practices. Its own session-start freshness work does not
  catch it either — a source that fails to resolve is a NOTE, not a
  failure. **The general shape, worth a rule if it recurs: a rename is a
  fan-out to every repo that declares the thing, and the declaring repos
  are not discoverable from the renamed one.** `cross-source-rollout`
  covers rolling a change out to attached sources; nothing yet covers
  rolling one out to attached CONSUMERS.

  **What is NOT done, and cannot be done from a session:** the GitHub
  repository itself. No tool here renames a repository — the GitHub Model
  Context Protocol (MCP) surface has `create_repository` and nothing that patches one — and
  creating a new repository instead would have lost the set's issue and
  pull-request history and left the account holding two. So this landed on
  the understanding that Morgan renames it in Settings, which is what makes
  every reference above resolve. GitHub redirects the old URL afterwards, so
  the order is safe in one direction only: **rename first, then merge this**.

## How It Closes

Already closed 2026-09-11 -- see the item's own text above for what finished it.

## Notes

2026-09-19: this item was dropped by the 2026-09-16 todo/gotcha migration
(`9a08363b`) along with 53 others -- see
[`todo-2026-09-19-migration-dropped-54-items.md`](todo-2026-09-19-migration-dropped-54-items.md)
for the full catalogue and root cause. Recreated verbatim from
`git show 9a08363b^:TODO.md`, with its relative links repointed one level
up into `../` and its old-style `TODO.md`-anchor citations repointed to the
real `todo/` files they now resolve to.
