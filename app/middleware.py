# app/middleware.py
class StoreSubdomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host().split(':')[0]  # remove port if present
        parts = host.split('.')

        if len(parts) > 2:
            request.subdomain = parts[0]
        elif host.startswith('local-'):  # e.g., local-ekeson.waapfolio.com
            request.subdomain = host.split('-')[1]
        else:
            request.subdomain = None

        return self.get_response(request)
