# Deployment entry point

Use the existing runbooks and scripts:

- VPS_DEPLOYMENT.md: host, DNS, secrets, services and initial deployment.
- RELEASING.md: exact-commit gates, release artifact verification, backups,
  deployment, smoke checks and rollback.
- OBSERVABILITY.md: health, metrics and incident signals.
- `scripts/prod_config_check.sh`: validate environment before deployment.
- `scripts/deploy_prod.sh`: build/deploy with backup and smoke checks.
- `scripts/prod_smoke.sh`: verify running services and release provenance.

Stage an Engagement candidate on an isolated host/domain with separate database,
Redis and media storage. Populate `.env.prod` on that host without committing
secrets. Validate configuration, deploy the selected SHA and record the version
and build returned by `/api/v1/version/`.

For 1.1.7, test social/community recommendations through the browser BFF, all
three feed modes beyond page one, delayed/failed draft saving, message history,
reconnect catch-up, privacy and uploads. Require CI, Load Gate and Release
Candidate Gate to succeed on the same source commit before release promotion.

This documentation does not provision or deploy a host. A deployed staging URL
and smoke results must be recorded when the operator has supplied that target.
