# Lease board

Work in flight across concurrent sessions: one JSON file per lease under
`leases/`. Written only by the lease board tool, never by hand; every
take, update and release is a commit on this branch, so `git log` here is
the full history of who held what.
