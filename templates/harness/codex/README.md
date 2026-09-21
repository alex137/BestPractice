# Codex adapter

Codex reads **`AGENTS.md` natively** — no pointer file needed; instantiate
[../../AGENTS.md.template](../../AGENTS.md.template) at the repo root and the
instructions load automatically.

Wiring the rest:

- **Bootstrap:** Codex cloud environments support a setup/maintenance script
  configured in the environment settings — point it at `bash
  tools/bootstrap.sh`. For local Codex CLI use, rely on the instructions-file
  directive (the AGENTS.md template includes a "run `bash tools/bootstrap.sh`
  at session start" line) — a soft guarantee; see the enforcement caveat in
  [../README.md](../README.md).
- **Pre-approved commands:** no allowlist equivalent — sessions will prompt
  (or run under the sandbox policy configured for the environment). Nothing
  in the practice layer depends on the allowlist; it only reduces prompts.
- **Audits:** unchanged — `python3 process/upstream/tools/practice_audit.py`
  and `python3 process/upstream/tools/doc_lint.py` are plain Python and run
  identically here.
- **Commit identity and signing:** `tools/bootstrap.sh` calls
  `.claude/hooks/commit-identity.sh` automatically now (since 2026-09-16),
  so this runs wherever the Bootstrap step above is actually configured —
  a hard guarantee in a cloud environment with the setup script wired, a
  soft one for local CLI use relying on the instructions-file directive
  alone. See [../LEDGER.md](../LEDGER.md) for the history of this gap; if
  your environment signs commits by default in a way that collides with a
  human-only authorship policy, see
  [CLOUD_SETUP.md](<upstream-docs>/documentation/CLOUD_SETUP.md#when-the-containers-own-signing-collides-with-a-human-only-policy).

## The Markdown Check Does Not Run Here

**Read this before assuming your documents are checked.** On 2026-09-21
Precedent's Markdown lint left GitHub Actions entirely and was replaced by
`.claude/hooks/doc-lint-gate.sh`, which refuses a `git commit` whose staged
Markdown fails [doc_lint.py](../../../tools/doc_lint.py). That is a Claude Code mechanism: it needs a
`PreToolUse` hook, and Codex has no hook mechanism at all to wire one into — the same
reason every hook row in [../LEDGER.md](../LEDGER.md) records no transfer to this adapter.

**So on this adapter, nothing checks your Markdown before it reaches a
shared branch** — not the hook, and not CI, because the workflow the hook
replaced is retired and deleted. This is the first adapter gap with that
property. Every earlier one cost you a guard you never had; this one costs
you a guard that was there last week.

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

**Doing only the first is the arrangement that just failed upstream.** "A
session is supposed to run the check before committing" was written down
and followed for months, and still nothing refused a commit that skipped
it — which was only ever safe because CI was behind it.

**What this harness does not get that Claude Code does, mechanism by
mechanism: [../PARALLELS.md](../PARALLELS.md).** The Markdown gate below
is one row of it. The others are the path-triggered practice loading, the
reply gate, the turn-end git check, and the private individual source —
each with the parallel where one exists and the reason where none does.
