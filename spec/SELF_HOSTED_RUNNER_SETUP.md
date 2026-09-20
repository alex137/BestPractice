---
title:         Setting up a self-hosted GitHub Actions runner on a RunCloud-managed Linux server
kind:          procedure
status:        current
opened:        2026-09-20
closed:        null
superseded_by: null
supersedes:    []
audience:      contributor
summary:       Step-by-step mechanics for registering a self-hosted GitHub Actions runner on a Linux server managed through RunCloud, for CI_MINUTES_PLAN.md's item 6 pilot -- not yet authorized to run against any specific repo.
---
# Setting up a self-hosted GitHub Actions runner on a RunCloud-managed Linux server

**This is mechanics only.** The decision this would carry out --
whether to run the item 6 pilot, and on which repos -- is still open at
[todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md](../todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md).
Writing this guide does not answer that; running any step below against a
real repo does. **Never point this at BestPractice's own
[deep-check.yml](../.github/workflows/deep-check.yml)** -- that specific
case already has its own analysis and a harder bar in
[spec/DEEP_CHECK_SELF_HOSTED_RUNNER.md](DEEP_CHECK_SELF_HOSTED_RUNNER.md),
because that workflow runs on a public repo. This guide is scoped to
[spec/CI_MINUTES_PLAN.md](CI_MINUTES_PLAN.md) item 6: Morgan's own private,
single-author repos, where that risk does not apply.

## What a self-hosted runner actually is

A GitHub-hosted runner is a fresh virtual machine (VM) GitHub spins up per
job and tears down afterward. A self-hosted runner is a long-lived agent
process you install on a machine you already control -- here, a Linux
server RunCloud manages -- that polls GitHub outbound for work. **No inbound
port needs to open for it**; it reaches out to GitHub, never the other way
around. The only workflow-file change is `runs-on: [self-hosted, <label>]`
in place of `runs-on: ubuntu-latest`.

## Before touching anything

- **Confirm which repo this is for, and that it is private.** Register the
  runner at the repository level (Settings → Actions → Runners), not the
  organization level -- narrower blast radius if the box is ever
  compromised.
- **Never combine this with a `pull_request:` trigger from forks.** A
  self-hosted runner executing arbitrary workflow code from an untrusted
  fork is the exact combination GitHub's own hardening guidance warns
  against. A private, single-author repo with no outside contributors does
  not have this exposure today -- keep it that way, and re-check this
  before ever accepting an outside contribution on a repo that uses this
  runner.
- **Pick a dedicated box, not daily-driver hardware.** Per
  [spec/DEEP_CHECK_SELF_HOSTED_RUNNER.md](DEEP_CHECK_SELF_HOSTED_RUNNER.md)'s
  hosting-options section, a small dedicated Linux server (what RunCloud
  manages) is the right shape here -- never a home machine or a device that
  also does other things.

## Step 1 — get the server into RunCloud

If the server is not already connected to RunCloud: create the server
record in the RunCloud dashboard, then run RunCloud's own connect script
over SSH (Secure Shell) as `root` on the box (RunCloud's dashboard gives
you this exact command when you add a server -- copy it from there rather
than from memory, since it is versioned and can change). This installs
RunCloud's agent, which manages Nginx and web applications on top of the
server; it does not take away your own root SSH access, which the rest of
this guide uses directly.

## Step 2 — create a dedicated system user for the runner

In RunCloud, create a **new System User** just for the runner (do not reuse
a system user that already serves a web application on the same box). This
keeps the runner's filesystem access separate from anything else RunCloud
is running there, so a problem in one does not reach the other.

## Step 3 — install prerequisites over SSH

SSH into the server as (or `su` to) the system user you just created, and
install whatever the target repo's jobs actually need -- at minimum:

```bash
sudo apt update
sudo apt install -y curl tar
```

Add the language runtime(s) the workflow uses (for example, `python3` and
`pip` for a Python-based lint job, or Node via a version manager for a
Node-based one). Match what the job's own `setup-python`/`setup-node`
step currently installs on the GitHub-hosted runner -- a self-hosted runner
does not get that step's version-provisioning for free the way a fresh
GitHub VM does, so the box needs it pre-installed.

