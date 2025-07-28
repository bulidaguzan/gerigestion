from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from .views import dashboard_view

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home
    path('', dashboard_view, name='index'),
    
    # Web interface endpoints will be added in later tasks
]