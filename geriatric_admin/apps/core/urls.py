from django.urls import path
from .views import (
    SecureLoginView, SecureLogoutView, TwoFactorAuthView,
    PasswordChangeRequiredView, center_switch_view, SessionSecurityView,
    PasswordResetRequestView, PasswordResetConfirmView, 
    PasswordResetDoneView, PasswordResetCompleteView
)

app_name = 'core'

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', SecureLoginView.as_view(), name='login'),
    path('auth/logout/', SecureLogoutView.as_view(), name='logout'),
    path('auth/2fa/', TwoFactorAuthView.as_view(), name='two_factor_auth'),
    path('auth/password-change-required/', PasswordChangeRequiredView.as_view(), name='password_change_required'),
    path('auth/center-switch/', center_switch_view, name='center_switch'),
    path('auth/session-security/', SessionSecurityView.as_view(), name='session_security'),
    
    # Password reset endpoints
    path('auth/password-reset/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('auth/password-reset/done/', PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('auth/password-reset/confirm/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('auth/password-reset/complete/', PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # API endpoints will be added in later tasks
]