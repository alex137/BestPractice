# How to install BestPractice for you and your team

Instructions for wiring BestPractice into a *dependent repo*, keeping it
current, and flowing improvements back. Read [PRACTICES.md](PRACTICES.md)
first for what each practice is and why.

You don't need to run the technical steps yourself to follow, or approve,
this setup: read just the shaded **"In plain terms"** note at the start of
each section below, in order, and skip everything underneath it — together
they walk through the whole setup without requiring GitHub knowledge. The
last section,
[For approvers: your checklist](#for-approvers-your-checklist), gathers every
point in the process that actually needs a decision from you into one list.
To have this conversation live with your assistant rather than reading about
it, start at [SETUP.md](SETUP.md) instead — this page is the detailed
reference it works from.

> **In plain terms.** BestPractice is a set of working habits — how a
> project remembers its decisions, how contributors avoid overwriting each
> other's work, and how private information stays private even though this
> rulebook itself is public. What follows is how that layer gets installed
> into your project, how it picks up improvements later, and how an
> improvement made in your project can be offered back for every other
> project's benefit.

The model in one paragraph: the dependent repo **vendors** this repo at
`process/upstream/` as plain tracked files. **Install is adaptive** — you
instantiate templates with the repo's subject matter, placing real files at
their real locations. **Export is abstractive** — when installed practice
improves, you fold the generic form back into `process/upstream/`. The
**manifest** records the mapping in both directions; the **audit** makes
drift and proprietary leakage loud instead of silent. **This is the
classic model** (§1) — the right default for essentially every install
today, and where the sections below start. A repo with no prior
BestPractice install that wants Precedent's three-source loader directly,
without ever going through `process/upstream/`, should use §0 instead —
covered after §1, since it is the rarer path; see §0's own note for when
it applies.

## 1. Install into a dependent repo

> **In plain terms.** This is the one-time setup. An assistant copies
> BestPractice's files into your project, then rewrites a handful of
> them to describe *your* project specifically — a map of where things
> live, a to-do list, a page that welcomes new members. Nothing from
> this step becomes visible to anyone but you until you (or whoever has
> authority to make it official) approve it: the work is committed on a
> private branch (step 7), and it becomes official only at the
> review-and-merge that the [guided install](SETUP.md) walks an
> administrator through in conversation rather than as a technical
> checklist. Two decisions only you can make: **which private names and
> code words must never leak into a public file** (step 4) — your
> assistant cannot guess your project's secrets, so it will ask you
> directly — and **whether your team or you personally already have your
> own practices repo to wire in** (step 9) — most projects don't yet, and
> that's a fine answer, but you're the only one who'd know if you do.

1. **Vendor:** copy this repo's working tree (not its `.git`) into
   `process/upstream/` and commit it as ordinary tracked files. Record the
   upstream commit hash you copied from (used by updates, step 2).
2. **Instantiate the templates** (adaptive — rewrite with the repo's actual
   subject matter, don't copy verbatim):
   - `templates/AGENTS.md.template` → `AGENTS.md` at the repo root: the
     **harness-neutral** canonical instructions file. Fill the quick-index
     table with this repo's real lookups; adapt the merge runbook's file
     classes; keep the section structure.
   - `templates/MAP.md.template` → `MAP.md`; `templates/TODO.md.template` →
     `TODO.md`; `templates/GLOSSARY.md.template` → `GLOSSARY.md` (or a
     domain-appropriate name).
   - `templates/VOICE.md.template` → `VOICE.md`; `templates/STYLEGUIDE.md.template`
     → `STYLEGUIDE.md`. Unlike the files above, these are **not** rewritten
     with the repo's subject matter — VOICE.md ships with its default
     writing-style rules unchanged, and STYLEGUIDE.md ships as an empty
     skeleton. Instead, **prompt the administrator explicitly**: show them
     VOICE.md's defaults and ask if anything should change; ask whether a
     formal brand guideline exists (a PDF, a slide deck, a design team's
     style manual) to fill in STYLEGUIDE.md from. If one exists, read it and
     transcribe the relevant rules into STYLEGUIDE.md as plain text — never
     attach, vendor, or link the source document itself into the repo. If no
     visual identity exists yet, leave STYLEGUIDE.md's sections marked
     `<undecided>` rather than inventing values. Record both as `local-only`
     in the manifest (§5) — **neither file is ever exported upstream**
     (§3–§4): a project's voice and brand are its own identity, not a
     generic practice, and both live at the repo root rather than under
     `process/upstream/`, so the check-in tooling structurally never touches
     them.
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
     `GETTING_STARTED.md`. **The project comes first** (practice 38): if
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
     `tools/`. Add this repo's own generated-deliverable globs (practice 8)
     to the same file rather than a second one.
   - **Apply the harness adapter(s)** for whichever agent(s) will work this
     repo — see [templates/harness/README.md](templates/harness/README.md).
     E.g. Claude Code: `harness/claude-code/CLAUDE.md` → repo root (a
     one-line import of `AGENTS.md`), `harness/claude-code/settings.json` →
     `.claude/settings.json`, `harness/claude-code/hooks/session-start.sh` →
     `.claude/hooks/session-start.sh`, `harness/claude-code/hooks/stop-git-check.sh`
     → `.claude/hooks/stop-git-check.sh`. Codex reads `AGENTS.md` natively.
     Multiple adapters can be installed side by side.
   - `tools/doc_lint.py` → run it from `process/upstream/tools/` in place,
     or copy to the repo's tools dir if it needs local adaptation.
   - `tools/doc_sync.py` (practice 19) and `tools/model_audit.py`
     (practice 30) → copy to the repo's tools dir and wire their registries
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
4. **If the dependent repo is private** (and it usually is): create
   `process/scrub_blocklist.txt` — one regex per line (`#` comments), the
   repo's private vocabulary: project and product names, internal code
   words, identifier patterns, anything that must never appear in the
   public vendored tree. Err broad; false positives are a one-line review,
   false negatives are published.

   > **In plain terms.** This is the list of words your project can
   > never say in public — your product's real name, internal
   > nicknames, client names, anything you'd wince at seeing on a public
   > website. It's the only step in this whole document where the
   > assistant genuinely needs information only you have; everything
   > else it can do by reading your project's files. When your assistant
   > asks for this list, be generous — listing a word that turns out to
   > be harmless costs nothing, but a word you forget to list is the one
   > that could actually leak.

5. **Add the export-gate section** to the instructions file (the template
   includes it): the copy-back rule, the scrub rule, and the periodic
   check-in item (add one to `TODO.md`).
6. **Root hygiene — the layout rule.** The ONLY files an install may
   create at the dependent repo's root are the instantiated ones:
   `AGENTS.md` (plus a harness pointer such as `CLAUDE.md`), `MAP.md`,
   `TODO.md`, `GLOSSARY.md`, `GETTING_STARTED.md`, `VOICE.md`,
   `STYLEGUIDE.md`, `.gitignore`, and the README entry-block edit — plus
   `tools/bootstrap.sh`, `.github/workflows/bestpractice-docs.yml`, and
   `.github/pull_request_template.md`. Everything else that ships
   with BestPractice (INSTALL.md, PRACTICES.md, SETUP.md,
   GITHUB_ACTIONS.md, MOBILE.md, METHOD.md, GIT.md, templates/, tools/,
   deck/) exists ONLY under `process/upstream/` — never copy any of it to
   the root. A contributor browsing the root should see the project's own
   subject matter plus the instantiated files, and nothing about how
   BestPractice works internally. The audit enforces this: an
   upstream-internal doc found at the root fails unless the manifest
   records it as the repo's own document.
7. Run `python3 process/upstream/tools/practice_audit.py` — it must pass.
   Commit.

   > **In plain terms.** "The audit must pass" means an automatic check
   > has confirmed nothing looks wrong — no private words leaked, no
   > files ended up in the wrong place. Think of it as a spell-checker
   > for the rules themselves: green means safe to show you, red means
   > the assistant fixes it before you ever see the result. You should
   > never be shown a failing install.

8. **Disclose anything GitHub-specific** (practice 37): if any step above
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
   what's generic enough for the public BestPractice? Does anyone here
   have their own personal one — facts specific to them, like a commit
   identity or a personal shorthand?"* Most projects have neither yet, and
   that's a complete, valid answer — but don't let it be the end of the
   question. **This step's default follow-up is an active offer, not a
   passive one:** if the answer to either half is no, the very next thing
   this session says is *"Want me to set one up for you right now? It only
   takes a minute and needs nothing from you but a name."* — not a
   once-mentioned option left for the administrator to bring back up
   later. Nobody using BestPractice should have to already know
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
         {"level": "team", "name": "<their repo's name>", "path": "../<their repo's name>"}
       ]
     }
     ```
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
     --repo-url <the individual repo's URL>` rather than by hand: it
     instantiates
     [`templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template`](templates/harness/claude-code/hooks/individual-source-bootstrap.sh.template)
     at `.claude/hooks/precedent-individual-bootstrap.sh`, which delegates
     to the vendored, retry-capable
     [`tools/precedent_source_bootstrap.py`](tools/precedent_source_bootstrap.py)
     rather than a one-off hand-written clone.

     **That clone still needs the session to actually have git read access
     to the individual repo first, and on a hosted agent platform that
     access is not automatic just because the hook exists** — a session's
     git access is scoped per session, and a shell hook has no way to
     grant itself more of it. The consuming repo's own instructions file
     still needs the standing instruction
     [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)'s
     step 4 gives in full (`add_repo` for both sibling sources at the very
     start of every session, unconditionally) — but **read the next
     sentence even if you already know that instruction, because two
     independent adopters had it in place and still hit the gap it was
     supposed to close**: a
     `SessionStart` hook runs before the agent's own first turn starts, so
     telling the agent to call `add_repo` "before running any bootstrap
     script" cannot make that tool call precede a hook the harness has
     already started running — the instruction is necessary, not
     sufficient, and both incidents are recorded in
     [`practices/session-bootstrap.md`](practices/session-bootstrap.md)'s
     Story. What actually closes the residual race now lives in the
     engine rather than in prose: the hook above retries the clone with a
     bound instead of trying once, and `tools/precedent_resolve.py`'s own
     `load_config()` treats a still-missing individual config, on a remote
     session, as "try the bootstrap hook once more" rather than "no
     individual set." The `add_repo` instruction above is still required
     — the retry has nothing to succeed *into* without real repo access —
     it is just no longer asked to win the race by itself. See
     [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)'s
     step 4 for the worked pattern, including the access gate and exactly
     how it's closed now.
   - See [examples/practice-set/](examples/practice-set) for what an
     individual set's files actually look like, and
     [PRACTICE_ENGINE_PLAN.md](PRACTICE_ENGINE_PLAN.md)'s Vocabulary table
     for **universal source**, **team source**, and **individual source**
     as terms.
   - This step isn't only for a fresh install — see §2 step 3 for asking it
     again on an update, since a project's answer can change after this
     one-time question at install.

