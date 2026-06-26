from django.conf import settings
from django.http import Http404
from .models import Store
import logging

logger = logging.getLogger(__name__)

class StoreSubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        request.store = None

        # Ignore system routes
        ignored_prefixes = [
            "/payment/",
            "/paystack/",
            "/admin/",
            "/account/",
            "/pricing/",
            "/register/",
            "/store/",
        ]

        if any(request.path.startswith(x) for x in ignored_prefixes):
            return self.get_response(request)
    def __call__(self, request):
        request.store = None  # default, always safe

        # -----------------------------
        # Get host without port
        # -----------------------------
        host = request.get_host().split(':')[0].lower()

        # -----------------------------
        # Ignore localhost for dev
        # -----------------------------
        if settings.DEBUG:
            if host in ["127.0.0.1", "localhost"]:
                return self.get_response(request)

            parts = host.split('.')

            # local subdomain testing only
            # example: mystore.localhost
            if len(parts) >= 2 and parts[-1] == "localhost":
                subdomain = parts[0]
                try:
                    request.store = Store.objects.get(slug=subdomain)
                except Store.DoesNotExist:
                    request.store = None

            return self.get_response(request)

        # -----------------------------
        # Ignore main domain
        # -----------------------------
        if host in ["waapfolio.com", "www.waapfolio.com"]:
            return self.get_response(request)

        # -----------------------------
        # Extract subdomain safely
        # -----------------------------
        parts = host.split('.')
        if len(parts) < 3:  # e.g., waapfolio.com only
            return self.get_response(request)

        subdomain = parts[0]

        # -----------------------------
        # Map subdomain → store
        # -----------------------------
        try:
            request.store = Store.objects.get(slug=subdomain)
        except Store.DoesNotExist:
            request.store = None  # fail silently
            logger.warning(f"Subdomain '{subdomain}' does not match any store in DB.")

        return self.get_response(request)
