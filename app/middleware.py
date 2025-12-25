from django.conf import settings
from django.http import Http404
from .models import Store

class StoreSubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.store = None  # default, always safe

        host = request.get_host().split(':')[0]

        # -----------------------------
        # Ignore localhost completely
        # -----------------------------
        if settings.DEBUG:
            return self.get_response(request)

        # -----------------------------
        # Ignore main domain
        # -----------------------------
        if host in ["waapfolio.com", "www.waapfolio.com"]:
            return self.get_response(request)

        # -----------------------------
        # Extract subdomain
        # -----------------------------
        parts = host.split('.')
        if len(parts) < 3:
            return self.get_response(request)

        subdomain = parts[0]

        # -----------------------------
        # Load store safely (fail gracefully)
        # -----------------------------
        try:
            request.store = Store.objects.get(slug=subdomain)
        except Store.DoesNotExist:
            request.store = None  # ← no 404, fail silently

        return self.get_response(request)
