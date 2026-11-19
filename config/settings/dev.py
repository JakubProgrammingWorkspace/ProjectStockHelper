from config.settings.base import *

DEBUG = True
# CORS settings for React frontend
CORS_ALLOW_ALL_ORIGINS = True
# CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS')

ALLOWED_HOSTS = ["*"]

# dev tools
# INSTALLED_APPS += ['django_extensions']

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
