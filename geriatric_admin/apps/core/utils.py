"""
Utility functions for the core application.

This module provides common utility functions used throughout
the geriatric administration system.
"""

import uuid
import hashlib
import secrets
from datetime import datetime, timedelta
from django.utils import timezone
from django.conf import settings
from django.core.cache import cache
from django.contrib.auth import get_user_model
from cryptography.fernet import Fernet
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


def generate_employee_id(center_code=None):
    """
    Generate a unique employee ID.
    
    Args:
        center_code: Optional center code to include in ID
        
    Returns:
        str: Unique employee ID
    """
    timestamp = datetime.now().strftime('%Y%m')
    random_part = secrets.token_hex(3).upper()
    
    if center_code:
        return f"{center_code}-{timestamp}-{random_part}"
    else:
        return f"EMP-{timestamp}-{random_part}"


def generate_secure_token(length=32):
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token in bytes
        
    Returns:
        str: Secure random token
    """
    return secrets.token_urlsafe(length)


def hash_sensitive_data(data):
    """
    Hash sensitive data for storage or comparison.
    
    Args:
        data: Data to hash
        
    Returns:
        str: Hashed data
    """
    if not data:
        return None
        
    # Use SHA-256 with salt
    salt = settings.SECRET_KEY.encode('utf-8')
    return hashlib.pbkdf2_hmac('sha256', str(data).encode('utf-8'), salt, 100000).hex()


def encrypt_data(data):
    """
    Encrypt sensitive data using Fernet encryption.
    
    Args:
        data: Data to encrypt
        
    Returns:
        str: Encrypted data
    """
    if not data:
        return None
        
    encryption_settings = getattr(settings, 'ENCRYPTION_SETTINGS', {})
    if not encryption_settings.get('ENABLED', True):
        return data
        
    key = encryption_settings.get('KEY')
    if not key:
        logger.warning("Encryption key not configured, storing data unencrypted")
        return data
        
    try:
        fernet = Fernet(key.encode())
        encrypted_data = fernet.encrypt(str(data).encode('utf-8'))
        return encrypted_data.decode('utf-8')
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        return data


def decrypt_data(encrypted_data):
    """
    Decrypt data using Fernet encryption.
    
    Args:
        encrypted_data: Encrypted data to decrypt
        
    Returns:
        str: Decrypted data
    """
    if not encrypted_data:
        return None
        
    encryption_settings = getattr(settings, 'ENCRYPTION_SETTINGS', {})
    if not encryption_settings.get('ENABLED', True):
        return encrypted_data
        
    key = encryption_settings.get('KEY')
    if not key:
        return encrypted_data
        
    try:
        fernet = Fernet(key.encode())
        decrypted_data = fernet.decrypt(encrypted_data.encode('utf-8'))
        return decrypted_data.decode('utf-8')
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        return encrypted_data


def get_client_ip(request):
    """
    Get the client IP address from a request.
    
    Args:
        request: Django request object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    """
    Get the user agent string from a request.
    
    Args:
        request: Django request object
        
    Returns:
        str: User agent string
    """
    return request.META.get('HTTP_USER_AGENT', '')


def cache_key_for_user(user, key_suffix):
    """
    Generate a cache key for a specific user.
    
    Args:
        user: User instance
        key_suffix: Suffix for the cache key
        
    Returns:
        str: Cache key
    """
    return f"user_{user.id}_{key_suffix}"


def cache_key_for_center(center, key_suffix):
    """
    Generate a cache key for a specific center.
    
    Args:
        center: GeriatricCenter instance
        key_suffix: Suffix for the cache key
        
    Returns:
        str: Cache key
    """
    center_id = center.id if hasattr(center, 'id') else center
    return f"center_{center_id}_{key_suffix}"


def invalidate_user_cache(user):
    """
    Invalidate all cache entries for a user.
    
    Args:
        user: User instance
    """
    # Common cache keys to invalidate
    cache_keys = [
        cache_key_for_user(user, 'permissions'),
        cache_key_for_user(user, 'centers'),
        cache_key_for_user(user, 'preferences'),
        cache_key_for_user(user, 'profile'),
    ]
    
    cache.delete_many(cache_keys)


def invalidate_center_cache(center):
    """
    Invalidate all cache entries for a center.
    
    Args:
        center: GeriatricCenter instance
    """
    cache_keys = [
        cache_key_for_center(center, 'occupancy'),
        cache_key_for_center(center, 'staff'),
        cache_key_for_center(center, 'statistics'),
    ]
    
    cache.delete_many(cache_keys)


def format_phone_number(phone_number):
    """
    Format a phone number for display.
    
    Args:
        phone_number: Raw phone number string
        
    Returns:
        str: Formatted phone number
    """
    if not phone_number:
        return ''
        
    # Remove all non-digit characters
    digits = ''.join(filter(str.isdigit, phone_number))
    
    # Format based on length
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone_number  # Return original if can't format


