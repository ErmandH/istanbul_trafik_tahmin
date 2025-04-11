"""
WSGI config for trafik_tahmin project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trafik_tahmin.settings.production')

application = get_wsgi_application() 