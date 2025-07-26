"""
Custom validators for the Geriatric Administration System.

This module provides enhanced validation for passwords, user data,
and other security-sensitive information.
"""

import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext as _
from django.contrib.auth import get_user_model
from django.conf import settings


class CustomPasswordValidator:
    """
    Custom password validator for enhanced security requirements.
    
    This validator enforces:
    - Minimum length of 12 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    - No common patterns or dictionary words
    - No personal information (username, name, etc.)
    """
    
    def __init__(self):
        self.min_length = 12
        self.special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        
    def validate(self, password, user=None):
        """
        Validate password according to custom security rules.
        
        Args:
            password: The password to validate
            user: The user instance (optional)
            
        Raises:
            ValidationError: If password doesn't meet requirements
        """
        errors = []
        
        # Check minimum length
        if len(password) < self.min_length:
            errors.append(
                _("Password must be at least %(min_length)d characters long.") % {
                    'min_length': self.min_length
                }
            )
        
        # Check for uppercase letter
        if not re.search(r'[A-Z]', password):
            errors.append(_("Password must contain at least one uppercase letter."))
        
        # Check for lowercase letter
        if not re.search(r'[a-z]', password):
            errors.append(_("Password must contain at least one lowercase letter."))
        
        # Check for digit
        if not re.search(r'\d', password):
            errors.append(_("Password must contain at least one digit."))
        
        # Check for special character
        if not any(char in self.special_chars for char in password):
            errors.append(
                _("Password must contain at least one special character: %(chars)s") % {
                    'chars': self.special_chars
                }
            )
        
        # Check for common patterns
        self._check_common_patterns(password, errors)
        
        # Check against user information if provided
        if user:
            self._check_user_information(password, user, errors)
        
        # Check for sequential characters
        self._check_sequential_characters(password, errors)
        
        # Check for repeated characters
        self._check_repeated_characters(password, errors)
        
        if errors:
            raise ValidationError(errors)
    
    def _check_common_patterns(self, password, errors):
        """
        Check for common password patterns.
        
        Args:
            password: Password to check
            errors: List to append errors to
        """
        common_patterns = [
            r'password',
            r'123456',
            r'qwerty',
            r'admin',
            r'login',
            r'welcome',
            r'geriatric',
            r'healthcare',
            r'medical',
        ]
        
        password_lower = password.lower()
        
        for pattern in common_patterns:
            if re.search(pattern, password_lower):
                errors.append(
                    _("Password cannot contain common words or patterns.")
                )
                break
    
    def _check_user_information(self, password, user, errors):
        """
        Check if password contains user information.
        
        Args:
            password: Password to check
            user: User instance
            errors: List to append errors to
        """
        password_lower = password.lower()
        
        # Check against username
        if user.username and user.username.lower() in password_lower:
            errors.append(_("Password cannot contain your username."))
        
        # Check against employee ID
        if hasattr(user, 'employee_id') and user.employee_id:
            if user.employee_id.lower() in password_lower:
                errors.append(_("Password cannot contain your employee ID."))
        
        # Check against first name
        if user.first_name and len(user.first_name) > 2:
            if user.first_name.lower() in password_lower:
                errors.append(_("Password cannot contain your first name."))
        
        # Check against last name
        if user.last_name and len(user.last_name) > 2:
            if user.last_name.lower() in password_lower:
                errors.append(_("Password cannot contain your last name."))
        
        # Check against email
        if user.email:
            email_parts = user.email.split('@')[0].lower()
            if len(email_parts) > 3 and email_parts in password_lower:
                errors.append(_("Password cannot contain parts of your email address."))
    
    def _check_sequential_characters(self, password, errors):
        """
        Check for sequential characters (abc, 123, etc.).
        
        Args:
            password: Password to check
            errors: List to append errors to
        """
        # Check for sequential letters
        for i in range(len(password) - 2):
            if (ord(password[i]) + 1 == ord(password[i + 1]) and 
                ord(password[i + 1]) + 1 == ord(password[i + 2])):
                errors.append(_("Password cannot contain sequential characters."))
                break
        
        # Check for sequential numbers
        for i in range(len(password) - 2):
            if (password[i:i+3].isdigit() and 
                int(password[i]) + 1 == int(password[i + 1]) and 
                int(password[i + 1]) + 1 == int(password[i + 2])):
                errors.append(_("Password cannot contain sequential numbers."))
                break
    
    def _check_repeated_characters(self, password, errors):
        """
        Check for excessive repeated characters.
        
        Args:
            password: Password to check
            errors: List to append errors to
        """
        # Check for more than 2 consecutive identical characters
        for i in range(len(password) - 2):
            if password[i] == password[i + 1] == password[i + 2]:
                errors.append(_("Password cannot contain more than 2 consecutive identical characters."))
                break
    
    def get_help_text(self):
        """
        Return help text for password requirements.
        
        Returns:
            String describing password requirements
        """
        return _(
            "Your password must contain at least %(min_length)d characters, "
            "including uppercase and lowercase letters, digits, and special "
            "characters (%(special_chars)s). It cannot contain common words, "
            "sequential characters, or personal information."
        ) % {
            'min_length': self.min_length,
            'special_chars': self.special_chars[:10] + '...'
        }


