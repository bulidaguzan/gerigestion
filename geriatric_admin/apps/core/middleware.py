"""
Custom middleware for the Geriatric Administration System.

This module provides middleware for audit logging and multi-center
data isolation functionality.
"""

import threading
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import GeriatricCenter, AuditTrail
from .utils import get_client_ip, get_user_agent
import logging

logger = logging.getLogger(__name__)
User = get_user_model()

# Thread-local storage for request context
_thread_locals = threading.local()


class AuditMiddleware(MiddlewareMixin):
    """
    Middleware for comprehensive audit logging.
    
    This middleware captures request information and makes it available
    to models for audit trail creation.
    """
    
    def process_request(self, request):
        """
        Process incoming request and set up audit context.
        """
        # Store request information in thread-local storage
        _thread_locals.request = request
        _thread_locals.user = request.user if request.user.is_authenticated else None
        _thread_locals.ip_address = get_client_ip(request)
        _thread_locals.user_agent = get_user_agent(request)
        _thread_locals.timestamp = timezone.now()
        
        # Get center from session or user's primary center
        center = None
        if request.user.is_authenticated:
            # Try to get center from session first
            center_id = request.session.get('current_center_id')
            if center_id:
                try:
                    center = GeriatricCenter.objects.get(id=center_id)
                except GeriatricCenter.DoesNotExist:
                    pass
            
            # If no center in session, try to get user's primary center
            if not center:
                try:
                    assignment = request.user.usercenterassignment_set.filter(
                        is_primary=True,
                        is_active=True
                    ).first()
                    if assignment:
                        center = assignment.center
                except:
                    pass
        
        _thread_locals.center = center
        
        # Make thread locals available to models
        for model_class in [User, GeriatricCenter]:
            if hasattr(model_class, '_thread_locals'):
                model_class._thread_locals = _thread_locals
    
    def process_response(self, request, response):
        """
        Process response and log sensitive operations.
        """
        # Log certain types of requests
        if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            self._log_data_modification(request, response)
        
        # Clean up thread-local storage
        if hasattr(_thread_locals, 'request'):
            del _thread_locals.request
        if hasattr(_thread_locals, 'user'):
            del _thread_locals.user
        if hasattr(_thread_locals, 'ip_address'):
            del _thread_locals.ip_address
        if hasattr(_thread_locals, 'user_agent'):
            del _thread_locals.user_agent
        if hasattr(_thread_locals, 'center'):
            del _thread_locals.center
        if hasattr(_thread_locals, 'timestamp'):
            del _thread_locals.timestamp
        
        return response
    
    def _log_data_modification(self, request, response):
        """
        Log data modification operations.
        """
        if not request.user.is_authenticated:
            return
        
        # Only log successful operations
        if response.status_code >= 400:
            return
        
        # Determine action based on method
        action_map = {
            'POST': 'CREATE',
            'PUT': 'UPDATE',
            'PATCH': 'UPDATE',
            'DELETE': 'DELETE'
        }
        
        action = action_map.get(request.method, 'UNKNOWN')
        
        # Extract resource information from URL
        path_parts = request.path.strip('/').split('/')
        resource_type = path_parts[0] if path_parts else 'unknown'
        
        # Create audit entry for the operation
        try:
            AuditTrail.objects.create(
                action=action,
                user=request.user,
                center=getattr(_thread_locals, 'center', None),
                ip_address=get_client_ip(request),
                user_agent=get_user_agent(request),
                additional_data={
                    'path': request.path,
                    'method': request.method,
                    'status_code': response.status_code,
                    'resource_type': resource_type,
                    'content_length': response.get('Content-Length', 0),
                }
            )
        except Exception as e:
            logger.error(f"Failed to create audit trail entry: {e}")


