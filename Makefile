.PHONY: up down build bootstrap check migrations migrate storage logs

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
