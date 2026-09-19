# How to Use This — Technical Guide

*The question this document answers:* **I'm technical — how do I actually
work inside a Precedent project day to day, step by step?**

The install itself is summarized below, in **Installing It on a
Project**; [INSTALL.md](../INSTALL.md) is the full reference each step
links into. Everything after that section is about using Precedent once
it's there.

## Installing It on a Project

The model in one paragraph: the project **vendors** Precedent as plain
tracked files — the practice catalogue and the engine that reads it — and
declares in a `precedent.json` which practice sources bind it; a generated
block in `AGENTS.md` then puts the handful of practices that matter in
front of every session, and the ones that can be checked mechanically are
checked on every run. **Install is adaptive**: you instantiate templates
with the project's own subject matter, at their real locations. Nothing is
fetched while you work.

Two paths, and since 2026-09-14 the default is the first:

- **[INSTALL.md §0](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using)**
  — straight onto Precedent's three-source loader: the practice catalogue
  vendored at `precedent/universal/`, the engine at `tools/`, and
  `AGENTS.md`'s generated block (resident practices, occasion index,
  enforced checks). **One command does it**, from a sibling clone of
  Precedent:

  ```
  python3 tools/precedent_install.py <project path> --project-name "<name>"
  ```

  It prints the placeholders it left for you to adapt and stops before
  committing. What it does step by step is §0's numbered list.
