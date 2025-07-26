"""
Signal handlers for the core application.

This module contains signal handlers that respond to model events
and perform additional processing like audit logging and cache invalidation.
"""

from django.db.models.signals import post_save, post_delete, pre_save
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import GeriatricCenter, UserCenterAssignment, AuditTrail
from .utils import invalidate_user_cache, invalidate_center_cache, log_security_event
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """
    Handle user creation and updates.
    """
    if created:
        logger.info(f"New user created: {instance.username} ({instance.employee_id})")
        
        # Log user creation in audit trail
        AuditTrail.objects.create(
            action='CREATE',
            user=instance,
            additional_data={
                'user_created': True,
                'employee_id': instance.employee_id,
                'role': instance.role,
            }
        )
    else:
        # Invalidate user cache on update
        invalidate_user_cache(instance)
        
        logger.info(f"User updated: {instance.username}")


@receiver(post_save, sender=GeriatricCenter)
def center_post_save(sender, instance, created, **kwargs):
    """
    Handle center creation and updates.
    """
    if created:
        logger.info(f"New center created: {instance.name} ({instance.code})")
    else:
        # Invalidate center cache on update
        invalidate_center_cache(instance)
        
        logger.info(f"Center updated: {instance.name}")


@receiver(post_save, sender=UserCenterAssignment)
def user_center_assignment_post_save(sender, instance, created, **kwargs):
    """
    Handle user-center assignment changes.
    """
    # Invalidate user cache when assignments change
    invalidate_user_cache(instance.user)
    
    if created:
        logger.info(f"User {instance.user.username} assigned to center {instance.center.name}")
    else:
        logger.info(f"User-center assignment updated: {instance.user.username} -> {instance.center.name}")


@receiver(user_logged_in)
def user_logged_in_handler(sender, request, user, **kwargs):
    """
    Handle successful user login.
    """
    # Create audit trail entry
    AuditTrail.objects.create(
        action='LOGIN',
        user=user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        additional_data={
            'login_successful': True,
            'session_key': request.session.session_key,
        }
    )
    
    # Log security event
    log_security_event(
        'USER_LOGIN_SUCCESS',
        user=user,
        request=request,
        details={'method': 'password'}
    )
    
    logger.info(f"User logged in: {user.username}")


@receiver(user_logged_out)
def user_logged_out_handler(sender, request, user, **kwargs):
    """
    Handle user logout.
    """
    if user:
        # Create audit trail entry
        AuditTrail.objects.create(
            action='LOGOUT',
            user=user,
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            additional_data={
                'logout': True,
                'session_key': request.session.session_key,
            }
        )
        
        # Log security event
        log_security_event(
            'USER_LOGOUT',
            user=user,
            request=request
        )
        
        logger.info(f"User logged out: {user.username}")


@receiver(user_login_failed)
def user_login_failed_handler(sender, credentials, request, **kwargs):
    """
    Handle failed login attempts.
    """
    username = credentials.get('username', 'unknown')
    
    # Try to find the user
    user = None
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        try:
            user = User.objects.get(employee_id=username)
        except User.DoesNotExist:
            pass
    
    # Create audit trail entry
    AuditTrail.objects.create(
        action='LOGIN',
        user=user,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        additional_data={
            'login_failed': True,
            'attempted_username': username,
            'failure_reason': 'invalid_credentials',
        }
    )
    
    # Log security event
    log_security_event(
        'USER_LOGIN_FAILED',
        user=user,
        request=request,
        details={
            'attempted_username': username,
            'reason': 'invalid_credentials'
        }
    )
    
    logger.warning(f"Failed login attempt for username: {username}")


@receiver(pre_save, sender=User)
def user_pre_save(sender, instance, **kwargs):
    """
    Handle user model changes before saving.
    """
    if instance.pk:
        try:
            old_instance = User.objects.get(pk=instance.pk)
            
            # Check if password was changed
            if old_instance.password != instance.password:
                instance.password_changed_at = timezone.now()
                instance.must_change_password = False
                
                logger.info(f"Password changed for user: {instance.username}")
                
                # Log security event
                log_security_event(
                    'PASSWORD_CHANGED',
                    user=instance,
                    details={'password_changed': True}
                )
            
            # Check if account was locked/unlocked
            if old_instance.account_locked_until != instance.account_locked_until:
                if instance.account_locked_until:
                    logger.warning(f"Account locked: {instance.username}")
                    log_security_event(
                        'ACCOUNT_LOCKED',
                        user=instance,
                        details={'locked_until': instance.account_locked_until.isoformat()}
                    )
                else:
                    logger.info(f"Account unlocked: {instance.username}")
                    log_security_event(
                        'ACCOUNT_UNLOCKED',
                        user=instance,
                        details={'account_unlocked': True}
                    )
            
            # Check if account was deactivated
            if old_instance.is_active and not instance.is_active:
                logger.warning(f"Account deactivated: {instance.username}")
                log_security_event(
                    'ACCOUNT_DEACTIVATED',
                    user=instance,
                    details={'account_deactivated': True}
                )
            elif not old_instance.is_active and instance.is_active:
                logger.info(f"Account reactivated: {instance.username}")
                log_security_event(
                    'ACCOUNT_REACTIVATED',
                    user=instance,
                    details={'account_reactivated': True}
                )
                
        except User.DoesNotExist:
            pass  # New user, no old instance to compare