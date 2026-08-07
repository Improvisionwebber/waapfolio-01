from django.conf import settings
from .models import Store
import logging

logger = logging.getLogger(__name__)


class StoreSubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    def __call__(self, request):
        print("STORE MIDDLEWARE HIT")
        print("HOST:", request.get_host())

        response = self.get_response(request)
        return response
    def __call__(self, request):

        request.store = None

        # -----------------------------
        # Ignore system routes
        # -----------------------------
        ignored_prefixes = [
            "/admin/",
            "/account/",
            "/payment/",
            "/paystack/",
            "/pricing/",
            "/register/",
            "/store/",
            "/static/",
            "/media/",
        ]

        if any(request.path.startswith(prefix) for prefix in ignored_prefixes):
            return self.get_response(request)

        # -----------------------------
        # Current host
        # -----------------------------
        host = request.get_host().split(":")[0].lower()

        # -----------------------------
        # Development
        # -----------------------------
        if settings.DEBUG:

            # localhost and 127.0.0.1 should never use subdomains
            if host in ["127.0.0.1", "localhost"]:
                return self.get_response(request)

            # Example:
            # mystore.localhost
            if host.endswith(".localhost"):

                subdomain = host.split(".")[0]

                try:
                    request.store = Store.objects.get(slug=subdomain)

                except Store.DoesNotExist:
                    logger.warning(
                        f"Store '{subdomain}' not found."
                    )

            return self.get_response(request)

        # -----------------------------
        # Production
        # -----------------------------
        main_domains = [
            "waapfolio.com",
            "www.waapfolio.com",
        ]

        if host in main_domains:
            return self.get_response(request)

        parts = host.split(".")

        # Needs:
        # mystore.waapfolio.com
        if len(parts) < 3:
            return self.get_response(request)

        subdomain = parts[0]

        try:

            request.store = Store.objects.get(
                slug=subdomain
            )

        except Store.DoesNotExist:

            logger.warning(
                f"Store '{subdomain}' not found."
            )

            request.store = None

        return self.get_response(request)