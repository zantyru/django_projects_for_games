from builtins import FileNotFoundError
from pathlib import Path
from decouple import Config, RepositoryEnv, Csv


# ### Paths for files and directories

BASE_DIR = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = BASE_DIR.parent / ".env"
SQLITE_FILE_PATH = BASE_DIR / "db.sqlite3"
COMMON_TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_ROOT = BASE_DIR.parent / "django_projects_static"
# MEDIA_ROOT = BASE_DIR.parent / "django_projects_media"

try:
    config_env = Config(RepositoryEnv(ENV_FILE_PATH))
except FileNotFoundError:
    from decouple import config
    config_env = config


# ### Main flags and secrets

SECRET_KEY = config_env("SECRET_KEY")
DEBUG = config_env("DEBUG", cast=bool)
TEMPLATE_DEBUG = DEBUG
PRODUCTION_DATABASE = config_env("PRODUCTION_DATABASE", cast=bool)


# ### Log configuration

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'format': '%(name)-12s %(levelname)-8s %(message)s',
        },
        'file': {
            'format': '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'formatter': 'file',
            'filename': 'django_projects.log',
        },
    },
    'loggers': {
        '': {
            'level': 'DEBUG',
            'handlers': ['file'],
            'propagate': True,
        },
    },
}


# ### Internationalization, localization and datetime configuration

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_L10N = True
USE_TZ = True


# ### URLs configuration

ALLOWED_HOSTS = config_env("ALLOWED_HOSTS", cast=Csv())
STATIC_URL = "static/"
# MEDIA_URL = "media/"
# LOGIN_REDIRECT_URL = "/"
# LOGOUT_REDIRECT_URL = "/"


# ### Databases configuration

if PRODUCTION_DATABASE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config_env("DB_NAME"),
            "USER": config_env("DB_USER"),
            "PASSWORD": config_env("DB_PASSWORD"),
            "HOST": config_env("DB_HOST"),
            "PORT": config_env("DB_PORT"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": SQLITE_FILE_PATH,
        }
    }

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# ### Applications, middlewares and other Django's configuration

WSGI_APPLICATION = "wsgi.application"

ROOT_URLCONF = "urls"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": (COMMON_TEMPLATES_DIR,),
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": (
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ),
        },
    },
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ### Third-party modules configuration

# ...
