---
slug:              todo-2026-10-08-less-reliant-on-github
kind:              decision
domain:            mechanism
severity:          null
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        Alex's or Morgan's approval of the plan below, stage by stage
noted:             2026-10-08
closed:            null
---
## What

Make BestPractice, and the repositories that use it, keep working when
parts of GitHub are down, and able to move to another git host without a
rewrite. Not a goal: a second, local BestPractice to work from. Alex,
2026-10-08: "We just want to have the option of moving BestPractice if we
become unhappy with GitHub and to be less reliant on GitHub uptime because
often parts of GitHub are down."

**The principle that already holds.** Every consuming repository carries
its own copy of BestPractice's engine and catalogue. When GitHub's git
service itself is down, a consumer keeps working from that copy, and what
changed upstream reaches it at the next Update Vendors once GitHub is back
(Alex, 2026-10-08: "if github git service itself is down we can use the
vendor version knowing it will propagate when GitHub gets back online").
The gap is in the tools around it: an update, a freshness check or a
landing that cannot reach GitHub must say "could not reach it; working
from the vendored copy" and carry on, never fail the work.

**What depends on GitHub today** (surveyed 2026-10-08):

- the full check after a merge into main runs as GitHub Actions
  ([.github/workflows/deep-check.yml](../.github/workflows/deep-check.yml));
- unattended jobs report a blocker by opening a GitHub issue
  ([automation-issues](../practices/automation-issues.md)), which needs `gh`
  signed in -- in cloud sessions it usually is not, and the report is lost;
- the promotion into main opens a pull request and waits on GitHub's check;
- six tools call the GitHub API for advisory answers: whether CI ran
  ([precedent_ci_verified.py](../tools/precedent_ci_verified.py)), branch protection
  ([precedent_boundary_check.py](../tools/precedent_boundary_check.py)), repository renames
  ([precedent_source_names.py](../tools/precedent_source_names.py)), the API allowance ([github_budget.py](../tools/github_budget.py)),
  [very_deep_check.py](../tools/very_deep_check.py) and the harness;
- about 560 links in practice files are absolute GitHub file URLs.

Everything else -- Update Vendors, the push check, the engine copy, the
check-ins -- already runs on plain git against any remote.

## Proposed

In order of how often each piece hurts during an outage:

1. **Degrade, never fail, when GitHub is unreachable.** Update Vendors, the
   freshness check and the vendor step of a landing report that the source
   could not be reached and finish on the vendored copy. Small; mostly
   wording and exit codes.
2. **Checks after a merge run on our side.** The full check of what landed
   runs locally in the background after the push (built in a consuming
   repository on 2026-10-08 as `land_next.py --check-after`), so GitHub
   Actions becomes one more place a failure can show up, not the only one.
3. **Failures are filed in the repository.** A failure no one is watching is
   written as a blocker item under `todo/` and pushed, and listed at session
   start (built in the same consuming repository on 2026-10-08 as the
   practice `failures-go-in-todo`); an issue is opened as well where `gh`
   works. This becomes the fallback `automation-issues` names.
4. **Main can be landed by a plain push.** The promotion into main (and the
   direct route) can merge and push with git when the pull-request service
   is down, its check then running per 2.
5. **A second git host.** One push mirror (GitLab, Codeberg, or a plain git
   server) that receives every push, and tools that fetch from it when
   GitHub does not answer. The only piece that adds something new to run.
6. **One setting names the host.** `precedent.json` names where the sources
   live; links in practice files and tool messages are built from it (the
   existing `PRECEDENT_SOURCE_BASE_URL` is the start of this), and the six
   GitHub-only tools skip quietly elsewhere. With this, moving off GitHub is
   a change of addresses.

Stages 2 and 3 exist in a consuming repository and mostly need moving here
behind the host setting. Stage 4 changes how main is protected here, which
was Morgan's design (the three branch tiers), so it is his call as much as
Alex's.

## How It Closes

Each stage is approved and built, or dropped with the decider's reason;
the item closes when every stage has one or the other.
