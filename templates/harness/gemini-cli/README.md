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
- **Commit identity and signing:** Gemini CLI has no hook mechanism to run
  `commit-identity.sh` automatically (see
  [../LEDGER.md](../LEDGER.md) for the running list of what that costs).
  Several of its effects are plain `git config`/OS settings that need no
  hook at all, though — running the script once by hand still sets them for
  this checkout. If your environment signs commits by default in a way that
  collides with a human-only authorship policy, see
  [CLOUD_SETUP.md](<upstream-docs>/documentation/CLOUD_SETUP.md#when-the-containers-own-signing-collides-with-a-human-only-policy).
