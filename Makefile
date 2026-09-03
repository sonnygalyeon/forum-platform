.PHONY: up down build bootstrap check migrations migrate storage logs worker-logs beat-logs api-validate smoke schema test test-all e2e load-smoke observability prod-init prod-config prod-up prod-down prod-logs prod-backup prod-smoke

up:
	docker compose up -d

build:
	docker compose build api

bootstrap:
	docker compose run --rm api sh scripts/bootstrap_dev.sh

check:
	docker compose run --rm api python manage.py check

migrations:
	docker compose run --rm api python manage.py makemigrations

migrate:
	docker compose run --rm api python manage.py migrate

storage:
	docker compose run --rm api python manage.py ensure_object_storage

logs:
	docker compose logs -f api

down:
	docker compose down

worker-logs:
	docker compose logs -f worker

beat-logs:
	docker compose logs -f beat

api-validate:
	docker compose run --rm api sh scripts/validate_api.sh

schema:
	docker compose run --rm api python manage.py spectacular --file /tmp/forum-openapi.yml --validate --fail-on-warn

smoke:
	sh scripts/smoke_api.sh

test:
	./scripts/test_backend.sh

test-all:
	./scripts/test_all.sh

e2e:
	./scripts/run_e2e.sh

load-smoke:
	python3 scripts/load_smoke.py

observability:
	docker compose run --rm api python manage.py observability_report

prod-config:
	./scripts/prod_config_check.sh

prod-up:
	./scripts/deploy_prod.sh

prod-down:
	docker compose --env-file .env.prod -f compose.prod.yaml down

prod-logs:
	docker compose --env-file .env.prod -f compose.prod.yaml logs -f caddy api frontend worker beat

prod-backup:
	./scripts/backup_all.sh

prod-smoke:
	./scripts/prod_smoke.sh

prod-init:
	./scripts/init_prod_env.sh
