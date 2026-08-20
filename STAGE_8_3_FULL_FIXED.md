# Night Iris Forum — Stage 8.3 Full Fixed

Полный исходный проект Stage 8.3.

Включает:
- Django backend;
- PostgreSQL / Redis / MinIO Docker Compose configuration;
- Night Iris Next.js frontend;
- чистый старт без mock-публикаций;
- JWT/BFF authentication flow;
- пользовательские страницы;
- кастомную административную панель;
- исправленный полный набор Django apps;
- исправленную discriminated-union типизацию ContentBlock;
- Next.js 16.3.1;
- PostCSS >= 8.5.23.

Архив не содержит `.env`, `node_modules`, Docker volumes или пользовательские данные.

## Проверка backend

```bash
docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py showmigrations
docker compose run --rm api python manage.py migrate --plan
```

## Frontend

```bash
cd frontend
cp .env.example .env.local   # только если .env.local ещё нет
npm install
npm run build
npm run dev
```

Открыть: http://localhost:3000
Админка: http://localhost:3000/admin
