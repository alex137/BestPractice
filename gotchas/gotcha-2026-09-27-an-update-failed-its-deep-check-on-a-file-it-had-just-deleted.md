---
slug:            gotcha-2026-09-27-an-update-failed-its-deep-check-on-a-file-it-had-just-deleted
status:          retired
noted:           2026-09-27
severity:        null
retired:         "2026-09-27"
retires_when:    null
---
## Symptom

`precedent_update.py` came back FAILED from the deep check with
`timestamps-carry-offset` reporting "could not be parsed, so it was NOT
checked for naive timestamps" for a file under `process/upstream/` that no
longer exists.

## Story

A consumer taking main @ c9da15b, 2026-09-27. `checkin.py update` deleted
`tools/precedent_upstream_check.py` and `tools/upstream_watermark.json` from
the vendored catalogue, because upstream had dropped both. The deletions sat
unstaged. The deep check then ran, and `timestamps-carry-offset` listed
Python files with `git ls-files --cached --others --exclude-standard`.
`ls-files` reads the INDEX, not the disk, so a file deleted in the working
tree but not yet staged is still listed. `read_text()` then raised OSError,
the check turned it into a finding, and a whole update failed on a file that
was simply gone. Plain `git ls-files` has the same property. Staging
everything (`git add -A`) in the consumer made the next run pass, which is
what proved the cause.

## Fix

Two, each covering the case on its own. `precedent_check.py`'s
`_ls_files_on_disk()` drops any listed path missing from disk, and the
checks and scope lists that read file contents use it. `precedent_update.py`
stages what the update wrote and deleted before the deep check, and leaves
anything already uncommitted as it was. `verify_harness.py`'s
`check_update_vendors_survives_an_upstream_deletion` rebuilds the case
from an installed consumer. Anywhere else: a list from `git ls-files` is
the index, and a file on it may not be on disk.
