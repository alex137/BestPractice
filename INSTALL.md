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
drift and proprietary leakage loud instead of silent.

## 1. Install into a dependent repo

> **In plain terms.** This is the one-time setup. An assistant copies
> BestPractice's files into your project, then rewrites a handful of
> them to describe *your* project specifically — a map of where things
> live, a to-do list, a page that welcomes new members. Nothing from
> this step becomes visible to anyone but you until you (or whoever has
> authority to make it official) approve it — see step 7 below and the [guided
> install](SETUP.md), which walks an administrator through this exact
> process in conversation rather than as a technical checklist. The one
> decision only you can make: **which private names and code words must
> never leak into a public file** (step 4) — your assistant cannot guess
> your project's secrets, so it will ask you directly.

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
     `GETTING_STARTED.md`.
   - `templates/bootstrap.sh` → `tools/bootstrap.sh` (add the repo's own
     setup needs).
   - **Apply the harness adapter(s)** for whichever agent(s) will work this
     repo — see [templates/harness/README.md](templates/harness/README.md).
     E.g. Claude Code: `harness/claude-code/CLAUDE.md` → repo root (a
     one-line import of `AGENTS.md`), `harness/claude-code/settings.json` →
     `.claude/settings.json`, `harness/claude-code/hooks/session-start.sh` →
     `.claude/hooks/session-start.sh`. Codex reads `AGENTS.md` natively.
     Multiple adapters can be installed side by side.
   - `tools/doc_lint.py` → run it from `process/upstream/tools/` in place,
     or copy to the repo's tools dir if it needs local adaptation.
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
   `TODO.md`, `GLOSSARY.md`, `GETTING_STARTED.md`, and the README
   entry-block edit — plus `tools/bootstrap.sh` and
   `.github/workflows/bestpractice-docs.yml`. Everything else that ships
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

`.gitignore` / `.gitattributes` stanzas for generated artifacts (practice 8):

```gitignore
# generated deliverables — only shipped artifacts get force-added
<your-build-output-glob>
```

```gitattributes
*.docx binary
*.pdf binary
<generated-md-glob> binary   # stop git text-merging generated files
```

## 2. Take an upstream update

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
   or the Actions check
   ([templates/github-actions/](templates/github-actions/README.md)).
   Instantiate them exactly as §1 describes and add manifest entries.
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
   the vendored tree**, and writes the landed hash into `upstream.commit`.
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
      "upstream_path": "templates/CLAUDE.md.template",
      "local_path": "CLAUDE.md",
      "granularity": "section",
      "section_marker": "## Merge runbook",
      "status": "synced",
      "notes": "file classes adapted to this repo"
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
  the assistant built and either approve it or ask for changes. See the
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
