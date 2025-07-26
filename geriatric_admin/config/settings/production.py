"""
Production settings for Geriatric Administration System.
"""

from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database with connection pooling
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'sslmode': 'require',
            'options': '-c default_transaction_isolation=serializable'
        },
        'CONN_MAX_AGE': 600,
    }
}

# Redis cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'CONNECTION_POOL_KWARGS': {
                'max_connections': 50,
                'retry_on_timeout': True,
            },
            'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
            'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
        }
    }
}

# Session configuration for production
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'
SESSION_COOKIE_AGE = 3600  # 1 hour

# CSRF configuration
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Strict'

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')

# Static files configuration for production
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'

# Media files configuration for production
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Security settings for production
SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# CORS settings for production
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True

# Logging configuration for production
LOGGING['handlers']['file']['level'] = 'WARNING'
LOGGING['handlers']['console']['level'] = 'ERROR'
LOGGING['loggers']['django']['level'] = 'WARNING'

# Add security logging
LOGGING['handlers']['security_file'] = {
    'level': 'WARNING',
    'class': 'logging.handlers.RotatingFileHandler',
    'filename': BASE_DIR / 'logs' / 'security.log',
    'maxBytes': 1024*1024*15,  # 15MB
    'backupCount': 10,
    'formatter': 'json',
}

LOGGING['loggers']['django.security'] = {
    'handlers': ['security_file', 'console'],
    'level': 'WARNING',
    'propagate': False,
}

# Production-specific settings
GERIATRIC_ADMIN_SETTINGS.update({
    'AUDIT_ENABLED': True,
    'MULTI_CENTER_ENABLED': True,
    'ENCRYPTION_ENABLED': True,
    'BACKUP_RETENTION_DAYS': 2555,  # 7 years for compliance
    'SESSION_TIMEOUT_MINUTES': 30,  # Shorter for security
    'PASSWORD_EXPIRY_DAYS': 60,  # More frequent password changes
    'MAX_LOGIN_ATTEMPTS': 3,  # Stricter for production
    'LOCKOUT_DURATION_MINUTES': 60,  # Longer lockout for security
})

# Performance optimizations
CONN_MAX_AGE = 600
DATABASES['default']['CONN_MAX_AGE'] = CONN_MAX_AGE

# Ensure logs directory exists
import os
os.makedirs(BASE_DIR / 'logs', exist_ok=True)