# Night Iris Forum — Stage 8.3 Admin

Кастомная staff-only панель находится по адресу `http://localhost:3000/admin`.
Она работает только с реальными данными Django API и не содержит mock-данных.

## Первый администратор

Если superuser ещё не создан:

```bash
cd ~/forum_platform
docker compose run --rm api python manage.py createsuperuser
```

После создания войдите на обычной странице `/login` под этим аккаунтом. В навигации появится пункт **Админка**.

## Разделы

- Обзор — реальные агрегаты базы.
- Пользователи — активность и staff-доступ; staff выдаёт только superuser.
- Контент — публикации, комментарии, ответы, hide/unhide с причиной.
- Жалобы — open/reviewing/resolved/dismissed.
- Сообщества — включение/отключение без удаления истории.
- Журнал действий — immutable moderation actions.
- Система — readiness DB/Redis/S3.

Backend endpoints добавлены под `/api/v1/admin/*`. Новых моделей и миграций Stage 8.3 не добавляет.
