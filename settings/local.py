from settings.base import *


INSTALLED_APPS.extend([
    # Place here your apps
])

MIDDLEWARE.extend([
    # Place here your middleware
])

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