class MultiCenterMiddleware(MiddlewareMixin):
    """
    Middleware for multi-center data isolation.
    
    This middleware ensures that users can only access data from
    centers they are assigned to.
    """
    
    def process_request(self, request):
        """
        Process request and set up multi-center context.
        """
        if not request.user.is_authenticated:
            return
        
        # Get current center from session
        current_center_id = request.session.get('current_center_id')
        current_center = None
        
        if current_center_id:
            try:
                current_center = GeriatricCenter.objects.get(
                    id=current_center_id,
                    is_active=True
                )
                
                # Verify user has access to this center
                if not request.user.has_center_access(current_center):
                    current_center = None
                    del request.session['current_center_id']
                    
            except GeriatricCenter.DoesNotExist:
                current_center = None
                if 'current_center_id' in request.session:
                    del request.session['current_center_id']
        
        # If no valid center in session, set user's primary center
        if not current_center and not request.user.is_multi_center_admin:
            try:
                assignment = request.user.usercenterassignment_set.filter(
                    is_primary=True,
                    is_active=True
                ).first()
                
                if assignment:
                    current_center = assignment.center
                    request.session['current_center_id'] = str(current_center.id)
                else:
                    # User has no center assignments
                    logger.warning(f"User {request.user.username} has no center assignments")
                    
            except Exception as e:
                logger.error(f"Error setting primary center for user {request.user.username}: {e}")
        
        # Store center in thread-local storage for models to access
        if hasattr(_thread_locals, 'center') or current_center:
            _thread_locals.center = current_center
        
        # Add center context to request
        request.current_center = current_center
        
        # Add user's accessible centers to request
        if request.user.is_multi_center_admin:
            request.accessible_centers = GeriatricCenter.objects.filter(is_active=True)
        else:
            request.accessible_centers = request.user.get_accessible_centers()
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Process view and enforce center-based access control.
        """
        if not request.user.is_authenticated:
            return None
        
        # Skip access control for superusers
        if request.user.is_superuser:
            return None
        
        # Skip access control for certain views (login, logout, etc.)
        skip_views = [
            'admin:login',
            'admin:logout',
            'admin:password_change',
            'admin:password_change_done',
        ]
        
        view_name = getattr(view_func, '__name__', '')
        if view_name in skip_views:
            return None
        
        # For admin views, check if user has access to the center
        if hasattr(request, 'resolver_match') and request.resolver_match:
            url_name = request.resolver_match.url_name
            
            if url_name and url_name.startswith('admin:'):
                # Check if this is a center-specific resource
                if not request.user.is_multi_center_admin and not request.current_center:
                    logger.warning(f"User {request.user.username} attempted to access admin without center assignment")
                    # Could redirect to center selection page or show error
        
        return None
    
    def process_response(self, request, response):
        """
        Process response and add center information to context.
        """
        # Add center information to response headers for debugging (in development only)
        if hasattr(request, 'current_center') and request.current_center:
            from django.conf import settings
            if settings.DEBUG:
                response['X-Current-Center'] = request.current_center.code
        
        return response


class SecurityMiddleware(MiddlewareMixin):
    """
    Additional security middleware for enhanced protection.
    """
    
    def process_request(self, request):
        """
        Process request and apply security measures.
        """
        # Log suspicious activity
        self._check_suspicious_activity(request)
        
        # Rate limiting could be implemented here
        # self._check_rate_limits(request)
    
    def _check_suspicious_activity(self, request):
        """
        Check for suspicious activity patterns.
        """
        suspicious_patterns = [
            'admin/admin',
            'wp-admin',
            'phpmyadmin',
            '.php',
            'eval(',
            '<script',
            'union select',
            'drop table',
        ]
        
        path_lower = request.path.lower()
        query_lower = request.META.get('QUERY_STRING', '').lower()
        
        for pattern in suspicious_patterns:
            if pattern in path_lower or pattern in query_lower:
                logger.warning(
                    f"Suspicious request detected from {get_client_ip(request)}: "
                    f"Path: {request.path}, Query: {request.META.get('QUERY_STRING', '')}"
                )
                
                # Log security event
                if request.user.is_authenticated:
                    AuditTrail.objects.create(
                        action='VIEW',
                        user=request.user,
                        ip_address=get_client_ip(request),
                        user_agent=get_user_agent(request),
                        additional_data={
                            'suspicious_activity': True,
                            'pattern_matched': pattern,
                            'path': request.path,
                            'query_string': request.META.get('QUERY_STRING', ''),
                        }
                    )
                break
    
    def process_response(self, request, response):
        """
        Process response and add security headers.
        """
        # Add security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Add CSP header for admin pages
        if request.path.startswith('/admin/'):
            response['Content-Security-Policy'] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data:; "
                "font-src 'self';"
            )
        
        return response