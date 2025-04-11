from .base import *
DEBUG = False

ALLOWED_HOSTS = ['45.147.47.221', 'istanbultrafiksistemi.site', 'www.istanbultrafiksistemi.site', 'localhost', '127.0.0.1']

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')