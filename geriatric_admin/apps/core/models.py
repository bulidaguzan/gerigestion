"""
Core models for the Geriatric Administration System.

This module contains base models and mixins that provide common functionality
across all applications in the system, including audit trails, multi-center
data isolation, and user management.
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from encrypted_model_fields.fields import EncryptedCharField, EncryptedTextField
from .managers import (
    ActiveModelManager, CenterAwareManager, UserManager, 
    GeriatricCenterManager, UserCenterAssignmentManager, AuditTrailManager
)


class BaseModel(models.Model):
    """
    Abstract base model that provides common fields for all models in the system.
    
    This model includes:
    - UUID primary key for better security and scalability
    - Creation and modification timestamps
    - User tracking for who created/modified records
    - Soft delete functionality
    - Common metadata fields
    """
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        help_text="Unique identifier for this record"
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when this record was created"
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp when this record was last updated"
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_created',
        null=True,
        blank=True,
        help_text="User who created this record"
    )
    
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='%(class)s_updated',
        null=True,
        blank=True,
        help_text="User who last updated this record"
    )
    
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this record is active (soft delete functionality)"
    )
    
    version = models.PositiveIntegerField(
        default=1,
        help_text="Version number for optimistic locking"
    )
    
    notes = models.TextField(
        blank=True,
        help_text="Additional notes or comments about this record"
    )
    
    objects = ActiveModelManager()
    
    class Meta:
        abstract = True
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        """
        Override save to implement version control and validation.
        """
        if self.pk:
            # Increment version on update
            self.version += 1
            
        # Call full_clean to ensure validation
        self.full_clean()
        
        super().save(*args, **kwargs)
        
    def soft_delete(self, user=None):
        """
        Perform a soft delete by setting is_active to False.
        
        Args:
            user: The user performing the deletion
        """
        self.is_active = False
        if user:
            self.updated_by = user
        self.save(update_fields=['is_active', 'updated_by', 'updated_at', 'version'])
        
    def restore(self, user=None):
        """
        Restore a soft-deleted record by setting is_active to True.
        
        Args:
            user: The user performing the restoration
        """
        self.is_active = True
        if user:
            self.updated_by = user
        self.save(update_fields=['is_active', 'updated_by', 'updated_at', 'version'])
        
    def __str__(self):
        """
        Default string representation showing the model name and ID.
        """
        return f"{self.__class__.__name__} ({str(self.id)[:8]}...)"


class AuditMixin(models.Model):
    """
    Mixin that provides comprehensive audit trail functionality.
    
    This mixin tracks all changes to model instances and provides
    a complete audit history for compliance and security purposes.
    """
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        """
        Override save to create audit trail entries.
        """
        # Determine if this is a create or update operation
        is_create = self.pk is None
        
        # Store original values for comparison
        original_values = {}
        if not is_create:
            try:
                original = self.__class__.objects.get(pk=self.pk)
                original_values = {
                    field.name: getattr(original, field.name)
                    for field in self._meta.fields
                    if hasattr(original, field.name)
                }
            except self.__class__.DoesNotExist:
                pass
        
        # Call the parent save method
        super().save(*args, **kwargs)
        
        # Create audit trail entry
        self._create_audit_entry(
            action='CREATE' if is_create else 'UPDATE',
            original_values=original_values
        )
        
    def delete(self, *args, **kwargs):
        """
        Override delete to create audit trail entry.
        """
        # Store current values before deletion
        current_values = {
            field.name: getattr(self, field.name)
            for field in self._meta.fields
            if hasattr(self, field.name)
        }
        
        # Call the parent delete method
        result = super().delete(*args, **kwargs)
        
        # Create audit trail entry
        self._create_audit_entry(
            action='DELETE',
            original_values=current_values
        )
        
        return result
        
    def _create_audit_entry(self, action, original_values=None):
        """
        Create an audit trail entry for this model instance.
        
        Args:
            action: The action performed (CREATE, UPDATE, DELETE)
            original_values: Dictionary of original field values (for updates)
        """
        from django.contrib.auth import get_user_model
        from threading import local
        
        # Get current user from thread-local storage (set by middleware)
        _thread_locals = getattr(self, '_thread_locals', local())
        current_user = getattr(_thread_locals, 'user', None)
        
        # Get current center from thread-local storage
        current_center = getattr(_thread_locals, 'center', None)
        
        # Prepare changed fields for UPDATE actions
        changed_fields = {}
        if action == 'UPDATE' and original_values:
            for field_name, original_value in original_values.items():
                current_value = getattr(self, field_name, None)
                if original_value != current_value:
                    changed_fields[field_name] = {
                        'old': str(original_value) if original_value is not None else None,
                        'new': str(current_value) if current_value is not None else None
                    }
        
        # Create the audit entry
        AuditTrail.objects.create(
            content_type=ContentType.objects.get_for_model(self),
            object_id=str(self.pk),
            action=action,
            user=current_user,
            center=current_center,
            changed_fields=changed_fields,
            ip_address=getattr(_thread_locals, 'ip_address', None),
            user_agent=getattr(_thread_locals, 'user_agent', None)
        )


class MultiCenterMixin(models.Model):
    """
    Mixin that provides multi-center data isolation functionality.
    
    This mixin ensures that data is properly isolated between different
    geriatric centers while allowing for consolidated reporting and management.
    """
    
    center = models.ForeignKey(
        'core.GeriatricCenter',
        on_delete=models.PROTECT,
        help_text="The geriatric center this record belongs to"
    )
    
    class Meta:
        abstract = True
        
    def save(self, *args, **kwargs):
        """
        Override save to ensure center assignment.
        """
        # If no center is assigned, try to get it from thread-local storage
        if not self.center_id:
            from threading import local
            _thread_locals = getattr(self, '_thread_locals', local())
            current_center = getattr(_thread_locals, 'center', None)
            
            if current_center:
                self.center = current_center
            else:
                raise ValidationError("Center must be specified for this record")
        
        super().save(*args, **kwargs)
        
    @classmethod
    def get_for_center(cls, center):
        """
        Get all records for a specific center.
        
        Args:
            center: The GeriatricCenter instance or ID
            
        Returns:
            QuerySet filtered by center
        """
        return cls.objects.filter(center=center, is_active=True)
        
    @classmethod
    def get_for_user_centers(cls, user):
        """
        Get all records for centers accessible to a user.
        
        Args:
            user: The User instance
            
        Returns:
            QuerySet filtered by user's accessible centers
        """
        user_centers = user.centers.all()
        return cls.objects.filter(center__in=user_centers, is_active=True)


class User(AbstractUser):
    """
    Custom user model extending Django's AbstractUser.
    
    This model provides additional fields and functionality specific
    to the geriatric administration system, including multi-center
    support and enhanced security features.
    """
    
    ROLE_CHOICES = [
        ('administrator', 'Administrator'),
        ('nurse', 'Nurse'),
        ('caregiver', 'Caregiver'),
        ('doctor', 'Doctor'),
        ('manager', 'Manager'),
        ('receptionist', 'Receptionist'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique employee identifier"
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        help_text="User's primary role in the system"
    )
    
    centers = models.ManyToManyField(
        'core.GeriatricCenter',
        through='core.UserCenterAssignment',
        through_fields=('user', 'center'),
        help_text="Centers this user has access to"
    )
    
    phone_number = EncryptedCharField(
        max_length=20,
        blank=True,
        help_text="User's phone number (encrypted)"
    )
    
    emergency_contact_name = EncryptedCharField(
        max_length=100,
        blank=True,
        help_text="Emergency contact name (encrypted)"
    )
    
    emergency_contact_phone = EncryptedCharField(
        max_length=20,
        blank=True,
        help_text="Emergency contact phone (encrypted)"
    )
    
    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text="User's date of birth"
    )
    
    hire_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date when user was hired"
    )
    
    is_multi_center_admin = models.BooleanField(
        default=False,
        help_text="Whether user can access multiple centers"
    )
    
    failed_login_attempts = models.PositiveIntegerField(
        default=0,
        help_text="Number of consecutive failed login attempts"
    )
    
    last_failed_login = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of last failed login attempt"
    )
    
    account_locked_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Account locked until this timestamp"
    )
    
    password_changed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When password was last changed"
    )
    
    must_change_password = models.BooleanField(
        default=False,
        help_text="Whether user must change password on next login"
    )
    
    two_factor_enabled = models.BooleanField(
        default=False,
        help_text="Whether two-factor authentication is enabled"
    )
    
    two_factor_secret = EncryptedCharField(
        max_length=32,
        blank=True,
        help_text="Two-factor authentication secret (encrypted)"
    )
    
    # Password reset fields
    password_reset_token = EncryptedCharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="Token for password reset (encrypted)"
    )
    
    password_reset_token_created = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When password reset token was created"
    )
    
    password_reset_token_expires = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When password reset token expires"
    )
    
    preferences = models.JSONField(
        default=dict,
        blank=True,
        help_text="User preferences and settings"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserManager()
    
    class Meta:
        db_table = 'core_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    def __str__(self):
        return f"{self.get_full_name()} ({self.employee_id})"
        
    def get_full_name(self):
        """
        Return the user's full name.
        """
        return f"{self.first_name} {self.last_name}".strip() or self.username
        
    def is_account_locked(self):
        """
        Check if the account is currently locked.
        """
        if self.account_locked_until:
            return timezone.now() < self.account_locked_until
        return False
        
    def lock_account(self, duration_minutes=30):
        """
        Lock the account for a specified duration.
        
        Args:
            duration_minutes: How long to lock the account (default 30 minutes)
        """
        from datetime import timedelta
        self.account_locked_until = timezone.now() + timedelta(minutes=duration_minutes)
        self.save(update_fields=['account_locked_until'])
        
    def unlock_account(self):
        """
        Unlock the account and reset failed login attempts.
        """
        self.account_locked_until = None
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.save(update_fields=['account_locked_until', 'failed_login_attempts', 'last_failed_login'])
        
    def record_failed_login(self):
        """
        Record a failed login attempt and lock account if necessary.
        """
        self.failed_login_attempts += 1
        self.last_failed_login = timezone.now()
        
        # Lock account after max attempts
        max_attempts = getattr(settings, 'GERIATRIC_ADMIN_SETTINGS', {}).get('MAX_LOGIN_ATTEMPTS', 5)
        if self.failed_login_attempts >= max_attempts:
            lockout_duration = getattr(settings, 'GERIATRIC_ADMIN_SETTINGS', {}).get('LOCKOUT_DURATION_MINUTES', 30)
            self.lock_account(lockout_duration)
            
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'account_locked_until'])
        
    def record_successful_login(self):
        """
        Record a successful login and reset failed attempts.
        """
        self.failed_login_attempts = 0
        self.last_failed_login = None
        self.last_login = timezone.now()
        self.save(update_fields=['failed_login_attempts', 'last_failed_login', 'last_login'])
        
    def needs_password_change(self):
        """
        Check if user needs to change their password.
        """
        if self.must_change_password:
            return True
            
        if self.password_changed_at:
            from datetime import timedelta
            expiry_days = getattr(settings, 'GERIATRIC_ADMIN_SETTINGS', {}).get('PASSWORD_EXPIRY_DAYS', 90)
            expiry_date = self.password_changed_at + timedelta(days=expiry_days)
            return timezone.now().date() > expiry_date.date()
            
        return False
        
    def get_accessible_centers(self):
        """
        Get all centers this user has access to.
        """
        return self.centers.filter(is_active=True)
        
    def has_center_access(self, center):
        """
        Check if user has access to a specific center.
        
        Args:
            center: GeriatricCenter instance or ID
        """
        if self.is_multi_center_admin:
            return True
        return self.centers.filter(id=center.id if hasattr(center, 'id') else center).exists()
    
    def generate_password_reset_token(self):
        """
        Generate a secure password reset token.
        
        Returns:
            str: Generated token
        """
        import secrets
        import hashlib
        
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        
        # Hash the token for storage
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        
        # Set expiration (24 hours from now)
        from datetime import timedelta
        expires = timezone.now() + timedelta(hours=24)
        
        # Save token hash and expiration
        self.password_reset_token = token_hash
        self.password_reset_token_created = timezone.now()
        self.password_reset_token_expires = expires
        self.save(update_fields=[
            'password_reset_token', 
            'password_reset_token_created', 
            'password_reset_token_expires'
        ])
        
        return token
    
    def verify_password_reset_token(self, token):
        """
        Verify if a password reset token is valid.
        
        Args:
            token: Token to verify
            
        Returns:
            bool: True if token is valid, False otherwise
        """
        import hashlib
        
        if not self.password_reset_token or not self.password_reset_token_expires:
            return False
        
        # Check if token has expired
        if timezone.now() > self.password_reset_token_expires:
            return False
        
        # Hash the provided token and compare
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        return token_hash == self.password_reset_token
    
    def clear_password_reset_token(self):
        """
        Clear the password reset token.
        """
        self.password_reset_token = None
        self.password_reset_token_created = None
        self.password_reset_token_expires = None
        self.save(update_fields=[
            'password_reset_token', 
            'password_reset_token_created', 
            'password_reset_token_expires'
        ])


class GeriatricCenter(BaseModel):
    """
    Model representing a geriatric care center.
    
    This model stores information about individual geriatric centers
    and is used for multi-center data isolation.
    """
    
    name = models.CharField(
        max_length=200,
        help_text="Name of the geriatric center"
    )
    
    code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Unique code for the center"
    )
    
    address = EncryptedTextField(
        help_text="Physical address of the center (encrypted)"
    )
    
    phone_number = EncryptedCharField(
        max_length=20,
        help_text="Main phone number (encrypted)"
    )
    
    email = models.EmailField(
        help_text="Main email address"
    )
    
    license_number = EncryptedCharField(
        max_length=50,
        help_text="Operating license number (encrypted)"
    )
    
    capacity = models.PositiveIntegerField(
        help_text="Maximum resident capacity"
    )
    
    administrator = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='administered_centers',
        help_text="Center administrator"
    )
    
    settings = models.JSONField(
        default=dict,
        blank=True,
        help_text="Center-specific configuration settings"
    )
    
    objects = GeriatricCenterManager()
    
    class Meta:
        db_table = 'core_geriatric_center'
        verbose_name = 'Geriatric Center'
        verbose_name_plural = 'Geriatric Centers'
        
    def __str__(self):
        return f"{self.name} ({self.code})"
        
    def get_current_occupancy(self):
        """
        Get current occupancy count for this center.
        """
        # This will be implemented when the residents app is created
        return 0
        
    def get_occupancy_rate(self):
        """
        Get current occupancy rate as a percentage.
        """
        if self.capacity == 0:
            return 0
        return (self.get_current_occupancy() / self.capacity) * 100


class UserCenterAssignment(BaseModel):
    """
    Through model for User-Center many-to-many relationship.
    
    This model tracks which users have access to which centers
    and provides additional metadata about the assignment.
    """
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        help_text="User being assigned to center"
    )
    
    center = models.ForeignKey(
        GeriatricCenter,
        on_delete=models.CASCADE,
        help_text="Center being assigned to user"
    )
    
    is_primary = models.BooleanField(
        default=False,
        help_text="Whether this is the user's primary center"
    )
    
    assigned_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When user was assigned to this center"
    )
    
    assigned_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='center_assignments_made',
        help_text="User who made this assignment"
    )
    
    objects = UserCenterAssignmentManager()
    
    class Meta:
        db_table = 'core_user_center_assignment'
        unique_together = ['user', 'center']
        verbose_name = 'User Center Assignment'
        verbose_name_plural = 'User Center Assignments'
        
    def __str__(self):
        return f"{self.user} -> {self.center}"


class AuditTrail(models.Model):
    """
    Model for storing comprehensive audit trail information.
    
    This model tracks all changes to sensitive data for compliance
    and security purposes.
    """
    
    ACTION_CHOICES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('VIEW', 'View'),
        ('LOGIN', 'Login'),
        ('LOGOUT', 'Logout'),
        ('EXPORT', 'Export'),
        ('IMPORT', 'Import'),
    ]
    
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False
    )
    
    timestamp = models.DateTimeField(
        auto_now_add=True,
        help_text="When the action occurred"
    )
    
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="User who performed the action"
    )
    
    center = models.ForeignKey(
        GeriatricCenter,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Center context for the action"
    )
    
    action = models.CharField(
        max_length=10,
        choices=ACTION_CHOICES,
        help_text="Type of action performed"
    )
    
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        help_text="Type of object that was modified"
    )
    
    object_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="ID of the object that was modified"
    )
    
    content_object = GenericForeignKey('content_type', 'object_id')
    
    changed_fields = models.JSONField(
        default=dict,
        blank=True,
        help_text="Fields that were changed and their old/new values"
    )
    
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address of the user"
    )
    
    user_agent = models.TextField(
        blank=True,
        null=True,
        help_text="User agent string from the request"
    )
    
    additional_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context data"
    )
    
    objects = AuditTrailManager()
    
    class Meta:
        db_table = 'core_audit_trail'
        verbose_name = 'Audit Trail Entry'
        verbose_name_plural = 'Audit Trail Entries'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['user']),
            models.Index(fields=['center']),
            models.Index(fields=['action']),
            models.Index(fields=['content_type', 'object_id']),
        ]
        
    def __str__(self):
        return f"{self.action} by {self.user} at {self.timestamp}"