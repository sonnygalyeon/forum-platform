# Обновление и локальный запуск Night Iris

Актуальная линия разработки после этапа 1.1.7: **`ver1.2-discovery`**.
`main` не используется для получения актуального приложения. Команды ниже
предназначены для локальной разработки, в том числе macOS Apple Silicon.

## 1. Подготовить Docker

Установите [Docker Desktop для Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
в варианте **Apple silicon** для MacBook M4. Откройте Docker Desktop и дождитесь
готовности движка. Проверьте в терминале:

```bash
git --version
docker --version
docker compose version
docker info
```

Нужна актуальная версия Docker Compose v2 с поддержкой `up --wait`.
Python 3.13, Node.js 24, PostgreSQL 18, Redis 8 и MinIO запускаются в контейнерах;
устанавливать их отдельно на Mac для этого способа не требуется.

## 2. Обновить существующую папку

Откройте терминал **в существующей папке репозитория**. Не переименовывайте её и
не меняйте Compose project name: от него зависят имена Docker-томов с данными.
Путь ниже приведён как пример — используйте фактический путь своей копии:

```bash
cd ~/forum-platform
pwd
git remote -v
git status --short
```

`origin` должен указывать на `sonnygalyeon/forum-platform`.

Если `git status --short` пустой, рабочая копия чистая. Если есть изменения,
сначала сохраните их. Следующая команда сохраняет изменённые и новые
неотслеживаемые файлы во временный Git stash:

```bash
git stash push -u -m "local-before-1.2-update"
git stash list
```

`.env` и игнорируемые каталоги в stash не включаются и остаются на месте.
Не применяйте stash автоматически после обновления: сначала запустите новую
версию, затем при необходимости перенесите собственные изменения и разрешите
возможные конфликты. `frontend/next-env.d.ts` может изменяться после сборки;
его тоже можно сохранить этой командой.

Если приложение сейчас запущено, перед сменой ветки остановите его процессы:

```bash
docker compose stop frontend api worker beat
```

Получите ветку и обновите её:

```bash
git fetch origin
git switch ver1.2-discovery
git pull --ff-only origin ver1.2-discovery
git log -1 --oneline
```

При первом переключении Git обычно сам создаёт локальную ветку из одноимённой
ветки `origin`. Если он сообщает, что локальная ветка не найдена, выполните:

```bash
git switch --track -c ver1.2-discovery origin/ver1.2-discovery
```

Если `pull --ff-only` сообщает о расхождении истории, остановитесь и сохраните
вывод `git status` и `git log --oneline --graph -12`. Не используйте сброс с
удалением локальных изменений.

**Если проекта ещё нет**, выполните вместо раздела выше:

```bash
git clone --branch ver1.2-discovery https://github.com/sonnygalyeon/forum-platform.git
cd forum-platform
```

## 3. Запустить или обновить приложение

Из корня репозитория:

```bash
sh scripts/dev_up.sh
```

Скрипт выполняет следующее:

1. Проверяет Docker и Compose.
2. Создаёт `.env` из `.env.example`, только если `.env` ещё отсутствует.
3. Проверяет Compose-конфигурацию и собирает образы.
4. Останавливает приложение на время миграций и обновления зависимостей.
5. Запускает PostgreSQL, Redis и MinIO и ждёт готовности.
6. Настраивает MinIO bucket и учётную запись приложения.
7. Применяет миграции и проверяет объектное хранилище.
8. Выполняет `npm ci` в постоянном Docker-томе `node_modules`.
9. Запускает API, Celery worker, beat и frontend.
10. Проверяет Django, `/api/v1/ready/` и ответ frontend.

Существующий `.env` не перезаписывается. Тома PostgreSQL, MinIO и Redis не
удаляются. При ошибке скрипт останавливается; исправьте причину по логам и
запустите его повторно. Успешный финал: `Night Iris is ready` и адрес приложения.
Первая сборка требует загрузки образов и зависимостей, поэтому занимает время.

Если старый `.env` существенно отличается от текущего `.env.example`, добавьте
недостающие параметры вручную. Не заменяйте существующие пароли PostgreSQL/MinIO
произвольными значениями: они должны соответствовать сохранённым данным.

Для стандартного локального режима в `.env` используются:

```dotenv
POSTGRES_HOST=db
POSTGRES_PORT=5432
S3_INTERNAL_ENDPOINT=http://minio:9000
S3_PUBLIC_ENDPOINT=http://localhost:9000
REDIS_CACHE_URL=redis://redis:6379/1
CHANNEL_REDIS_URL=redis://redis:6379/2
CELERY_BROKER_URL=redis://redis:6379/0
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,api
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
S3_CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
API_DOCS_ENABLED=1
READINESS_CHECK_S3=1
```

`frontend/.env.local` для Docker-запуска не нужен: Compose задаёт
`BACKEND_API_URL=http://api:8000/api/v1` внутри сети контейнеров. Используйте
`http://localhost:3000` в браузере; доступ из локальной сети/интернета требует
отдельной настройки адресов, WebSocket и медиа.

## 4. Открыть приложение и проверить

| Назначение | Адрес |
| --- | --- |
| Форум | http://localhost:3000 |
| Поиск | http://localhost:3000/search |
| Swagger API | http://localhost:8000/api/docs/ |
| OpenAPI | http://localhost:8000/api/schema/ |
| Готовность API/БД/Redis/MinIO | http://localhost:8000/api/v1/ready/ |
| Версия и Git SHA | http://localhost:8000/api/v1/version/ |
| Django admin | http://localhost:8000/admin/ |
| MinIO console | http://localhost:9001 |

Проверки из терминала:

```bash
docker compose ps
curl -fsS http://localhost:8000/api/v1/ready/
curl -fsS http://localhost:8000/api/v1/version/
```

В readiness ожидается `status: ok`, а в `checks` — успешные проверки БД, Redis и
объектного хранилища. В `build` версии после запуска скриптом будет SHA текущего
Git-коммита. Поле `version` пока равно `1.0.0`: номер этапа разработки 1.2.0
не является выпущенным релизом.

Зарегистрируйтесь через интерфейс. Для Django admin отдельно создайте
администратора интерактивной командой:

```bash
docker compose exec api python manage.py createsuperuser
```

Введите запрошенные поля. Пароль при вводе не отображается. Для MinIO console
используются `MINIO_ROOT_USER` и `MINIO_ROOT_PASSWORD` из локального `.env`.

Для проверки поиска создайте несколько публикаций с общим уникальным словом
и откройте `/search?q=ваше-слово&scope=publications&page_size=2`. Проверьте
следующую страницу, фильтры и кнопки «назад/вперёд» браузера.

## 5. Логи, остановка и следующие обновления

```bash
# Логи приложения; Ctrl+C завершает просмотр, контейнеры продолжают работать.
docker compose logs -f --tail=100 api frontend worker beat

# Остановить, сохранив контейнеры и данные.
docker compose stop

# Запустить ранее созданные контейнеры без обновления кода/зависимостей.
docker compose start
```

После следующих изменений в Git повторите:

```bash
git status --short
git fetch origin
git switch ver1.2-discovery
git pull --ff-only origin ver1.2-discovery
sh scripts/dev_up.sh
```

При локальных изменениях сначала используйте сохранение из раздела 2.
`docker compose restart` сам по себе не пересобирает образы и не применяет
миграции — для обновления используйте скрипт.

## 6. Если запуск не удался

**Cannot connect to Docker daemon:** запустите Docker Desktop, дождитесь
готовности и повторите `docker info`.

**Port is already allocated:** проверьте занятость 3000, 8000, 9000 и 9001.
Возможно, работает прежний frontend/backend вне Docker или другая копия стека.
Завершите соответствующий процесс/стек и повторите запуск. Не меняйте порты
без согласованного изменения адресов API, WebSocket и медиа.

**Ошибка миграции, БД или MinIO:**

```bash
docker compose logs --tail=150 db minio api
```

Смотрите также ошибку одноразового `migrate`/`minio-init` в выводе скрипта.
Данные одноразовых контейнеров удаляются с `--rm`, поэтому их вывод важен.
Если после смены имени папки пропали данные, проверьте старое имя проекта
через `docker compose ls -a` и `docker volume ls`: вероятно, выбран другой набор
томов. Не удаляйте тома при диагностике.

**Модуль frontend не найден:** повторите `sh scripts/dev_up.sh`; он обновляет
`node_modules` по `package-lock.json` даже после пересборки образа.

**Файлы не загружаются:** проверьте `S3_PUBLIC_ENDPOINT`, S3 CORS origins,
готовность MinIO и результат `/api/v1/ready/`. Если включён `MEDIA_REQUIRE_SCAN=1`,
должен быть настроен доступный сканер.

**Интерфейс открылся, но нет realtime:** проверьте доступность порта 8000 и
`docker compose logs --tail=100 api`. В локальном режиме сокеты идут напрямую
к `ws://localhost:8000`; `daphne` включён в Django `INSTALLED_APPS` и обеспечивает
ASGI `runserver`.

## 7. Проверки разработчика и production

Backend-тесты используют отдельную тестовую БД:

```bash
docker compose exec api pytest -q
docker compose exec api python manage.py makemigrations --check --dry-run
```

Полный Playwright E2E использует отдельный Compose-проект с изолированными
данными, но те же локальные порты. Сначала остановите обычный стек и следуйте
TESTING.md. Не запускайте `scripts/e2e_reset.sh` для сброса обычной разработки.

Эта инструкция предназначена для **локального** запуска. Для публичного
сервера нужны production-конфигурация, домен и TLS: см. VPS_DEPLOYMENT.md,
RELEASING.md и deployment.md. Не публикуйте development-стек с примерными
паролями в интернете.
