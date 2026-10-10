---
slug:            gotcha-2026-10-10-git-config-global-with-dev-null-replaces-dev-null
status:          live
noted:           2026-10-10
severity:        notable
retired:         null
retires_when:    "never: git writes config by renaming a lock file over its target, whatever that target is"
---
## Symptom

Every git command in a test fixture fails with "fatal: bad config line 1
in file /dev/null". `ls -l /dev/null` shows an ordinary file (`-rw-rw-rw-`)
instead of a character device (`crw-rw-rw-`), holding text such as
"/bin/bash: line 1: unalias: unsetenv: not found".

## Story

2026-10-10, BestPractice. A new harness test ran
[tools/commit-identity.sh](https://github.com/alex137/BestPractice/blob/staging/tools/commit-identity.sh)
with the fixture environment, which sets `GIT_CONFIG_GLOBAL=/dev/null` to
give git an empty global config. The hook runs `git config --global`, and
git writes a config by renaming a lock file over its target, so it replaced
the container's `/dev/null` with an ordinary file. From then on every
`2>/dev/null` in every shell wrote into that file, and every fixture that
read `/dev/null` as its global config failed to parse it. Restoring the
device needs `mknod`, which the session's auto mode refused as destructive.

## Fix

- The hook now skips every global config write, and says why, when
  `GIT_CONFIG_GLOBAL` names anything other than a regular file.
- A fixture that runs a tool that might write global config points
  `GIT_CONFIG_GLOBAL` at an empty file of its own, never at `/dev/null`.
- In a container where it has already happened, `truncate -s 0 /dev/null`
  lets git read it again until something writes to it, and a new container
  has the real device. Restoring it in place takes
  `rm /dev/null && mknod -m 666 /dev/null c 1 3`, as root.
