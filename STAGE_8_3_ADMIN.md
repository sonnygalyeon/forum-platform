# Forum Platform Stage 8.3 — Night Iris Admin

Этот snapshot объединяет backend Stage 7.2.x, clean frontend Stage 8.2 и новую кастомную админ-панель Stage 8.3.

## Backend changes
- `apps.adminpanel` — staff-only API для dashboard, users, content, communities, reports и audit.
- `UserMeSerializer` теперь возвращает `is_active`, `is_staff`, `is_superuser`.
- новых таблиц и миграций нет.

## Frontend
- `/admin` — overview
- `/admin/users`
- `/admin/content`
- `/admin/reports`
- `/admin/communities`
- `/admin/audit`
- `/admin/system`

Админка не создаёт фейковые данные и не делает hard-delete публикаций/комментариев.
