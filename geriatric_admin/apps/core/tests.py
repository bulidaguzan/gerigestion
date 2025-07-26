"""
Tests for the core application authentication system.

This module tests the custom authentication backends, password validation,
and security features implemented in task 4.
"""

from django.test import TestCase, Client
from django.contrib.auth import authenticate
from django.urls import reverse
from django.utils import timezone
from django.conf import settings
from unittest.mock import patch
from .models import User, GeriatricCenter, UserCenterAssignment
from .backends import GeriatricAuthenticationBackend, TwoFactorAuthenticationBackend
from .validators import CustomPasswordValidator
import uuid


class AuthenticationBackendTest(TestCase):
    """Test custom authentication backends."""
    
    def setUp(self):
        """Set up test data."""
        self.backend = GeriatricAuthenticationBackend()
        
        # Create user first
        self.user = User.objects.create_user(
            username="testuser",
            employee_id="TEST001",
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
            role="nurse"
        )
        
        # Create center with administrator
        self.center = GeriatricCenter.objects.create(
            name="Test Center",
            code="TEST",
            address="123 Test St",
            phone_number="555-0123",
            email="test@example.com",
            license_number="LIC123",
            capacity=100,
            administrator=self.user
        )
        
        # Create user-center assignment
        UserCenterAssignment.objects.create(
            user=self.user,
            center=self.center,
            is_primary=True,
            assigned_by=self.user
        )
    
    def test_authenticate_with_username(self):
        """Test authentication with username."""
        user = self.backend.authenticate(
            request=None,
            username="testuser",
            password="TestPassword123!"
        )
        self.assertEqual(user, self.user)
    
    def test_authenticate_with_employee_id(self):
        """Test authentication with employee ID."""
        user = self.backend.authenticate(
            request=None,
            username="TEST001",
            password="TestPassword123!"
        )
        self.assertEqual(user, self.user)
    
    def test_authenticate_invalid_password(self):
        """Test authentication with invalid password."""
        user = self.backend.authenticate(
            request=None,
            username="testuser",
            password="wrongpassword"
        )
        self.assertIsNone(user)
        
        # Check that failed login attempt was recorded
        self.user.refresh_from_db()
        self.assertEqual(self.user.failed_login_attempts, 1)
    
    def test_authenticate_nonexistent_user(self):
        """Test authentication with non-existent user."""
        user = self.backend.authenticate(
            request=None,
            username="nonexistent",
            password="password"
        )
        self.assertIsNone(user)
    
    def test_authenticate_locked_account(self):
        """Test authentication with locked account."""
        # Lock the account
        self.user.lock_account()
        
        user = self.backend.authenticate(
            request=None,
            username="testuser",
            password="TestPassword123!"
        )
        self.assertIsNone(user)
    
    def test_authenticate_inactive_user(self):
        """Test authentication with inactive user."""
        self.user.is_active = False
        self.user.save()
        
        user = self.backend.authenticate(
            request=None,
            username="testuser",
            password="TestPassword123!"
        )
        self.assertIsNone(user)
    
    def test_get_user(self):
        """Test get_user method."""
        user = self.backend.get_user(self.user.id)
        self.assertEqual(user, self.user)
        
        # Test with non-existent user
        user = self.backend.get_user(uuid.uuid4())
        self.assertIsNone(user)


class PasswordValidatorTest(TestCase):
    """Test custom password validator."""
    
    def setUp(self):
        """Set up test data."""
        self.validator = CustomPasswordValidator()
        self.user = User(
            username="testuser",
            employee_id="TEST001",
            first_name="John",
            last_name="Doe",
            email="john.doe@example.com"
        )
    
    def test_valid_password(self):
        """Test validation of a valid password."""
        password = "MySecureP@ssw9rd!2024"  # Changed to avoid sequential characters
        try:
            self.validator.validate(password, self.user)
        except Exception:
            self.fail("Valid password should not raise ValidationError")
    
    def test_password_too_short(self):
        """Test validation of password that's too short."""
        password = "Short1!"
        with self.assertRaises(Exception):
            self.validator.validate(password, self.user)
    
    def test_password_no_uppercase(self):
        """Test validation of password without uppercase letters."""
        password = "mysecurep@ssw0rd123"
        with self.assertRaises(Exception):
            self.validator.validate(password, self.user)
    
    def test_password_no_lowercase(self):
        """Test validation of password without lowercase letters."""
        password = "MYSECUREP@SSW0RD123"
        with self.assertRaises(Exception):
            self.validator.validate(password, self.user)
    
    def test_password_no_digit(self):
        """Test validation of password without digits."""
        password = "MySecureP@ssword"
        with self.assertRaises(Exception):
            self.validator.validate(password, self.user)
    
    def test_password_no_special_char(self):
        """Test validation of password without special characters."""
        password = "MySecurePassword123"
        with self.assertRaises(Exception):
            self.validator.validate(password, self.user)
    
    def test_password_contains_username(self):
        """Test validation of password containing username."""
        password = "testuser123!A"
        with self.assertRaises(Exception):
            self.validator.validate(password, self.user)
    
    def test_password_contains_common_pattern(self):
        """Test validation of password containing common patterns."""
        password = "Password123!"
        with self.assertRaises(Exception):
            self.validator.validate(password, self.user)


