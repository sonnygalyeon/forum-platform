
# Night Iris Forum Web — 0.8.11

Next.js frontend for the Night Iris Forum Django API.

## Recommended development

Run the frontend in the same Docker network as Django:

```bash
cd ..
cp .env.example .env
docker compose up -d --build frontend
```

Open `http://127.0.0.1:3000`.

## Host-only development

If you intentionally run Node on macOS:

```bash
cp .env.example .env.local
npm ci
npm run dev
```

The host profile uses `BACKEND_DISABLE_KEEPALIVE=1` because Docker Desktop
host-to-container keep-alive sockets can reset under Node/Undici. Production and
Docker-to-Docker development keep connection pooling enabled.

## E2E

```bash
npm ci
npx playwright test
```

Local Playwright starts an isolated Docker E2E stack automatically. Set
`PLAYWRIGHT_MANAGE_WEBSERVER=0` only when you deliberately manage the server
outside Playwright.
