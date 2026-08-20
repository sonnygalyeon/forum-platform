# Night Iris Forum — Stage 8.4 Complete User Experience

Stage 8.4 turns the clean frontend into an end-to-end forum experience backed by the real Django API.

## User flow

1. Register / log in.
2. Configure social profile.
3. Upload avatar and profile banner through multipart object-storage upload.
4. Create a community or subscribe to an existing one.
5. Create a post, article, or topic with structured content blocks.
6. Add paragraphs, headings, quotes, code, images, videos, and file attachments.
7. Open a publication, answer/comment, create nested replies, vote, and accept a topic answer.
8. Open public profiles and follow, mute, or block users.
9. Use the personalized subscriptions feed and notification preferences.

## New database migration

`users/0002_profile_media.py` adds nullable `avatar_asset` and `banner_asset` links to ready `MediaAsset` objects.

Run:

```bash
docker compose run --rm api python manage.py check
docker compose run --rm api python manage.py migrate --plan
docker compose run --rm api python manage.py migrate
```

## Frontend

```bash
cd frontend
cp .env.example .env.local   # only if it does not already exist
npm install
npm run build
npm run dev
```

Open `http://localhost:3000`.

## Media architecture

The browser never sends large files through Django/Next.js. It requests a multipart session through the authenticated API, uploads parts directly to MinIO/S3 using presigned URLs, and then completes the upload through the API. Structured publication blocks reference the resulting asset UUIDs. The backend synchronizes current inline/attachment links before taking the immutable revision snapshot.

## Still intentionally deferred

- avatar frames / cosmetics;
- full-text search UI;
- production deployment hardening;
- richer community roles and permissions.