- **[INSTALL.md §1](../INSTALL.md#1-install-into-a-dependent-repo)** — the
  older vendored model: the whole upstream tree at `process/upstream/`, a
  **manifest** recording the mapping both ways, and a check-in loop in
  which an improvement made here is folded back upstream in generic form.
  It installs the practice *prose* and none of the loader; take it only if
  the project specifically wants the export-and-check-in loop. A project
  that *already* vendored BestPractice this way and wants the loader takes
  [spec/MIGRATING_EXISTING_INSTALLS.md](../spec/MIGRATING_EXISTING_INSTALLS.md).

The §1 sequence, in short, for a project that takes that path — each step
is spelled out in full at the link:

1. **Vendor** this repo's working tree (not its `.git`) into
   `process/upstream/`, as ordinary tracked files, and record the upstream
   commit you copied from. Skip `evals/` — Precedent's own measurement
   fixtures, which nothing a consumer runs reads.
2. **Instantiate the templates**, rewritten with the project's real
   subject matter rather than copied verbatim: `AGENTS.md`, `MAP.md`,
   `TODO.md`, `GLOSSARY.md`, `GETTING_STARTED.md`, the PR template, the
   `.gitignore` baseline, and the harness adapter(s) from
   [templates/harness/](../templates/harness/) for whichever assistant
   will work the repo. `local/practices/project-voice.md` (a repo-local
   practice, not a plain document) and `STYLEGUIDE.md` are the exception:
   both ship near-empty and **stay that way** — see "Optional, and
   deliberately left for later" below.
3. **Ask the two questions only a person can answer** — which private
   names and code words must never reach a public file (this becomes the
   leak blocklist), and whether the team or the person already has a
   practices repo to wire in.
4. **Write the manifest** ([INSTALL.md §5](../INSTALL.md#5-the-manifest-schema-processmanifestjson))
   and **run the audit** ([§6](../INSTALL.md#6-the-audit-toolspractice_auditpy)).
5. **Commit on a branch and open a pull request.** Nothing is official
   until it's reviewed and merged.

Afterwards: **[§2](../INSTALL.md#2-take-an-upstream-update)** takes an
upstream update (the `Update Vendors` command), **[§3](../INSTALL.md#3-optional-give-back-an-improvement--the-export-gate)**
and **[§4](../INSTALL.md#4-optional-periodic-check-in--propose-your-improvements-upstream)**
flow an improvement back upstream, **[§7](../INSTALL.md#7-practice-packs-domain-layers)**
covers domain practice packs, and
**[PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md)**
is what each person sets on each machine — including the credential that
lets a hosted session reach a private practice source without an
`add_repo` dance.

### Optional, and Deliberately Left for Later

**An install does the essentials and stops**
([INSTALL.md](../INSTALL.md#essentials-only--what-an-install-upgrade-or-migration-leaves-for-later)).
Two files ship near-empty on purpose and are not filled in by an install,
an upgrade or a migration:

- **`local/practices/project-voice.md`** — how this project sounds: its
  voice, its audiences, its domain vocabulary, and any deliberate departure
  from a catalogue rule. A repo-local practice, not a plain document —
  reached through the same occasion index as every other rule in force
  here. General writing quality is not in it; the practice catalogue
  covers that for every project at once.
- **`STYLEGUIDE.md`** — the visual identity, transcribed as plain text from
  whatever brand guideline exists. Never attach, vendor or link the source
  document into the repo.

Both stay local to the project and are never exported upstream. **Fill
either in whenever you want by asking your assistant** — *"help me fill in
my project's voice"* — and a section left `<undecided>` is a real answer, not a gap.
The same goes for anything else that would refine a working project rather
than make it work: it is a later conversation by design, not an oversight.

### What Actually Bites

The five-step summary above is honest about the *shape* of an install and
misleading about its *difficulty*. These are the places real installs have
gone wrong; each one fails quietly, which is why they are worth naming
here rather than leaving to be discovered at the link.

- **The harness hooks are not four judgment calls.** A real install
  (2026-09-07) treated them as four and declined all four; three of those
  calls were right and one was wrong.
  [INSTALL.md §1 step 2](../INSTALL.md#1-install-into-a-dependent-repo)
  carries a table saying which is which. `commit-identity.sh` in
  particular names nobody and pins nothing — **declining it is what leaves
  one person's name on another person's commits.**
- **The vendored engine has a seed step and a refresh step, and `refresh`
  cannot bootstrap itself.** With no `tools/ENGINE_MANIFEST.json`, all
  three verbs exit 2 with "No such file or directory" — which reads like a
  broken instruction and is a missing baseline.
  [§2 step 6](../INSTALL.md#2-take-an-upstream-update) has the seed
  command and the rename trap that forces a manual reseed.
- **`output_paths` in `precedent.json` is usually the key you want**, and
  omitting it is not neutral: `title_case.py` falls back to reasoning from
  *Precedent's* directory names, so your whole tree reads as published and
  `headline-capitalization` reports headings you never meant to rewrite.
  [§0 step 2](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using).
- **The timezone in `identity.json` is the field that fails silently.**
  Name and email resolve from the GitHub account the session is
  authenticated as, so a half-filled identity looks fine; nothing anywhere
  can resolve a zone, so the author-date check drops from enforced to
  guessed and wrong-offset commits reach the remote.
  [PER_MACHINE_SETUP.md](PER_MACHINE_SETUP.md).
- **A repo attached mid-session runs none of its own hooks**, so every
  guarantee the install wired up is absent while you work in it — and the
  failure looks like a broken tool rather than an unrun hook. The
  project's own `AGENTS.md` gotchas section is the list.

**A word you don't recognize** — *practice*, *source*, *resident set*,
*capture gate*, *deep check* — is probably in
[GLOSSARY.md](../GLOSSARY.md), which is generated from the `defines:` field
of whichever practice owns the term, so each entry links to the rule that
defines it.

**Not technical, or handing this to someone who isn't?**
[SETUP.md](../SETUP.md) runs the same install as a conversation: the
administrator pastes it to their assistant and answers three questions.

## All Interaction Happens Through Chat or Voice With an Assistant

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

## Four Levels, Each Just Another Repo

Before explaining how practices are created, it's useful to understand the
different levels a practice can live at — every stage below names one.

A practice lives at one of four levels, in precedence order (highest wins
on conflict): **team > repo-local > individual > universal**. The team
sits above the individual on purpose: your preference for a casual tone is
about how you work, your team's rule that anything sent to a client is
formal is about what you all ship, and the second has to win. A practice
marked `severity: blocking` cannot be overridden from above at all, and
every override is reported rather than applied silently.

- **Universal** — the shared, public Precedent library everyone starts
  from.
- **Team** — a private repository of practices for one team. You can have
  more than one (an engineering-conventions team repo and a separate
  editorial-conventions team repo, say).
- **Individual** — a private, personal set of practices, declared in your
  own user-level configuration, never in a shared project's tracked
  files. One per person, however many teams you are on: your own facts
  (name, timezone, pronouns, how technical your replies should be) and
  your own habits, which follow you into every project.
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

### Moving a Practice Between Levels

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

## Walkthrough: Turning a Habit Into a Practice

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
   Precedent, merged once its own deep check passes — no second sign-off
   required, same as any other PR into `precedent-beta-v01`.

## Who May Change What

Three roles, and each is a list in a file rather than a label on a person
— nothing anywhere records whether somebody is "technical"
([technical-describes-people](../practices/technical-describes-people.md)):

- **Collaborator** — anyone invited to the project repository with GitHub's
  Write role. They write, change and merge the project's content, through
  their assistant, with `Go merge`.
- **Maintainer** — named under `maintainers` in the project's
  `precedent.json`. Their review is required before a change to the
  machinery lands: `.github/`, `.claude/`, `tools/`, the vendored catalogue,
  `precedent.json`, `AGENTS.md`. Which paths count is the `owned_paths` list
  beside it, each with its reason.
- **Approver** — named in a practice set's `approvers.json`. Only an
  approver lands a practice at that level; everyone else, developer or not,
  suggests one (next section).

What makes the maintainer line real is one generated file and one GitHub
setting. `python3 tools/build_codeowners.py` writes `.github/CODEOWNERS`
from the registry (never hand-edit it; `--check` says whether it is
current), and branch protection on the base branch — require a pull
request, required approvals 0, require review from code owners, no bypass —
is what makes GitHub enforce the file (a paid GitHub plan on a private
personal-account repository; see [GITHUB_SETTINGS.md](GITHUB_SETTINGS.md)'s
"Plan limits"). A documents-only pull request is then
its author's to merge; one touching an owned path waits for the maintainer.
Two tools keep it honest: `python3 tools/precedent_boundary_check.py` asks
GitHub whether the protection is actually on (`PASS`, `FAIL` naming the
setting, or `UNVERIFIED` when it could not ask — never a pass by silence),
and `python3 tools/precedent_owned_paths.py` says before a pull request
which changed files will wait for review, in words a contributor can act on.
Keep workflows secret-free: `CODEOWNERS` gates the merge of an edited
workflow, not its first run on a collaborator's branch.

Every GitHub setting in this section, and what GitHub itself does with a
CODEOWNERS file, is [GITHUB_SETTINGS.md](GITHUB_SETTINGS.md). The install
step is [INSTALL.md §0 step 10](../INSTALL.md#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using);
the design, and the three GitHub behaviours it still rests on unverified,
is [spec/CONTRIBUTOR_ACCESS.md](../spec/CONTRIBUTOR_ACCESS.md);
[templates/document-project/](../templates/document-project/) is the
ready-made shape for a project where most collaborators only ever touch
documents.

## How Practices Are Approved

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
  Precedent repository, merged once its own deep check passes — the same
  branch-level gate as any other PR into `precedent-beta-v01`, not a
  second reviewer's sign-off.

## How Enforcement Works

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

### Retiring a Practice Nobody Uses

`python3 tools/precedent_retire.py --against <path>` is the periodic
retirement report: anything never cited, never routed to, or whose check
never trips gets listed as a candidate for retirement. It only *proposes*
— removing a practice still goes through that level's own approval, same
as landing one.

## Where to Go Next

[TEN_THINGS.md](TEN_THINGS.md) is the one-page map of the ideas above,
each linked to its section here and in the plain-language guide.
[DAILY_HABITS.md](DAILY_HABITS.md) for the
working habits and the standing command vocabulary — short, and worth
reading even if everything above was obvious.
[INSTALL.md](../INSTALL.md) for wiring this into a project.
[PRACTICE_ENGINE_PLAN.md](../spec/PRACTICE_ENGINE_PLAN.md) for the full design
and reasoning behind all of the above. [spec/CANDIDATE_FORMAT.md](../spec/CANDIDATE_FORMAT.md)
for the candidate file's exact shape and signal vocabulary.