`.gitignore` / `.gitattributes` stanzas for generated artifacts (practice 8),
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

## 0. Installing directly onto the Precedent loader (new, 2026-09-03 — read the caveat before using)

> **In plain terms.** This is an alternative to §1 above, for a project
> that has never installed BestPractice before and wants to start on
> Precedent's newer three-source system (universal + team + individual)
> directly, rather than installing the older single-source model first and
> migrating later. Most projects today should still use §1 — this path is
> new and has not yet been rehearsed end to end against a real project
> (see the caveat at the end of this section). [SETUP.md](SETUP.md)'s
> guided conversation still uses §1 by default; ask for this path by name
> if you want it.

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
   to write `precedent_resolve.py`, `precedent_materialize.py`,
   `precedent_sync_views.py`, `build_views.py`, `precedent_show.py`,
   `precedent_paths.py`, `precedent_gate.py`, `split_practices.py`, and the
   vendoring tool itself into this repo's own `tools/`, plus a trimmed
   `routing_scope.json` and a tracked `tools/ENGINE_MANIFEST.json`
   recording the exact commit and a sha256 per file — see "Keep the
   vendored engine current (consumer repos)" under §2 for what that buys
   over a hand-copy, and how to refresh it later. Separately, copy
   `precedent_check.py` by hand (`checked_by: "tools/precedent_check.py"`
   claims are hollow without it) — it belongs to phase 4's enforced-checks
   channel, not this loader engine, so `precedent_vendor_engine.py` does
   not vendor it.
