"""
Django admin configuration for core models.

This module provides admin interfaces for managing users, centers,
and audit trails with appropriate security and usability considerations.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import User, GeriatricCenter, UserCenterAssignment, AuditTrail


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Admin interface for the custom User model.
    """
    
    list_display = [
        'username', 'employee_id', 'get_full_name', 'role', 
        'is_active', 'is_staff', 'last_login', 'account_status'
    ]
    
    list_filter = [
        'role', 'is_active', 'is_staff', 'is_superuser', 
        'is_multi_center_admin', 'two_factor_enabled',
        'must_change_password', 'date_joined'
    ]
    
    search_fields = [
        'username', 'employee_id', 'first_name', 'last_name', 'email'
    ]
    
    ordering = ['username']
    
    readonly_fields = [
        'id', 'date_joined', 'last_login', 'created_at', 'updated_at',
        'failed_login_attempts', 'last_failed_login', 'password_changed_at'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('username', 'password', 'employee_id')
        }),
        ('Personal info', {
            'fields': (
                'first_name', 'last_name', 'email', 'phone_number',
                'date_of_birth', 'hire_date'
            )
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone'),
            'classes': ('collapse',)
        }),
        ('Role and Permissions', {
            'fields': (
                'role', 'is_active', 'is_staff', 'is_superuser',
                'is_multi_center_admin', 'groups', 'user_permissions'
            )
        }),
        ('Security', {
            'fields': (
                'two_factor_enabled', 'must_change_password',
                'failed_login_attempts', 'last_failed_login',
                'account_locked_until', 'password_changed_at'
            ),
            'classes': ('collapse',)
        }),
        ('Preferences', {
            'fields': ('preferences',),
            'classes': ('collapse',)
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'employee_id', 'password1', 'password2',
                'first_name', 'last_name', 'email', 'role'
            ),
        }),
    )
    
    def account_status(self, obj):
        """
        Display account status with visual indicators.
        """
        if obj.is_account_locked():
            return format_html(
                '<span style="color: red;">🔒 Locked until {}</span>',
                obj.account_locked_until.strftime('%Y-%m-%d %H:%M')
            )
        elif obj.needs_password_change():
            return format_html('<span style="color: orange;">⚠️ Password Change Required</span>')
        elif obj.failed_login_attempts > 0:
            return format_html(
                '<span style="color: orange;">⚠️ {} Failed Attempts</span>',
                obj.failed_login_attempts
            )
        else:
            return format_html('<span style="color: green;">✅ Active</span>')
    
    account_status.short_description = 'Account Status'
    
    def get_queryset(self, request):
        """
        Customize queryset based on user permissions.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Non-superusers can only see users from their centers
            if hasattr(request.user, 'centers'):
                user_centers = request.user.centers.all()
                qs = qs.filter(centers__in=user_centers).distinct()
        return qs


class UserCenterAssignmentInline(admin.TabularInline):
    """
    Inline admin for user-center assignments.
    """
    model = UserCenterAssignment
    extra = 1
    readonly_fields = ['assigned_at', 'created_at']
    
    def get_queryset(self, request):
        """
        Filter assignments based on user permissions.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'centers'):
            user_centers = request.user.centers.all()
            qs = qs.filter(center__in=user_centers)
        return qs


@admin.register(GeriatricCenter)
class GeriatricCenterAdmin(admin.ModelAdmin):
    """
    Admin interface for GeriatricCenter model.
    """
    
    list_display = [
        'name', 'code', 'administrator', 'capacity', 
        'occupancy_info', 'is_active', 'created_at'
    ]
    
    list_filter = ['is_active', 'created_at', 'capacity']
    
    search_fields = ['name', 'code', 'administrator__username']
    
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'created_by', 'updated_by'
    ]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'administrator')
        }),
        ('Contact Information', {
            'fields': ('address', 'phone_number', 'email')
        }),
        ('Operational Details', {
            'fields': ('license_number', 'capacity', 'is_active')
        }),
        ('Configuration', {
            'fields': ('settings',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'notes', 'created_at', 'updated_at', 
                'created_by', 'updated_by'
            ),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [UserCenterAssignmentInline]
    
    def occupancy_info(self, obj):
        """
        Display occupancy information.
        """
        current = obj.get_current_occupancy()
        rate = obj.get_occupancy_rate()
        
        if rate >= 90:
            color = 'red'
            icon = '🔴'
        elif rate >= 75:
            color = 'orange'
            icon = '🟡'
        else:
            color = 'green'
            icon = '🟢'
            
        return format_html(
            '<span style="color: {};">{} {}/{} ({:.1f}%)</span>',
            color, icon, current, obj.capacity, rate
        )
    
    occupancy_info.short_description = 'Occupancy'
    
    def get_queryset(self, request):
        """
        Filter centers based on user permissions.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'centers'):
            user_centers = request.user.centers.all()
            qs = qs.filter(id__in=user_centers)
        return qs


@admin.register(UserCenterAssignment)
class UserCenterAssignmentAdmin(admin.ModelAdmin):
    """
    Admin interface for UserCenterAssignment model.
    """
    
    list_display = [
        'user', 'center', 'is_primary', 'assigned_at', 
        'assigned_by', 'is_active'
    ]
    
    list_filter = ['is_primary', 'is_active', 'assigned_at']
    
    search_fields = [
        'user__username', 'user__employee_id', 
        'center__name', 'center__code'
    ]
    
    readonly_fields = [
        'id', 'assigned_at', 'created_at', 'updated_at'
    ]
    
    def get_queryset(self, request):
        """
        Filter assignments based on user permissions.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'centers'):
            user_centers = request.user.centers.all()
            qs = qs.filter(center__in=user_centers)
        return qs


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    """
    Admin interface for AuditTrail model (read-only).
    """
    
    list_display = [
        'timestamp', 'user', 'action', 'content_type', 
        'object_id', 'center', 'ip_address'
    ]
    
    list_filter = [
        'action', 'timestamp', 'content_type', 'center'
    ]
    
    search_fields = [
        'user__username', 'object_id', 'ip_address'
    ]
    
    readonly_fields = [
        'id', 'timestamp', 'user', 'center', 'action',
        'content_type', 'object_id', 'changed_fields',
        'ip_address', 'user_agent', 'additional_data'
    ]
    
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        """
        Audit trails cannot be manually created.
        """
        return False
    
    def has_change_permission(self, request, obj=None):
        """
        Audit trails cannot be modified.
        """
        return False
    
    def has_delete_permission(self, request, obj=None):
        """
        Audit trails cannot be deleted through admin.
        """
        return False
    
    def get_queryset(self, request):
        """
        Filter audit trails based on user permissions.
        """
        qs = super().get_queryset(request)
        if not request.user.is_superuser and hasattr(request.user, 'centers'):
            user_centers = request.user.centers.all()
            qs = qs.filter(center__in=user_centers)
        return qs
    
    def changelist_view(self, request, extra_context=None):
        """
        Add additional context to the changelist view.
        """
        extra_context = extra_context or {}
        
        # Add summary statistics
        qs = self.get_queryset(request)
        extra_context['total_entries'] = qs.count()
        extra_context['recent_entries'] = qs.recent(7).count()
        extra_context['security_events'] = qs.security_events().count()
        extra_context['data_changes'] = qs.data_changes().count()
        
        return super().changelist_view(request, extra_context)


# Customize admin site headers
admin.site.site_header = 'Geriatric Administration System'
admin.site.site_title = 'Geriatric Admin'
admin.site.index_title = 'System Administration'