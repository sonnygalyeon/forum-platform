# Night Iris Forum Web — 0.8.5

Next.js frontend for the Night Iris Forum Django API.

## Run

```bash
cp .env.example .env.local
npm install
npm run build
npm run dev
```

Open `http://localhost:3000`.

`BACKEND_API_URL` is server-only and normally points to `http://localhost:8000/api/v1`.

## Main routes

- `/` — latest / subscriptions feed
- `/register`, `/login`
- `/profile`, `/profile/edit`
- `/users/<uuid>` — public social profile
- `/new` — structured publication editor
- `/publications/<uuid>` — publication + discussion
- `/publications/<uuid>/edit`
- `/publications/<uuid>/revisions`
- `/communities`
- `/communities/<uuid>`
- `/notifications`
- `/admin` — custom staff panel

Large media files are uploaded directly to object storage using presigned multipart URLs.