2. **Write `precedent.json`** at the repo root, naming the universal
   source (`level: "universal"`, `path` pointing at step 1's vendored
   copy) and, if the administrator answered yes to the team/individual
   question (step 3 below, same question §1 step 9 asks), a `team` source
   too — resolved live from a sibling clone, per
   [spec/MIGRATING_EXISTING_INSTALLS.md](spec/MIGRATING_EXISTING_INSTALLS.md)'s
   §3, **never vendored**. Never declare a `level: "individual"` entry —
   `tools/precedent_resolve.py` refuses this by name, and for good
   reason: naming a person's individual set in a repo anyone else on the
   team can read leaks its existence and location to them.
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
   `TODO.md`, `GLOSSARY.md`, `GETTING_STARTED.md`, `VOICE.md`,
   `STYLEGUIDE.md`, the README agent-entry block, the harness adapter(s),
   `tools/bootstrap.sh`, the Actions check, the PR template — unchanged
   by which install model this is. **Skip** `process/manifest.json` and
   `process/scrub_blocklist.txt` — those are §1's own bookkeeping for a
   model this path doesn't use.
6. **Run `python3 tools/precedent_sync_views.py`** — it resolves every
   source `precedent.json` declares and writes `AGENTS.md`'s generated
   block from the result (the resident block, the occasion index, the
   standing instruction). Confirm it prints `OK`, not `FAIL`, and that
   the reported resident-block size is inside its stated budget.
