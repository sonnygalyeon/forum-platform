
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

RUN pip install --no-cache-dir uv

# The lock file is part of the build input. Code and image dependencies can no
# longer silently drift apart after a bind mount or a rebuild.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --group dev --no-install-project

COPY . .

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
