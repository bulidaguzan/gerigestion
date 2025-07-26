"""
Development settings for Geriatric Administration System.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Database - Use SQLite for development if PostgreSQL is not available
if os.environ.get('USE_SQLITE', 'False').lower() == 'true':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db_dev.sqlite3',
        }
    }
else:
    try:
        import psycopg2
        # Test PostgreSQL connection
        import psycopg2
        conn = psycopg2.connect(
            host=os.environ.get('DB_HOST', 'localhost'),
            port=os.environ.get('DB_PORT', '5432'),
            user=os.environ.get('DB_USER', 'postgres'),
            password=os.environ.get('DB_PASSWORD', ''),
            database=os.environ.get('DB_NAME', 'geriatric_admin_dev')
        )
        conn.close()
        
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_NAME', 'geriatric_admin_dev'),
                'USER': os.environ.get('DB_USER', 'postgres'),
                'PASSWORD': os.environ.get('DB_PASSWORD', ''),
                'HOST': os.environ.get('DB_HOST', 'localhost'),
                'PORT': os.environ.get('DB_PORT', '5432'),
                'CONN_MAX_AGE': 60,
            }
        }
    except (ImportError, Exception):
        # Fallback to SQLite for development if PostgreSQL is not available
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db_dev.sqlite3',
            }
        }

# Cache configuration for development - use Redis if available, fallback to local memory
try:
    import redis
    redis_client = redis.Redis.from_url(os.environ.get('REDIS_URL', 'redis://localhost:6379/1'))
    redis_client.ping()
    
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL', 'redis://localhost:6379/1'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 10,
                    'retry_on_timeout': True,
                },
                'IGNORE_EXCEPTIONS': True,
            },
            'TIMEOUT': 300,
            'KEY_PREFIX': 'geriatric_admin_dev',
        }
    }
except (redis.ConnectionError, redis.TimeoutError, ImportError):
    # Fallback to local memory cache if Redis is not available
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'geriatric-admin-dev-cache',
        }
    }

# Session configuration for development
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_AGE = 86400  # 24 hours for development

# Email backend for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Static files for development
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Development-specific middleware
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

# Add debug toolbar to installed apps
INSTALLED_APPS += [
    'debug_toolbar',
]

# Debug toolbar configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

# Disable security settings for development
SECURE_SSL_REDIRECT = False
SECURE_HSTS_SECONDS = 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

# CORS settings for development
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# Logging configuration for development
LOGGING['handlers']['console']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': True,
}

# Development-specific settings
GERIATRIC_ADMIN_SETTINGS.update({
    'AUDIT_ENABLED': True,
    'MULTI_CENTER_ENABLED': True,
    'ENCRYPTION_ENABLED': False,  # Disabled for easier development
    'SESSION_TIMEOUT_MINUTES': 480,  # 8 hours for development
    'MAX_LOGIN_ATTEMPTS': 10,  # More lenient for development
    'LOCKOUT_DURATION_MINUTES': 5,  # Shorter lockout for development
})