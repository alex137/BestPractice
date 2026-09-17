# Gemini CLI adapter

`GEMINI.md` is the file Gemini CLI auto-loads at the repo root; it points at
`AGENTS.md` (harness-neutral) and directs a session to run
`bash tools/bootstrap.sh` before other work. See [GEMINI.md](GEMINI.md) for
the file itself — this page covers the parts a person, not the agent, needs
to know.

- **Bootstrap:** the instructions-file directive above is a soft guarantee
  (the agent has to actually read and follow it) — see the enforcement
  caveat in [../README.md](../README.md). Recent Gemini CLI versions can be
  configured to read `AGENTS.md` directly via settings `contextFileName`;
  prefer that and drop `GEMINI.md` if your version supports it.
- **Pre-approved commands:** no allowlist equivalent — sessions will prompt,
  or run under whatever sandbox policy the environment configures. Nothing
  in the practice layer depends on the allowlist; it only reduces prompts.
- **Audits:** unchanged — `python3 process/upstream/tools/practice_audit.py`
  and `python3 process/upstream/tools/doc_lint.py` are plain Python and run
  identically here.
- **Commit identity and signing:** `tools/bootstrap.sh` calls
  `.claude/hooks/commit-identity.sh` automatically now (since 2026-09-16),
  so this runs wherever the Bootstrap step above actually runs — a soft
  guarantee here, the same as the bootstrap step itself, since Gemini CLI
  has no hook mechanism of its own to make it a hard one. See
  [../LEDGER.md](../LEDGER.md) for the history of this gap; if your
  environment signs commits by default in a way that collides with a
  human-only authorship policy, see
  [CLOUD_SETUP.md](<upstream-docs>/documentation/CLOUD_SETUP.md#when-the-containers-own-signing-collides-with-a-human-only-policy).