def validate_employee_id(employee_id):
    """
    Validate an employee ID format.
    
    Args:
        employee_id: Employee ID to validate
        
    Returns:
        bool: True if valid, False otherwise
    """
    if not employee_id:
        return False
        
    # Basic format validation (can be customized)
    import re
    pattern = r'^[A-Z0-9]{3,}-\d{6}-[A-F0-9]{6}$'
    return bool(re.match(pattern, employee_id))


def get_password_strength(password):
    """
    Evaluate password strength.
    
    Args:
        password: Password to evaluate
        
    Returns:
        dict: Password strength information
    """
    if not password:
        return {'score': 0, 'feedback': ['Password is required']}
    
    score = 0
    feedback = []
    
    # Length check
    if len(password) >= 12:
        score += 2
    elif len(password) >= 8:
        score += 1
    else:
        feedback.append('Password should be at least 8 characters long')
    
    # Character variety checks
    if any(c.islower() for c in password):
        score += 1
    else:
        feedback.append('Include lowercase letters')
        
    if any(c.isupper() for c in password):
        score += 1
    else:
        feedback.append('Include uppercase letters')
        
    if any(c.isdigit() for c in password):
        score += 1
    else:
        feedback.append('Include numbers')
        
    if any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password):
        score += 1
    else:
        feedback.append('Include special characters')
    
    # Common password check
    common_passwords = ['password', '123456', 'qwerty', 'admin']
    if password.lower() in common_passwords:
        score = max(0, score - 2)
        feedback.append('Avoid common passwords')
    
    return {
        'score': min(score, 5),  # Max score of 5
        'feedback': feedback
    }


def generate_audit_context(request, action, resource_type=None, resource_id=None):
    """
    Generate context information for audit logging.
    
    Args:
        request: Django request object
        action: Action being performed
        resource_type: Type of resource being accessed
        resource_id: ID of the resource
        
    Returns:
        dict: Audit context information
    """
    return {
        'timestamp': timezone.now().isoformat(),
        'user_id': request.user.id if request.user.is_authenticated else None,
        'username': request.user.username if request.user.is_authenticated else None,
        'ip_address': get_client_ip(request),
        'user_agent': get_user_agent(request),
        'action': action,
        'resource_type': resource_type,
        'resource_id': resource_id,
        'session_key': request.session.session_key,
        'path': request.path,
        'method': request.method,
    }


def log_security_event(event_type, user=None, details=None, request=None):
    """
    Log a security-related event.
    
    Args:
        event_type: Type of security event
        user: User involved in the event
        details: Additional event details
        request: Django request object
    """
    security_logger = logging.getLogger('django.security')
    
    log_data = {
        'event_type': event_type,
        'timestamp': timezone.now().isoformat(),
        'user_id': user.id if user else None,
        'username': user.username if user else None,
        'details': details or {},
    }
    
    if request:
        log_data.update({
            'ip_address': get_client_ip(request),
            'user_agent': get_user_agent(request),
            'path': request.path,
            'method': request.method,
        })
    
    security_logger.warning(f"Security Event: {event_type}", extra=log_data)


def is_business_hours(center=None):
    """
    Check if current time is within business hours.
    
    Args:
        center: Optional center to check specific hours
        
    Returns:
        bool: True if within business hours
    """
    now = timezone.now()
    current_time = now.time()
    current_day = now.weekday()  # 0 = Monday, 6 = Sunday
    
    # Default business hours (can be customized per center)
    start_time = datetime.strptime('06:00', '%H:%M').time()
    end_time = datetime.strptime('22:00', '%H:%M').time()
    
    # Check if it's a weekday (Monday-Friday)
    if current_day < 5:  # Monday to Friday
        return start_time <= current_time <= end_time
    else:  # Weekend
        # Reduced hours on weekends
        weekend_start = datetime.strptime('08:00', '%H:%M').time()
        weekend_end = datetime.strptime('20:00', '%H:%M').time()
        return weekend_start <= current_time <= weekend_end


def sanitize_filename(filename):
    """
    Sanitize a filename for safe storage.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    import re
    
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]
    
    # Replace unsafe characters
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    
    # Limit length
    if len(filename) > 100:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:95] + ('.' + ext if ext else '')
    
    return filename


def get_system_health_status():
    """
    Get basic system health status.
    
    Returns:
        dict: System health information
    """
    from django.db import connection
    
    health_status = {
        'timestamp': timezone.now().isoformat(),
        'database': 'unknown',
        'cache': 'unknown',
        'disk_space': 'unknown',
    }
    
    # Check database connection
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            health_status['database'] = 'healthy'
    except Exception as e:
        health_status['database'] = f'error: {str(e)}'
        logger.error(f"Database health check failed: {e}")
    
    # Check cache
    try:
        cache.set('health_check', 'test', 10)
        if cache.get('health_check') == 'test':
            health_status['cache'] = 'healthy'
        else:
            health_status['cache'] = 'error: cache not working'
    except Exception as e:
        health_status['cache'] = f'error: {str(e)}'
        logger.error(f"Cache health check failed: {e}")
    
    return health_status