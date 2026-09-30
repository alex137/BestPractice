---
slug:              todo-2026-09-29-push-gate-reads-a-quoted-pipe-as-a-command
kind:              analysis
domain:            mechanism
severity:          medium
status:            done
disposition:       wait
remind_on:         null
blocked_on:        null
batch:             null
decision:          null
decision_strength: null
waiting_on:        null
noted:             2026-09-29
closed:            2026-09-30
---
## What

**`.claude/hooks/push-check-gate.sh` took a read-only grep for a
`git push`, and ran a full check on it.** The hook ships to every consumer.
The command, run in this repo on 2026-09-29, verbatim:

    cd /home/user/BestPractice && sed -n 1,80p tools/checkin.py; echo ----; grep -n "^def \|REFUSES\|upstream.commit\|scrub\|leak_gate\|git push\|def main" tools/checkin.py | head -90

Nothing in it pushes. The grep's pattern holds the alternation
`\|git push`, inside double quotes. The hook's test for "a real
`git push`, in command position" is a regular expression over the raw
command text,

    (^|[|;&]|&&|\|\||\$\()[[:space:]]*git[[:space:]]+(-C[[:space:]]+[^[:space:]]+[[:space:]]+)?push\b

and it reads the `|` inside the quotes as a pipe, so `git push` after it
looks like a command. The hook then ran the push check, the full nine-step
one, which took 766 s and refused, blocking the grep.

gotcha-2026-09-21 covers the same false match for a commit message and a
heredoc; a quoted argument to any other command is not covered.

## What would close it

Decide "is this a push" on the command with quoted strings removed (or with
a real shell tokenizer, such as Python's `shlex`, which the hook already has
available), not on the raw text. A harness case with this exact command
must pass the hook untouched, next to the existing cases for a real push
behind `&&`, `;` and `|`.

Closes when that case is in the harness and passes.

## Closed

2026-09-30. The hook now decides "is this a push" on the command with its quoted strings and heredoc bodies blanked, not on the raw text. The same block went into the three sibling hooks that ask the same kind of question (commit-identity-push-gate.sh, doc-lint-gate.sh, merge-check-gate.sh), since they had the same misread. [tools/verify_harness.py](../tools/verify_harness.py)'s check_push_check_gate runs this item's command verbatim and lets it through, beside real pushes after `;`, `|` and `&&`; check_hooks_share_one_quote_blanking_block keeps the four copies identical.
