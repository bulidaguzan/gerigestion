"""
Custom forms for the core application.

This module provides forms for user management, authentication,
and other core functionality with proper validation and security.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, AuthenticationForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.db import models
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from crispy_forms.bootstrap import FormActions
from .models import User, GeriatricCenter, UserCenterAssignment


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user creation form with additional fields.
    """
    
    class Meta:
        model = User
        fields = (
            'username', 'employee_id', 'first_name', 'last_name', 
            'email', 'role', 'phone_number', 'date_of_birth', 'hire_date'
        )
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make certain fields required
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['employee_id'].required = True
        self.fields['role'].required = True
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Basic Information',
                Row(
                    Column('first_name', css_class='form-group col-md-6 mb-0'),
                    Column('last_name', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('username', css_class='form-group col-md-6 mb-0'),
                    Column('employee_id', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'email',
                'role',
            ),
            Fieldset(
                'Personal Details',
                Row(
                    Column('phone_number', css_class='form-group col-md-6 mb-0'),
                    Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'hire_date',
            ),
            Fieldset(
                'Security',
                'password1',
                'password2',
            ),
            FormActions(
                Submit('submit', 'Create User', css_class='btn btn-primary'),
                HTML('<a href="{% url "admin:core_user_changelist" %}" class="btn btn-secondary">Cancel</a>')
            )
        )
        
    def save(self, commit=True):
        """
        Save the user with additional processing.
        """
        user = super().save(commit=False)
        user.password_changed_at = timezone.now()
        
        if commit:
            user.save()
            
        return user


class CustomUserChangeForm(UserChangeForm):
    """
    Custom user change form with additional fields.
    """
    
    class Meta:
        model = User
        fields = (
            'username', 'employee_id', 'first_name', 'last_name',
            'email', 'role', 'phone_number', 'date_of_birth', 'hire_date',
            'emergency_contact_name', 'emergency_contact_phone',
            'is_active', 'is_staff', 'is_multi_center_admin',
            'two_factor_enabled', 'must_change_password'
        )
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Remove password field from change form
        if 'password' in self.fields:
            del self.fields['password']
            
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Basic Information',
                Row(
                    Column('first_name', css_class='form-group col-md-6 mb-0'),
                    Column('last_name', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('username', css_class='form-group col-md-6 mb-0'),
                    Column('employee_id', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'email',
                'role',
            ),
            Fieldset(
                'Personal Details',
                Row(
                    Column('phone_number', css_class='form-group col-md-6 mb-0'),
                    Column('date_of_birth', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'hire_date',
            ),
            Fieldset(
                'Emergency Contact',
                Row(
                    Column('emergency_contact_name', css_class='form-group col-md-6 mb-0'),
                    Column('emergency_contact_phone', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Permissions',
                Row(
                    Column('is_active', css_class='form-group col-md-4 mb-0'),
                    Column('is_staff', css_class='form-group col-md-4 mb-0'),
                    Column('is_multi_center_admin', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('two_factor_enabled', css_class='form-group col-md-6 mb-0'),
                    Column('must_change_password', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            FormActions(
                Submit('submit', 'Update User', css_class='btn btn-primary'),
                HTML('<a href="{% url "admin:core_user_changelist" %}" class="btn btn-secondary">Cancel</a>')
            )
        )


class CustomAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form with enhanced security features.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'username',
            'password',
            FormActions(
                Submit('submit', 'Sign In', css_class='btn btn-primary btn-block'),
            )
        )
        
        # Add placeholders
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Username or Employee ID',
            'class': 'form-control'
        })
        self.fields['password'].widget.attrs.update({
            'placeholder': 'Password',
            'class': 'form-control'
        })
        
    def clean(self):
        """
        Enhanced authentication with account lockout protection.
        """
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Try to get user by username or employee_id
            try:
                user = User.objects.get(
                    models.Q(username=username) | models.Q(employee_id=username)
                )
            except User.DoesNotExist:
                user = None
            
            if user:
                # Check if account is locked
                if user.is_account_locked():
                    raise ValidationError(
                        f"Account is locked until {user.account_locked_until.strftime('%Y-%m-%d %H:%M')}. "
                        "Please contact an administrator."
                    )
                
                # Check if account is active
                if not user.is_active:
                    raise ValidationError("This account has been deactivated.")
                
                # Attempt authentication
                self.user_cache = authenticate(
                    self.request,
                    username=user.username,
                    password=password
                )
                
                if self.user_cache is None:
                    # Record failed login attempt
                    user.record_failed_login()
                    
                    remaining_attempts = 5 - user.failed_login_attempts
                    if remaining_attempts > 0:
                        raise ValidationError(
                            f"Invalid credentials. {remaining_attempts} attempts remaining."
                        )
                    else:
                        raise ValidationError(
                            "Account has been locked due to too many failed login attempts."
                        )
                else:
                    # Check if password change is required
                    if self.user_cache.needs_password_change():
                        raise ValidationError(
                            "Password change required. Please contact an administrator."
                        )
                    
                    # Record successful login
                    self.user_cache.record_successful_login()
            else:
                raise ValidationError("Invalid credentials.")
        
        return self.cleaned_data


class GeriatricCenterForm(forms.ModelForm):
    """
    Form for creating and editing geriatric centers.
    """
    
    class Meta:
        model = GeriatricCenter
        fields = [
            'name', 'code', 'address', 'phone_number', 'email',
            'license_number', 'capacity', 'administrator', 'notes'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter administrators to only show users with administrator role
        self.fields['administrator'].queryset = User.objects.filter(
            role='administrator',
            is_active=True
        )
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Basic Information',
                Row(
                    Column('name', css_class='form-group col-md-8 mb-0'),
                    Column('code', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                'administrator',
            ),
            Fieldset(
                'Contact Information',
                'address',
                Row(
                    Column('phone_number', css_class='form-group col-md-6 mb-0'),
                    Column('email', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Operational Details',
                Row(
                    Column('license_number', css_class='form-group col-md-6 mb-0'),
                    Column('capacity', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Additional Information',
                'notes',
            ),
            FormActions(
                Submit('submit', 'Save Center', css_class='btn btn-primary'),
                HTML('<a href="{% url "admin:core_geriatriccenter_changelist" %}" class="btn btn-secondary">Cancel</a>')
            )
        )
        
    def clean_code(self):
        """
        Validate that center code is unique.
        """
        code = self.cleaned_data['code']
        
        # Check for existing centers with same code
        existing = GeriatricCenter.objects.filter(code=code)
        if self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
            
        if existing.exists():
            raise ValidationError("A center with this code already exists.")
            
        return code.upper()  # Store codes in uppercase
        
    def clean_capacity(self):
        """
        Validate capacity is reasonable.
        """
        capacity = self.cleaned_data['capacity']
        
        if capacity <= 0:
            raise ValidationError("Capacity must be greater than zero.")
            
        if capacity > 1000:
            raise ValidationError("Capacity seems unreasonably high. Please verify.")
            
        return capacity


class UserCenterAssignmentForm(forms.ModelForm):
    """
    Form for assigning users to centers.
    """
    
    class Meta:
        model = UserCenterAssignment
        fields = ['user', 'center', 'is_primary']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filter active users and centers
        self.fields['user'].queryset = User.objects.filter(is_active=True)
        self.fields['center'].queryset = GeriatricCenter.objects.filter(is_active=True)
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            'user',
            'center',
            'is_primary',
            FormActions(
                Submit('submit', 'Assign User', css_class='btn btn-primary'),
                HTML('<a href="{% url "admin:core_usercenterassignment_changelist" %}" class="btn btn-secondary">Cancel</a>')
            )
        )
        
    def clean(self):
        """
        Validate the assignment.
        """
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        center = cleaned_data.get('center')
        is_primary = cleaned_data.get('is_primary')
        
        if user and center:
            # Check if assignment already exists
            existing = UserCenterAssignment.objects.filter(
                user=user,
                center=center,
                is_active=True
            )
            
            if self.instance.pk:
                existing = existing.exclude(pk=self.instance.pk)
                
            if existing.exists():
                raise ValidationError("This user is already assigned to this center.")
            
            # If this is a primary assignment, check if user already has one
            if is_primary:
                existing_primary = UserCenterAssignment.objects.filter(
                    user=user,
                    is_primary=True,
                    is_active=True
                )
                
                if self.instance.pk:
                    existing_primary = existing_primary.exclude(pk=self.instance.pk)
                    
                if existing_primary.exists():
                    raise ValidationError(
                        "User already has a primary center assignment. "
                        "Please unset the existing primary assignment first."
                    )
        
        return cleaned_data


class PasswordChangeRequiredForm(forms.Form):
    """
    Form for mandatory password changes.
    """
    
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Current Password"
    )
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="New Password"
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label="Confirm New Password"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<div class="alert alert-warning">Your password has expired and must be changed.</div>'),
            'old_password',
            'new_password1',
            'new_password2',
            FormActions(
                Submit('submit', 'Change Password', css_class='btn btn-primary'),
            )
        )
        
    def clean_old_password(self):
        """
        Validate the old password.
        """
        old_password = self.cleaned_data['old_password']
        
        if not self.user.check_password(old_password):
            raise ValidationError("Current password is incorrect.")
            
        return old_password
        
    def clean(self):
        """
        Validate the new passwords match and meet requirements.
        """
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("New passwords don't match.")
                
            # Validate against Django's password validators
            from django.contrib.auth.password_validation import validate_password
            try:
                validate_password(new_password1, self.user)
            except ValidationError as e:
                raise ValidationError(e.messages)
        
        return cleaned_data
        
    def save(self):
        """
        Save the new password.
        """
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.password_changed_at = timezone.now()
        self.user.must_change_password = False
        self.user.save(update_fields=['password', 'password_changed_at', 'must_change_password'])
        return self.user


class PasswordResetRequestForm(forms.Form):
    """
    Form for requesting password reset.
    """
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address'
        }),
        label="Email Address"
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<div class="alert alert-info">Enter your email address to receive password reset instructions.</div>'),
            'email',
            FormActions(
                Submit('submit', 'Send Reset Link', css_class='btn btn-primary'),
            )
        )
    
    def clean_email(self):
        """
        Validate email and check if user exists.
        """
        email = self.cleaned_data['email']
        
        # Check if user with this email exists
        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        
        return email


class PasswordResetConfirmForm(forms.Form):
    """
    Form for confirming password reset with token.
    """
    
    new_password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter new password'
        }),
        label="New Password"
    )
    
    new_password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        }),
        label="Confirm New Password"
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Add crispy forms helper
        self.helper = FormHelper()
        self.helper.layout = Layout(
            HTML('<div class="alert alert-warning">Create a new secure password for your account.</div>'),
            'new_password1',
            'new_password2',
            FormActions(
                Submit('submit', 'Reset Password', css_class='btn btn-primary'),
            )
        )
    
    def clean(self):
        """
        Validate the new passwords match and meet requirements.
        """
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError("New passwords don't match.")
                
            # Validate against Django's password validators
            from django.contrib.auth.password_validation import validate_password
            try:
                validate_password(new_password1, self.user)
            except ValidationError as e:
                raise ValidationError(e.messages)
        
        return cleaned_data
    
    def save(self):
        """
        Save the new password.
        """
        password = self.cleaned_data['new_password1']
        self.user.set_password(password)
        self.user.password_changed_at = timezone.now()
        self.user.must_change_password = False
        self.user.save(update_fields=['password', 'password_changed_at', 'must_change_password'])
        return self.user