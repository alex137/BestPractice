---
slug:            gotcha-2026-09-13-the-leak-gate-s-vocabulary-layer-fails-open-unless-you-also-
status:          live
noted:           2026-09-13
severity:        null
retired:         null
retires_when:    null
---
## Symptom

The leak gate's vocabulary layer fails open unless you also set the git config.

## Story

**The leak gate's vocabulary layer fails open unless you also set the git
config.** `export PRECEDENT_LEAK_BLOCKLIST=<a path OUTSIDE this repo>` is half
of it; without `git config precedent.requireVocabulary true` a shell that
starts without the variable prints `PARTIAL`, exits 0, and the push goes
through with only the structural rules applied. Every push here is publication
into a public repository, so the half-configured state is the dangerous one.
See `python3 tools/leak_gate.py --explain`. **Narrowed 2026-09-12**: with the
variable unset the gate now reads `leak-blocklist.txt` from the individual set
`~/.config/precedent/config.json` names, so the common case — a list sitting
where INSTALL.md section 8 puts it, in a shell nobody exported anything in —
runs the full layer instead of reporting `PARTIAL`. The trap that remains is
the one this entry is really about: a list somewhere ELSE, with neither the
variable nor the git config set, still fails open and still looks like a pass.

## Fix

(migration could not isolate a distinct Fix paragraph -- read ## Story.)
