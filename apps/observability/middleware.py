import logging
import re
import time
import uuid
from contextlib import ExitStack

from django.conf import settings
from django.db import connections
from django.utils.deprecation import MiddlewareMixin

from .context import request_id_var, request_method_var, request_route_var
from .metrics import DB_DURATION, DB_QUERIES, DB_SLOW, HTTP_ACTIVE, HTTP_DURATION, HTTP_REQUESTS

access_logger = logging.getLogger("nightiris.request")
db_logger = logging.getLogger("nightiris.db")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _route_label(request):
    match = getattr(request, "resolver_match", None)
    if match is None:
        return "__unmatched__"
    route = getattr(match, "route", None)
    if route:
        return route
    return getattr(match, "view_name", None) or "__unnamed__"


def _operation(sql):
    text = (sql or "").lstrip()
    if not text:
        return "OTHER"
    return text.split(None, 1)[0].upper()[:16]


def _sql_shape(sql):
    return " ".join((sql or "").split())[:700]


class QueryMetricsWrapper:
    def __call__(self, execute, sql, params, many, context):
        operation = _operation(sql)
        started = time.perf_counter()
        try:
            return execute(sql, params, many, context)
        finally:
            duration = time.perf_counter() - started
            DB_QUERIES.labels(operation=operation).inc()
            DB_DURATION.labels(operation=operation).observe(duration)
            threshold = max(0, settings.SLOW_QUERY_MS) / 1000
            if threshold and duration >= threshold:
                DB_SLOW.labels(operation=operation).inc()
                db_logger.warning(
                    "slow database query",
                    extra={
                        "operation": operation,
                        "duration_ms": round(duration * 1000, 2),
                        "sql": _sql_shape(sql),
                    },
                )


class RequestObservabilityMiddleware(MiddlewareMixin):
    def process_request(self, request):
        incoming = request.headers.get("X-Request-ID", "").strip()
        request_id = incoming if REQUEST_ID_RE.fullmatch(incoming) else uuid.uuid4().hex
        request._observability_started = time.perf_counter()
        request._observability_request_id = request_id
        request._observability_tokens = (
            request_id_var.set(request_id),
            request_method_var.set(request.method),
            request_route_var.set("-"),
        )
        request._observability_stack = ExitStack()
        wrapper = QueryMetricsWrapper()
        for connection in connections.all():
            request._observability_stack.enter_context(connection.execute_wrapper(wrapper))
        HTTP_ACTIVE.inc()


    def process_view(self, request, view_func, view_args, view_kwargs):
        request_route_var.set(_route_label(request))

    def process_exception(self, request, exception):
        access_logger.exception(
            "unhandled request exception",
            extra={"exception_type": type(exception).__name__},
        )

    def process_response(self, request, response):
        request_id = getattr(request, "_observability_request_id", uuid.uuid4().hex)
        route = _route_label(request)
        route_token = request_route_var.set(route)
        started = getattr(request, "_observability_started", time.perf_counter())
        duration = max(0.0, time.perf_counter() - started)
        method = getattr(request, "method", "UNKNOWN")
        status = str(getattr(response, "status_code", 500))

        response["X-Request-ID"] = request_id
        HTTP_REQUESTS.labels(method=method, route=route, status=status).inc()
        HTTP_DURATION.labels(method=method, route=route).observe(duration)
        HTTP_ACTIVE.dec()

        log_method = access_logger.warning if int(status) >= 500 else access_logger.info
        log_method(
            "http request",
            extra={
                "status": int(status),
                "duration_ms": round(duration * 1000, 2),
                "content_length": response.get("Content-Length"),
            },
        )

        stack = getattr(request, "_observability_stack", None)
        if stack is not None:
            stack.close()
        request_route_var.reset(route_token)
        tokens = getattr(request, "_observability_tokens", None)
        if tokens:
            request_id_var.reset(tokens[0])
            request_method_var.reset(tokens[1])
            request_route_var.reset(tokens[2])
        return response
