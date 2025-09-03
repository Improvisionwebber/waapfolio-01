import sys
import os

# Add your project directory to the Python path
sys.path.insert(0, '/home/waapfoli/waapfolio')

# Set the Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
