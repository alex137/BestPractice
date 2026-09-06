# How to Use This — Technical Guide

*The question this document answers:* **I'm technical — how do I actually
work inside a Precedent project day to day, step by step?**

For installing Precedent on a project in the first place, see
[INSTALL.md](../INSTALL.md). This document is about using it once it's
there.

## All interaction happens through chat or voice with an assistant

You don't edit the project's files directly, and running the practice
tooling by hand isn't the normal way of working here. Connect the
repository to a large language model (LLM) assistant of your choice —
Claude Code is the best-supported (*as of 2026-09*); other assistants have
supported paths, see [MOBILE.md](../MOBILE.md) — and talk to it about the
work. The
assistant reads and writes the repository, runs the checks, and drafts
changes for review. Every session starts by reading the repo's own
instructions file (`AGENTS.md`), so it already knows which practices are
in force before you say anything.

*This repo expects no files to be touched directly — all interaction
happens mediated by the AI assistant the repo is attached to. The code
and technical descriptions below exist only to clarify how it works.*

## Four levels, each just another repo

Before explaining how practices are created, it's useful to understand the
different levels a practice can live at — every stage below names one.

A practice lives at one of four levels, in precedence order (highest wins
on conflict): **team > repo-local > individual > universal**.

- **Universal** — the shared, public Precedent library everyone starts
  from.
- **Team** — a private repository of practices for one team. You can have
  more than one (an engineering-conventions team repo and a separate
  editorial-conventions team repo, say).
- **Individual** — a private, personal set of practices, declared in your
  own user-level configuration, never in a shared project's tracked
  files. You can keep more than one if you work across separate contexts.
- **Repo-local** — practices that live inside the project repository
  itself, at a `practices/` directory named `local`, for rules specific to
  that one project only.

Every level except repo-local is a genuinely separate git repository,
resolved live into the project rather than copied in — a team or
individual source is a sibling checkout your session needs read access
to, not a folder inside the shared project. A project declares which
sources apply to it in a `precedent.json` at its root:

```json
{
  "sources": [
    {"level": "universal", "name": "precedent", "path": "process/upstream"},
    {"level": "team", "name": "<your team repo>", "path": "../<your team repo>"}
  ]
}
```

No new team or individual source? `precedent_bootstrap_source.py`
instantiates a real starter set from a skeleton in one command:
```
python3 tools/precedent_bootstrap_source.py --level team \
    --name <name> --dest <local clone path> --approver "Your Name:your-github-handle"
```
(`--level individual` for a personal set — no `--approver` needed there;
add `--write-session-hook <project path> --repo-url <URL>` to wire it into
a hosted session automatically.)

### Moving a practice between levels

A practice that already exists and is still wanted, just at the wrong
level (a team habit that turns out to be one person's, or a personal habit
the whole team adopted) moves in two deliberate steps — never a silent
edit or a copy-and-delete (see [spec/MOVING_PRACTICES.md](../spec/MOVING_PRACTICES.md)):

1. **Land it at the new home**, through that level's own approval —
   exactly the four-stage walkthrough below, using the existing practice's
   Rule/Detail/Why/Story as the candidate's content rather than
   re-deriving it from scratch.
2. **Retire it at the old home**, through *that* level's own removal
   approval: set the old file's `status: retired` and add one line to its
   `## Story` naming where it went. Order matters in this direction only —
   land first, so there's never a gap where nobody is bound by a rule
   everyone still wants.

## Walkthrough: turning a habit into a practice

This is the pipeline underneath "your assistant notices and proposes a
rule." Four stages, in order, and the commands your assistant actually
runs at each one:

1. **Raise it as a candidate.** Say "from now on, always X" (or the
   assistant notices a repeated correction). It runs
   `precedent_candidate.py create` at the level the idea belongs to:
   ```
   python3 tools/precedent_candidate.py create \
       --level individual --path <your individual repo> \
       --slug always-date-external-quotes --title "Date every quoted external fact" \
       --signal explicit-instruction --raised-by "<you>" \
       --observed "You corrected a stale API-pricing figure twice this week." \
       --proposed-rule "Any quoted external fact carries the date it was checked."
   ```
   This writes one dated file to `candidates/*.md` — nothing is loaded
   into context, filed as a practice, or shown to anyone else yet. For a
   **team** candidate, the same command with `--level team --path <team
   repo>`; pass `--as-issue true` instead of writing a file when whoever's
   raising it isn't a listed approver (see "How practices are approved,"
   below) — that drafts a GitHub Issue body instead, since a quiet file
   nobody's watching doesn't get anyone's actual yes. A **universal**
   candidate skips `--path` entirely — `--level universal` drafts a GitHub
   Issue body for `alex137/BestPractice`, labeled `precedent-candidate`,
   since nothing world-readable is ever committed to a `candidates/`
   directory here (see [spec/SOURCES.md](../spec/SOURCES.md)).
