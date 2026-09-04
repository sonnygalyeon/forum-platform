#!/bin/sh
set -eu
./scripts/backup_postgres.sh
./scripts/backup_minio.sh
