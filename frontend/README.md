# Night Iris Forum — Frontend Stage 8.2

Чистый frontend без демонстрационных постов, пользователей и сообществ. Интерфейс работает только с реальными данными Django API.

## Что уже работает

- регистрация и вход через существующий Django API;
- JWT хранится только в `HttpOnly` cookies через Next.js BFF, а не в `localStorage`;
- автоматическое обновление access token через refresh token;
- выход с blacklist refresh token на backend;
- публичная лента публикаций и персональная лента после входа;
- реальные empty states для пустого форума;
- создание первой публикации (`post`, `article`, `topic`);
- реальные страницы публикаций по UUID;
- ответы/комментарии, вложенные replies, голосование и accepted answer;
- реальные сообщества + создание первого сообщества;
- уведомления;
- социальный профиль с шапкой, статистикой подписок и реальной активностью;
- тёмная и светлая темы;
- адаптивная desktop/mobile навигация;
- никаких mock-данных и ссылок на несуществующие разделы.

## Запуск

Backend:

```bash
cd ~/forum_platform
docker compose up -d
```

Frontend:

```bash
cd ~/forum_platform/frontend
cp .env.example .env.local
npm install
npm run dev
```

Открыть: http://localhost:3000

## Важно

`BACKEND_API_URL` — server-only переменная. Browser обращается к `/api/auth/*` и `/api/forum/*` на Next.js, а Next.js уже проксирует запросы в Django. Access/refresh JWT недоступны JavaScript-коду страницы.

Первый запуск действительно будет пустым. После регистрации можно создать первую публикацию или сообщество через UI.
