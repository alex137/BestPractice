---
slug:              todo-2026-11-24-a-standing-yes-to-clone-permissions-was-held-for-a-fresh-ask
kind:              decision
domain:            engine
severity:          low
status:            open
disposition:       ask
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        "Alex's yes or no, in the session that filed this, on changing what Update Vendors prints and one sentence of the runbook"
noted:             2026-11-24
closed:            null
---
## What

- [ ] **Update Vendors applied a permission change on a yes already on record, and a careful session held it anyway and asked again.** Reported 2026-11-24 from a project: the only change in an update was four lines letting sessions clone, without a prompt, repositories of the account one of its declared practice sets lives under. Alex, relayed by that project's coordinating session: "Yea on cloning other repos, but they are public so why do you need to ask me. Is there a fix to BestPractice so we don't have this problem in the future?" (needs: decision -- Alex)

**What the tool does today, read from the code.** It already behaves the way Alex wants. [precedent_update.py](../tools/precedent_update.py) treats a recorded yes to the permission list as standing "for every later allow-list-only change" (Morgan, 2026-11-02), and applied this one on it. The clone lines come from [precedent_vendor_engine.py](../tools/precedent_vendor_engine.py) (`clone_allow_rules`, `source_owners`): one set of lines per account that a declared practice set lives under.

**Why a session stopped anyway.** The tool's line said only that the settings file changed "with the person's recorded yes to the allow-list change", and quoted the old yes. It did not say what the new lines permit or why they appeared. A session reading four new lines naming a second account, beside a yes given for something else, could not tell they were in the class the yes covers. Stopping was the careful reading of an unclear message.

**The fix, smallest first.**

1. **The tool says what each new line is for.** For clone lines: "lets a session clone, without a prompt, repositories of ACCOUNT, where the declared practice set NAME lives; read-only; covered by the yes on record". A session then has nothing to judge.
2. **The runbook says the class in a sentence** ([vendor-update-runbook](../practices/vendor-update-runbook.md)): a permission line the engine derives from a declared practice set, and that only lets a session read it, rides on the recorded yes. Anything the engine did not derive, or that permits more than reading, is asked fresh.
3. **Not proposed: widening what is applied without a yes.** A repository with no yes on record is still asked once.

**One thing to decide with it.** The lines permit cloning any repository of that account (`ACCOUNT/*`), not only the declared set. The code's own comment calls that a deliberate narrowing to accounts. Cloning needs the session to have read access anyway, so the lines add no access, only fewer prompts. If that is wider than wanted, the lines can name the one repository where the set's address is known; where it is declared by name only, the account is all the tool has.

**The cost of leaving it.** Each time a repository's declared sets change, a careful session stops an update for a question whose answer is already written down, and the person is asked something they have said yes to.

## How It Closes

`status` becomes `done` when Alex has said yes or no; on a yes, when the tool's message and the runbook sentence are on `main` and the harness test that covers the recorded answer still passes.