class AuthenticationViewTest(TestCase):
    """Test authentication views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create user first
        self.user = User.objects.create_user(
            username="testuser",
            employee_id="TEST001",
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
            role="nurse"
        )
        
        # Create center with administrator
        self.center = GeriatricCenter.objects.create(
            name="Test Center",
            code="TEST",
            address="123 Test St",
            phone_number="555-0123",
            email="test@example.com",
            license_number="LIC123",
            capacity=100,
            administrator=self.user
        )
        
        UserCenterAssignment.objects.create(
            user=self.user,
            center=self.center,
            is_primary=True,
            assigned_by=self.user
        )
    
    def test_login_view_get(self):
        """Test GET request to login view."""
        response = self.client.get(reverse('core:login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sign In')
        self.assertContains(response, 'Username or Employee ID')
    
    def test_login_view_post_valid(self):
        """Test POST request to login view with valid credentials."""
        response = self.client.post(reverse('core:login'), {
            'username': 'testuser',
            'password': 'TestPassword123!'
        })
        
        # Should redirect to dashboard
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, '/dashboard/')
        
        # User should be logged in
        user = response.wsgi_request.user
        self.assertTrue(user.is_authenticated)
    
    def test_login_view_post_invalid(self):
        """Test POST request to login view with invalid credentials."""
        response = self.client.post(reverse('core:login'), {
            'username': 'testuser',
            'password': 'wrongpassword'
        })
        
        # Should stay on login page
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid credentials')
        
        # User should not be logged in
        user = response.wsgi_request.user
        self.assertFalse(user.is_authenticated)
    
    def test_logout_view(self):
        """Test logout view."""
        # First log in
        self.client.login(username='testuser', password='TestPassword123!')
        
        # Then log out
        response = self.client.post(reverse('core:logout'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Successfully Signed Out')
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/api/v1/auth/login/', response.url)
    
    def test_dashboard_with_login(self):
        """Test dashboard access with authentication."""
        self.client.login(username='testuser', password='TestPassword123!')
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard')


class UserModelTest(TestCase):
    """Test User model security features."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            username="testuser",
            employee_id="TEST001",
            email="test@example.com",
            password="TestPassword123!",
            first_name="Test",
            last_name="User",
            role="nurse"
        )
    
    def test_account_locking(self):
        """Test account locking functionality."""
        # Account should not be locked initially
        self.assertFalse(self.user.is_account_locked())
        
        # Lock the account
        self.user.lock_account(duration_minutes=30)
        self.assertTrue(self.user.is_account_locked())
        
        # Unlock the account
        self.user.unlock_account()
        self.assertFalse(self.user.is_account_locked())
    
    def test_failed_login_tracking(self):
        """Test failed login attempt tracking."""
        # Initially no failed attempts
        self.assertEqual(self.user.failed_login_attempts, 0)
        
        # Record failed login
        self.user.record_failed_login()
        self.assertEqual(self.user.failed_login_attempts, 1)
        
        # Record successful login (should reset)
        self.user.record_successful_login()
        self.assertEqual(self.user.failed_login_attempts, 0)
    
    def test_password_change_requirement(self):
        """Test password change requirement checking."""
        # Initially should not need password change
        self.assertFalse(self.user.needs_password_change())
        
        # Set must_change_password flag
        self.user.must_change_password = True
        self.user.save()
        self.assertTrue(self.user.needs_password_change())
        
        # Test password expiry
        self.user.must_change_password = False
        self.user.password_changed_at = timezone.now() - timezone.timedelta(days=100)
        self.user.save()
        self.assertTrue(self.user.needs_password_change())
    
    def test_get_full_name(self):
        """Test get_full_name method."""
        self.assertEqual(self.user.get_full_name(), "Test User")
        
        # Test with empty names
        user = User(username="testuser2")
        self.assertEqual(user.get_full_name(), "testuser2")


class SessionSecurityTest(TestCase):
    """Test session security features."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser",
            employee_id="TEST001",
            email="test@example.com",
            password="TestPassword123!",
            role="nurse"
        )
    
    def test_session_timeout_setting(self):
        """Test that session timeout is properly configured."""
        # Login
        self.client.login(username='testuser', password='TestPassword123!')
        
        # Check session expiry is set
        session = self.client.session
        self.assertIsNotNone(session.get_expiry_age())
        
        # Should be 1 hour (3600 seconds) by default
        expected_timeout = getattr(settings, 'GERIATRIC_ADMIN_SETTINGS', {}).get(
            'SESSION_TIMEOUT_MINUTES', 60
        ) * 60
        self.assertEqual(session.get_expiry_age(), expected_timeout)
    
    def test_session_security_info(self):
        """Test session security information storage."""
        # Login
        response = self.client.post(reverse('core:login'), {
            'username': 'testuser',
            'password': 'TestPassword123!'
        })
        
        # Check session contains security information
        session = self.client.session
        self.assertIn('login_timestamp', session)
        self.assertIn('login_ip', session)
        self.assertIn('user_agent_hash', session)
        self.assertIn('security_token', session)


if __name__ == '__main__':
    import django
    from django.conf import settings
    from django.test.utils import get_runner
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner()
    failures = test_runner.run_tests(["apps.core.tests"])