## Step 4 — register the runner with GitHub

In the target repo: **Settings → Actions → Runners → New self-hosted
runner**, choose Linux, and copy the commands GitHub shows there. They
look like this (GitHub generates the actual token and URL per-repo, and
the token is short-lived -- **run the `config.sh` step within about an
hour of copying it**, or generate a fresh one):

```bash
mkdir actions-runner && cd actions-runner
curl -o actions-runner.tar.gz -L <URL GitHub gives you>
tar xzf actions-runner.tar.gz
./config.sh --url https://github.com/<owner>/<repo> --token <TOKEN>
```

When `config.sh` asks for runner name and labels, give it a label that
names the box and its purpose (for example, `self-hosted-runcloud`) rather
than accepting only the defaults -- the workflow file will target this
label explicitly.

## Step 5 — run it as a persistent service

Two ways to keep the runner alive across reboots and crashes; pick one.

**Option A — GitHub's own systemd service (recommended).** Since RunCloud
gives you full root SSH on the underlying server, systemd is available:

```bash
sudo ./svc.sh install
sudo ./svc.sh start
```

This registers the runner as a systemd service that restarts automatically
and starts on boot. Check it with `sudo ./svc.sh status`.

**Option B — RunCloud's Supervisor.** RunCloud's own Supervisor feature (on
the server's dashboard) keeps an arbitrary long-running command alive and
restarts it if it dies, without touching systemd directly. Point it at
`/path/to/actions-runner/run.sh` if you would rather manage the runner
through RunCloud's own UI alongside your web applications. Do not run both
options at once against the same runner directory.

## Step 6 — point the workflow at it

In the target repo's workflow file, change the specific job(s) you decided
to migrate -- per item 6, start with the highest-volume, lowest-sensitivity
ones, not a blanket switch:

```yaml
runs-on: [self-hosted, self-hosted-runcloud]
```

Leave every other job on `runs-on: ubuntu-latest` unless there's a
specific reason to move it too. This is a per-job decision, not an
all-or-nothing one.

## Step 7 — verify

Push a commit that triggers the migrated job and watch it in the repo's
Actions tab -- it should show as running on your runner's name, not on a
GitHub-hosted one. In Settings → Actions → Runners, the runner should show
**Idle** between jobs and **Active** while one runs. If it never picks up
the job, check `sudo ./svc.sh status` (or the Supervisor process, for
option B) on the server, and confirm the label in the workflow file matches
the label the runner registered with.

## Ongoing care

- **Patch the box.** GitHub's runner binary self-updates by default; the
  underlying OS does not. Keep it patched the way you would any server you
  are responsible for (`apt update && apt upgrade`, or unattended-upgrades).
- **A hung or offline runner is now your problem, not GitHub's.** A job
  that never picks up because the runner process died is invisible to
  GitHub's own status checks; the Runners page under Settings → Actions is
  the place to notice it.
- **Rotate the registration token's usefulness.** The token used in Step 4
  is single-use for setup and expires quickly on its own; there's nothing
  to rotate afterward, but if you ever need to re-register (new box, moved
  runner), generate a fresh token rather than reusing an old one.

## Rolling it back

1. In the workflow file, change `runs-on: [self-hosted, ...]` back to
   `runs-on: ubuntu-latest`.
2. On the server: `sudo ./svc.sh stop && sudo ./svc.sh uninstall` (or stop
   the Supervisor process for option B).
3. In the repo's Settings → Actions → Runners, remove the runner entry so
   it stops appearing as a registered target.

## What this does not decide

This procedure does not itself authorize running the pilot on any repo --
that answer, and the billing-ceiling check that goes with it, are still
open at
[todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md](../todo/todo-2026-09-16-revisit-ci-minutes-items-6-7.md).
It also does not apply to BestPractice's own workflows: see
[spec/DEEP_CHECK_SELF_HOSTED_RUNNER.md](DEEP_CHECK_SELF_HOSTED_RUNNER.md)
for why that case needs a separate, harder call.
