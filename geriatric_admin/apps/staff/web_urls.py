from django.urls import path
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required

app_name = 'staff_web'

urlpatterns = [
    path('', login_required(TemplateView.as_view(template_name='staff/index.html')), name='index'),
]