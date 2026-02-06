from django.conf import settings
from django.http import JsonResponse


def json_nostore(data, status=200):
    """JsonResponse with cache disabled (important for Safari / proxies)."""
    resp = JsonResponse(data, status=status)
    resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    resp["Pragma"] = "no-cache"
    resp["Expires"] = "0"
    return resp


def require_auth(request):
    """Return a response if unauthenticated, else None."""
    if not request.user.is_authenticated:
        return json_nostore({"error": "Authentication required"}, status=401)
    return None