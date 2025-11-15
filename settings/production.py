from settings.base import *


CSRF_TRUSTED_ORIGINS = config_env("CSRF_TRUSTED_ORIGINS", cast=Csv(), default='')

INSTALLED_APPS.extend([
    # Place here your apps
])

MIDDLEWARE.extend([
    # Place here your middleware
])

STATICFILES_DIRS.extend([
    #...
])


# ### Security

SECURE_HSTS_SECONDS = 60 * 60 * 24 * 7 * 52  # one year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_SSL_REDIRECT = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

X_FRAME_OPTIONS = 'DENY'

SESSION_COOKIE_SECURE = True
# SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

CSRF_COOKIE_SECURE = True
# CSRF_COOKIE_HTTPONLY = True

# Add django-referrer-policy
# Add django-csp
