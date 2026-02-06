import json

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect, ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .responses import json_nostore


@require_GET
def auth_me_api(request):
    user = request.user
    if user.is_authenticated:
        return json_nostore(
            {
                "authenticated": True,
                "user": {"id": user.id, "username": user.get_username(), "email": user.email},
            }
        )
    return json_nostore({"authenticated": False, "user": None})


@require_POST
def auth_login_api(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return json_nostore({"error": "Invalid JSON body"}, status=400)

    username = payload.get("username")
    password = payload.get("password")
    if not username or not password:
        return json_nostore({"error": "Missing credentials"}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is None:
        return json_nostore({"error": "Invalid username or password"}, status=401)

    login(request, user)
    return json_nostore(
        {
            "authenticated": True,
            "user": {"id": user.id, "username": user.get_username(), "email": user.email},
        }
    )


@require_POST
def auth_logout_api(request):
    logout(request)
    return json_nostore({"authenticated": False})


if not settings.DEBUG:
    auth_login_api = csrf_protect(auth_login_api)
    auth_logout_api = csrf_protect(auth_logout_api)


@ensure_csrf_cookie
@require_GET
def auth_csrf_api(request):
    get_token(request)
    return json_nostore({"ok": True})