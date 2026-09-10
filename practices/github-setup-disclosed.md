---
slug:        github-setup-disclosed
title:       GitHub-specific setup is disclosed where the reader will actually see it
tier:        on-demand
severity:    default
applies_to:  [".github/**", "templates/github-actions/**"]
occasion:    "an install step adds something GitHub-specific, or a first install finishes"
gates:       []
index_clause: "disclose GitHub setup where its people read; offer owner settings at install"
checked_by:  "tools/precedent_check.py"
defines:     []
status:      active
in_force_at: null
supersedes:  []
overrides:   null
added:       null
approved_by: "BestPractice (pre-fork)"
source_practice_number: 37
---
## Rule
Whenever an install step adds something GitHub-specific that a
project's own people need to know about — a required Actions workflow, a
repository secret, a branch-protection or required-check setting, a
permission grant — the fact, and the exact detail needed to act on it (what
it's called, what it does, any manual click to enable it), is written into
the document that project's own people actually read, not left only inside
Precedent's internal install playbook. For a dependent repo, that
document is [templates/GETTING_STARTED.md](../templates/GETTING_STARTED.md)'s
administrator section — [INSTALL.md](../INSTALL.md) records the installation
mechanics; GETTING_STARTED.md records the consequence for this project's
administrator.

**A first install also offers the settings only the owner can click** —
private unless it is meant to be public, a developer token as a repository
secret, a default branch named `main`, *Allow GitHub Actions to create and
approve pull requests*. Briefly, as suggestions, in the reply and that
section.

## Detail
**Why the closing reply and the file, when one would do.** The reply is what
gets acted on; the file is what survives the conversation. An administrator
who is told once, in chat, and never again has been informed and not
equipped — and a line written only into a file during an install is a line
nobody was looking at when it was written. Neither substitutes for the
other, so both are done.

**Said weakly, and kept short.** These are suggestions that avoid a later
surprise, not a gate an install fails — an install that leans on them
teaches its reader that the GitHub plumbing is the point, which it is not.
The technical path gets a sentence on the token and leaves the rest to a
developer; the non-technical path gets the steps written out, and an offer
of more specific instructions on any of them.

**The owner-only settings, and why each is standing rather than
discovered.** Every one needs a person with admin rights clicking in
GitHub's own settings, so no install can do them and no later session can
notice they were skipped:

1. **The repository is private**, unless it is meant to be public. Decided
   at creation time, changed afterwards only at **Settings → General →
   Danger Zone** — and by then whatever was pushed has been public for as
   long as it took to notice.
2. **A developer token, stored in the repository as a secret**
   (**Settings → Secrets and variables → Actions → New repository secret**).
   The credential a workflow gets by default is scoped to that one run;
   pushing a branch or opening a pull request on the project's behalf needs
   a key of its own. Distinct from the environment-level, read-only
   `PRECEDENT_GIT_TOKEN` that clones practice sets
   ([INSTALL.md](../INSTALL.md) §8) — name which one you mean.
3. **A default branch named `main`** (**Settings → General → Default
   branch**). The shipped workflow template names `main` as a literal
   string, so a repository that calls it anything else runs no check on
   merges while looking, from the outside, exactly like one that passes.
4. **Allow GitHub Actions to create and approve pull requests**
   (**Settings → Actions → General → Workflow permissions**). Anything that
   opens a pull request for the project fails at the attempt without it.

*(Click-paths as of 2026-09-10.)* The procedure is
[INSTALL.md](../INSTALL.md) §1 step 10 and §0 step 9; the plain-language
step-by-step version an installing session actually says is
[SETUP.md](../SETUP.md) step 7.

## Why
An install can turn on a GitHub Actions workflow and record that
fact faithfully in this repo's own technical install log — a document a
project's administrator has no ordinary reason to reopen. Nothing points
them at it from the page they'll actually return to, so a check that needs
one click to enable can sit off, silently, until someone happens to look at
the Actions tab.

## Story
**A check that needed one click sat off, silently.** An install turned on a
hosted-automation workflow and recorded that fact faithfully -- in this
repo's own technical install log, which is a document a project's
administrator has no ordinary reason to ever reopen. Nothing pointed them at
it from the page they actually return to, so the setting stayed unset until
somebody happened to look at the automation tab.

The failure is not that the fact went unrecorded. It was recorded,
accurately, in a reasonable place. The failure is that **recording and
disclosing are different acts with different audiences**, and doing the
first well makes the second feel done.

That is why the rule names the destination rather than the content: the
document that project's own people read, not the install log, and with the
exact detail needed to act -- what it is called, what it does, and any
manual click required. A disclosure a reader cannot act on without asking a
follow-up question has the same effect as no disclosure. See also
[decisions/2026-09-03-setup-getting-started-disclosure-gap.md](../decisions/2026-09-03-setup-getting-started-disclosure-gap.md).

## Install
[templates/GETTING_STARTED.md](../templates/GETTING_STARTED.md)'s
administrator section carries a standing note for "automatic checks
installed for this project," naming each workflow and what it does. Any
future GitHub-specific addition — a required secret, a new required check —
gets a line there too, added by whichever install step introduces it.

**What the check reads, and why it reads two files.** `github-setup-disclosed`
in [tools/precedent_check.py](../tools/precedent_check.py) fires when a
change adds a `.github/workflows/*.yml` file whose filename appears in
neither the repo's root `GETTING_STARTED.md` nor its root
`GITHUB_ACTIONS.md`. Until 2026-09-10 it read only the second, which put
this practice, its check, and [INSTALL.md](../INSTALL.md) §1 step 6's
root-hygiene list in a three-way contradiction: the Rule named
GETTING_STARTED.md, the check demanded GITHUB_ACTIONS.md, and root hygiene
forbade GITHUB_ACTIONS.md at a dependent repo's root. A repo that followed
the Rule failed the check; a repo that satisfied the check tripped root
hygiene. The Rule won, because it is the one of the three that carries the
reasoning. GITHUB_ACTIONS.md is still accepted for a repo that has its own
— this repo, being the upstream, is exactly that case.

The owner-only settings above are the first-install case of the same rule,
and they ship as procedure rather than as a thing to remember:
[INSTALL.md](../INSTALL.md) §1 step 10 (and §0 step 9) keeps the technical
path to a short paragraph, [SETUP.md](../SETUP.md) step 7 gives the guided
conversation's plain-language steps, and
[templates/GETTING_STARTED.md](../templates/GETTING_STARTED.md) ships a
"Settings Only You Can Turn On" section so the instantiated file carries
them from the moment it is written.
