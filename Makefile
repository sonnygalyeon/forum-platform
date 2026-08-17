.PHONY: up down build bootstrap check migrations migrate storage logs worker-logs beat-logs api-validate smoke schema

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
