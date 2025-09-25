import sys
import os
import traceback

try:
    # -------------------------------
    # 0️⃣ Activate server virtual environment
    # -------------------------------
    activate_this = '/home/waapfoli/virtualenv/waapfolio/3.11/bin/activate_this.py'
    with open(activate_this) as f:
        exec(f.read(), {'__file__': activate_this})

    # -------------------------------
    # 1️⃣ Add project paths
    # -------------------------------
    sys.path.insert(0, '/home/waapfoli/public_html')          # project root
    sys.path.insert(1, '/home/waapfoli/public_html/project')  # settings folder

    # -------------------------------
    # 2️⃣ Set Django settings
    # -------------------------------
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

    # -------------------------------
    # 3️⃣ Load WSGI application
    # -------------------------------
    from django.core.wsgi import get_wsgi_application
    application = get_wsgi_application()

except Exception:
    log_path = "/home/waapfoli/public_html/wsgi_debug.log"
    with open(log_path, "w") as f:
        f.write(traceback.format_exc())
    raise
