"""
Custom model managers for the core application.

This module provides custom managers that implement business logic
for querying and managing core models with proper data isolation
and security considerations.
"""

from django.db import models
from django.contrib.auth.models import UserManager as BaseUserManager
from django.utils import timezone


class ActiveModelManager(models.Manager):
    """
    Manager that filters out soft-deleted records by default.
    """
    
    def get_queryset(self):
        """
        Return only active (non-soft-deleted) records.
        """
        return super().get_queryset().filter(is_active=True)
    
    def with_deleted(self):
        """
        Return all records including soft-deleted ones.
        """
        return super().get_queryset()
    
    def deleted_only(self):
        """
        Return only soft-deleted records.
        """
        return super().get_queryset().filter(is_active=False)


class CenterAwareManager(ActiveModelManager):
    """
    Manager that provides center-aware querying for multi-center data isolation.
    """
    
    def for_center(self, center):
        """
        Filter records for a specific center.
        
        Args:
            center: GeriatricCenter instance or ID
        """
        center_id = center.id if hasattr(center, 'id') else center
        return self.get_queryset().filter(center_id=center_id)
    
    def for_user_centers(self, user):
        """
        Filter records for centers accessible to a user.
        
        Args:
            user: User instance
        """
        if user.is_multi_center_admin:
            return self.get_queryset()
        
        user_centers = user.centers.all()
        return self.get_queryset().filter(center__in=user_centers)


