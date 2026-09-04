# Stage 8.12.6 — Backup & Disaster Recovery

## Goal

A backup is not considered valid merely because a file exists. Night Iris now treats backup creation, integrity verification and restore as one operational contract.

## Backup sets

`scripts/backup_all.sh` generates one UTC `BACKUP_SET_ID` shared by PostgreSQL and MinIO. The set contains:

- PostgreSQL custom-format dump;
- SHA-256 for the database dump;
- mirrored MinIO bucket directory;
- SHA-256 manifest for MinIO objects;
- a set manifest under `backups/manifests/`.

The backup command immediately runs `verify_backup.sh` before declaring success.

## Verification

`verify_backup.sh` checks:

1. all declared backup components exist;
2. PostgreSQL checksum;
3. all MinIO object checksums;
4. `pg_restore --list` can parse the PostgreSQL archive.

This catches corrupt/truncated dumps that a checksum generated after truncation would otherwise happily bless.

## Restore

Destructive restore commands require the exact environment variable `RESTORE_CONFIRM=YES`.

- `restore_postgres.sh` terminates active sessions, recreates the application database and restores with `--exit-on-error`.
- `restore_minio.sh` mirrors the chosen backup set back to the bucket with deletion of objects absent from the backup.
- `restore_all.sh` verifies the set first, stops application traffic, restores both stores, runs migrations, starts services, waits for readiness and executes the production smoke test.

## Scheduling

The existing systemd backup timer/service remains the production scheduling mechanism. `backup_all.sh` is now safe to use from that service because a non-verifiable backup exits non-zero.

## Off-site requirement

Local retention is not disaster recovery against host loss. Production operations must copy completed `backups/` sets to independent storage with encryption and restricted credentials. This repository deliberately does not hard-code a cloud vendor.

## Recovery objectives

Initial beta objectives:

- RPO: <= 24 hours with daily scheduled backups;
- RTO: <= 2 hours for a documented single-host recovery drill.

Tighter objectives require measured restore drills and, eventually, database/object-storage replication rather than optimistic documentation.

## Acceptance criteria

- backup set creation exits non-zero on verification failure;
- PostgreSQL and MinIO belong to the same set identifier;
- restore requires explicit destructive confirmation;
- full restore finishes with readiness and production smoke checks;
- a restore drill is performed before public beta and its duration is recorded.
