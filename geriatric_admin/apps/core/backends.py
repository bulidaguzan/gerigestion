"""
Custom authentication backends for the Geriatric Administration System.

This module provides enhanced authentication backends with additional
security features like account lockout, audit logging, and multi-center
support.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone
from django.conf import settings
from .models import AuditTrail
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class GeriatricAuthenticationBackend(ModelBackend):
    """
    Custom authentication backend with enhanced security features.
    
    This backend supports authentication by username or employee ID,
    implements account lockout protection, and provides comprehensive
    audit logging for all authentication attempts.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user with enhanced security checks.
        
        Args:
            request: The HTTP request object
            username: Username or employee ID
            password: User's password
            **kwargs: Additional authentication parameters
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        if username is None or password is None:
            return None
        
        # Try to find user by username or employee_id
        try:
            user = User.objects.get(
                Q(username=username) | Q(employee_id=username),
                is_active=True
            )
        except User.DoesNotExist:
            # Log failed authentication attempt for non-existent user
            self._log_authentication_attempt(
                request=request,
                username=username,
                success=False,
                reason='user_not_found'
            )
            return None
        except User.MultipleObjectsReturned:
            # This shouldn't happen with proper constraints, but handle it
            logger.error(f"Multiple users found for identifier: {username}")
            self._log_authentication_attempt(
                request=request,
                username=username,
                success=False,
                reason='multiple_users_found'
            )
            return None
        
        # Check if account is locked
        if user.is_account_locked():
            self._log_authentication_attempt(
                request=request,
                username=username,
                user=user,
                success=False,
                reason='account_locked'
            )
            return None
        
        # Check password
        if user.check_password(password):
            # Password is correct, perform additional checks
            
            # Check if password change is required
            if user.needs_password_change():
                self._log_authentication_attempt(
                    request=request,
                    username=username,
                    user=user,
                    success=False,
                    reason='password_change_required'
                )
                # Don't return None here - let the view handle password change requirement
                # But mark it in the user object for the view to check
                user._password_change_required = True
            
            # Check if user has center assignments (unless they're a superuser)
            if not user.is_superuser and not user.is_multi_center_admin:
                if not user.centers.filter(is_active=True).exists():
                    self._log_authentication_attempt(
                        request=request,
                        username=username,
                        user=user,
                        success=False,
                        reason='no_center_assignment'
                    )
                    return None
            
            # Authentication successful
            user.record_successful_login()
            
            self._log_authentication_attempt(
                request=request,
                username=username,
                user=user,
                success=True,
                reason='success'
            )
            
            return user
        else:
            # Password is incorrect
            user.record_failed_login()
            
            self._log_authentication_attempt(
                request=request,
                username=username,
                user=user,
                success=False,
                reason='invalid_password'
            )
            
            return None
    
    def get_user(self, user_id):
        """
        Get user by ID with additional security checks.
        
        Args:
            user_id: User's primary key
            
        Returns:
            User instance if found and active, None otherwise
        """
        try:
            user = User.objects.get(pk=user_id, is_active=True)
            
            # Additional security check - ensure account is not locked
            if user.is_account_locked():
                return None
                
            return user
        except User.DoesNotExist:
            return None
    
    def _log_authentication_attempt(self, request, username, success, reason, user=None):
        """
        Log authentication attempt for audit purposes.
        
        Args:
            request: HTTP request object
            username: Attempted username/employee_id
            success: Whether authentication was successful
            reason: Reason for success/failure
            user: User object if found
        """
        try:
            from .utils import get_client_ip, get_user_agent
            
            # Create audit trail entry
            AuditTrail.objects.create(
                action='LOGIN',
                user=user,
                ip_address=get_client_ip(request) if request else None,
                user_agent=get_user_agent(request) if request else '',
                additional_data={
                    'attempted_username': username,
                    'success': success,
                    'reason': reason,
                    'timestamp': timezone.now().isoformat(),
                    'user_agent_full': request.META.get('HTTP_USER_AGENT', '') if request else '',
                    'remote_addr': request.META.get('REMOTE_ADDR', '') if request else '',
                    'http_x_forwarded_for': request.META.get('HTTP_X_FORWARDED_FOR', '') if request else '',
                }
            )
            
            # Also log to security logger
            if success:
                logger.info(
                    f"Successful authentication for user {username} from "
                    f"{get_client_ip(request) if request else 'unknown'}"
                )
            else:
                logger.warning(
                    f"Failed authentication attempt for user {username} from "
                    f"{get_client_ip(request) if request else 'unknown'}: {reason}"
                )
                
        except Exception as e:
            # Don't let audit logging failures break authentication
            logger.error(f"Failed to log authentication attempt: {e}")


