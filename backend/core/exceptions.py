from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        detail = response.data
        response.data = {
            "success": False,
            "status_code": response.status_code,
            "message": _get_error_message(detail),
            "errors": detail,
        }

    return response


def _get_error_message(detail):
    if isinstance(detail, dict):
        for field, errors in detail.items():
            if isinstance(errors, list) and len(errors) > 0:
                return str(errors[0])
            return str(errors)
    if isinstance(detail, list) and len(detail) > 0:
        return str(detail[0])
    return str(detail)
