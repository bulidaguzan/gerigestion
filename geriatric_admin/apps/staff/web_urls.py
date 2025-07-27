from django.urls import path
from . import views

app_name = 'staff_web'

urlpatterns = [
    # Dashboard principal del personal
    path('', views.staff_dashboard, name='index'),
    
    # URLs para empleados
    path('list/', views.staff_list, name='staff_list'),
    path('create/', views.staff_create, name='staff_create'),
    path('<int:staff_id>/', views.staff_detail, name='staff_detail'),
    path('<int:staff_id>/edit/', views.staff_update, name='staff_update'),
    path('<int:staff_id>/delete/', views.staff_delete, name='staff_delete'),
    path('search/', views.staff_search, name='staff_search'),
    path('<int:staff_id>/update-status/', views.staff_update_status, name='staff_update_status'),
]