class UserManager(BaseUserManager):
    """
    Custom manager for the User model with additional functionality.
    """
    
    def create_user(self, username, email=None, password=None, **extra_fields):
        """
        Create and save a regular user with the given username, email, and password.
        """
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        
        # Set password change timestamp
        extra_fields['password_changed_at'] = timezone.now()
        
        return self._create_user(username, email, password, **extra_fields)
    
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        """
        Create and save a superuser with the given username, email, and password.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_multi_center_admin', True)
        extra_fields.setdefault('role', 'administrator')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        # Set password change timestamp
        extra_fields['password_changed_at'] = timezone.now()
        
        return self._create_user(username, email, password, **extra_fields)
    
    def active_users(self):
        """
        Return only active users.
        """
        return self.get_queryset().filter(is_active=True)
    
    def by_role(self, role):
        """
        Filter users by role.
        
        Args:
            role: User role string
        """
        return self.get_queryset().filter(role=role, is_active=True)
    
    def for_center(self, center):
        """
        Get users who have access to a specific center.
        
        Args:
            center: GeriatricCenter instance or ID
        """
        center_id = center.id if hasattr(center, 'id') else center
        return self.get_queryset().filter(
            centers__id=center_id,
            is_active=True
        ).distinct()
    
    def administrators(self):
        """
        Get all administrator users.
        """
        return self.by_role('administrator')
    
    def nurses(self):
        """
        Get all nurse users.
        """
        return self.by_role('nurse')
    
    def caregivers(self):
        """
        Get all caregiver users.
        """
        return self.by_role('caregiver')
    
    def doctors(self):
        """
        Get all doctor users.
        """
        return self.by_role('doctor')
    
    def locked_accounts(self):
        """
        Get all currently locked user accounts.
        """
        now = timezone.now()
        return self.get_queryset().filter(
            account_locked_until__gt=now,
            is_active=True
        )
    
    def password_expired(self):
        """
        Get users whose passwords have expired.
        """
        from datetime import timedelta
        from django.conf import settings
        
        expiry_days = getattr(settings, 'GERIATRIC_ADMIN_SETTINGS', {}).get('PASSWORD_EXPIRY_DAYS', 90)
        expiry_threshold = timezone.now() - timedelta(days=expiry_days)
        
        return self.get_queryset().filter(
            models.Q(password_changed_at__lt=expiry_threshold) |
            models.Q(must_change_password=True),
            is_active=True
        )


class GeriatricCenterManager(ActiveModelManager):
    """
    Custom manager for GeriatricCenter model.
    """
    
    def by_code(self, code):
        """
        Get center by its unique code.
        
        Args:
            code: Center code string
        """
        try:
            return self.get_queryset().get(code=code)
        except self.model.DoesNotExist:
            return None
    
    def for_user(self, user):
        """
        Get centers accessible to a user.
        
        Args:
            user: User instance
        """
        if user.is_multi_center_admin:
            return self.get_queryset()
        
        return self.get_queryset().filter(
            id__in=user.centers.values_list('id', flat=True)
        )
    
    def with_capacity_info(self):
        """
        Annotate centers with occupancy information.
        """
        # This will be enhanced when residents app is implemented
        return self.get_queryset().annotate(
            current_occupancy=models.Value(0, output_field=models.IntegerField())
        )
    
    def over_capacity_threshold(self, threshold=0.9):
        """
        Get centers that are over a certain capacity threshold.
        
        Args:
            threshold: Capacity threshold as a decimal (0.9 = 90%)
        """
        # This will be enhanced when residents app is implemented
        return self.get_queryset().filter(
            capacity__gt=0
        ).annotate(
            current_occupancy=models.Value(0, output_field=models.IntegerField()),
            occupancy_rate=models.Case(
                models.When(capacity=0, then=models.Value(0.0)),
                default=models.F('current_occupancy') * 1.0 / models.F('capacity'),
                output_field=models.FloatField()
            )
        ).filter(occupancy_rate__gte=threshold)


class UserCenterAssignmentManager(ActiveModelManager):
    """
    Custom manager for UserCenterAssignment model.
    """
    
    def for_user(self, user):
        """
        Get all center assignments for a user.
        
        Args:
            user: User instance
        """
        return self.get_queryset().filter(user=user)
    
    def for_center(self, center):
        """
        Get all user assignments for a center.
        
        Args:
            center: GeriatricCenter instance
        """
        return self.get_queryset().filter(center=center)
    
    def primary_assignments(self):
        """
        Get only primary center assignments.
        """
        return self.get_queryset().filter(is_primary=True)
    
    def assign_user_to_center(self, user, center, is_primary=False, assigned_by=None):
        """
        Assign a user to a center.
        
        Args:
            user: User instance
            center: GeriatricCenter instance
            is_primary: Whether this is the primary center assignment
            assigned_by: User who made the assignment
        """
        # If this is a primary assignment, unset other primary assignments
        if is_primary:
            self.get_queryset().filter(user=user, is_primary=True).update(is_primary=False)
        
        assignment, created = self.get_or_create(
            user=user,
            center=center,
            defaults={
                'is_primary': is_primary,
                'assigned_by': assigned_by,
            }
        )
        
        if not created and is_primary:
            assignment.is_primary = True
            assignment.save(update_fields=['is_primary'])
        
        return assignment


class AuditTrailManager(models.Manager):
    """
    Custom manager for AuditTrail model.
    """
    
    def for_user(self, user):
        """
        Get audit entries for a specific user.
        
        Args:
            user: User instance
        """
        return self.get_queryset().filter(user=user)
    
    def for_center(self, center):
        """
        Get audit entries for a specific center.
        
        Args:
            center: GeriatricCenter instance
        """
        return self.get_queryset().filter(center=center)
    
    def for_object(self, obj):
        """
        Get audit entries for a specific object.
        
        Args:
            obj: Model instance
        """
        from django.contrib.contenttypes.models import ContentType
        content_type = ContentType.objects.get_for_model(obj)
        return self.get_queryset().filter(
            content_type=content_type,
            object_id=str(obj.pk)
        )
    
    def by_action(self, action):
        """
        Filter audit entries by action type.
        
        Args:
            action: Action string (CREATE, UPDATE, DELETE, etc.)
        """
        return self.get_queryset().filter(action=action)
    
    def recent(self, days=30):
        """
        Get recent audit entries within specified days.
        
        Args:
            days: Number of days to look back
        """
        from datetime import timedelta
        threshold = timezone.now() - timedelta(days=days)
        return self.get_queryset().filter(timestamp__gte=threshold)
    
    def security_events(self):
        """
        Get security-related audit entries.
        """
        security_actions = ['LOGIN', 'LOGOUT', 'VIEW']
        return self.get_queryset().filter(action__in=security_actions)
    
    def data_changes(self):
        """
        Get data modification audit entries.
        """
        change_actions = ['CREATE', 'UPDATE', 'DELETE']
        return self.get_queryset().filter(action__in=change_actions)
    
    def failed_access_attempts(self):
        """
        Get audit entries for failed access attempts.
        """
        return self.get_queryset().filter(
            additional_data__contains={'access_denied': True}
        )
    
    def create_audit_entry(self, action, user=None, center=None, content_object=None, 
                          changed_fields=None, ip_address=None, user_agent=None, 
                          additional_data=None):
        """
        Create a new audit trail entry.
        
        Args:
            action: Action type
            user: User who performed the action
            center: Center context
            content_object: Object that was modified
            changed_fields: Dictionary of changed fields
            ip_address: IP address of the request
            user_agent: User agent string
            additional_data: Additional context data
        """
        from django.contrib.contenttypes.models import ContentType
        
        entry_data = {
            'action': action,
            'user': user,
            'center': center,
            'changed_fields': changed_fields or {},
            'ip_address': ip_address,
            'user_agent': user_agent,
            'additional_data': additional_data or {},
        }
        
        if content_object:
            entry_data['content_type'] = ContentType.objects.get_for_model(content_object)
            entry_data['object_id'] = str(content_object.pk)
        
        return self.create(**entry_data)