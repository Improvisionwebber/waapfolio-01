import sys
import os
import traceback

try:
    # Add the public_html folder (app root)
    sys.path.insert(0, '/home/waapfoli/public_html')
    sys.path.insert(1, '/home/waapfoli/public_html/project')  # Django settings folder

    # Set Django settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

    # Get WSGI application
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

except Exception:
    with open("/home/waapfoli/public_html/wsgi_debug.log", "w") as f:
        f.write(traceback.format_exc())
    raise
