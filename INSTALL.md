# Installing Precedent — The Install Runbook

**This page is written for the assistant doing the install**, not for the
person approving it. It is the full reference: every file, every command,
every trap. A person reading it over the assistant's shoulder is welcome
to, but nothing here needs them.

**If you are a person, you almost certainly want one of these instead:**

| You are… | Read |
|---|---|
| not a programmer, and want this installed | [SETUP.md](SETUP.md) — paste it to an assistant and it runs the whole install as a conversation, asking you three questions |
| still deciding whether to adopt it | [documentation/WHY_PRECEDENT.md](documentation/WHY_PRECEDENT.md), then [documentation/ADOPTING.md](documentation/ADOPTING.md) |
| a developer who wants the short form plus how to work here | [documentation/FOR_DEVELOPERS.md](documentation/FOR_DEVELOPERS.md) |
| not a developer, and it is already installed | [documentation/FOR_EVERYONE_ELSE.md](documentation/FOR_EVERYONE_ELSE.md), then [documentation/DAILY_HABITS.md](documentation/DAILY_HABITS.md) |
| setting up your own machine rather than a repository | [PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md) |

**The model in one paragraph.** The dependent repo **vendors** this repo at
`process/upstream/` as plain tracked files. **Install is adaptive** — you
instantiate templates with the repo's subject matter, placing real files at
their real locations. **Export is abstractive** — when installed practice
improves, you fold the generic form back into `process/upstream/`. The
**manifest** records the mapping in both directions; the **audit** makes
drift and proprietary leakage loud instead of silent. **That is the classic
model, §1** — the right default for essentially every install today, and
where the sections below start. A repo with no prior BestPractice install
that wants the three-source loader directly, never going through
`process/upstream/`, uses §0 instead; it sits after §1 because it is the
rarer path.

## Essentials Only — What an Install, Upgrade or Migration Leaves for Later

**Read this before §0, §1 or §2, because it governs all three.** An
install, an upgrade and a migration do the essentials, correctly, and stop.
Everything that would merely make the result *better* is named once, in a
sentence, and left for a later conversation.

**The test, applied per step: would the project work correctly without this
today?** If yes, it is not install work. Say it exists, say it is optional,
say the administrator can have it done any time by asking an assistant —
then move on. Do not walk them through it, and do not ask a question whose
answer only refines something already working.

**Why, since the temptation is to be thorough:** the person is at their
least informed about Precedent on the day they install it, so a decision
put to them then is the worst version of that decision they will ever make.
It also lengthens the conversation that most needs to feel short, and every
extra question is a chance to lose them before the essentials land.

`local/practices/project-voice.md` and `STYLEGUIDE.md` are the standing
examples — both ship near-empty, both stay that way through install, upgrade
and migration alike. **The rule is not about those two files.** It is about every
refinement is deferred whether or not it appears on a list here.

**What is never deferred as "polish":** the private-word blocklist, the
commit identity, the team and individual source question, the audit passing,
and anything a mechanical check fails without. Those are not refinements —
the project is wrong without them, and an install that skips one has not
installed. **[spec/INSTALL_QUESTIONS.md](spec/INSTALL_QUESTIONS.md) is the
canonical list of every question this asks a person**, fresh install or
migration alike — edit that table, not the prose in this file or SETUP.md,
when a question is added, dropped or reworded.

For what each practice is and why, read [practices/](practices/) — indexed
by [MAP.md](MAP.md), one rule at a time with
`python3 tools/precedent_show.py SLUG`. ([PRACTICES.md](PRACTICES.md) is
the frozen pre-fork catalogue, kept for its prose; it is no longer the live
list.)


## 1. Install Into a Dependent Repo

