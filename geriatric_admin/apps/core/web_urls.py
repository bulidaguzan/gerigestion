from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

app_name = 'dashboard'

urlpatterns = [
    # Dashboard home
    path('', login_required(TemplateView.as_view(template_name='core/dashboard/index.html')), name='index'),
    
    # Web interface endpoints will be added in later tasks
]