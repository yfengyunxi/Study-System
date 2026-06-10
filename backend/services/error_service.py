from flask import jsonify


def build_error(code, message, *, details=None, field_errors=None, retryable=False, request_id=None):
    return {
        "message": message,
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "field_errors": field_errors or {},
            "retryable": bool(retryable),
            "request_id": request_id,
        },
    }


def error_response(code, message, *, status=400, details=None, field_errors=None, retryable=False, request_id=None):
    return jsonify(
        build_error(
            code,
            message,
            details=details,
            field_errors=field_errors,
            retryable=retryable,
            request_id=request_id,
        )
    ), status
