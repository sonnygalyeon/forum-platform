from rest_framework.exceptions import ErrorDetail, Throttled, ValidationError
from rest_framework.views import exception_handler as drf_exception_handler


def _to_plain(value):
    if isinstance(value, ErrorDetail):
        return str(value)
    if isinstance(value, dict):
        return {key: _to_plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_plain(item) for item in value]
    return value


def api_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    original_data = response.data

    if isinstance(exc, ValidationError):
        code = "validation_error"
        message = "Request validation failed."
        fields = _to_plain(original_data)
    else:
        try:
            code = exc.get_codes()
        except AttributeError:
            code = getattr(exc, "default_code", "api_error")

        if isinstance(code, (dict, list)):
            code = getattr(exc, "default_code", "api_error")

        if isinstance(original_data, dict) and "detail" in original_data:
            message = str(original_data["detail"])
        else:
            message = str(getattr(exc, "detail", "Request failed."))

        fields = None

    payload = {
        "error": {
            "code": str(code),
            "message": message,
            "status": response.status_code,
        }
    }

    if fields is not None:
        payload["error"]["fields"] = fields

    if isinstance(exc, Throttled):
        payload["error"]["retry_after"] = exc.wait

    response.data = payload
    return response
