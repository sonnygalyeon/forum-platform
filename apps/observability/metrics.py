from prometheus_client import Counter, Gauge, Histogram, Info

BUILD_INFO = Info("night_iris_build", "Night Iris build information")

HTTP_REQUESTS = Counter(
    "night_iris_http_requests_total",
    "HTTP requests processed by the Django API",
    ["method", "route", "status"],
)
HTTP_DURATION = Histogram(
    "night_iris_http_request_duration_seconds",
    "HTTP request duration",
    ["method", "route"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10),
)
HTTP_ACTIVE = Gauge(
    "night_iris_http_requests_active",
    "HTTP requests currently being processed",
)
DB_QUERIES = Counter(
    "night_iris_db_queries_total",
    "Database statements executed during HTTP requests",
    ["operation"],
)
DB_DURATION = Histogram(
    "night_iris_db_query_duration_seconds",
    "Database statement duration",
    ["operation"],
    buckets=(0.001, 0.0025, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5),
)
DB_SLOW = Counter(
    "night_iris_db_slow_queries_total",
    "Database statements above the configured slow-query threshold",
    ["operation"],
)
WEBSOCKET_CONNECTIONS = Gauge(
    "night_iris_messenger_websocket_connections",
    "Currently connected authenticated messenger WebSockets",
)
MESSENGER_EVENTS = Counter(
    "night_iris_messenger_events_total",
    "Durable messenger events persisted",
    ["type"],
)
CELERY_HEARTBEAT_AGE = Gauge(
    "night_iris_celery_heartbeat_age_seconds",
    "Age of the latest Celery heartbeat stored in Redis",
)
CELERY_TASKS_SUCCEEDED = Gauge(
    "night_iris_celery_tasks_succeeded_total",
    "Celery tasks reported successful through the shared Redis counter",
)
CELERY_TASKS_FAILED = Gauge(
    "night_iris_celery_tasks_failed_total",
    "Celery tasks reported failed through the shared Redis counter",
)
