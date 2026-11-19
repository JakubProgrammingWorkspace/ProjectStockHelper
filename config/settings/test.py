from config.settings.base import *

DEBUG = False

# Use in-memory SQLite for fast testing
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Speed up tests by disabling migrations where possible
# pytest-django --nomigrations is also an option, but this is a fallback
# MIGRATION_MODULES = {
#     "stock_data": None,
# }

# In-memory cache for tests
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "unique-snowflake",
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Celery / Task queue settings (if any) should be synchronous
# CELERY_TASK_ALWAYS_EAGER = True

# Custom flag to use mock API clients in services
USE_MOCK_API_CLIENTS = True

# Disable logging during tests
import logging

logging.disable(logging.CRITICAL)
