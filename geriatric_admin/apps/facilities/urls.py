from django.urls import path
from . import views

app_name = 'facilities'

urlpatterns = [
    # Dashboard principal de facilities
    path('', views.room_dashboard, name='dashboard'),
    
    # URLs para habitaciones
    path('rooms/', views.room_list, name='room_list'),
    path('rooms/create/', views.room_create, name='room_create'),
    path('rooms/<int:room_id>/', views.room_detail, name='room_detail'),
    path('rooms/<int:room_id>/edit/', views.room_update, name='room_update'),
    path('rooms/<int:room_id>/delete/', views.room_delete, name='room_delete'),
    path('rooms/<int:room_id>/update-occupancy/', views.room_update_occupancy, name='room_update_occupancy'),
]