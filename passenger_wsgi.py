import sys, os, traceback

try:
    sys.path.insert(0, '/home/waapfoli/waapfolio')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()
except Exception:
    with open("/home/waapfoli/waapfolio/wsgi_debug.log", "w") as f:
        f.write(traceback.format_exc())
    raise
