import re

from django.conf import settings
from django.core.cache import cache
from django.http import HttpResponse, JsonResponse


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
        count = cache.get(cache_key, 0)
        if count >= limit:
            retry_after = self.window
            response_data = {"detail": "Too many requests. Please try again later.", "retry_after_seconds": retry_after}
            return JsonResponse(response_data, status=429)
        cache.set(cache_key, count + 1, timeout=self.window)
        return self.get_response(request)

    def _is_auth_path(self, path):
        return any(pattern.match(path) for pattern in self.auth_patterns)

    @staticmethod
    def _client_identifier(request):
        forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "unknown")
