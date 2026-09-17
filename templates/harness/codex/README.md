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
- **Commit identity and signing:** Codex has no hook mechanism to run
  `commit-identity.sh` automatically (see
  [../LEDGER.md](../LEDGER.md) for the running list of what that costs).
  Several of its effects are plain `git config`/OS settings that need no
  hook at all, though — running the script once by hand still sets them for
  this checkout. If your environment signs commits by default in a way that
  collides with a human-only authorship policy, see
  [CLOUD_SETUP.md](<upstream-docs>/documentation/CLOUD_SETUP.md#when-the-containers-own-signing-collides-with-a-human-only-policy).
