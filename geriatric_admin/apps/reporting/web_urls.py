from django.urls import path
from . import views

app_name = 'reporting_web'

urlpatterns = [
    # Dashboard principal
    path('', views.reporting_dashboard, name='index'),
    path('dashboard/', views.reporting_dashboard, name='dashboard'),
    
    # Gestión de reportes
    path('reports/', views.report_list, name='report_list'),
    path('reports/create/', views.report_create, name='report_create'),
    path('reports/<int:report_id>/', views.report_detail, name='report_detail'),
    path('reports/<int:report_id>/update/', views.report_update, name='report_update'),
    path('reports/<int:report_id>/delete/', views.report_delete, name='report_delete'),
    
    # Reportes rápidos
    path('quick-report/', views.quick_report, name='quick_report'),
    
    # Reportes específicos
    path('residents/', views.resident_report, name='resident_report'),
    path('staff/', views.staff_report, name='staff_report'),
    
    # Plantillas y widgets eliminados para simplificar
    
    # AJAX endpoints
    path('api/reports/search/', views.report_search, name='report_search'),
    path('api/reports/<int:report_id>/status/', views.report_status_update, name='report_status_update'),
    
    # Acciones de reportes
    path('reports/<int:report_id>/download/', views.report_download, name='report_download'),
    path('reports/<int:report_id>/regenerate/', views.report_regenerate, name='report_regenerate'),
]