class TwoFactorAuthenticationBackend(GeriatricAuthenticationBackend):
    """
    Authentication backend with two-factor authentication support.
    
    This backend extends the base authentication to support TOTP-based
    two-factor authentication for enhanced security.
    """
    
    def authenticate(self, request, username=None, password=None, totp_token=None, **kwargs):
        """
        Authenticate user with two-factor authentication.
        
        Args:
            request: The HTTP request object
            username: Username or employee ID
            password: User's password
            totp_token: TOTP token for 2FA
            **kwargs: Additional authentication parameters
            
        Returns:
            User instance if authentication successful, None otherwise
        """
        # First, perform standard authentication
        user = super().authenticate(request, username, password, **kwargs)
        
        if user is None:
            return None
        
        # Check if 2FA is enabled for this user
        if user.two_factor_enabled:
            if totp_token is None:
                # 2FA token required but not provided
                self._log_authentication_attempt(
                    request=request,
                    username=username,
                    user=user,
                    success=False,
                    reason='2fa_token_required'
                )
                # Mark user as requiring 2FA
                user._requires_2fa = True
                return user
            
            # Verify TOTP token
            if not self._verify_totp_token(user, totp_token):
                self._log_authentication_attempt(
                    request=request,
                    username=username,
                    user=user,
                    success=False,
                    reason='invalid_2fa_token'
                )
                return None
            
            # 2FA verification successful
            self._log_authentication_attempt(
                request=request,
                username=username,
                user=user,
                success=True,
                reason='2fa_success'
            )
        
        return user
    
    def _verify_totp_token(self, user, token):
        """
        Verify TOTP token for two-factor authentication.
        
        Args:
            user: User instance
            token: TOTP token to verify
            
        Returns:
            True if token is valid, False otherwise
        """
        if not user.two_factor_secret:
            return False
        
        try:
            import pyotp
            
            # Create TOTP object with user's secret
            totp = pyotp.TOTP(user.two_factor_secret)
            
            # Verify token with some time window tolerance
            return totp.verify(token, valid_window=1)
            
        except ImportError:
            logger.error("pyotp library not installed - 2FA verification failed")
            return False
        except Exception as e:
            logger.error(f"Error verifying TOTP token: {e}")
            return False


class EmergencyAccessBackend(ModelBackend):
    """
    Emergency access backend for system administrators.
    
    This backend provides emergency access capabilities for system
    administrators when normal authentication systems are unavailable.
    """
    
    def authenticate(self, request, username=None, password=None, emergency_code=None, **kwargs):
        """
        Authenticate using emergency access credentials.
        
        Args:
            request: The HTTP request object
            username: Username
            password: Password
            emergency_code: Emergency access code
            **kwargs: Additional parameters
            
        Returns:
            User instance if emergency authentication successful, None otherwise
        """
        # Emergency access is only available in specific circumstances
        if not self._is_emergency_access_enabled():
            return None
        
        if emergency_code is None:
            return None
        
        # Verify emergency code
        if not self._verify_emergency_code(emergency_code):
            self._log_emergency_access_attempt(
                request=request,
                username=username,
                success=False,
                reason='invalid_emergency_code'
            )
            return None
        
        # Try to find user
        try:
            user = User.objects.get(username=username, is_superuser=True, is_active=True)
        except User.DoesNotExist:
            self._log_emergency_access_attempt(
                request=request,
                username=username,
                success=False,
                reason='user_not_found'
            )
            return None
        
        # Verify password
        if not user.check_password(password):
            self._log_emergency_access_attempt(
                request=request,
                username=username,
                user=user,
                success=False,
                reason='invalid_password'
            )
            return None
        
        # Emergency access granted
        self._log_emergency_access_attempt(
            request=request,
            username=username,
            user=user,
            success=True,
            reason='emergency_access_granted'
        )
        
        return user
    
    def _is_emergency_access_enabled(self):
        """
        Check if emergency access is enabled.
        
        Returns:
            True if emergency access is enabled, False otherwise
        """
        return getattr(settings, 'GERIATRIC_ADMIN_SETTINGS', {}).get('EMERGENCY_ACCESS_ENABLED', False)
    
    def _verify_emergency_code(self, code):
        """
        Verify emergency access code.
        
        Args:
            code: Emergency access code
            
        Returns:
            True if code is valid, False otherwise
        """
        expected_code = getattr(settings, 'GERIATRIC_ADMIN_SETTINGS', {}).get('EMERGENCY_ACCESS_CODE')
        return expected_code and code == expected_code
    
    def _log_emergency_access_attempt(self, request, username, success, reason, user=None):
        """
        Log emergency access attempt.
        
        Args:
            request: HTTP request object
            username: Attempted username
            success: Whether access was granted
            reason: Reason for success/failure
            user: User object if found
        """
        try:
            from .utils import get_client_ip, get_user_agent
            
            AuditTrail.objects.create(
                action='LOGIN',
                user=user,
                ip_address=get_client_ip(request) if request else None,
                user_agent=get_user_agent(request) if request else '',
                additional_data={
                    'emergency_access': True,
                    'attempted_username': username,
                    'success': success,
                    'reason': reason,
                    'timestamp': timezone.now().isoformat(),
                }
            )
            
            # Log to security logger with high priority
            if success:
                logger.critical(
                    f"EMERGENCY ACCESS GRANTED for user {username} from "
                    f"{get_client_ip(request) if request else 'unknown'}"
                )
            else:
                logger.error(
                    f"EMERGENCY ACCESS ATTEMPT FAILED for user {username} from "
                    f"{get_client_ip(request) if request else 'unknown'}: {reason}"
                )
                
        except Exception as e:
            logger.error(f"Failed to log emergency access attempt: {e}")