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
