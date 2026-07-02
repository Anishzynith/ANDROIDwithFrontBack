from rest_framework.response import Response


def success_response(message="Operation successful", data=None, status_code=200, **extra):
    payload = {"success": True, "message": message, "data": data or {}}
    payload.update(extra)
    return Response(payload, status=status_code)


def error_response(message="Operation failed", errors=None, status_code=400, **extra):
    payload = {"success": False, "message": message, "errors": errors or {}}
    payload.update(extra)
    return Response(payload, status=status_code)
