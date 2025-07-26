"""
Testing settings for Geriatric Administration System.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Use in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use local memory cache for testing
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
    }
}

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True
    
    def __getitem__(self, item):
        return None

MIGRATION_MODULES = DisableMigrations()

# Use console email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable password validation for testing
AUTH_PASSWORD_VALIDATORS = []

# Use weak password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable security features for testing
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0

# Disable logging during tests
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'class': 'logging.NullHandler',
        },
    },
    'root': {
        'handlers': ['null'],
    },
    'loggers': {
        'django': {
            'handlers': ['null'],
            'propagate': False,
        },
        'apps': {
            'handlers': ['null'],
            'propagate': False,
        },
    }
}

# Testing-specific settings
GERIATRIC_ADMIN_SETTINGS.update({
    'AUDIT_ENABLED': False,  # Disable for faster tests
    'MULTI_CENTER_ENABLED': True,  # Keep enabled to test multi-center logic
    'ENCRYPTION_ENABLED': False,  # Disable for faster tests
    'SESSION_TIMEOUT_MINUTES': 60,
    'MAX_LOGIN_ATTEMPTS': 5,
    'LOCKOUT_DURATION_MINUTES': 1,  # Short for testing
})

# Test runner configuration
TEST_RUNNER = 'django.test.runner.DiscoverRunner'

# Media files for testing
MEDIA_ROOT = '/tmp/geriatric_admin_test_media'

# Static files for testing
STATIC_ROOT = '/tmp/geriatric_admin_test_static'