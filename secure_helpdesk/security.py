import re

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse


class BasicWAFMiddleware:
    BLOCK_PATTERNS = [
        re.compile(r"(?i)(\bunion\b\s+\bselect\b)"),
        re.compile(r"(?i)(<\s*script\b)"),
        re.compile(r"(?i)(\.\./)"),
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        payload = " ".join(
            [
                request.META.get("QUERY_STRING", ""),
                request.META.get("HTTP_USER_AGENT", ""),
                request.POST.urlencode() if request.method == "POST" else "",
            ]
        )
        if any(pattern.search(payload) for pattern in self.BLOCK_PATTERNS):
            return HttpResponse("Request blocked by security policy.", status=400)
        return self.get_response(request)


class RequestSafetyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.max_body_bytes = getattr(settings, "MAX_REQUEST_BODY_BYTES", 1_048_576)
        self.max_query_chars = getattr(settings, "MAX_QUERY_STRING_LENGTH", 2048)

    def __call__(self, request):
        content_length = request.META.get("CONTENT_LENGTH")
        if content_length and content_length.isdigit() and int(content_length) > self.max_body_bytes:
            return HttpResponse("Payload too large.", status=413)
        if len(request.META.get("QUERY_STRING", "")) > self.max_query_chars:
            return HttpResponse("Query string too long.", status=414)
        return self.get_response(request)


class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.window = getattr(settings, "RATE_LIMIT_WINDOW_SECONDS", 900)
        self.auth_limit = getattr(settings, "AUTH_RATE_LIMIT_ATTEMPTS", 5)
        self.default_limit = getattr(settings, "DEFAULT_RATE_LIMIT_ATTEMPTS", 120)
        self.auth_patterns = [re.compile(pattern) for pattern in getattr(settings, "AUTH_RATE_LIMIT_PATHS", [])]

    def __call__(self, request):
        identifier = self._client_identifier(request)
        path = request.path
        limit = self.auth_limit if self._is_auth_path(path) else self.default_limit
        cache_key = f"ratelimit:{identifier}:{path}"
        if self._is_limited(cache_key, limit):
            retry_after = self.window
            response_data = {"detail": "Too many requests. Please try again later.", "retry_after_seconds": retry_after}
            return JsonResponse(response_data, status=429)
        if self._is_auth_path(path):
            username = (request.POST.get("username") or "").strip().lower() if request.method == "POST" else ""
            if username:
                user_key = f"ratelimit:auth-user:{username}:{path}"
                if self._is_limited(user_key, self.auth_limit):
                    response_data = {"detail": "Too many authentication attempts for this account. Please try again later."}
                    return JsonResponse(response_data, status=429)
        return self.get_response(request)

    def _is_limited(self, key, limit):
        count = cache.get(key, 0)
        if count >= limit:
            return True
        cache.set(key, count + 1, timeout=self.window)
        return False

    def _is_auth_path(self, path):
        return any(pattern.match(path) for pattern in self.auth_patterns)

    @staticmethod
    def _client_identifier(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