7. **Root-hygiene rule, adapted from §1**: nothing from Precedent lands
   loose at the repo root except the instantiated files above — the
   vendored engine and universal catalogue live under `tools/` and step
   1's tracked path, not scattered elsewhere.
8. Commit everything on a branch, same as §1.

**The caveat, stated plainly rather than left to be discovered.** This
section is new. Steps 1–2 and 6 (vendoring, `precedent.json`, and
`precedent_sync_views.py` actually producing a working `AGENTS.md`) were
dry-run tested in a scratch fixture while writing this section and do
work as described — but the section as a whole has not yet been rehearsed
end to end against a real repo, which
[spec/PHASE6_BRIEF.md](spec/PHASE6_BRIEF.md) names as still ahead. Two
things it deliberately does **not** cover, by design and not oversight:

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

## 2. Take an upstream update

*Knowing* an update exists is automated: the session-start bootstrap runs
`checkin.py fresh` (one `ls-remote`, notice-only). *Taking* it is the
deliberate procedure below.

> **In plain terms.** BestPractice itself keeps improving — other
> projects find better ways of doing things and publish them here. This
> section is how your project pulls those improvements in later,
> without losing anything you've customized. Nothing here needs you
> personally unless the assistant flags a conflict between an upstream
> change and something your project changed on purpose — in that case it
> will show you both versions and ask which should win, the same as
> reviewing any proposed edit.

1. Fetch the new upstream tree; diff it against the vendored copy at the
   **recorded base commit** (manifest `upstream.commit`).
