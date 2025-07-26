"""
Views for the core application.

This module provides authentication views and other core functionality
with enhanced security features and proper audit logging.
"""

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic import FormView, TemplateView
from django.http import JsonResponse, HttpResponseRedirect
from django.utils import timezone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from .forms import CustomAuthenticationForm, PasswordChangeRequiredForm, PasswordResetRequestForm, PasswordResetConfirmForm
from .models import User, GeriatricCenter, AuditTrail
from .utils import get_client_ip, get_user_agent
import logging

logger = logging.getLogger(__name__)


class SecureLoginView(LoginView):
    """
    Secure login view with enhanced security features.
    
    This view provides:
    - Account lockout protection
    - Audit logging
    - Two-factor authentication support
    - Session security
    - Rate limiting protection
    """
    
    form_class = CustomAuthenticationForm
    template_name = 'core/auth/login.html'
    redirect_authenticated_user = True
    
    @method_decorator(sensitive_post_parameters())
    @method_decorator(csrf_protect)
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch with security decorators.
        """
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context for the login form.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'site_name': 'Geriatric Administration System',
            'page_title': 'Sign In',
            'show_2fa': False,  # Will be set dynamically if needed
        })
        return context
    
    def form_valid(self, form):
        """
        Handle successful form validation with additional security checks.
        """
        user = form.get_user()
        
        # Check if password change is required
        if hasattr(user, '_password_change_required') and user._password_change_required:
            # Store user ID in session for password change
            self.request.session['password_change_user_id'] = str(user.id)
            messages.warning(
                self.request,
                'Your password has expired and must be changed before you can continue.'
            )
            return redirect('core:password_change_required')
        
        # Check if 2FA is required
        if hasattr(user, '_requires_2fa') and user._requires_2fa:
            # Store user ID in session for 2FA
            self.request.session['2fa_user_id'] = str(user.id)
            return redirect('core:two_factor_auth')
        
        # Standard login process
        login(self.request, user)
        
        # Set up session security
        self._setup_secure_session(user)
        
        # Log successful login
        self._log_login_success(user)
        
        # Add success message
        messages.success(
            self.request,
            f'Welcome back, {user.get_full_name() or user.username}!'
        )
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Handle form validation errors with security logging.
        """
        # Log failed login attempt
        username = form.cleaned_data.get('username', '')
        if username:
            self._log_login_failure(username, 'form_validation_failed')
        
        return super().form_invalid(form)
    
    def _setup_secure_session(self, user):
        """
        Set up secure session configuration.
        
        Args:
            user: Authenticated user
        """
        # Set session timeout
        timeout_minutes = getattr(settings, 'GERIATRIC_ADMIN_SETTINGS', {}).get(
            'SESSION_TIMEOUT_MINUTES', 60
        )
        self.request.session.set_expiry(timeout_minutes * 60)
        
        # Store security information in session
        self.request.session.update({
            'login_timestamp': timezone.now().isoformat(),
            'login_ip': get_client_ip(self.request),
            'user_agent_hash': hash(get_user_agent(self.request)),
            'security_token': user.id.hex,  # Simple security token
        })
        
        # Set user's primary center if not already set
        if not self.request.session.get('current_center_id'):
            try:
                assignment = user.usercenterassignment_set.filter(
                    is_primary=True,
                    is_active=True
                ).first()
                
                if assignment:
                    self.request.session['current_center_id'] = str(assignment.center.id)
            except Exception as e:
                logger.error(f"Error setting primary center for user {user.username}: {e}")
    
    def _log_login_success(self, user):
        """
        Log successful login attempt.
        
        Args:
            user: Authenticated user
        """
        try:
            AuditTrail.objects.create(
                action='LOGIN',
                user=user,
                ip_address=get_client_ip(self.request),
                user_agent=get_user_agent(self.request),
                additional_data={
                    'success': True,
                    'login_method': 'web_form',
                    'session_id': self.request.session.session_key,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log successful login: {e}")
    
    def _log_login_failure(self, username, reason):
        """
        Log failed login attempt.
        
        Args:
            username: Attempted username
            reason: Reason for failure
        """
        try:
            AuditTrail.objects.create(
                action='LOGIN',
                ip_address=get_client_ip(self.request),
                user_agent=get_user_agent(self.request),
                additional_data={
                    'success': False,
                    'attempted_username': username,
                    'reason': reason,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log login failure: {e}")


class SecureLogoutView(LogoutView):
    """
    Secure logout view with audit logging and session cleanup.
    """
    
    template_name = 'core/auth/logout.html'
    next_page = None  # Don't redirect, show template
    
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch with security decorators.
        """
        return super().dispatch(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """
        Handle logout with audit logging.
        """
        user = request.user if request.user.is_authenticated else None
        
        # Log logout attempt
        if user:
            self._log_logout(user)
        
        # Clear session data
        self._cleanup_session(request)
        
        # Perform logout
        logout(request)
        
        # Add success message
        messages.success(request, 'You have been successfully logged out.')
        
        # Return template response instead of redirect
        return self.render_to_response(self.get_context_data())
    
    def _log_logout(self, user):
        """
        Log logout attempt.
        
        Args:
            user: User being logged out
        """
        try:
            AuditTrail.objects.create(
                action='LOGOUT',
                user=user,
                ip_address=get_client_ip(self.request),
                user_agent=get_user_agent(self.request),
                additional_data={
                    'session_id': self.request.session.session_key,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log logout: {e}")
    
    def _cleanup_session(self, request):
        """
        Clean up session data on logout.
        
        Args:
            request: HTTP request
        """
        # Clear sensitive session data
        sensitive_keys = [
            'current_center_id',
            'login_timestamp',
            'login_ip',
            'user_agent_hash',
            'security_token',
            '2fa_user_id',
            'password_change_user_id',
        ]
        
        for key in sensitive_keys:
            if key in request.session:
                del request.session[key]


class TwoFactorAuthView(FormView):
    """
    Two-factor authentication view for TOTP verification.
    """
    
    template_name = 'core/auth/two_factor.html'
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for 2FA form.
        """
        # Check if user is in 2FA flow
        user_id = request.session.get('2fa_user_id')
        if not user_id:
            messages.error(request, 'Invalid two-factor authentication session.')
            return redirect('core:login')
        
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            messages.error(request, 'Invalid user session.')
            return redirect('core:login')
        
        if not user.two_factor_enabled:
            messages.error(request, 'Two-factor authentication is not enabled for this account.')
            return redirect('core:login')
        
        return super().get(request, *args, **kwargs)
    
    def post(self, request, *args, **kwargs):
        """
        Handle 2FA token verification.
        """
        user_id = request.session.get('2fa_user_id')
        if not user_id:
            return JsonResponse({'error': 'Invalid session'}, status=400)
        
        try:
            user = User.objects.get(id=user_id, is_active=True)
        except User.DoesNotExist:
            return JsonResponse({'error': 'Invalid user'}, status=400)
        
        token = request.POST.get('totp_token', '').strip()
        if not token:
            return JsonResponse({'error': 'Token is required'}, status=400)
        
        # Verify TOTP token
        if self._verify_totp_token(user, token):
            # 2FA successful - complete login
            login(request, user)
            
            # Clean up 2FA session
            del request.session['2fa_user_id']
            
            # Set up secure session
            self._setup_secure_session(user)
            
            # Log successful 2FA
            self._log_2fa_success(user)
            
            messages.success(request, 'Two-factor authentication successful.')
            
            return JsonResponse({
                'success': True,
                'redirect_url': reverse('dashboard:index')
            })
        else:
            # 2FA failed
            self._log_2fa_failure(user)
            return JsonResponse({'error': 'Invalid authentication code'}, status=400)
    
    def _verify_totp_token(self, user, token):
        """
        Verify TOTP token.
        
        Args:
            user: User instance
            token: TOTP token
            
        Returns:
            True if token is valid, False otherwise
        """
        try:
            import pyotp
            totp = pyotp.TOTP(user.two_factor_secret)
            return totp.verify(token, valid_window=1)
        except ImportError:
            logger.error("pyotp library not installed")
            return False
        except Exception as e:
            logger.error(f"Error verifying TOTP token: {e}")
            return False
    
    def _setup_secure_session(self, user):
        """
        Set up secure session after 2FA.
        
        Args:
            user: Authenticated user
        """
        timeout_minutes = getattr(settings, 'GERIATRIC_ADMIN_SETTINGS', {}).get(
            'SESSION_TIMEOUT_MINUTES', 60
        )
        self.request.session.set_expiry(timeout_minutes * 60)
        
        self.request.session.update({
            'login_timestamp': timezone.now().isoformat(),
            'login_ip': get_client_ip(self.request),
            'user_agent_hash': hash(get_user_agent(self.request)),
            'security_token': user.id.hex,
            '2fa_verified': True,
        })
    
    def _log_2fa_success(self, user):
        """
        Log successful 2FA verification.
        
        Args:
            user: User instance
        """
        try:
            AuditTrail.objects.create(
                action='LOGIN',
                user=user,
                ip_address=get_client_ip(self.request),
                user_agent=get_user_agent(self.request),
                additional_data={
                    'success': True,
                    'two_factor_auth': True,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log 2FA success: {e}")
    
    def _log_2fa_failure(self, user):
        """
        Log failed 2FA verification.
        
        Args:
            user: User instance
        """
        try:
            AuditTrail.objects.create(
                action='LOGIN',
                user=user,
                ip_address=get_client_ip(self.request),
                user_agent=get_user_agent(self.request),
                additional_data={
                    'success': False,
                    'two_factor_auth': True,
                    'reason': 'invalid_2fa_token',
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log 2FA failure: {e}")


class PasswordChangeRequiredView(FormView):
    """
    View for mandatory password changes.
    """
    
    form_class = PasswordChangeRequiredForm
    template_name = 'core/auth/password_change_required.html'
    success_url = reverse_lazy('core:login')
    
    def get_form_kwargs(self):
        """
        Add user to form kwargs.
        """
        kwargs = super().get_form_kwargs()
        
        user_id = self.request.session.get('password_change_user_id')
        if user_id:
            try:
                kwargs['user'] = User.objects.get(id=user_id, is_active=True)
            except User.DoesNotExist:
                pass
        
        return kwargs
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request for password change form.
        """
        user_id = request.session.get('password_change_user_id')
        if not user_id:
            messages.error(request, 'Invalid password change session.')
            return redirect('core:login')
        
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        """
        Handle successful password change.
        """
        user = form.save()
        
        # Clean up session
        if 'password_change_user_id' in self.request.session:
            del self.request.session['password_change_user_id']
        
        # Log password change
        self._log_password_change(user)
        
        messages.success(
            self.request,
            'Your password has been successfully changed. Please log in with your new password.'
        )
        
        return super().form_valid(form)
    
    def _log_password_change(self, user):
        """
        Log password change event.
        
        Args:
            user: User who changed password
        """
        try:
            AuditTrail.objects.create(
                action='UPDATE',
                user=user,
                ip_address=get_client_ip(self.request),
                user_agent=get_user_agent(self.request),
                additional_data={
                    'password_changed': True,
                    'forced_change': True,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log password change: {e}")


@login_required
def center_switch_view(request):
    """
    View for switching between accessible centers.
    """
    if request.method == 'POST':
        center_id = request.POST.get('center_id')
        
        if center_id:
            try:
                center = GeriatricCenter.objects.get(id=center_id, is_active=True)
                
                # Verify user has access to this center
                if request.user.has_center_access(center):
                    request.session['current_center_id'] = str(center.id)
                    
                    # Log center switch
                    AuditTrail.objects.create(
                        action='UPDATE',
                        user=request.user,
                        center=center,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        additional_data={
                            'center_switched': True,
                            'new_center_id': str(center.id),
                            'timestamp': timezone.now().isoformat(),
                        }
                    )
                    
                    messages.success(request, f'Switched to {center.name}')
                else:
                    messages.error(request, 'You do not have access to this center.')
                    
            except GeriatricCenter.DoesNotExist:
                messages.error(request, 'Invalid center selected.')
        
        return redirect(request.META.get('HTTP_REFERER', '/dashboard/'))
    
    # GET request - show center selection
    accessible_centers = request.user.get_accessible_centers()
    current_center_id = request.session.get('current_center_id')
    
    context = {
        'accessible_centers': accessible_centers,
        'current_center_id': current_center_id,
    }
    
    return render(request, 'core/auth/center_switch.html', context)


class SessionSecurityView(TemplateView):
    """
    View for session security information and management.
    """
    
    template_name = 'core/auth/session_security.html'
    
    @method_decorator(login_required)
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Add session security information to context.
        """
        context = super().get_context_data(**kwargs)
        
        # Get session information
        login_timestamp = self.request.session.get('login_timestamp')
        login_ip = self.request.session.get('login_ip')
        
        context.update({
            'login_timestamp': login_timestamp,
            'login_ip': login_ip,
            'session_expiry': self.request.session.get_expiry_date(),
            'two_factor_enabled': self.request.user.two_factor_enabled,
            'last_password_change': self.request.user.password_changed_at,
            'failed_login_attempts': self.request.user.failed_login_attempts,
        })
        
        return context


class PasswordResetRequestView(FormView):
    """
    View for requesting password reset.
    """
    
    form_class = PasswordResetRequestForm
    template_name = 'core/auth/password_reset_request.html'
    success_url = reverse_lazy('core:password_reset_done')
    
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch with security decorators.
        """
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'site_name': 'Geriatric Administration System',
            'page_title': 'Password Reset Request',
        })
        return context
    
    def form_valid(self, form):
        """
        Handle successful form submission.
        """
        email = form.cleaned_data['email']
        
        try:
            user = User.objects.get(email=email, is_active=True)
            
            # Generate password reset token
            token = user.generate_password_reset_token()
            
            # Send password reset email
            self._send_password_reset_email(user, token)
            
            # Log password reset request
            self._log_password_reset_request(user)
            
        except User.DoesNotExist:
            # Don't reveal if email exists or not for security
            pass
        
        # Always show success message to prevent email enumeration
        messages.success(
            self.request,
            'If an account with that email address exists, you will receive password reset instructions shortly.'
        )
        
        return super().form_valid(form)
    
    def _send_password_reset_email(self, user, token):
        """
        Send password reset email to user.
        
        Args:
            user: User instance
            token: Password reset token
        """
        from django.core.mail import send_mail
        from django.conf import settings
        
        # Build reset URL
        reset_url = self.request.build_absolute_uri(
            reverse('core:password_reset_confirm', kwargs={'token': token})
        )
        
        # Email subject and content
        subject = 'Password Reset Request - Geriatric Administration System'
        
        message = f"""
Hello {user.get_full_name() or user.username},

You recently requested to reset your password for your Geriatric Administration System account.

To reset your password, please click the following link:

{reset_url}

This link will expire in 24 hours for security reasons.

If you did not request this password reset, please ignore this email. Your password will remain unchanged.

For security reasons, this link can only be used once. If you need to reset your password again, please request a new reset link.

Best regards,
Geriatric Administration System Team

---
This is an automated message. Please do not reply to this email.
        """
        
        # Send email
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Failed to send password reset email to {user.email}: {e}")
    
    def _log_password_reset_request(self, user):
        """
        Log password reset request.
        
        Args:
            user: User who requested password reset
        """
        try:
            AuditTrail.objects.create(
                action='PASSWORD_RESET_REQUEST',
                user=user,
                ip_address=get_client_ip(self.request),
                user_agent=get_user_agent(self.request),
                additional_data={
                    'email': user.email,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log password reset request: {e}")


class PasswordResetConfirmView(FormView):
    """
    View for confirming password reset with token.
    """
    
    form_class = PasswordResetConfirmForm
    template_name = 'core/auth/password_reset_confirm.html'
    success_url = reverse_lazy('core:password_reset_complete')
    
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch with security decorators.
        """
        return super().dispatch(request, *args, **kwargs)
    
    def get_form_kwargs(self):
        """
        Add user to form kwargs.
        """
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.get_user()
        return kwargs
    
    def get_user(self):
        """
        Get user from token.
        """
        token = self.kwargs.get('token')
        if not token:
            return None
        
        # Find user with valid token
        for user in User.objects.filter(is_active=True):
            if user.verify_password_reset_token(token):
                return user
        
        return None
    
    def get_context_data(self, **kwargs):
        """
        Add additional context.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'site_name': 'Geriatric Administration System',
            'page_title': 'Reset Password',
            'user': self.get_user(),
            'token': self.kwargs.get('token'),
        })
        return context
    
    def get(self, request, *args, **kwargs):
        """
        Handle GET request.
        """
        user = self.get_user()
        if not user:
            messages.error(request, 'Invalid or expired password reset link.')
            return redirect('core:password_reset_request')
        
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        """
        Handle successful form submission.
        """
        user = self.get_user()
        if not user:
            messages.error(self.request, 'Invalid or expired password reset link.')
            return redirect('core:password_reset_request')
        
        # Save new password
        user = form.save()
        
        # Clear password reset token
        user.clear_password_reset_token()
        
        # Log password reset
        self._log_password_reset(user)
        
        messages.success(
            self.request,
            'Your password has been successfully reset. You can now log in with your new password.'
        )
        
        return super().form_valid(form)
    
    def _log_password_reset(self, user):
        """
        Log password reset.
        
        Args:
            user: User who reset their password
        """
        try:
            AuditTrail.objects.create(
                action='PASSWORD_RESET',
                user=user,
                ip_address=get_client_ip(self.request),
                user_agent=get_user_agent(self.request),
                additional_data={
                    'password_reset': True,
                    'timestamp': timezone.now().isoformat(),
                }
            )
        except Exception as e:
            logger.error(f"Failed to log password reset: {e}")


class PasswordResetDoneView(TemplateView):
    """
    View shown after password reset request is submitted.
    """
    
    template_name = 'core/auth/password_reset_done.html'
    
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch with security decorators.
        """
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'site_name': 'Geriatric Administration System',
            'page_title': 'Password Reset Email Sent',
        })
        return context


class PasswordResetCompleteView(TemplateView):
    """
    View shown after password reset is completed.
    """
    
    template_name = 'core/auth/password_reset_complete.html'
    
    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        """
        Dispatch with security decorators.
        """
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """
        Add additional context.
        """
        context = super().get_context_data(**kwargs)
        context.update({
            'site_name': 'Geriatric Administration System',
            'page_title': 'Password Reset Complete',
        })
        return context