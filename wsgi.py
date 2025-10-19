import os
import django.core.wsgi


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings.production")
application = django.core.wsgi.get_wsgi_application()
