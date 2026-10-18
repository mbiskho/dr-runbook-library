---
service: core-db
scenario: Bad migration or accidental deletion
tier: 1
rto: 4h
owner: platform-oncall
last_tested: 2026-08-30
---
## When to use
Data was deleted or corrupted by a migration, script or application bug, and you know approximately when it happened.

## Decision
Platform lead plus the data owner. Choose between restoring only the affected tables (preferred: no downtime) and cutting over the whole database (only if corruption is widespread).

## Steps
1. Find the last good timestamp from the audit log or the deploy time, minus one minute.
   Expect: a UTC timestamp agreed in the incident channel.
2. Restore to a new cluster at that time: `aws rds restore-db-cluster-to-point-in-time --source-db-cluster-identifier core-db --db-cluster-identifier core-db-pitr --restore-to-time <ts> --use-latest-restorable-time false`.
   Expect: `core-db-pitr` reaches `available` (20-60 minutes depending on size).
3. Export the affected rows from `core-db-pitr` with `pg_dump --table=<t> --data-only` (or a `COPY (SELECT ...)` for a subset).
   Expect: row count matches what the data owner expects to be missing.
4. Load into production inside a transaction, after checking primary keys don't collide.
   Expect: `BEGIN; ... ; SELECT count(*) ...;` shows the restored rows, then `COMMIT`.

## Verify
- The data owner confirms the records in the application.
- Restore verification job (`restorecheck`) passes on the next run.

## Rollback
Step 4 is in a transaction: `ROLLBACK` before commit. After commit, the restored rows are ordinary rows; remove them by primary key if needed. Delete `core-db-pitr` when the incident closes.