2. **Promote it.** `precedent_promote.py` runs the candidate against four
   criteria — recurrence or real cost, reachability (a check, a narrow
   `applies_to`, or an occasion), non-duplication, and resident-budget fit
   — and drafts a practice file only if all four pass:
   ```
   python3 tools/precedent_promote.py --file candidates/always-date-...-2026-09-10.md \
       --level individual
   ```
   A failure here names exactly which criterion it failed, so there's
   nothing to guess at.
3. **Get the approval the level requires** — see the next section. This is
   the one human step nothing here skips.
4. **Land it.** `precedent_land.py` re-runs the same four criteria (it
   never trusts a prior promotion), then writes the file and regenerates
   the repo's generated views:
   ```
   python3 tools/precedent_land.py --file <the drafted candidate> \
       --level individual --path <your individual repo> --approved-by "<you>"
   ```
   For team, add `--level team --path <team repo>` with `--approved-by`
   naming a listed approver. For universal, `precedent_land.py` only
   *drafts* `practices/<slug>.md` — landing it for real means committing
   that draft to a branch and opening a pull request (PR) against
   Precedent, reviewed and merged by someone else.

## How practices are approved

Getting a practice to take effect always comes down to one question: *who
has to say yes?*

- **Yours alone (individual level):** you're the only approver. Agreeing
  to it in conversation is the `--approved-by` step above — it lands
  immediately.
- **Your team's:** a listed approver (an entry in that team repo's
  `approvers.json`, matched by name or GitHub handle) has to agree. If
  you're one of them, your yes in conversation *is* the approval, landed
  the same way. If not, `precedent_candidate.py create --as-issue true`
  drafts a GitHub Issue for an actual approver to act on later —
  proposing a candidate is a slower path here on purpose, not a shortcut
  around needing someone else's agreement.
- **Everyone's (universal):** goes up as a PR against the shared
  Precedent repository, reviewed and merged by someone other than
  whoever proposed it. No single person, including whoever maintains the
  library, can land a universal practice alone.

## How enforcement works

Some practices are Rules an assistant is expected to read and follow —
loaded into context when the work at hand matches the practice's stated
occasion. Nothing structurally stops an assistant from missing one; this
channel is advisory. A few concrete commands for working with it day to
day:

- **What applies to a file I'm about to touch?**
  `python3 tools/precedent_paths.py <file>` matches it against every
  practice's `applies_to` glob and prints the ones that fire — no need to
  hold the whole occasion index in your head.
- **What does a specific practice actually say?**
  `python3 tools/precedent_show.py <slug>` prints its Rule (and, with
  `--detail`, `--why`, or `--story`, the rest).
- **What fires at a named moment** (merging, reviewing, pushing, ending a
  reply) rather than on a file path: `python3 tools/precedent_gate.py
  merge|review|push|reply`.

Where a rule can be turned into a mechanical check, it is: the practice's
file names a script that runs against the repository (or the current
change) and fails loudly when the rule is broken. The check's failure
message *is* the rule at that point, rather than a paraphrase of it.

- `python3 tools/precedent_check.py --list` — which practices are enforced
  this way in a given repository.
- `python3 tools/precedent_check.py --explain` — for each one, exactly
  what its check tests **and what it's blind to**. An enforced practice
  guards against what its check actually asserts, not automatically
  against everything the written rule describes.
- `python3 tools/precedent_check.py --only <slug>` — run just one check;
  `--paths <file,file>` or `--range <A..B>` to scope a run to specific
  files or commits instead of the whole tree.

Landing a *new* enforced practice carries a hard rule, not a suggestion:
`precedent_land.py` refuses a `checked_by` claim with no registered,
tested check behind it — a slug has to already be a key in
`precedent_check.py`'s registry (universal) or have both a
`tools/checks/check_<name>.py` and a passing
`tools/checks/tests/test_<name>.sh` (team/individual) before it can land.

### Retiring a practice nobody uses

`python3 tools/precedent_retire.py --against <path>` is the periodic
retirement report: anything never cited, never routed to, or whose check
never trips gets listed as a candidate for retirement. It only *proposes*
— removing a practice still goes through that level's own approval, same
as landing one.

## Where to go next

[INSTALL.md](../INSTALL.md) for wiring this into a project.
[PRACTICE_ENGINE_PLAN.md](../PRACTICE_ENGINE_PLAN.md) for the full design
and reasoning behind all of the above. [spec/CANDIDATE_FORMAT.md](../spec/CANDIDATE_FORMAT.md)
for the candidate file's exact shape and signal vocabulary.
