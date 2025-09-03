import os
import sys

# Add your public_html folder (app root)
sys.path.insert(0, '/home/waapfoli/public_html')
sys.path.insert(1, '/home/waapfoli/public_html/project')  # Django settings folder

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
