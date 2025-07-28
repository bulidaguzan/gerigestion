from django.urls import path
from . import views

app_name = 'residents_web'

urlpatterns = [
    # Dashboard principal de residentes
    path('', views.resident_dashboard, name='dashboard'),
    path('index/', views.resident_dashboard, name='index'),  # URL alternativa para compatibilidad
    
    # URLs para residentes
    path('list/', views.resident_list, name='resident_list'),
    path('create/', views.resident_create, name='resident_create'),
    path('<int:resident_id>/', views.resident_detail, name='resident_detail'),
    path('<int:resident_id>/edit/', views.resident_update, name='resident_update'),
    path('<int:resident_id>/delete/', views.resident_delete, name='resident_delete'),
    path('search/', views.resident_search, name='resident_search'),
    
    # URLs para informes periódicos
    path('<int:resident_id>/reports/', views.resident_reports_list, name='resident_reports_list'),
    path('<int:resident_id>/reports/create/', views.resident_report_create, name='resident_report_create'),
    path('<int:resident_id>/reports/<int:report_id>/', views.resident_report_detail, name='resident_report_detail'),
    path('<int:resident_id>/reports/<int:report_id>/edit/', views.resident_report_update, name='resident_report_update'),
    path('<int:resident_id>/reports/<int:report_id>/delete/', views.resident_report_delete, name='resident_report_delete'),
]