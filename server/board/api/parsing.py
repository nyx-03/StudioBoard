import json


def parse_payload(request):
    """
    Parse request payload.
    - JSON body has priority when present
    - Fallback to request.POST
    - Always returns a dict
    """
    if not request.body:
        try:
            return request.POST.dict()
        except Exception:
            return {}

    try:
        data = json.loads(request.body.decode("utf-8"))
        return data if isinstance(data, dict) else {}
    except (json.JSONDecodeError, UnicodeDecodeError):
        try:
            return request.POST.dict()
        except Exception:
            return {}
    except Exception:
        try:
            return request.POST.dict()
        except Exception:
            return {}


def get_int(payload, key, default=None):
    """
    Safely extract an integer from payload (strings like "3" are accepted).
    Returns `default` if missing or invalid.
    """
    try:
        value = payload.get(key, default)
        if value is None:
            return default
        return int(value)
    except (TypeError, ValueError):
        return default