> **Two install paths, and this is the older one.** A project that has
> never had BestPractice before can install straight onto Precedent's
> three-source model instead — that is
> [§0](#0-installing-directly-onto-the-precedent-loader-new-2026-09-03--read-the-caveat-before-using),
> which sits *below* this section rather than above it because it was
> added later and renumbering would have broken every link to §1-§7.
> Most projects still use §1; read §0's own caveat before choosing it.
> A repo that already vendored BestPractice the old way wants neither,
> but [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md).

1. **Vendor:** copy this repo's working tree (not its `.git`) into
   `process/upstream/` and commit it as ordinary tracked files. Record the
   upstream commit hash you copied from (used by updates, step 2).
   **Skip [evals/](evals/), [philosophy/](philosophy/), [spec/](spec/),
   [todo/](todo/), [decisions/](decisions/), [deck/](deck/), [record/](record/),
   AGENTS.md and CLAUDE.md.** The first seven fail the same test: they
   answer a question about *building* Precedent rather than using it, and
   nothing a consumer runs reads any of them. AGENTS.md/CLAUDE.md fail a
   different, sharper test: a harness auto-loads a file with that exact
   name as *live instructions* for wherever a session is working — and
   this repo's own copies carry a tail that is BestPractice talking about
   itself ("this repo is the shared upstream", "PRs are the norm here"),
   false when read as instructions for a consumer's own repo. A consumer's
   real root AGENTS.md already comes from
   [templates/AGENTS.md.template](templates/AGENTS.md.template), never
   from mirroring this file, so nothing generic is lost by skipping it.

   - [evals/](evals/) is Precedent's own routing-quality measurement corpus
     (the fixtures behind [spec/LOADER.md](spec/LOADER.md)'s recall and
     precision figures).
   - [philosophy/](philosophy/) is the argument *for* the ideas, and
     [binds nothing outside itself](local/practices/philosophy-is-not-repo-policy.md)
     even here.
   - [spec/](spec/), [todo/](todo/), [decisions/](decisions/) and
     [deck/](deck/) are the engine's own build plans, backlog, dated design
     decisions and pitch-deck tooling — contributor material, per
     [spec/DOCUMENT_LIFECYCLE.md](spec/DOCUMENT_LIFECYCLE.md)'s own
     audience table.
   - [record/](record/) holds the fuller, pre-migration text behind the
     current [gotchas/](gotchas/) split, cited from vendored practices by
     external GitHub link, never a local one.

   **`gotchas/` and `examples/` are checked against the same tests and kept
   in.** `gotchas/` is troubleshooting for *running* the vendored tooling,
   and a resident practice's own Rule says to `grep gotchas/` — a local
   operation that finds nothing not actually vendored. `examples/` shows an
   adopter how to build their own practice set, a use of Precedent, not a
   step in building it.

   **Which is not the same as "skip the reader-facing prose".**
   [documentation/](documentation/) vendors, in full and on purpose:
   [spec/DOCUMENT_LIFECYCLE.md](spec/DOCUMENT_LIFECYCLE.md)'s placement
   table sorts every directory by audience, and `documentation/`'s audience
   is *"someone using Precedent on their own project"* — exactly who a
   vendored tree is for. That table is the test to apply to any directory
   this list does not name. **And nothing here skips a practice** — every
   file under `practices/` still vendors.

   Run `python3 tools/checkin.py not-vendored` for the share against the
   tree in front of you rather than trusting a figure typed here, which
   goes stale the week it is written.
   [tools/checkin.py](tools/checkin.py) excludes the same directories from
   its drift comparison, so an install that skips them is not reported as
   having drifted, and an existing install that already carries a copy is
   not either — deleting that stale copy is a re-vendor, not something the
   tooling reaches in and does. **No link goes dead by skipping either
   one**: [tools/doc_lint.py](tools/doc_lint.py) skips the link check
   inside a mirrored tree outright, so the vendored README's references
   into `philosophy/` report nothing in a consumer.
2. **Instantiate the templates** (adaptive — rewrite with the repo's actual
   subject matter, don't copy verbatim):
   - `templates/AGENTS.md.template` → `AGENTS.md` at the repo root: the
     **harness-neutral** canonical instructions file. Fill the quick-index
     table with this repo's real lookups; adapt the merge runbook's file
     classes; keep the section structure.
   - `templates/MAP.md.template` → `MAP.md`; `templates/TODO.md.template` →
     `TODO.md`; `templates/GLOSSARY.md.template` → `GLOSSARY.md` (or a
     domain-appropriate name).
   - `templates/local-practices/project-voice.md.template` →
     `local/practices/project-voice.md` — **a repo-local practice, not a
     root document.** Declare the `"local"` source in `precedent.json` if
     this repo has not already (`{"level": "repo-local", "name": "local",
     "path": "local"}` — the name and path are both fixed by
     [source-naming](practices/source-naming.md), never chosen). This is
     what makes the file actually reachable: it is what puts this project's
     voice in front of every session through the same occasion index as
     every other rule in force here, rather than a document nobody is
     pointed at.
     `templates/STYLEGUIDE.md.template` → `STYLEGUIDE.md` at the repo root.
     **Copy the skeletons and stop.** Unlike the files above, these are not
     rewritten with the repo's subject matter, and **filling them in is out
     of scope for an install** — see [Essentials only](#essentials-only--what-an-install-upgrade-or-migration-leaves-for-later).
     Do not walk the administrator through project-voice.md's sections and
     do not ask whether a brand guideline exists; say once that both exist,
     are optional, and can be filled in any time by asking an assistant.
     Record both as `local-only` in the manifest (§5) — **neither is ever
     exported upstream** (§3–§4): a project's voice and brand are its own
     identity, not a generic practice. `local/practices/` is this repo's
     own tree exactly as `STYLEGUIDE.md` at the root is, so the check-in
     tooling structurally never touches either.
   - `templates/GETTING_STARTED.md` → `GETTING_STARTED.md` at the repo
     root: the member-facing onboarding page, one section per kind of AI
     user. (This template keeps a plain `.md` name on purpose — it
     doubles as the rendered sample linked from the README.) Replace the
     backticked `<placeholders>` with the project's real values, adapt
     the opening pitch to the project, and keep the per-assistant section
     structure so upstream onboarding improvements propagate on updates
     (§2). Refresh its dated assistant-capability notes from the upstream
     [MOBILE.md](MOBILE.md) when taking updates. Improvements a project
     makes to its own onboarding page are exported like any other
     practice improvement: fold the generic form back into this template
     in `process/upstream/` (§3), so better onboarding reaches every
     project.
   - `templates/README_AGENT_ENTRY.md.template` → insert near the top of
     the repo's root README: an agent-entry HTML comment (invisible on the
     rendered page, read by assistants opening the source) routing agents
     to `AGENTS.md`, plus one visible line pointing people to
     `GETTING_STARTED.md`. **The project comes first**
     ([lead-with-what-it-is](practices/lead-with-what-it-is.md)): if
     the repo already has a README describing the project, insert only
     this block near its top — don't rewrite the opening. If the repo has
     no README yet, write a short project-specific opening first — from
     the administrator's "what is this project about" answer (see
     [SETUP.md](SETUP.md) step 2) — so a reader learns what the project
     *is* before anything about how it's maintained. The entry block and
     the Getting Started line come after that opening, never before it.
   - `templates/pull_request_template.md.template` →
     `.github/pull_request_template.md`: copy verbatim (no adaptation
     needed) — same treatment as `AGENTS.md`, installed once and
     propagated to existing installs on update (§2). GitHub picks it up
     automatically for every PR opened against the repo.
   - `templates/bootstrap.sh` → `tools/bootstrap.sh` (add the repo's own
     setup needs).
   - `templates/gitignore.template` → `.gitignore` at the repo root (create
     it) or merge into an existing one (append, don't overwrite): baseline
     ignores for ordinary tool/interpreter caches — `__pycache__/` in
     particular, left behind by every run of the vendored Python audits in
     `tools/`. Add this repo's own generated-deliverable globs
     ([generated-artifact-provenance](practices/generated-artifact-provenance.md))
     to the same file rather than a second one.
   - **Apply the harness adapter(s)** for whichever agent(s) will work this
     repo — see [templates/harness/README.md](templates/harness/README.md).
     E.g. Claude Code: `harness/claude-code/CLAUDE.md` → repo root (a
     one-line import of `AGENTS.md`), `harness/claude-code/settings.json` →
     `.claude/settings.json`, `harness/claude-code/hooks/session-start.sh` →
     `.claude/hooks/session-start.sh`, `harness/claude-code/hooks/stop-git-check.sh`
     → `.claude/hooks/stop-git-check.sh`, and — since 2026-09-06 —
     `harness/claude-code/hooks/freshness-guard.sh` and
     `harness/claude-code/hooks/commit-identity.sh` → `.claude/hooks/`, which
     keep a session off a stale checkout and keep a commit's author a person
     rather than the container's own agent account — and, since 2026-09-13,
     `harness/claude-code/hooks/reply-gate.sh` → `.claude/hooks/`, which puts
     the reply gate's practices in front of the session at the START of a
     turn rather than after its reply is already written. **Replace the base-branch
     argument in all three `freshness-guard.sh` commands** (SessionStart,
     UserPromptSubmit and PreToolUse) with this repo's real base branch; it is passed explicitly because detecting it gets this repo
     itself wrong. Codex reads `AGENTS.md` natively.
     Multiple adapters can be installed side by side.

     **Which of these are decisions and which are not.** A real install
     (2026-09-07) treated all four hooks as four judgment calls and declined
     all four; three of those calls were right and one was wrong, so the list
     now says which is which rather than leaving a session to guess:

     | Hook | Wire it? |
     |---|---|
     | `session-start.sh` | **Always.** It is the install. |
     | `commit-identity.sh` | **Always, and it asks nobody anything.** See below. |
     | `freshness-guard.sh` | **Always**, unless this repo's own bootstrap already fetches and fast-forwards — then it is duplicated work, not a conflict. |
     | `stop-git-check.sh` | **Wired by default** — the adapter's settings.json carries it, and an install leaves it. It blocks ending a turn on uncommitted or unpushed work: good discipline for a repo you own, intrusive in one shared with someone who did not choose it, so the one thing to say to the administrator is that the `Stop` entry can be removed if the team objects. Not a question at install. |
     | `precedent-paths.sh` | **Only with the Precedent loader.** It surfaces path-triggered practice Rules; without a resolved catalogue it has nothing to read. |
     | `reply-gate.sh` | **Only with the Precedent loader**, same reason. One line per reply-gate practice, on every prompt; it never blocks (a `UserPromptSubmit` hook that exits non-zero eats the person's message). |

     **`commit-identity.sh` names no person, and that is the whole point.**
     The install that declined it did so because it looked like it would pin
     one person's name into a repository two people share — the opposite of
     what it does. It resolves *whoever is running the session*, in order: an
     explicit `PRECEDENT_COMMIT_*` override; an `identity.json` in this
     repository's own root; the person's own individual practice source; the
     harness's session-owner address; **the GitHub account the session is
     authenticated as**; and finally an already-configured local identity, as
     long as it is not the container's bot account. It then installs a
     `pre-commit` (and `prepare-commit-msg`) hook refusing a commit authored
     by that bot account. Declining it is what leaves one person's name on
     another person's commits — which is what happened.

     **One side effect worth knowing about.** `commit-identity.sh` also
     repoints the container's `/etc/localtime` to the resolved zone, so that
     every tool on the machine stamps the same offset (`PRECEDENT_LOCALTIME`
     names another file to repoint instead). On a shared or local machine
     that is a change to the machine, not to the repo — measured on
     2026-09-14 when a rehearsal moved a container from Buenos Aires to New
     York and could not move it back.

     **Timezone is the one thing guessed, deliberately.** Nothing in a GitHub
     profile says where a person is, and a container's own clock is UTC
     rather than anybody's local time — so a zone cannot be derived the way a
     name can. The `env` block's `TZ` is therefore a *stated default* for
     someone who has declared no zone anywhere, and **it is never enforced**:
     a commit whose offset does not match a guess earns a warning. Only a
     zone someone actually declared, in their individual set's
     `identity.json`, is enforced — because only then is a mismatch evidence
     of anything. Change the default to your own zone if you like; leaving it
     costs nothing.

     **A declared zone configures itself, from the second session on.** A
     hook cannot export `TZ` into the shells a session runs later, so for a
     while the enforcement above was a refusal plus a remedy line
     (`TZ="…" git commit …`) that had to be retyped on every single commit.
     Since 2026-09-07 `commit-identity.sh` instead **derives** the resolved
     zone into `.claude/settings.local.json`'s `env` block — the per-machine
     settings file, which the harness reads for the whole session. Nothing to
     configure: it happens at session start wherever an `identity.json`
     declares a zone, it is rewritten whenever the declaration changes
     ([registry-source-of-truth](practices/registry-source-of-truth.md) — the
     `identity.json` is the declaration, this file is a derived copy), and a
     *guessed* zone is never written, because propagating a guess would
     quietly enforce something nobody said.

     Two consequences worth knowing. It applies **from the next session on**,
     because environment is read before hooks run — so the session that
     installs it still sees the refusal once. And
     `.claude/settings.local.json` must be gitignored: it is one
     contributor's environment, not the repository's, and committing it
     pushes that person's timezone onto everyone.
     [templates/gitignore.template](templates/gitignore.template) carries the
     line; the hook warns if your repo does not.
   - `tools/doc_lint.py` → run it from `process/upstream/tools/` in place,
     or copy to the repo's tools dir if it needs local adaptation.
   - `tools/doc_sync.py` ([computed-numbers-in-scripts](practices/computed-numbers-in-scripts.md))
     and `tools/model_audit.py`
     ([scripts-assert-properties](practices/scripts-assert-properties.md))
     → copy to the repo's tools dir and wire their registries
     (`PAIRS` and `INSTRUMENTED` respectively); both are gates meant to run
     with the repo's other pre-commit checks. Install `doc_sync` when
     documents quote computed numbers, and `model_audit` as soon as any
     script consumes a quantity another script or an authoritative document
     owns.
3. **Write the manifest** at `process/manifest.json` — see §5 for the
   schema. One entry per installed practice artifact, recording where it
   landed, at what granularity, and what was adapted. Then run
   `python3 process/upstream/tools/practice_audit.py --update-baseline`
   to record content hashes.
4. **Create `process/scrub_blocklist.txt`** — whether or not the repo is
   private (read that from the remote; it is not a question for the
   administrator, and the file is harmless on a public repo): — one regex per line (`#` comments), the
   repo's private vocabulary: project and product names, internal code
   words, identifier patterns, anything that must never appear in the
   public vendored tree. Err broad; false positives are a one-line review,
   false negatives are published.

5. **Add the export-gate section** to the instructions file (the template
   includes it): the copy-back rule, the scrub rule, and the periodic
   check-in item (add one to `TODO.md`).
6. **Root hygiene — the layout rule.** The ONLY files an install may
   create at the dependent repo's root are the instantiated ones:
   `AGENTS.md` (plus a harness pointer such as `CLAUDE.md`), `MAP.md`,
   `TODO.md`, `GLOSSARY.md`, `GETTING_STARTED.md`,
   `STYLEGUIDE.md`, `.gitignore`, and the README entry-block edit — plus
   `local/practices/project-voice.md` (a repo-local practice, not a root
   file, but still an install artifact — nothing else may land under
   `local/`), `tools/bootstrap.sh`, `.github/workflows/bestpractice-docs.yml` (only
   when the individual or team source resolved declares `"ci_workflows":
   "enabled"` — disabled is the default; see GITHUB_ACTIONS.md), and
   `.github/pull_request_template.md`. Everything else that ships
   with Precedent (INSTALL.md, PRACTICES.md, SETUP.md,
   GITHUB_ACTIONS.md, MOBILE.md, METHOD.md, GIT.md, templates/, tools/,
   deck/) exists ONLY under `process/upstream/` — never copy any of it to
   the root. A contributor browsing the root should see the project's own
   subject matter plus the instantiated files, and nothing about how
   Precedent works internally. The audit enforces this: an
   upstream-internal doc found at the root fails unless the manifest
   records it as the repo's own document.

   **Where GitHub-specific setup gets disclosed, since this list is half of
   what used to be a contradiction.**
   [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) is on the never-copy list above,
   and the [github-setup-disclosed](practices/github-setup-disclosed.md)
   practice requires a workflow this install turns on to be disclosed where
   the project's own people read. Those are not in tension: the destination
   is [GETTING_STARTED.md](templates/GETTING_STARTED.md)'s administrator
   section, which this same list places at the root. Do not write a root
   [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md) to satisfy the check — until
   2026-09-10 the check only read that file, which is what made the two
   rules look mutually exclusive; it now reads
   [GETTING_STARTED.md](templates/GETTING_STARTED.md) first.
7. Run `python3 process/upstream/tools/practice_audit.py` — it must pass.
   Then lint the files this install created **by name** —
   `python3 process/upstream/tools/doc_lint.py AGENTS.md MAP.md TODO.md GLOSSARY.md GETTING_STARTED.md local/practices/project-voice.md STYLEGUIDE.md README.md`
   — because the bare light check scopes itself to files changed against
   `origin/<default branch>`, and on a repo that has not been pushed yet
   that is nothing at all: it reported `0 file(s) checked` on a fresh
   install (2026-09-14) whose STYLEGUIDE.md carried three dead links.
   Commit.

8. **Disclose anything GitHub-specific**
   ([github-setup-disclosed](practices/github-setup-disclosed.md)): if any step above
   added a required Actions workflow, a repository secret, a
   branch-protection or required-check setting, or any other
   GitHub-specific requirement, add a line for it in
   `GETTING_STARTED.md`'s administrator section naming what it is, what it
   does, and the exact click-path to enable or configure it — don't leave
   it recorded only in this file. This install's own Actions check and PR
   template both need a line there; anything a future update adds does
   too.
9. **Ask about team and individual practice sources** (PRACTICE_ENGINE_PLAN.md's
   "Source — Who a Practice Belongs To"). This universal layer is one of
   three a project can run. Ask the administrator directly: *"Does your
   team already have its own practices repo — shared conventions beyond
   what's generic enough for the public Precedent? Does anyone here
   have their own personal one — facts specific to them, like a commit
   identity or a personal shorthand?"* Most projects have neither yet, and
   that's a complete, valid answer — but don't let it be the end of the
   question. **This step's default follow-up is an active offer, not a
   passive one:** if the answer to either half is no, the very next thing
   this session says is *"Want me to set one up for you right now? It only
   takes a minute and needs nothing from you but a yes."* (The name is
   not theirs to pick — `precedent-individual`, or
   `precedent-team-<subject>` where the subject is the only word they
   supply; see the naming rule under the team branch below.) — not a
   once-mentioned option left for the administrator to bring back up
   later. Nobody using Precedent should have to already know
   `spec/BOOTSTRAP_NEW_SOURCES.md` exists to get offered it.
   - **If yes, set one (or both) up now — same flow whether this is the
     first ask or a "yes" to the active offer above:** follow
     [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md) — it
     creates the repository (or hands the administrator the exact
     command/click-path where this session can't create one itself), runs
     `tools/precedent_bootstrap_source.py` to instantiate a real starter
     set in the right format, and wires the result in exactly as the two
     "if yes, one already exists" branches below describe. Do this before
     those two branches, since after it the answer to this step's
     question is yes.
   - **If a source already exists (this session's first ask, or a prior
     session's), confirm this session can actually reach it — right now,
     in this step, not by assumption.** Call `add_repo` (read access) for
     it immediately, before moving on. A "yes, we have one" that this
     session cannot read yet is not wired — it is a promise the *next*
     step's hook will silently fail to keep. This is exactly the check
     that would have caught the incident
     [`practices/session-bootstrap.md`](practices/session-bootstrap.md)'s
     Story records: an install (or migration) that assumed a named source
     would resolve on some *future* session, purely because `add_repo` for
     it was named as a standing instruction, rather than confirming this
     session — the one doing the wiring — could reach it too.
   - **If yes to a team source:** add `precedent.json` at the project root
     (create it if this is the first source beyond universal) declaring it:
     ```json
     {
       "sources": [
         {"level": "universal", "name": "precedent", "path": "process/upstream"},
         {"level": "team", "name": "precedent-team-<slug>", "path": "../precedent-team-<slug>"},
         {"level": "team", "name": "precedent-team-<other>", "path": "../precedent-team-<other>"}
       ]
     }
     ```
     **A repo declares as many team sets as its work needs, and this is
     the ordinary case, not an exception.** Team sets are named for a
     **subject**, so one team declares several and one set serves several
     teams. Two team sets defining the same slug is refused outright —
     that guard is what keeps one rule to one home, and it is why a set
     you need is added by declaring it rather than by copying its rules
     in.

     **Which team sets does this repo declare?** Start from the kind of
     work the repo is for:

     | The repo is… | Declare |
     |---|---|
     | software or tooling, maintained by a team | that team's set + the writing set + the working-style set |
     | a document or content project | that team's set + the writing set + the working-style set |
     | a practice set's own repository | the maintaining team's set + the writing set |

     **Ask this out loud rather than inferring it**, here and on every
     migration and vendored update — `vendor-update-runbook` carries it as
     a numbered step for exactly that reason. A set that was never declared
     is **invisible**: no error, no warning, no missing file, just a repo
     resolving fewer practices than its owner believes. Nothing mechanical
     can raise it, because the sets a repo *could* declare are not
     derivable from the ones it *does*.

     The pattern underneath it: **a set that is about a kind of work is
     declared by everyone who does that work**, whatever team they are on,
     and a set that is about running a particular kind of repository is
     declared only by repositories of that kind. A document project that
     declares a repo-mechanics set receives a stack of rules about syncs,
     gates and branch setup it has no way to act on — and the cheap
     remedy is not declaring the set, not a `not_binding` entry per slug.

     **Names are fixed by level, not chosen** — `precedent` for the
     universal set, `precedent-individual` for a person's own,
     `precedent-team-<slug>` for a team's, `local` for a repo-local one.
     Say that out loud before anyone creates or renames a repository here,
     rather than correcting a name afterwards: renaming a set breaks every
     vendored reference to it, and
     [`tools/precedent_resolve.py`](tools/precedent_resolve.py) refuses a
     source declared under any other shape. See
     [`practices/source-naming.md`](practices/source-naming.md).
     A team source is **resolved live from a sibling checkout, never
     vendored** — it already has its own repo and its own maintainers, so
     copying it in would just be a second, driftable copy. `path` is
     relative to the project root; whoever works from the project needs
     that sibling repo checked out locally, or — on a hosted agent
     platform like Claude Code Remote/Web, where a session's git access is
     scoped per session rather than inherited from the project — the
     session needs to be granted read access to it. **That grant must be
     something the session does for itself, automatically, every session
     — never a manual step a person has to remember or a failure they
     have to notice and react to.** `templates/AGENTS.md.template`'s
     "Build-environment gotchas" section carries the exact bullet to
     instantiate for this — use it rather than writing your own version;
     see [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)'s
     step 4 for the worked pattern and the incident that made "write your
     own version" the wrong call once already (it covers both this and the
     individual source below together, since they hit the identical gap).
   - **Proposing a *new* practice into that team source later is a
     separate question from installing the source itself, worth
     mentioning here since it comes up the moment anyone actually uses
     one:** whether it lands immediately or needs someone else's say-so
     depends on whether whoever's proposing it is a listed approver in the
     team repo's own `approvers.json`, not on how much git access their
     session happens to have. A listed approver's own agreement already
     is the approval `precedent_land.py` looks for — land it directly,
     right in that conversation (`precedent_promote.py` then
     `precedent_land.py --approved-by NAME`). Someone who isn't a listed
     approver can't grant that regardless of what else they can write to,
     so `precedent_candidate.py create --level team --as-issue true`
     drafts a GitHub Issue on the team repo instead, for an actual
     approver to act on later — see
     [spec/CANDIDATE_FORMAT.md](spec/CANDIDATE_FORMAT.md#which-one-for-team-file-or-issue)
     for the full "file vs. Issue" reasoning (it also covers individual,
     which never needs this: you're always the one who gets to say yes to
     your own set).
   - **If yes to an individual source:** that person declares it
     themselves, in their **own** user-level config
     (`~/.config/precedent/config.json`, or wherever `PRECEDENT_USER_CONFIG`
     points) — **never** in this project's own tracked files. Naming a
     person's individual set in a shared project's `precedent.json` would
     leak its existence and location to everyone else who can read that
     project, and `tools/precedent_resolve.py` refuses it outright for
     exactly that reason. On an ephemeral or cloud coding environment where
     nothing under `$HOME` survives between sessions, that config has to be
     recreated every session — a `SessionStart` hook, committed to the
     *project* (not the individual repo). Write it with
     `python3 tools/precedent_bootstrap_source.py --level individual
     --name <the set's name> --dest <local clone path>
     --write-session-hook <this project's path>
     --repo-url <the individual repo's URL>` rather than by hand. **When
     the set already exists — the usual case, since the hook belongs to
     the consuming project while the set lives elsewhere — drop `--dest`**
     and the tool writes the hook and nothing else, creating and touching
     no set. (`--dest` was required either way until 2026-09-06, so the
     only route to the hook was creating or force-overwriting a whole
     individual set; this repo itself went without the hook for exactly
     that reason.) Either form instantiates
     [`templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template`](templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template)
     at `.claude/hooks/precedent-individual-bootstrap.sh`, which delegates
     to the vendored
     [`tools/precedent_source_bootstrap.py`](tools/precedent_source_bootstrap.py)
     rather than a one-off hand-written clone.

     **That clone still needs the session to have git read access to the
     individual repo, and on a hosted agent platform that access is not
     automatic just because the hook exists** — a session's git access is
     scoped per session, and a shell hook cannot grant itself more of it.
     The consuming repo's instructions file still needs the standing
     `add_repo` instruction that
     [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)'s
     step 4 gives in full.

     **Two independent adopters had that instruction in place and still hit
     the gap, so read this even if you know it.** A `SessionStart` hook
     runs entirely to completion before the agent's first turn — strict
     ordering, not a race — so no instruction to call `add_repo` "first"
     can make that call precede the hook, at any retry count or delay. What
     actually closes it is
     [tools/precedent_resolve.py](tools/precedent_resolve.py)'s
     `load_config()`, which treats a still-missing individual config on a
     remote session as *try the bootstrap hook once more*; that
     re-invocation happens inside the agent's own turn, after `add_repo`
     has run. **The `add_repo` instruction is still required** — the
     self-heal has nothing to succeed into without real repo access. Both
     incidents are in
     [practices/session-bootstrap.md](practices/session-bootstrap.md)'s
     Story.
   - **Whichever branch above ran, finish the person before moving on:
     an individual set is not wired until its `identity.json` says who
     they are.** The file ships with placeholders and
     [`tools/precedent_bootstrap_source.py`](tools/precedent_bootstrap_source.py)'s
     `--verify` reports it unfinished
     until its placeholders — `name`, `email`, `pronouns` and `timezone` — are replaced. **The timezone is
     the one that fails quietly.** Name and address can be resolved from
     the GitHub account the session is authenticated as, so a session with
     no `identity.json` still commits under a plausible person; nothing
     anywhere can resolve a zone — a GitHub profile does not carry one and
     the container's clock is UTC — so the author-date check silently
     drops from enforced to guessed and wrong-offset commits reach the
     remote before anyone notices. An Internet Assigned Numbers Authority (IANA) zone name
     (`America/New_York`), never a bare offset.

     Then confirm it by effect rather than by reading the config back:
     `env -u GIT_AUTHOR_NAME -u GIT_AUTHOR_EMAIL -u TZ git var GIT_AUTHOR_IDENT`
     must name the person and the declared offset. `commit-identity.sh`
     from step 2's hook table is what puts it there, which is why that
     table says **always**.

     `identity.json`'s `grandfathered_commit_shas` is the exemption list
     for the identity and timezone checks. **A fresh install leaves it
     empty and should** — it is for commits that were already published
     when a violation surfaced, where rewriting history costs more than
     the wrong value does
     ([no-rewrite-for-warnings](practices/no-rewrite-for-warnings.md)).
     An unpushed commit gets fixed, not listed. A repo with history that
     predates the check is the migration case, not this one:
     [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)'s
     step 4d.
   - See [examples/practice-set/](examples/practice-set) for what an
     individual set's files actually look like, and
     [spec/PRACTICE_ENGINE_PLAN.md](spec/PRACTICE_ENGINE_PLAN.md)'s Vocabulary table
     for **universal source**, **team source**, and **individual source**
     as terms.
   - This step isn't only for a fresh install — see §2 step 3 for asking it
     again on an update, since a project's answer can change after this
     one-time question at install.

10. **Optionally, mention the GitHub settings only the repository's owner
    can click.** None of them can be done from a session and each fails
    quietly rather than loudly, so an install that names them saves a later
    surprise — offer them as suggestions, briefly, not as a gate. Suggest
    making the repository **private** unless it is meant to be public; a
    **personal access token for this repository, saved as a repository
    secret** (**Settings → Secrets and variables → Actions**, named
    `PRECEDENT_REPO_TOKEN` unless something already expects another name),
    is what lets a session or workflow push a branch or open a pull request
    on the project's behalf, and is not §8's read-only, environment-level
    `PRECEDENT_GIT_TOKEN` — a developer can take it from there; the
    **default branch should be `main`** (**Settings → General → Default
    branch**), which the shipped workflow template names as a literal
    string; and ***Allow GitHub Actions to create and approve pull
    requests*** (**Settings → Actions → General → Workflow permissions**)
    is needed by anything that opens a pull request for the project. Worth
    repeating in `GETTING_STARTED.md`, where they survive the conversation.
    The plain-language, step-by-step version is [SETUP.md](SETUP.md)
    step 7, and the reference for every GitHub setting Precedent depends
    on is [documentation/GITHUB_SETTINGS.md](documentation/GITHUB_SETTINGS.md). *(Click-paths as of 2026-09-10.)*

`.gitignore` / `.gitattributes` stanzas for generated artifacts
([generated-artifact-provenance](practices/generated-artifact-provenance.md)),
appended to the baseline `.gitignore` instantiated above from
[templates/gitignore.template](templates/gitignore.template):

```gitignore
# generated deliverables — only shipped artifacts get force-added
<your-build-output-glob>
```

```gitattributes
*.docx binary
*.pdf binary
<generated-md-glob> binary   # stop git text-merging generated files
```

## 0. Installing Directly Onto the Precedent Loader (New, 2026-09-03 — Read the Caveat Before Using)

**This is the default install since 2026-09-14, and it is one command.**
It is the only install that turns the loader on — the resident block, the
occasion index, the enforced checks; §1 installs the vendored prose and none
of that, so a §1 project that wants Precedent later takes
[spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md).
[SETUP.md](SETUP.md)'s guided conversation runs this path (until 2026-09-14
it ran §1 — flipped on the very deep check's recommendation; `strength:
assented`).

From a sibling clone of Precedent, on `precedent-beta-v01`:

```
python3 tools/precedent_install.py <project path> --project-name "<name>" \
    [--about "<one sentence, for a README that does not exist yet>"] \
    [--visibility private|public] [--base-branch main] \
    [--output-paths docs,site] [--admin <github handle>] [--team NAME=PATH]
```

[tools/precedent_install.py](tools/precedent_install.py) does steps 1, 2,
4, 5 and 6 below exactly as written, lints the files it wrote, and prints
what it could not decide: the `<…>` placeholders left in the instantiated
files (the project's own subject matter), any line still naming a layout
the project does not have, and the two things that stay a conversation —
step 3's team-and-individual question, and giving the repository an
`origin`. It never commits. **The numbered steps stay here because they
are what the tool does**, in the order it does it, and because a repo
that wants to deviate from one of them needs to know what it is deviating
from. Rehearsed against a real project on 2026-09-14 (the closing paragraph
of this section says what it found); the tool's own fixture in
[tools/verify_harness.py](tools/verify_harness.py) installs into a scratch
project and runs that project's checks on every harness run.

**When to use this instead of §1**: a genuinely fresh repo, never
BestPractice-vendored before. A repo that already vendored BestPractice
the old way and wants to move to the three-source model is a different,
already-documented case —
[spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md),
not this section.

1. **Vendor the universal source.** Clone Precedent
   (`precedent-beta-v01` today; `main` once phase 7 merges it back) and
   copy two things into this repo as ordinary tracked files: its
   `practices/` tree, into a tracked path of your choosing (recommended:
   `precedent/universal/practices/`), and the loader engine itself.
   **Don't hand-copy the engine files** — from the Precedent clone, run
   `python3 tools/precedent_vendor_engine.py seed <this repo's path> --kind consumer`
   to write the engine into this repo's own `tools/`: the loader, the
   multi-source resolver, the enforced channel, the individual-source
   bootstrap, the vendoring tool itself and their companions — the exact
   list is `CONSUMER_ENGINE_FILES` in that tool, and the tracked
   `tools/ENGINE_MANIFEST.json` it writes records every file with the exact
   commit and a sha256 (a list typed here named fifteen files on the day it
   was written and the seed wrote thirty-one by 2026-09-14). **What does
   not travel this way**: the harness adapters this repo's `precedent.json`
   declares are copied by the sync only from a source's `precedent.json`,
   and step 1 copies `practices/` alone — so a §0 install gets its hooks
   from step 5's harness adapter, by hand, and the sync reports
   `0 harness adapter(s)`; that is expected, not a failure. See "Keep the vendored engine current (consumer repos)" under §2
   for what that buys over a hand-copy, and how to refresh it later.
   **Nothing here is hand-copied any more.** `precedent_check.py` used to
   be, on the reasoning that the enforced channel is not the loader engine
   — which left the one file whose absence makes every
   `checked_by: "tools/precedent_check.py"` claim hollow as the only
   untracked copy in the tree, with no manifest and no way to tell stale
   from current. Vendoring it from Precedent's own commit
   (2026-09-06) is what made a fresh install's first `precedent_check.py`
   run come back clean.
2. **Write `precedent.json`** at the repo root, naming the universal
   source (`level: "universal"`, `path` pointing at step 1's vendored
   copy), a **repo-local source** (`{"level": "repo-local", "name":
   "local", "path": "local"}` — name and path both fixed by
   [source-naming](practices/source-naming.md), never chosen; step 5
   instantiates `local/practices/project-voice.md` into it, and nothing
   resolves that file without this declaration), and, if the administrator
   answered yes to the team/individual question (step 3 below, same
   question §1 step 9 asks), a `team` source too — resolved live from a
   sibling clone, per
   [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)'s
   §3, **never vendored**. Never declare a `level: "individual"` entry —
   `tools/precedent_resolve.py` refuses this by name, and for good
   reason: naming a person's individual set in a repo anyone else on the
   team can read leaks its existence and location to them.

   Two optional keys are worth setting in the same file, because both
   default to the safe-but-noisy answer and only this repo knows the real
   one. **`visibility`** (`"public"` or `"private"`) says whether this
   repo's tracked files are a publication; omitting it counts as public,
   so a private repo that omits it silently loses its team and individual
   practices from the materialized tree. **`internal_paths`** is a list of
   repo-relative path prefixes — a directory (`"notes"`), a nested one
   (`"docs/drafts"`), or a single file (`"ROADMAP.md"`) — that are this
   project managing itself rather than documents published to anyone. It
   is what [tools/title_case.py](tools/title_case.py) adds to its own
   built-in exclusions, which are Precedent's directory names and not
   yours. The key only ever *adds* exclusions — nothing a repo declares
   here can pull a vendored `practices/` tree back into scope.

   **`output_paths` is usually the better answer, and most repos should
   reach for it first.** It inverts the question: list the paths this
   project actually publishes, and everything else is internal.

   ```json
   "output_paths": ["business-modeling", "book-joseph", "book-moses"]
   ```

   Three lines, where the exclusion form needs a list of every other
   directory kept current forever. Without either key, `title_case.py`
   falls back to reasoning from *Precedent's* directory names, which in
   your tree name almost nothing — so your whole working tree reads as
   published and `headline-capitalization` reports headings you never
   meant to rewrite. Declaring `output_paths` is opt-in and changes
   nothing for a repo that omits it. `internal_paths` still subtracts
   from whichever way the default fell, which is how you exclude a
   vendored or mirrored subtree sitting *inside* an output directory —
   headings "fixed" there would be correct until the next sync and then
   silently revert.
3. **Ask the team/individual-source question** exactly as §1 step 9
   describes, and wire the individual source's own bootstrap pattern the
   same way if the person has one — this step doesn't change between the
   two install models.
4. **Instantiate `AGENTS.md` from
   [templates/AGENTS.md.loader.template](templates/AGENTS.md.loader.template)**
   — not `templates/AGENTS.md.template`, which is §1's classic-model
   version. Adapt it the same way §1 step 2 describes (real subject
   matter, keep the section structure), and leave the
   `<!-- BEGIN GENERATED: precedent-loader -->` /
   `<!-- END GENERATED -->` markers exactly as the template has them,
   empty — step 6 fills them in.
5. **Instantiate everything else §1 step 2 already covers**: `MAP.md`,
   `TODO.md`, `GLOSSARY.md`, `GETTING_STARTED.md`,
   `local/practices/project-voice.md`, `STYLEGUIDE.md`, the README
   agent-entry block, the harness adapter(s),
   `tools/bootstrap.sh`, the Actions check, the PR template. **Skip**
   `process/manifest.json` and `process/scrub_blocklist.txt` — those are
   §1's own bookkeeping for a model this path doesn't use.

   **One thing does change with the install model, and this step used to
   say it didn't** ("unchanged by which install model this is", until
   2026-09-10). §1 vendors Precedent's *prose* under `process/upstream/`;
   §0 vendors the practices and the engine and no prose at all. Two
   templates referred to the §1 layout outright, and a real §0 install
   shipped with a red check and three dead references because of it:

   | Artifact | What a §0 install needs |
   |---|---|
   | [templates/github-actions/doc-lint.yml.template](templates/github-actions/doc-lint.yml.template) | **Nothing — already handled.** It discovers `doc_lint.py` at either `process/upstream/tools/` or `tools/` and watches both. Install it verbatim — but only when you actually want it installed: `precedent_install.py` writes it by default only when the individual or team source resolved declares `"ci_workflows": "enabled"` (GITHUB_ACTIONS.md), and a §0 install manually copying this template is opting in explicitly regardless of that field. |
   | [templates/github-actions/views-drift.yml.template](templates/github-actions/views-drift.yml.template) | **Not this repo's — skip it.** It gates the generated views of a repo that AUTHORS its `practices/` (an individual or team practice set). A consuming repo materializes `practices/` from sources a CI runner cannot reach, so there is nothing on the runner to check the views against, and the workflow exits non-zero saying so rather than passing blind. See [GITHUB_ACTIONS.md](GITHUB_ACTIONS.md)'s Limits. |
   | [templates/GETTING_STARTED.md](templates/GETTING_STARTED.md) | Replace the `<upstream-docs>` placeholder with `https://github.com/alex137/BestPractice/blob/main` — the upstream URL, because §0 leaves no local copy of `MOBILE.md`, `METHOD.md` or `GITHUB_ACTIONS.md` to point at. (§1 replaces it with `process/upstream`.) |
   | [templates/pull_request_template.md.template](templates/pull_request_template.md.template) | Mentions `process/upstream/` in prose, as a review-grouping hint. Harmless, but names a directory your repo does not have, so a reader follows a dead path. Reword or drop the line. (`templates/local-practices/project-voice.md.template` has no such mention — it is a repo-local practice under `local/`, not a `process/upstream/`-adjacent document.) |
   | [templates/TODO.md.template](templates/TODO.md.template), [templates/MAP.md.template](templates/MAP.md.template), [templates/STYLEGUIDE.md.template](templates/STYLEGUIDE.md.template) | Each names `process/` or `process/upstream/` once (a recurring check-in item, a map row, an export note). Same treatment: reword or drop the line — and `STYLEGUIDE.md` still ships as an empty skeleton, out of scope for the install; only its one path note changes. |
   | [templates/harness/claude-code/settings.json](templates/harness/claude-code/settings.json) | Four `process/upstream/tools/…` entries in the permission allowlist. Harmless (they match nothing), but replace them with the `tools/…` forms so the allowlist covers the commands this repo actually runs. |

   After instantiating, grep the new root for `process/upstream` — in a §0
   install every remaining hit is a path that does not exist. The table
   above is the list as of 2026-09-11 and the grep is what keeps it
   honest: trust the grep, not the table.
6. **Run `python3 tools/precedent_sync_views.py --repo .`** — from the
   repo's own root; `--repo` is required and the tool refuses without it.
   It resolves every
   source `precedent.json` declares and writes `AGENTS.md`'s generated
   block from the result (the resident block, the occasion index, the
   standing instruction). Confirm it prints `OK`, not `FAIL`, and that
   the reported resident-block size is inside its stated budget. **It also
   writes three things to commit**: a materialized `practices/` at the
   root (every source resolved into one tree — the copy the loading tools
   read), `MANIFEST.json` beside it (what was materialized from where), and
   `tools/checks/tests/run_all.sh`. All three are tracked output of the
   sync, regenerated on every run; commit them, never hand-edit them.
   The generated block's own header names `build_views.py` as the
   regeneration command; in a consuming repo the command is this one,
   `precedent_sync_views.py --repo .` — `build_views.py --check` alone
   reports the hand-templated `MAP.md` and `GLOSSARY.md` as drift, which
   they are not.
7. **Root-hygiene rule, adapted from §1**: nothing from Precedent lands
   loose at the repo root except the instantiated files above and step 6's
   `practices/` and `MANIFEST.json` — the vendored engine and universal
   catalogue live under `tools/` and step 1's tracked path, not scattered
   elsewhere.
8. Commit everything on a branch, same as §1 — and, as in §1 step 7, lint
   the instantiated files **by name** first
   (`python3 tools/doc_lint.py AGENTS.md MAP.md TODO.md GLOSSARY.md GETTING_STARTED.md local/practices/project-voice.md STYLEGUIDE.md README.md`),
   because the bare light check scopes itself to what changed against
   `origin/<base branch>` and a repo with no `origin` yet checks nothing.
   **Give the repo an `origin` before the first session works in it**: the
   freshness guard the harness adapter wires refuses the session's first
   write while it cannot reach one, by design — an unreachable origin is
   indistinguishable from a stale checkout — and a freshly `git init`ed
   project is exactly the repo with none (measured 2026-09-14).
9. **Mention the same optional owner-only settings** as §1 step 10 — this
   path installs a different layout, not a different GitHub account.
10. **Draw the contributor boundary, when the project has people who should
    write its content and not its machinery** — a document project is the
    usual case, and a project whose every collaborator is a maintainer can
    skip this. `precedent_install.py` does not do this step; it is a
    decision about people, made after the install. The line is
    [spec/CONTRIBUTOR_ACCESS.md](spec/CONTRIBUTOR_ACCESS.md)'s: **content is
    any contributor's; a protected path needs a maintainer's review; a
    practice is suggested by anyone and landed only by a listed approver.**
    Nothing in it is keyed to what kind of person somebody is
    ([technical-describes-people](practices/technical-describes-people.md)).
    Four moves, in order:
    1. Declare `maintainers` and `owned_paths` in `precedent.json` — who
       reviews the machinery, and which paths are the machinery, each with
       its reason. [templates/document-project/precedent.json](templates/document-project/precedent.json)
       carries the filled-in registry a document project starts from;
       `MAP.md` and `GLOSSARY.md` are deliberately not on it, because a
       thread that adds a document adds its row to the map.
    2. Run `python3 tools/build_codeowners.py` and commit the generated
       `.github/CODEOWNERS`. Never hand-edit it; edit the registry and
       regenerate.
    3. On GitHub, give each contributor the **Write** role, and in the same
       sitting protect the base branch: require a pull request, required
       approvals **0**, require review from code owners, do not allow
       bypassing. Write without that protection is unrestricted write.
       Neither setting has a tool in this repository's GitHub toolset; both
       are a person's clicks.
    4. Run `python3 tools/precedent_boundary_check.py` with a token that can
       read the repository's settings (`PRECEDENT_GITHUB_TOKEN`, per
       [PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md)). Only `PASS` means the
       boundary is on; `UNVERIFIED` means this run could not look, which is
       not the same thing, and `--check` refuses it.
    Two things to keep true afterwards: **workflows carry no secret** beyond
    the read-only default token, since `CODEOWNERS` gates the merge of an
    edited workflow and not its first run on a collaborator's branch; and
    **before every pull request a session runs
    `python3 tools/precedent_owned_paths.py`** and relays its sentence, so a
    contributor hears which files will wait for review before the merge
    button refuses them. Three GitHub behaviours the design rests on are
    unverified as of 2026-09-14 — the spec's "Verify these first" section
    names them, and the very deep check's `CONTRIBUTOR BOUNDARY` section
    reads the setting on every run. **Every GitHub setting this step
    touches — roles, branch protection, what CODEOWNERS does and how this
    system generates it, Actions permissions and secrets — is explained in
    one place, [documentation/GITHUB_SETTINGS.md](documentation/GITHUB_SETTINGS.md).**

**What has and has not been rehearsed, stated plainly rather than left to
be discovered.** Every step here has been walked end to end against a
scratch repository twice — 2026-09-06 (the
[pre-launch audit](spec/PRELAUNCH_AUDIT.md)) and again 2026-09-07 (the
[very deep check](practices/very-deep-check.md)'s pass 1) — vendoring,
declaring sources, instantiating, syncing, and running the deep check on
the result, which comes back clean. **No count is quoted here on purpose**
(the maintainers' team set names this `no-stale-counts`; that repo is
private, so this names the practice rather than linking a page most
readers cannot open): the first rehearsal
recorded "15 checks passed", the check suite has grown since, and the
figure was simply wrong by the second rehearsal rather than usefully
out of date. What matters is `0 violated`, which is what to expect and
what to report.

The 2026-09-07 rehearsal is worth knowing about before trusting the first
one: following these steps produced a repo that did **not** come back
clean, and the four things it ended on were all defects here, not in the
install. Two of them only bite a consumer declaring `visibility: public` —
private practice text was materialized into its tracked tree, and the
loader block the documented step wrote was one the enforced check then
reported as hand-edited. All four are fixed; the run is recorded in
[spec/VERY_DEEP_CHECK.md](spec/VERY_DEEP_CHECK.md).

**A real project has now done this, 2026-09-14**, which is what the
paragraph above used to say was still missing — a scratch repository has no
subject matter, so until then nothing here had been tested against an
adopter adapting the templates to their own work. It found three more
defects, all of them in this engine and none in the steps:

- two checks an individual practice source supplies crashed on a repository
  with **no commits** — which a fresh install is, exactly — and the
  traceback was reported as a violation of the practice itself. **Fixed
  2026-09-14**: both checks now skip, saying there is no history yet, and
  run clean as soon as the repo has its first commit.
  [TODO.md's `no-history-checks-unpushed` item](todo/todo-2026-09-14-no-history-checks-unpushed.md)
  carries what landed;
- a repo declaring its own `fallback_timezone` in `precedent.json` — the
  documented rung-5 override — was reported as drift by
  `timestamps-carry-offset`, which compared it against the engine constant
  it exists to override. The check now holds the three ENGINE copies in
  lockstep and leaves the repo's own declaration alone;
- the catalogue this section vendors to `precedent/universal/practices/`
  carries relative links written for its own repo, so `doc_lint.py`
  reported dozens of broken links in files an adopter must not edit. A
  mirrored tree is now exempt from the link check alone.

What is still untested is the rest of [spec/PHASE6_BRIEF.md](spec/PHASE6_BRIEF.md)'s
list, not the install itself. Two things this section deliberately does **not**
cover, by design and not oversight:

- **`MAP.md`/`GLOSSARY.md` generation.** `tools/precedent_sync_views.py`
  deliberately does not build these for a consuming repo (see its own
  docstring) — they stay hand-templated, same as §1.
- **The creation pipeline isn't wired into a fresh install yet.**
  Candidates, promotion, and approval routing
  (`tools/precedent_candidate.py` and friends) exist in Precedent's own
  `tools/` and in the private team/individual repos, not in what this
  section vendors. `templates/AGENTS.md.loader.template`'s own
  merge-runbook export-gate step says so explicitly and names the real
  mechanism until it is wired in: an ordinary pull request against the
  vendored source's own upstream repo.

## 2. Take an Upstream Update

*Knowing* an update exists is automated: the session-start bootstrap runs
`checkin.py fresh` (one `ls-remote`, notice-only). *Taking* it is the
deliberate procedure below.

**[Essentials only](#essentials-only--what-an-install-upgrade-or-migration-leaves-for-later)
governs an update exactly as it governs an install.** An update brings the
project to current and stops; a newly shipped template that is optional gets
one sentence, not a walkthrough. `local/practices/project-voice.md` and
`STYLEGUIDE.md` in particular are never filled in by an update.

**An update taking the 2026-09-17 project-voice change lands on a repo that
still has a root `VOICE.md`** from an earlier install. That is a migration,
not an ordinary template refresh — see
[spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)'s
project-voice step, and do not leave the old `VOICE.md` sitting beside the
new practice file: a repo with both is a repo where a session has no way to
know which one is meant to bind.

**Which install model is this? Steps 1–5 are §1's, and a §0 install skips
them.** §1 vendors upstream's *prose* under `process/upstream/` and tracks it
in `process/manifest.json`, which is what steps 1–5 merge, record and audit.
A §0 install has neither: it vendors a `practices/` tree and the engine, and
nothing else. So a §0 repo's whole update is **step 6 (the engine) first,
then step 0 (the catalogue), then step 0b (the wiring)** — the engine first
so the new checks read the new catalogue rather than the old checks reading
it uncommitted, which reported five false `acronyms-glossary` hits on
2026-09-14 when the steps ran the other way round. Step 0 is here because
until 2026-09-11 this section covered the engine and never mentioned the
catalogue, so a §0 repo following it exactly refreshed its tools, kept a
frozen practice catalogue, and got `OK` from every check. Measured that day
on a scratch consumer vendored at a 2026-09-07 commit: after the documented
update it still materialized 72 practices while upstream carried 98, with
nothing said. Step 0b is here for the same shape one layer out, found
2026-09-14: the engine manifest does not cover `tools/bootstrap.sh`, the
harness hooks or the instructions file, so a refreshed engine that changed
what a command accepts left a consumer's own session-start script calling
it the old way — a WARN at every session start naming a fix that failed the
same way.

0. **(§0 installs) Replace the vendored universal catalogue.** From a
   sibling Precedent clone, already on `precedent-beta-v01` and pulled:
   ```
   rm -rf <your universal source path>/practices
   cp -r ../BestPractice/practices <your universal source path>/practices
   ```
   `<your universal source path>` is the `path` of the `level: "universal"`
   entry in your `precedent.json` (§0 step 2 recommends
   `precedent/universal`). It is a wholesale replace, not a merge: this
   tree carries **zero** local variance by design, the same rule the
   engine follows in step 6 — a local edit here belongs upstream, through
   §3's export gate. Then re-run
   `python3 tools/precedent_sync_views.py --repo .` and review the diff to
   `AGENTS.md`'s generated block and your materialized `practices/`: new
   practices, changed Rules and retired ones all arrive here, and this is
   the only place a reader sees them.

   **Expect a refusal if anything was retired, and read it before reaching
   for the flag.** If anything was retired upstream since you installed
   (nothing may have been — a six-day update on 2026-09-14 saw none), the
   sync refuses
   rather than deleting a practice your committed `MANIFEST.json` records.
   Retirement is the ordinary case when you have just replaced the whole
   catalogue, and then `--allow-removals` is the correct answer — but the
   same refusal also fires when your vendored copy is *stale*, which needs a
   refresh instead. The message names both and says which is which; check
   the named practices against upstream's
   [MAP.md](MAP.md) withdrawn-practices table before overriding.

   **A second refusal names a source your `precedent.json` no longer
   declares**, and it is worth reading rather than flagging past: the match
   is by NAME, so a source somebody RENAMED looks exactly like a source
   somebody dropped, and overriding it there deletes practices that are
   still alive. Compare the recorded name against your declared ones first.
   `--allow-removals` proceeds once you know which you have.

0b. **(§0 installs) Re-instantiate the wiring the engine manifest does not
   cover.** `tools/bootstrap.sh`, the `.claude/hooks/*.sh` adapters and the
   instructions file are instantiated from `templates/` and adapted, so
   `refresh` never rewrites them — and it now ends by naming any of them
   that still invokes `precedent_sync_views.py` without `--repo`, which the
   refreshed engine refuses. Re-instantiate `tools/bootstrap.sh` from
   [templates/bootstrap.sh](templates/bootstrap.sh) and the hooks from
   [templates/harness/](templates/harness/) (carrying your adaptations
   across), or fix each named line. Then `python3 tools/precedent_check.py`
   should come back `0 violated`; `access-probe-is-wired` in particular is
   satisfied by the current `bootstrap.sh` and by nothing older.

1. Fetch the new upstream tree; diff it against the vendored copy at the
   **recorded base commit** (manifest `upstream.commit`).
2. Three-way merge per manifest entry: *old upstream* vs *new upstream* vs
   *your installed, adapted copy*. Apply upstream's changes to your installed
   files **through the adaptation** recorded in the entry's `notes` — don't
   clobber local adaptations.
2a. **When upstream DELETES content it previously told you to keep, the
   three-way merge above will not tell you what to rescue.** This is the one
   update shape step 2 handles badly, because a `local-only` file has no
   adaptation `notes` to merge through — you were told to keep the shipped
   defaults, so nothing recorded which parts you later made decisions about.
   Read the deleted block once and ask of each piece: *did anybody here
   actually decide this, or was it just what shipped?* Carry the decisions,
   drop the rest, and put each carried item where the new structure says it
   goes rather than re-adding the old section.

   **The worked example, and the reason this step exists** (2026-09-08):
   `templates/VOICE.md.template` lost 205 lines of general writing guidance,
   because the practice catalogue already carries all of it and one line —
   *"no bold inside paragraphs"* — had come to contradict the resident
   practice [bold-key-phrases](practices/bold-key-phrases.md) outright, so
   every session in every adopter repo was holding both instructions at
   once. A dependent repository taking that update had two things in the
   deleted region that were genuinely its own: a note distinguishing its
   sense of "voice" from a vendored pack's, and a sentence-case deviation.
   Both were carried. **An override nobody wrote down reads as a session
   ignoring a rule**, so moving them was not bookkeeping.

   **Where an override goes is its own question, and the first answer here
   was wrong.** This step originally said a departure from a catalogue rule
   belongs in `VOICE.md`'s `## Overrides`, full stop — and that competes
   with two mechanisms that were already there. Take the first that fits:
   a **`precedent.json` knob** (`not_binding`, `internal_paths`,
   `output_paths`, `filename_separator_exempt`) when the departure is
   mechanical, because the tool reads it and it cannot drift; a
   **`## Conventions` bullet in the instructions file** when a session has
   to know it while doing ordinary work; and (since 2026-09-17,
   `local/practices/project-voice.md`'s own `## Overrides` section — `VOICE.md`
   at the time of this incident) only for a voice departure with no knob.
   **A session applying a rule is not reading that file when it applies
   it** — which is why the repository that hit this moved its sentence-case
   deviation into the instructions file the next hour, and was right to.
   `local/practices/project-voice.md` may still name it in one line and
   point at where it lives; a pointer, never a copy.

3. **Instantiate anything the recorded install predates.** An update can
   introduce templates and root files that did not exist when this repo
   installed — e.g. `GETTING_STARTED.md`
   (from [templates/GETTING_STARTED.md](templates/GETTING_STARTED.md)),
   the README entry block
   ([templates/README_AGENT_ENTRY.md.template](templates/README_AGENT_ENTRY.md.template)),
   the Actions check
   ([templates/github-actions/](templates/github-actions/README.md)), or the
   PR template
   ([templates/pull_request_template.md.template](templates/pull_request_template.md.template)).
   The same applies to a question, not just a file: if this repo installed
   before §1 step 9 existed, **ask about team and individual practice
   sources now** — a project doesn't get only one chance at install to say
   yes, and a "no" the first time (or before the option existed at all)
   isn't permanent. Instantiate them exactly as §1 describes and add
   manifest entries — a short catch-up prompt ("take the Precedent
   update") is enough to
   propagate a newly introduced template like this to every repo that
   already installed Precedent before it existed.

   **And check the person, not only the repo — an update is the second
   chance the install may not have taken.** A set created before
   `identity.json` shipped does not have one, and a set that has one may
   still carry the placeholders, which nothing reports at commit time
   because the checks it feeds simply degrade to guesses. Run
   `python3 tools/precedent_bootstrap_source.py --verify <the set's path>`,
   fill in anything it names, and confirm the
   result by effect:
   `env -u GIT_AUTHOR_NAME -u GIT_AUTHOR_EMAIL -u TZ git var GIT_AUTHOR_IDENT`
   must name a person and the declared offset, not the assistant's bot
   account and not UTC-by-default. §1 step 9's last bullet has the full
   reasoning; this is the same check, run on a repo that already
   installed.
4. **Fix legacy layout.** Older installs sometimes scattered
   upstream-internal docs (INSTALL.md, GITHUB_ACTIONS.md, …) at the repo
   root; the audit's LAYOUT check now fails on them. Delete the strays —
   their content lives under `process/upstream/` — per §1's root-hygiene
   rule.
5. Replace `process/upstream/` with the new tree —
   `python3 process/upstream/tools/checkin.py update <upstream-clone>`
   mirrors the clone's freshly pulled default branch into the vendored
   tree, and refuses if the vendored tree carries unexported local work
   (export first, or `--force` to overwrite) — then update
   `upstream.commit` (`checkin.py record <upstream-clone>`), run the
   audit `--update-baseline`, commit.
6. **Keep the vendored engine current (consumer repos).**
   **First, look for `tools/ENGINE_MANIFEST.json` — it decides which
   command you run, and there is no way to discover that from the error.**
   No manifest means this repo predates the vendoring mechanism and its
   `tools/` is the old hand-copy: `precedent_vendor_engine.py` is not there
   to run, and `status` and `refresh` both read the manifest anyway, so
   neither verb can bootstrap the thing it needs. Seed it once, from a
   sibling BestPractice clone's own copy of the tool:
   ```
   python3 ../BestPractice/tools/precedent_vendor_engine.py seed . --kind consumer
   ```
   (Confirmed the hard way 2026-09-06, refreshing a private consumer repo:
   all three commands exited 2 with "No such file or directory", which reads
   like a broken instruction and is really a missing baseline.) With a
   manifest present, `status` and `refresh` below are the whole procedure.
   Steps 1–5 above
   are about `process/upstream/` — the vendored *content* (universal
   practices, `PRACTICES.md`, the audit scripts). This step is about the
   separate tree at this repo's own top-level `tools/`: the loader
   *engine* (`build_views.py`, `precedent_gate.py`, `precedent_paths.py`,
   `precedent_show.py`, `split_practices.py`, `precedent_materialize.py`,
   `precedent_resolve.py`, `precedent_sync_views.py`, and
   `precedent_vendor_engine.py` itself) that resolves universal + team +
   individual + repo-local into one materialized tree and regenerates
   `AGENTS.md`'s loader block from it. If this repo has
   `tools/ENGINE_MANIFEST.json`, it was vendored with
   [`tools/precedent_vendor_engine.py`](tools/precedent_vendor_engine.py)'s
   `'consumer'` kind (§0 step 1, or the migration path
   [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)
   step 7 documents) — the same mechanism
   [spec/BOOTSTRAP_NEW_SOURCES.md](spec/BOOTSTRAP_NEW_SOURCES.md)'s "The
   vendored engine" section already documents for an individual/team
   *source* set, extended to a four-source *consumer*'s larger file list.
   From a sibling BestPractice clone — **but check for
   `tools/ENGINE_MANIFEST.json` first: with no manifest, neither verb
   below can run, and this step's opening paragraph is your entry point,
   not these two lines:**
   ```
   # Precondition: tools/ENGINE_MANIFEST.json exists (i.e. a prior seed).
   # Without it, go back to this step's first paragraph and seed instead.
   python3 tools/precedent_vendor_engine.py status  ../BestPractice   # drift? behind?
   python3 tools/precedent_vendor_engine.py refresh ../BestPractice   # pull, re-vendor, re-stamp
   ```
   **If `refresh` exits with "`precedent-beta-v01 @ <commit>` has no
   `tools/<name>`", reseed — do not go looking for the missing file.**
   `refresh` runs *this repo's own vendored copy* of the tool, which
   carries the file list it was vendored with. So the first refresh after
   upstream renames or drops an engine file asks git for a path that is
   genuinely gone. Upstream stopped treating that as fatal on 2026-09-08
   (it skips the dropped name and converges on the second pass), but **that
   fix can only arrive through a refresh, and the refresh is the thing that
   is broken** — so every repo vendored before that date needs one manual
   reseed to escape, from a sibling clone as in this step's first
   paragraph:
   ```
   python3 ../BestPractice/tools/precedent_vendor_engine.py seed . --kind consumer
   ```
   Measured 2026-09-08 across three real practice sets, all of which
   refused with "has no `tools/precedent_retire_path.py`" after that file
   was renamed to `precedent_decommission.py`. Reseeding also deletes the
   renamed-away file, which it did not do before that date — so a repo
   reseeded earlier may still be carrying one. `status` names it
   (`RETIRED ENGINE FILE`) and says why; delete it once you have checked
   nothing in the repo still calls it.

   `refresh` reads `kind` back out of `ENGINE_MANIFEST.json` itself — no
   `--kind` flag needed here, only at first `seed`. It pulls
   `precedent-beta-v01` specifically (not this clone's configured default
   branch — see
   [local/practices/merge-target-is-beta-branch.md](local/practices/merge-target-is-beta-branch.md)),
   and refuses to overwrite a hand-edited vendored file unless `--force` —
   this engine carries zero local variance by design, so a local edit is a
   signal to move the change upstream into Precedent instead. After a
   refresh, run `python3 tools/precedent_sync_views.py --repo .` — **expect
   `--check` to FAIL first**: a refresh changes what the loader renders
   (the generated block, `MANIFEST.json`), so a byte-identical check against
   the old output fails every time, and it failed on every ordering tried
   on 2026-09-14. Run the sync, review both diffs together, and commit the
   refresh and the sync as one change; `--check` is then the confirmation.

## 3. (Optional) Give Back an Improvement — The Export Gate

For projects that choose to give back, run this check **before any thread
ends / before any merge to the default branch** (it is step 0b of the merge
runbook, beside the capture gate). Projects that don't intend to contribute
upstream can skip this section entirely:

> Did this thread improve a *generic* practice — a new convention, a
> sharpened runbook rule, a better audit, a template fix?

`local/practices/project-voice.md` and `STYLEGUIDE.md` never answer yes to
this question, even when a thread rewrites them substantially: the *files*
are project/company identity, not practice, so their content stays local by
category, not by judgment call.

**But watch for the thing that is not identity.** A writing rule that would
improve *anyone's* prose has no business in `local/practices/project-voice.md`,
and if a thread put one there, that IS a check-in — as a practice in the
exported catalogue, not as template content. Until 2026-09-08 this template
(then a plain document, `VOICE.md`) shipped 205 lines of exactly such rules
to every project, and one of them had come to contradict the universal
`bold-key-phrases` outright. A local copy of a generic rule does not merely
go stale; it argues with the live one.

If yes, in the **same branch**:

1. Write the **abstracted** form into the right file under
   `process/upstream/` — patterns and lessons only, subject matter stripped
   ([scrub-gate](practices/scrub-gate.md)). Abstraction is authorship, not copying: rewrite the
   incident generically, keep the lesson.
2. Update the touched manifest entries (`notes`, status) and run
   `python3 process/upstream/tools/practice_audit.py` — the scrub must pass.
3. If the *installed* file changed but you are not exporting yet, flip its
   manifest entry to `"diverged"` — the audit will keep reminding until the
   export happens or the baseline is deliberately updated.

## 4. (Optional) Periodic Check-In — Propose Your Improvements Upstream

**Session scope note (hosted agent platforms).** Repo access is typically
fixed when a session is created: a session opened on the dependent repo
alone can usually *read* the public Precedent repo (clone, fetch, diff)
but **cannot push branches or open PRs there** — writes fail even though
the day-to-day export loop (§3) works fine, because that loop is purely
local commits. So: **open check-in sessions with BOTH repos selected at
creation.** Everything else can be prepared, scrubbed, and audited in
ordinary single-repo sessions; only this step needs the dual-repo session.

For projects that choose to give back: on a schedule (a recurring
`TODO.md` item), in a session with access to the Precedent repo.
[tools/checkin.py](tools/checkin.py) drives the mechanical steps against a
local clone of the upstream repo; the deliberate steps (review, PR, merge)
stay manual:

1. Review the vendored tree's accumulated changes and every `diverged`
   manifest entry — export what's ready, or record in the entry's notes why
   an entry genuinely stays local.
   `python3 process/upstream/tools/checkin.py status <upstream-clone>`
   lists exactly what has accumulated.
   **The check-in carries ALL pending vendored additions, not just the
   ones your own thread made.** A two-way sync that ends by replacing the
   vendored tree with upstream's copy ("tree-identical") silently deletes
   any accumulated addition it did not first include in the check-in PR —
   so before replacing, diff the vendored tree against upstream and
   either check in every local addition found or record, per addition,
   why it stays behind. *(Origin: a same-day sync verified tree-identical
   and erased another thread's two hours-old practice additions; the loss
   surfaced only because that thread's session was still open to notice.)*
2. `python3 process/upstream/tools/checkin.py push <upstream-clone>` —
   runs the **scrub audit first (must pass; nothing is copied on failure)**,
   then mirrors the vendored tree into the clone's working tree.
3. Commit in the clone on a branch and open a PR against Precedent.
   Human review of that PR is the second scrub line — the blocklist catches
   known vocabulary; the reviewer catches what the blocklist doesn't know
   yet (and adds it to the blocklist).
4. When the PR merges:
   `python3 process/upstream/tools/checkin.py record <upstream-clone> --note "PR #N"`
   — pulls the upstream default branch, **verifies it is byte-identical to
   the vendored tree**, and — enforcing step 1's carry-all rule mechanically
   — **verifies every pending vendored addition committed on the dependent
   default branch since the recorded base is present in the landed tree**,
   refusing to record a cycle that dropped content (a deliberate removal
   needs `--accept-loss`, which prints what is let go). Then writes the
   landed hash into `upstream.commit`.
   Commit the manifest change (and `--update-baseline` if entries moved).

**Freshness and ordering (learned in the field, 2026-08).** Work from
fresh refs at every step: fetch before comparing anything — a stale
`origin/<default>` (or a local `<default>` branch left pointing at an old
commit) reports "up to date", and `git archive <default>` mirrors an old
tree, while upstream has actually moved. If upstream's default branch
gained commits since the vendored tree's recorded base, the check-in PR
merges on top of them and `record` will refuse the mismatched tree — not
an error to work around: take the update (§2, `checkin.py update`) in the
same round, then `record`. And when the dependent repo has its own PR
open for the same round, merge the upstream check-in PR **first**, take
any drift, record, and only then land the dependent PR — the reverse
order records a hash the vendored tree doesn't match.

## 5. The Manifest Schema (`process/manifest.json`)

```json
{
  "upstream": {
    "repo": "https://github.com/<owner>/BestPractice",
    "vendored_at": "process/upstream",
    "commit": "<hash of the upstream commit last synced>"
  },
  "entries": [
    {
      "practice": "doc-lint",
      "upstream_path": "tools/doc_lint.py",
      "local_path": "tools/doc_lint.py",
      "granularity": "file",
      "status": "synced",
      "local_sha256": "<filled by practice_audit --update-baseline>",
      "notes": "what was adapted, and anything an updater must preserve"
    },
    {
      "practice": "merge-runbook",
      "upstream_path": "templates/AGENTS.md.template",
      "local_path": "CLAUDE.md",
      "granularity": "section",
      "section_marker": "## Merge runbook",
      "status": "synced",
      "notes": "file classes adapted to this repo"
    },
    {
      "practice": "voice",
      "upstream_path": "templates/local-practices/project-voice.md.template",
      "local_path": "local/practices/project-voice.md",
      "granularity": "file",
      "status": "local-only",
      "notes": "a repo-local practice, not a root document; filled in this project's own voice at install, and the template ships no general writing rules (those are the catalogue's). Never exported (INSTALL.md §3) — a project's voice is its own identity, not a generic practice"
    }
  ]
}
```

- `granularity: "file"` — audited exactly: `local_sha256` is the baseline;
  any later change to the local file flags the entry until it is exported
  and re-baselined, or flipped to `diverged`.
- `granularity: "section"` — audited approximately: the audit only verifies
  `section_marker` still occurs in `local_path` (warn on miss). Used where a
  practice was woven into an existing document rather than installed as a
  file. This is the fuzziest part of the machinery — prefer file granularity
  where you can.
- `status`: `synced` (installed copy matches its baseline) · `diverged`
  (local improvement pending export) · `local-only` (deliberately not
  exported; say why in `notes`).

## 6. The Audit (`tools/practice_audit.py`)

```
python3 process/upstream/tools/practice_audit.py                    # full check (gate)
python3 process/upstream/tools/practice_audit.py --update-baseline  # re-record hashes
```

Checks, in order — any FAIL exits non-zero:

1. **Scrub** ([scrub-gate](practices/scrub-gate.md)): every text file under `process/upstream/`
   scanned against `process/scrub_blocklist.txt`. Any hit → FAIL. (Skipped,
   with a notice, if no blocklist exists — a public dependent repo.)
2. **Drift** ([registry-source-of-truth](practices/registry-source-of-truth.md)): for each `file`-granularity entry, current hash
   vs `local_sha256`. Changed while `status: "synced"` → FAIL (export it or
   flip to `diverged`). `diverged` entries are listed as pending export,
   not failed.
3. **Integrity:** manifest paths exist; `section_marker`s found (warn);
   `local-only` entries have notes.

## 7. Practice Packs (Domain Layers)

A repo can install additional practice layers beside this upstream —
**packs** ([layered-practice-packs](practices/layered-practice-packs.md)): domain-scoped practice sets (a compliance regime, a
lab workflow, a regulated-filing process) that are too domain-bound for this
public upstream but too general to be one repo's local rules. Mechanics:

1. **Anatomy mirrors this upstream.** A pack is a vendored tree at
   `process/<pack>/` — its own `PRACTICES.md`, `INSTALL.md`, `tools/`,
   `templates/harness/…` — destined for its own repo someday; until that
   repo exists, the vendored tree *is* the upstream and `upstream.commit`
   stays `null`.
2. **One manifest per layer.** The pack's manifest lives at
   `process/manifest_<pack>.json`, same schema as §5, with
   `upstream.vendored_at` pointing at the pack tree. `practice_audit.py`
   discovers and audits every `process/manifest*.json` in one run.
3. **Per-pack scrub.** The manifest's `upstream.scrub_blocklist` names the
   pack's own blocklist (the repo vocabulary that must not leak *into the
   pack*); an explicit JSON `null` opts a private pack out of the scrub.
   When the key is absent, the default `process/scrub_blocklist.txt`
   applies (the public gate).
4. **Routing.** A pack ships harness adapters that declare *when its rules
   apply* — for agent harnesses, a skill whose description triggers on the
   domain's work, pointing the agent at the repo's instantiation file and
   the pack catalog. The repo's base instructions stay lean; domain rules
   load when the domain work happens.
5. **The loops are shared.** Install (§1), update (§2), export gate (§3),
   and check-in (§4) all apply per pack, against the pack's own tree,
   manifest, and (eventual) upstream repo.

## 8. Per-Machine Setup — What Each Person Sets, on Each Machine

**Moved to [PER_MACHINE_SETUP.md](documentation/PER_MACHINE_SETUP.md).** Everything on
this page installs Precedent into a *repository*; that one is the other
axis — what a person sets on each computer they work from, none of which
lives in any repository and most of which fails quietly when absent. It
covers the user-level config, the leak blocklist, `identity.json`, and the
`PRECEDENT_GIT_TOKEN` / `PRECEDENT_SOURCE_BASE_URL` credential that lets a
hosted session reach a private practice source without an `add_repo` dance
— and, optionally, `PRECEDENT_GITHUB_TOKEN`, the token §0 step 10's boundary
check needs to read a repository's protection settings.

**Most people set this up on Claude Code on the web, not a local
checkout** — [CLOUD_SETUP.md](documentation/CLOUD_SETUP.md) is the fast path for exactly
that case; `PER_MACHINE_SETUP.md` is the complete reference underneath it.
