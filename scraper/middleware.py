from django.core.cache import cache
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

class RateLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/api/scrape/'):
            ip = request.META.get('REMOTE_ADDR')
            key = f'ratelimit:{ip}'
            if cache.get(key, 0) >= getattr(settings, 'RATE_LIMIT_PER_MINUTE', 60):
                return Response(
                    {"error": "Rate limit exceeded"},
                    status=status.HTTP_429_TOO_MANY_REQUESTS
                )
            cache.incr(key, 1)
            cache.expire(key, 60)  # Reset after 1 minute
        return self.get_response(request) 