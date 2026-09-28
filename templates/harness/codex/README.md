# Codex adapter

Codex reads **`AGENTS.md` natively** — no pointer file needed; instantiate
[../../AGENTS.md.template](../../AGENTS.md.template) at the repo root and the
instructions load automatically.

**Codex has hooks, and this adapter uses them since 2026-09-28.** Until then
this page said Codex had no hook mechanism at all, and every hook row in
[../LEDGER.md](../LEDGER.md) and [../PARALLELS.md](../PARALLELS.md) recorded
no transfer on that ground. It was wrong: Codex reads `hooks.json` with the
same event names, the same payload fields and the same deny that Claude
Code uses. [../PARALLELS.md](../PARALLELS.md) lists the sources and what was
checked.

Wiring the rest:

- **Hooks: [hooks.json](hooks.json).** Copy it to `.codex/hooks.json` in the
  repository (or `~/.codex/hooks.json` for every repository you open). It
  wires the same scripts [../claude-code/settings.json](../claude-code/settings.json)
  wires for Claude Code:
  - `SessionStart` runs `bash tools/bootstrap.sh`;
  - `PreToolUse` on `Bash` runs `.claude/hooks/doc-lint-gate.sh` (refuses a
    `git commit` whose staged Markdown fails the lint) and
    `.claude/hooks/push-check-gate.sh` (refuses a `git push` whose checks
    fail);
  - `Stop` runs `.claude/hooks/stop-git-check.sh` (refuses to end a turn
    with uncommitted, untracked or unpushed work).

  Four things to know before relying on it:
  1. **The scripts come from the claude-code adapter.** Install its
     `hooks/` directory as `.claude/hooks/` too, even in a repository no one
     opens in Claude Code. The scripts are plain shell; only their folder
     name says Claude.
  2. **Codex runs a project hook only after it is trusted.** Until someone
     trusts these, Codex lists them and runs none of them. How Codex asks
     for that was not checked here; its source keeps a trusted hash per hook
     and skips any hook without one.
  3. **Keep the file to two top-level keys**, `description` and `hooks`.
     Codex parses it strictly, so a `_comment` key (the convention every
     `settings.json` here uses) makes it reject the whole file with only a
     warning.
  4. **Not yet seen to fire in a live Codex session.** The file was written
     against the openai/codex source on 2026-09-28 and is checked by
     `check_codex_hooks_template_runs_the_claude_gates` in
     [tools/verify_harness.py](../../../tools/verify_harness.py), which feeds
     the scripts the payload Codex's source says it sends. A real run is
     still the proof. On a Codex release older than the one that made hooks
     stable, the feature was behind a `codex_hooks` flag in
     `~/.codex/config.toml` (reported, not re-checked here).
- **Bootstrap:** the `SessionStart` hook above is the hard guarantee for
  the CLI. Codex cloud environments also run a setup script configured in
  the environment settings: point it at `bash tools/bootstrap.sh`. Without
  either, the AGENTS.md template's "run `bash tools/bootstrap.sh` at
  session start" line is all there is, a soft guarantee; see the
  enforcement caveat in [../README.md](../README.md).
- **Pre-approved commands:** Codex has an exec-policy language whose
  `prefix_rule` can allow a command prefix, but where a repository's own
  rules file loads from was not checked, so there is no template. Sessions
  will prompt, or run under the sandbox policy configured for the
  environment. Nothing in the practice layer depends on the allowlist; it
  only reduces prompts.
- **Audits:** unchanged — `python3 process/upstream/tools/practice_audit.py`
  and `python3 process/upstream/tools/doc_lint.py` are plain Python and run
  identically here.
- **Commit identity and signing:** `tools/bootstrap.sh` calls
  `.claude/hooks/commit-identity.sh` automatically (since 2026-09-16), so
  this runs wherever the Bootstrap step above runs — hard with the hook or
  a cloud setup script, soft with the instructions-file directive alone. See
  [../LEDGER.md](../LEDGER.md) for the history of this gap; if your
  environment signs commits by default in a way that collides with a
  human-only authorship policy, see
  [CLOUD_SETUP.md](<upstream-docs>/documentation/CLOUD_SETUP.md#when-the-containers-own-signing-collides-with-a-human-only-policy).

## The Markdown Check Needs the Hook File

**Read this before assuming your documents are checked.** On 2026-09-21
Precedent's Markdown lint left GitHub Actions entirely and was replaced by
`.claude/hooks/doc-lint-gate.sh`, which refuses a `git commit` whose staged
Markdown fails [doc_lint.py](../../../tools/doc_lint.py). With
[hooks.json](hooks.json) installed and trusted, Codex runs that same gate.

**Without it, nothing checks your Markdown before it reaches a shared
branch** — not the hook, and not CI, because the workflow the hook
replaced is retired and deleted. So if you do not install the hook file,
or cannot yet trust it, do both of these. Not one:

1. **Run it yourself before every commit:**
   `python3 tools/doc_lint.py <the markdown you touched>`. Nothing will
   remind you.
2. **Put a GitHub check back**, because step 1 is a habit and a habit is
   what the hook exists to replace. Copy
   [../../github-actions/light-check.yml.template](../../github-actions/light-check.yml.template)
   to `.github/workflows/light-check.yml`, set its `CUSTOMIZE` command to
   `python3 tools/doc_lint.py` and its `paths:` to `"**/*.md"`, then enable
   Actions for the repository at **Settings → Actions**.

**Doing only the first is the arrangement that failed upstream.** "A
session is supposed to run the check before committing" was written down
and followed for months, and still nothing refused a commit that skipped
it — which was only ever safe because CI was behind it.

**What this harness still does not get that Claude Code does, mechanism by
mechanism: [../PARALLELS.md](../PARALLELS.md).** The Markdown gate, the
push check and the turn-end git check now transfer. What does not yet:
the path-triggered practice loading (Codex edits files through a patch, not
a file path), the reply gate and reply check, the freshness guard's
per-tool-call mode, the merge check, and the private individual source —
each with the reason, and whether the gap is wiring or capability.