2. Three-way merge per manifest entry: *old upstream* vs *new upstream* vs
   *your installed, adapted copy*. Apply upstream's changes to your installed
   files **through the adaptation** recorded in the entry's `notes` — don't
   clobber local adaptations.
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
   manifest entries — a short catch-up prompt ("take the BestPractice
   update") is enough to
   propagate a newly introduced template like this to every repo that
   already installed BestPractice before it existed.
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
6. **Keep the vendored engine current (consumer repos).** Steps 1–5 above
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
   From a sibling BestPractice clone:
   ```
   python3 tools/precedent_vendor_engine.py status  ../BestPractice   # drift? behind?
   python3 tools/precedent_vendor_engine.py refresh ../BestPractice   # pull, re-vendor, re-stamp
   ```
   `refresh` reads `kind` back out of `ENGINE_MANIFEST.json` itself — no
   `--kind` flag needed here, only at first `seed`. It pulls
   `precedent-beta-v01` specifically (not this clone's configured default
   branch — see
   [local/practices/merge-target-is-beta-branch.md](local/practices/merge-target-is-beta-branch.md)),
   and refuses to overwrite a hand-edited vendored file unless `--force` —
   this engine carries zero local variance by design, so a local edit is a
   signal to move the change upstream into BestPractice instead. After a
   refresh, re-run `python3 tools/precedent_sync_views.py --repo . --check`
   to confirm the freshly refreshed engine still produces the same
   materialized tree and `AGENTS.md` (or, if the refresh changed loader
   behavior, review the diff before committing). A repo installed before
   this mechanism existed (a hand-copy with no `ENGINE_MANIFEST.json`) has
   nothing to refresh from yet — vendor it for the first time the same way
   §0 step 1 does, `--kind consumer`, from a sibling BestPractice clone
   instead of BestPractice's own checkout.

## 3. (Optional) Give back an improvement — the export gate

> **In plain terms.** This whole section, and §4 after it, are entirely
> **optional** — nothing about using BestPractice requires your project to
> give anything back. They exist for when your project discovers a *better
> way of working* — not a fact about your business, just a sharper habit
> (a clearer checklist, a smarter automatic check) — that could help every
> other project using BestPractice, the same way yours benefited from
> lessons other projects learned first. Think of it as reporting a better
> recipe back to a shared cookbook, with your kitchen's specific
> ingredients removed first. If your project chooses to do this, the
> drafting happens automatically, on your project's own private working
> copy, as part of the assistant's ordinary work; it doesn't leave your
> project until the check-in step below (§4), which does need your
> sign-off.

For projects that choose to give back, run this check **before any thread
ends / before any merge to the default branch** (it is step 0b of the merge
runbook, beside the capture gate). Projects that don't intend to contribute
upstream can skip this section entirely:

> Did this thread improve a *generic* practice — a new convention, a
> sharpened runbook rule, a better audit, a template fix?

`VOICE.md` and `STYLEGUIDE.md` never answer yes to this question, even
when a thread rewrites them substantially: the *files* are project/company
identity, not practice, so their content stays local by category, not by
judgment call. (The default ruleset the `VOICE.md.template` *ships with*
can still improve — that's a direct edit to the template in this repo,
made the way any of this repo's own content is edited, not something
inferred from a dependent repo's customized copy.)

If yes, in the **same branch**:

1. Write the **abstracted** form into the right file under
   `process/upstream/` — patterns and lessons only, subject matter stripped
   (see practice 15). Abstraction is authorship, not copying: rewrite the
   incident generically, keep the lesson.
2. Update the touched manifest entries (`notes`, status) and run
   `python3 process/upstream/tools/practice_audit.py` — the scrub must pass.
3. If the *installed* file changed but you are not exporting yet, flip its
   manifest entry to `"diverged"` — the audit will keep reminding until the
   export happens or the baseline is deliberately updated.

## 4. (Optional) Periodic check-in — propose your improvements upstream

> **In plain terms.** Like §3, this whole section is **optional** — skip
> it if your project would rather keep its improvements to itself. For
> projects that do want to give back, this is where §3's accumulated
> improvements actually leave your project: on a schedule, they get
> bundled up and offered to the public BestPractice project as a formal
> proposal — a pull request — so that everyone else using BestPractice can
> learn from what your team figured out. **This is the step where a human
> reviewer other than you looks at what's being shared**, as a second
> check that nothing private slipped through the automatic scrub. If
> you're the one with authority to approve changes on your own project,
> your part is: skim what the assistant proposes to share (it will
> summarize it in plain language), and either approve it or ask for
> something to be reworded or left out. Nothing leaves your project
> without a PR existing first, and a PR is just a draft sitting on GitHub
> until someone approves it.

**Session scope note (hosted agent platforms).** Repo access is typically
fixed when a session is created: a session opened on the dependent repo
alone can usually *read* the public BestPractice repo (clone, fetch, diff)
but **cannot push branches or open PRs there** — writes fail even though
the day-to-day export loop (§3) works fine, because that loop is purely
local commits. So: **open check-in sessions with BOTH repos selected at
creation.** Everything else can be prepared, scrubbed, and audited in
ordinary single-repo sessions; only this step needs the dual-repo session.

For projects that choose to give back: on a schedule (a recurring
`TODO.md` item), in a session with access to the BestPractice repo.
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
3. Commit in the clone on a branch and open a PR against BestPractice.
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

## 5. The manifest schema (`process/manifest.json`)

> **In plain terms.** The manifest is a receipt — a list of exactly what
> was installed, where each piece landed in your project, and whether
> it still matches what was originally installed or has since been
> customized. You will rarely need to open this file yourself; it exists
> so the assistant (and the automatic check in §6) never has to guess
> "did we already install this?" or "has this drifted from the
> original?" — the answer is always written down rather than
> re-derived.

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
      "upstream_path": "templates/VOICE.md.template",
      "local_path": "VOICE.md",
      "granularity": "file",
      "status": "local-only",
      "notes": "kept the shipped default ruleset as-is at install; never exported (INSTALL.md §3) — a project's voice is its own identity, not a generic practice"
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

## 6. The audit (`tools/practice_audit.py`)

> **In plain terms.** This is the automatic check that runs before
> almost every step above. It looks for two things: private words that
> shouldn't be public (§1 step 4's list), and files that were changed
> without anyone recording why. It's a machine doing the checking — not
> a person reading every line — which is precisely why it can run every
> single time without becoming a chore for anyone. If you ever hear
> "the audit failed," it means the assistant caught a problem itself,
> before it could reach you or the public repo; that is the system
> working as intended, not a crisis.

```
python3 process/upstream/tools/practice_audit.py                    # full check (gate)
python3 process/upstream/tools/practice_audit.py --update-baseline  # re-record hashes
```

Checks, in order — any FAIL exits non-zero:

1. **Scrub** (practice 15): every text file under `process/upstream/`
   scanned against `process/scrub_blocklist.txt`. Any hit → FAIL. (Skipped,
   with a notice, if no blocklist exists — a public dependent repo.)
2. **Drift** (practice 7): for each `file`-granularity entry, current hash
   vs `local_sha256`. Changed while `status: "synced"` → FAIL (export it or
   flip to `diverged`). `diverged` entries are listed as pending export,
   not failed.
3. **Integrity:** manifest paths exist; `section_marker`s found (warn);
   `local-only` entries have notes.

## 7. Practice packs (domain layers)

> **In plain terms.** Some rules are too specific to your industry or
> workflow to belong in the public BestPractice project, but too general
> to belong only to your one project either — think a compliance
> procedure that any project in your regulated field would need, not
> just yours. A "pack" is a separate, smaller rulebook for exactly that
> middle ground. Most projects never need one; if yours has a body of
> rules that would make sense handed to a sister project in the same
> field but not to an unrelated one, that's the sign a pack belongs
> here, and it's worth raising with whoever oversees your process
> setup.

A repo can install additional practice layers beside this upstream —
**packs** (practice 23): domain-scoped practice sets (a compliance regime, a
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

## For approvers: your checklist

Everything above is written for the assistant doing the work. Stripped
down to just the moments a non-technical approver actually needs to act
on, across the whole lifecycle:

- **At install (§1):** answer two questions — what the project is about,
  and what private names/words must never go public. Then look at what
  the assistant built and either approve it or ask for changes. You'll
  also be shown `VOICE.md`'s default writing-style rules and asked
  whether to change them, and asked whether a brand guideline exists to
  fill in `STYLEGUIDE.md` from — both stay entirely local to your project.
  You'll also be asked whether your team, or you personally, already have
  a practices repo of your own to wire in (§1 step 9) — most projects
  don't yet, and saying so is a complete answer. See the
  [guided install](SETUP.md) for the conversational version of this.
- **At every check-in (§4), only if your project gives back at all
  (§3–§4 are both optional):** review the plain-language summary of what's
  being proposed back to the public BestPractice project, and approve,
  adjust, or hold it back. This is the one recurring moment where content
  leaves your project's boundary, so it's the one worth actually reading
  rather than rubber-stamping.
- **When the audit flags something (§6):** if your assistant tells you an
  automatic check failed, that's it catching a problem before it reached
  you — not something you need to fix by hand. Ask it to explain what
  failed and fix it; you're confirming the fix makes sense, not debugging
  code yourself.
- **Everywhere else** (taking updates in §2, the day-to-day export gate in
  §3, the manifest and audit internals in §5–§6): these run inside your
  assistant's normal work and don't need your sign-off unless it
  specifically flags a conflict or a judgment call for you.
