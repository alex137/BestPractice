# Gemini CLI adapter

`GEMINI.md` is the file Gemini CLI auto-loads at the repo root; it points at
`AGENTS.md` (harness-neutral) and directs a session to run
`bash tools/bootstrap.sh` before other work. See [GEMINI.md](GEMINI.md) for
the file itself — this page covers the parts a person, not the agent, needs
to know.

**Gemini CLI has hooks.** Until 2026-09-28 this page said it had no hook
mechanism, and every hook row in [../LEDGER.md](../LEDGER.md) and
[../PARALLELS.md](../PARALLELS.md) recorded no transfer on that ground. It
has `SessionStart`, `BeforeTool`, `AfterAgent` and more, configured in
`.gemini/settings.json`
([Gemini CLI hooks documentation](https://github.com/google-gemini/gemini-cli/blob/main/docs/hooks/index.md),
read 2026-09-28). What it does not share with Claude Code is the deny: a
`BeforeTool` hook refuses a call with exit 2 or a top-level
`{"decision": "deny"}`, and a hook's stdout must be JSON and nothing else.
Claude Code's gate scripts print a different JSON shape, so wired as-is
they would let everything through.

- **Hooks: [settings.json](settings.json).** Merge its `hooks` key into
  `.gemini/settings.json`. It wires two hooks, both run from
  `$GEMINI_PROJECT_DIR`. `SessionStart` runs `bash tools/bootstrap.sh`,
  with its output sent to stderr to keep stdout clean. `AfterAgent` runs
  `.claude/hooks/stop-git-check.sh` (install the claude-code adapter's
  `hooks/` directory as `.claude/hooks/` for it): on exit 2 Gemini CLI
  retries the turn with the script's reasons as the prompt, which is what
  Claude Code's `Stop` does with them. Gemini CLI fingerprints project
  hooks and warns before running a new or changed one, so expect that
  warning the first time. Written from the documented shape and checked by
  `check_gemini_settings_template_keeps_stdout_clean` in
  [tools/verify_harness.py](../../../tools/verify_harness.py); **not yet
  seen to fire in a live Gemini CLI session**.
- **The gates are the next step, not a limit.** The Markdown gate and the
  push check need a small shim each: run the Claude Code script, and turn
  its `permissionDecision: "deny"` output into exit 2 with the reason on
  stderr. Until those land, the manual steps below stand.
- **Bootstrap:** the `SessionStart` hook above makes this a hard guarantee
  where it is installed. Without it, the instructions-file directive is a
  soft one (the agent has to actually read and follow it) — see the
  enforcement caveat in [../README.md](../README.md). Gemini CLI can be
  configured to read `AGENTS.md` directly: the setting is
  `context.fileName` in current documentation (read 2026-09-28), and
  `contextFileName` in older versions. Prefer that and drop `GEMINI.md` if
  your version supports it.
- **Pre-approved commands:** `tools.allowed` in `settings.json` lists tools
  that skip the confirmation prompt, shell prefixes included (for example
  `run_shell_command(git)`). The template does not fill it in yet. Nothing
  in the practice layer depends on the allowlist; it only reduces prompts.
- **Audits:** unchanged — `python3 process/upstream/tools/practice_audit.py`
  and `python3 process/upstream/tools/doc_lint.py` are plain Python and run
  identically here.
- **Commit identity and signing:** `tools/bootstrap.sh` calls
  `.claude/hooks/commit-identity.sh` automatically (since 2026-09-16), so
  this runs wherever the Bootstrap step above actually runs — hard with the
  `SessionStart` hook installed, soft with the directive alone. See
  [../LEDGER.md](../LEDGER.md) for the history of this gap; if your
  environment signs commits by default in a way that collides with a
  human-only authorship policy, see
  [CLOUD_SETUP.md](../../../documentation/CLOUD_SETUP.md#when-the-containers-own-signing-collides-with-a-human-only-policy).

## The Markdown Check Does Not Run Here Yet

**Read this before assuming your documents are checked.** On 2026-09-21
Precedent's Markdown lint left GitHub Actions entirely and was replaced by
`.claude/hooks/doc-lint-gate.sh`, which refuses a `git commit` whose staged
Markdown fails [doc_lint.py](../../../tools/doc_lint.py). Gemini CLI could
run it from a `BeforeTool` hook, but not unchanged (see above), and no shim
ships yet.

**So on this adapter, nothing checks your Markdown before it reaches a
shared branch** — not the hook, and not CI, because the workflow the hook
replaced is retired and deleted. Every earlier adapter gap cost you a
guard you never had; this one costs you a guard that used to be there.

Do both of these. Not one:

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

**What this harness does not get that Claude Code does, mechanism by
mechanism: [../PARALLELS.md](../PARALLELS.md).** The Markdown gate above
is one row of it. The others include the path-triggered practice loading,
the reply gate and the private individual source — each with the parallel
where one exists, and whether what is missing is a wiring or a capability.
