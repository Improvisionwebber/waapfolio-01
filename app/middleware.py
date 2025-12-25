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
        # 1. Ignore localhost completely
        # -----------------------------
        if settings.DEBUG:
            return self.get_response(request)

        # -----------------------------
        # 2. Ignore main domain
        # -----------------------------
        if host == "waapfolio.com" or host == "www.waapfolio.com":
            return self.get_response(request)

        # -----------------------------
        # 3. Extract subdomain
        # -----------------------------
        parts = host.split('.')

        # Expecting: slug.waapfolio.com
        if len(parts) < 3:
            return self.get_response(request)

        subdomain = parts[0]

        # -----------------------------
        # 4. Load store safely
        # -----------------------------
        try:
            request.store = Store.objects.get(slug=subdomain)
        except Store.DoesNotExist:
            raise Http404("Store not found")

        return self.get_response(request)
