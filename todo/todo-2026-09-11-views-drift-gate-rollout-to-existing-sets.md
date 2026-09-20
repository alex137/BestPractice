---
slug:              todo-2026-09-11-views-drift-gate-rollout-to-existing-sets
kind:              analysis
domain:            mechanism
severity:          null
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-11
closed:            2026-09-11
---
## What

- <a id="views-drift-gate-rollout-to-existing-sets"></a>**Install the views
   drift gate in the four existing private sets.**
   `templates/github-actions/views-drift.yml.template` (since removed; folded into `precedent-check.yml.template`)
   reaches a new set through
   [tools/precedent_bootstrap_source.py](../tools/precedent_bootstrap_source.py),
   and reaches an existing one through nothing: `precedent-individual`,
   `precedent-team-repo-maintenance`, `precedent-team-writing` and
   `precedent-team-working-style` all generate views and all carry no gate.
   The work in each is one file copied to `.github/workflows/views-drift.yml`
   plus one pull request; `python3 tools/precedent_bootstrap_source.py
   --verify <path>` names it as missing until it is there.

   Each set also needs its vendored engine refreshed
   (`python3 tools/precedent_vendor_engine.py refresh <bestpractice-clone>`)
   before the gate means anything, since a stale `build_views.py` regenerates
   the old header and the check would report drift on the header itself.

   **A second reason to refresh, added 2026-09-11
   ([cross-source-rollout](../practices/cross-source-rollout.md)):**
   [generated-edit-goes-upstream](../practices/generated-edit-goes-upstream.md)
   landed, and `build_views.py` now writes a `Source:` clause into every
   generated header — the clause that says where a change belongs instead of
   in the file. All four sets generate their own `MAP.md`, `GLOSSARY.md` and
   loader block from a vendored engine that predates it, so until each is
   refreshed their headers still say only how an edit gets destroyed. The
   universal check
   (`python3 tools/precedent_check.py --only generated-edit-goes-upstream`)
   travels with the engine and will fail in each set on the refresh commit
   until that set regenerates its views, which is the same one-command fix.

   **Closed 2026-09-11 — landed in all four.** Verified from this session by
   reading each set's own `origin/main`, not by being told:
   `.github/workflows/views-drift.yml` is present in `precedent-individual`
   (its PR #76), `precedent-team-repo-maintenance` (#38),
   `precedent-team-writing` (#7) and `precedent-team-working-style` (#10),
   each alongside a vendored-engine refresh, so the gate runs against a
   `build_views.py` that writes the corrected header rather than the old one.
   The work was done by a session rooted in those repositories, which is what
   this item was blocked on: a session rooted here can read those clones with
   `PRECEDENT_GIT_TOKEN` but cannot push to them — measured again 2026-09-11,
   `add_repo` with `access: "push"` refuses cross-owner and a direct
   `git push --dry-run` returns 403 from the git proxy.

   **What it also cleared:** the harness check comparing every reachable copy
   of `commit-identity.sh`. Those copies were never the problem — each set's
   committed copy was already canonical, and the drift was in one container's
   stale clones. The durable half of that is
   [tools/precedent_source_bootstrap.py](../tools/precedent_source_bootstrap.py)
   fast-forwarding an attached team clone at session start instead of
   reporting it `already on disk`.

   **Disposition:** wait ([open-item-disposition](../practices/open-item-disposition.md)).

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
