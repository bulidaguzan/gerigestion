"""
URL configuration for Geriatric Administration System.
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # API endpoints
    path('api/v1/', include('apps.core.urls', namespace='core')),
    path('api/v1/facilities/', include('apps.facilities.urls', namespace='facilities')),
    path('api/v1/residents/', include('apps.residents.urls', namespace='residents')),
    path('api/v1/staff/', include('apps.staff.urls', namespace='staff')),
    path('api/v1/medical/', include('apps.medical.urls', namespace='medical')),
    # path('api/v1/scheduling/', include('apps.scheduling.urls', namespace='scheduling')),
    path('api/v1/reporting/', include('apps.reporting.urls', namespace='reporting')),
    
    # Web interface
    path('', RedirectView.as_view(url='/dashboard/', permanent=False)),
    path('dashboard/', include('apps.core.web_urls', namespace='dashboard')),
    path('facilities/', include('apps.facilities.web_urls', namespace='facilities_web')),
    path('residents/', include('apps.residents.web_urls', namespace='residents_web')),
    path('staff/', include('apps.staff.web_urls', namespace='staff_web')),
    path('medical/', include('apps.medical.web_urls', namespace='medical_web')),
    # path('scheduling/', include('apps.scheduling.web_urls', namespace='scheduling_web')),
    path('reporting/', include('apps.reporting.web_urls', namespace='reporting_web')),
    
    # Authentication (use our custom views instead of Django's default)
    # path('auth/', include('django.contrib.auth.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Add debug toolbar in development
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns

# Customize admin site
admin.site.site_header = 'Geriatric Administration System'
admin.site.site_title = 'Geriatric Admin'
admin.site.index_title = 'Administration'