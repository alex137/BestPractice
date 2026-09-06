# How to Use This — Technical Guide

*The question this document answers:* **I'm technical — how do I actually
work inside a BestPractice/Precedent project day to day?**

For installing BestPractice on a project in the first place, see
[INSTALL.md](../INSTALL.md). This document is about using it once it's
there.

## All interaction happens through chat with an assistant

You don't edit the project's files directly, and running the practice
tooling by hand isn't the normal way of working here. Connect the
repository to a large language model (LLM) assistant of your choice —
Claude Code is the best-supported today; other assistants have supported
paths, see [MOBILE.md](../MOBILE.md) — and talk to it about the work. The
assistant reads and writes the repository, runs the checks, and drafts
changes for review. Every session starts by reading the repo's own
instructions file (`AGENTS.md`), so it already knows which practices are
in force before you say anything.

## How practices are approved

A practice is a written rule, plus the reasoning and the incident that
produced it. Getting a new one to take effect always comes down to one
question: *who has to say yes?*

- **Yours alone (individual level):** you're the only approver. Agreeing
  to it in conversation lands it immediately.
- **Your team's:** a listed approver (`approvers.json` in that team's own
  repository) has to agree. If you're one of them, your yes in the
  conversation *is* the approval and it lands right away. If not, it
  becomes a candidate — a file, or a GitHub Issue when nobody with
  landing authority is watching the file — for an approver to act on
  later.
- **Everyone's (universal):** goes up as a pull request against the
  shared BestPractice repository, reviewed and merged by someone other
  than whoever proposed it. No single person, including whoever
  maintains the library, can land a universal practice alone.

## Four levels, each just another repo

A practice lives at one of four levels, in precedence order (highest wins
on conflict): **team > repo-local > individual > universal**.

- **Universal** — the shared, public BestPractice library everyone starts
  from.
- **Team** — a private repository of practices for one team. You can have
  more than one (an engineering-conventions team repo and a separate
  editorial-conventions team repo, say).
- **Individual** — a private, personal set of practices, declared in your
  own user-level configuration, never in a shared project's tracked
  files. You can keep more than one if you work across separate contexts.
- **Repo-local** — practices that live inside the project repository
  itself, for rules specific to that one project only.

Every level except repo-local is a genuinely separate git repository,
resolved live into the project rather than copied in — a team or
individual source is a sibling checkout your session needs read access
to, not a folder inside the shared project.

A practice can move between levels later — a team habit that turns out to
be one person's preference, or a personal habit the whole team has since
adopted. Moving is always two deliberate steps: land it at the new home
through that level's own approval, then retire it at the old one — never
a silent edit or a copy-and-delete.

## How enforcement works

Some practices are Rules an assistant is expected to read and follow —
loaded into context when the work at hand matches the practice's stated
occasion. Nothing structurally stops an assistant from missing one; this
channel is advisory.

Where a rule can be turned into a mechanical check, it is: the practice's
file names a script that runs against the repository (or the current
change) and fails loudly when the rule is broken. The check's failure
message *is* the rule at that point, rather than a paraphrase of it. Run
`python3 tools/precedent_check.py --list` to see which practices are
enforced this way in a given repository, and `--explain` for exactly what
each check does and does not catch — an enforced practice guards against
what its check actually tests for, not automatically against everything
the written rule describes.

## Where to go next

[INSTALL.md](../INSTALL.md) for wiring this into a project.
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) for the full design
and reasoning behind all of the above.
