"""
ASGI config for trafik_tahmin project.
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'trafik_tahmin.settings')

application = get_asgi_application() 