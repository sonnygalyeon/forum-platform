from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")
request_route_var: ContextVar[str] = ContextVar("request_route", default="-")
request_method_var: ContextVar[str] = ContextVar("request_method", default="-")
