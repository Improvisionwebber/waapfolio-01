import os
import sys

# Add your project directory to the Python path
sys.path.insert(0, '/home/waapfoli/waapfolio')  # <- your cPanel project path
sys.path.insert(1, '/home/waapfoli/waapfolio/project')  # optional if Django settings are in 'project'

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')

application = get_wsgi_application()