class EmployeeIdValidator:
    """
    Validator for employee ID format and uniqueness.
    """
    
    def __init__(self):
        self.pattern = r'^[A-Z]{2,3}\d{4,6}$'  # e.g., GER001234, MED123456
    
    def __call__(self, value):
        """
        Validate employee ID format.
        
        Args:
            value: Employee ID to validate
            
        Raises:
            ValidationError: If employee ID format is invalid
        """
        if not re.match(self.pattern, value.upper()):
            raise ValidationError(
                _("Employee ID must be in format: 2-3 letters followed by 4-6 digits (e.g., GER001234)")
            )
        
        # Check uniqueness
        User = get_user_model()
        if User.objects.filter(employee_id=value.upper()).exists():
            raise ValidationError(_("This employee ID is already in use."))


class PhoneNumberValidator:
    """
    Validator for phone number format.
    """
    
    def __init__(self):
        # Support various phone number formats
        self.patterns = [
            r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$',  # US format
            r'^\+?[1-9]\d{1,14}$',  # International format
        ]
    
    def __call__(self, value):
        """
        Validate phone number format.
        
        Args:
            value: Phone number to validate
            
        Raises:
            ValidationError: If phone number format is invalid
        """
        if not value:
            return  # Allow empty values
        
        # Remove common separators for validation
        cleaned = re.sub(r'[-.\s()]', '', value)
        
        valid = False
        for pattern in self.patterns:
            if re.match(pattern, value):
                valid = True
                break
        
        if not valid:
            raise ValidationError(
                _("Enter a valid phone number (e.g., +1-555-123-4567 or (555) 123-4567)")
            )


class CenterCodeValidator:
    """
    Validator for geriatric center codes.
    """
    
    def __init__(self):
        self.pattern = r'^[A-Z]{2,5}$'  # 2-5 uppercase letters
    
    def __call__(self, value):
        """
        Validate center code format.
        
        Args:
            value: Center code to validate
            
        Raises:
            ValidationError: If center code format is invalid
        """
        if not re.match(self.pattern, value.upper()):
            raise ValidationError(
                _("Center code must be 2-5 uppercase letters (e.g., GER, MAIN, NORTH)")
            )


class SecureFieldValidator:
    """
    Validator for fields containing sensitive information.
    """
    
    def __init__(self, field_type='general'):
        self.field_type = field_type
        
    def __call__(self, value):
        """
        Validate sensitive field content.
        
        Args:
            value: Field value to validate
            
        Raises:
            ValidationError: If field contains suspicious content
        """
        if not value:
            return
        
        # Check for potential injection attempts
        suspicious_patterns = [
            r'<script',
            r'javascript:',
            r'eval\(',
            r'union\s+select',
            r'drop\s+table',
            r'insert\s+into',
            r'delete\s+from',
            r'update\s+set',
        ]
        
        value_lower = value.lower()
        
        for pattern in suspicious_patterns:
            if re.search(pattern, value_lower):
                raise ValidationError(
                    _("Field contains potentially unsafe content.")
                )
        
        # Field-specific validation
        if self.field_type == 'medical':
            self._validate_medical_field(value)
        elif self.field_type == 'personal':
            self._validate_personal_field(value)
    
    def _validate_medical_field(self, value):
        """
        Additional validation for medical fields.
        
        Args:
            value: Field value to validate
        """
        # Check for reasonable length
        if len(value) > 10000:
            raise ValidationError(
                _("Medical field content is too long (maximum 10,000 characters).")
            )
    
    def _validate_personal_field(self, value):
        """
        Additional validation for personal information fields.
        
        Args:
            value: Field value to validate
        """
        # Check for reasonable length
        if len(value) > 1000:
            raise ValidationError(
                _("Personal information field is too long (maximum 1,000 characters).")
            )