from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Room


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = [
        'room_number', 
        'floor', 
        'total_beds', 
        'occupied_beds', 
        'available_beds_display',
        'residents_count_display',
        'occupancy_rate_display',
        'status_display',
        'is_available_display'
    ]
    
    list_filter = [
        'floor',
        'status',
        'total_beds',
        'occupied_beds',
    ]
    
    search_fields = [
        'room_number',
        'description'
    ]
    
    list_editable = [
        'occupied_beds'
    ]
    
    readonly_fields = [
        'available_beds',
        'occupancy_rate',
        'is_full',
        'is_available',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('room_number', 'floor', 'description')
        }),
        (_('Capacidad'), {
            'fields': ('total_beds', 'occupied_beds', 'available_beds', 'occupancy_rate')
        }),
        (_('Estado'), {
            'fields': ('status', 'is_full', 'is_available')
        }),
        (_('Información del Sistema'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['floor', 'room_number']
    
    def available_beds_display(self, obj):
        """Muestra las camas disponibles con color"""
        available = obj.available_beds
        if available == 0:
            return format_html('<span style="color: red; font-weight: bold;">{}</span>', available)
        elif available <= 2:
            return format_html('<span style="color: orange; font-weight: bold;">{}</span>', available)
        else:
            return format_html('<span style="color: green; font-weight: bold;">{}</span>', available)
    available_beds_display.short_description = _('Camas Disponibles')
    available_beds_display.admin_order_field = 'occupied_beds'
    
    def residents_count_display(self, obj):
        """Muestra el número de residentes asignados"""
        count = obj.residents_count
        if count > 0:
            return format_html(
                '<span style="color: blue; font-weight: bold;">{} {}</span>', 
                count, 
                _('residente' if count == 1 else 'residentes')
            )
        else:
            return format_html('<span style="color: gray;">{}</span>', _('Sin residentes'))
    residents_count_display.short_description = _('Residentes')
    residents_count_display.admin_order_field = 'residents_count'
    
    def occupancy_rate_display(self, obj):
        """Muestra el porcentaje de ocupación con color"""
        rate = obj.occupancy_rate
        if rate >= 90:
            color = 'red'
        elif rate >= 70:
            color = 'orange'
        else:
            color = 'green'
        return format_html('<span style="color: {}; font-weight: bold;">{}%</span>', color, rate)
    occupancy_rate_display.short_description = _('Ocupación')
    occupancy_rate_display.admin_order_field = 'occupied_beds'
    
    def status_display(self, obj):
        """Muestra el estado con color"""
        status_colors = {
            'available': 'green',
            'maintenance': 'orange',
            'quarantine': 'red'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', 
            color, 
            obj.get_status_display()
        )
    status_display.short_description = _('Estado')
    
    def is_available_display(self, obj):
        """Muestra si la habitación está disponible"""
        if obj.is_available:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {}</span>', 
                _('Disponible')
            )
        else:
            return format_html(
                '<span style="color: red; font-weight: bold;">✗ {}</span>', 
                _('No Disponible')
            )
    is_available_display.short_description = _('Disponibilidad')
    
    def get_queryset(self, request):
        """Optimizar consultas con select_related"""
        return super().get_queryset(request)
    
    def save_model(self, request, obj, form, change):
        """Validar antes de guardar"""
        obj.full_clean()
        super().save_model(request, obj, form, change)
    
    actions = ['mark_as_available', 'mark_as_maintenance', 'mark_as_quarantine']
    
    def mark_as_available(self, request, queryset):
        """Marcar habitaciones como disponibles"""
        updated = queryset.update(status='available')
        self.message_user(
            request, 
            _('{} habitaciones marcadas como disponibles.').format(updated)
        )
    mark_as_available.short_description = _('Marcar como disponibles')
    
    def mark_as_maintenance(self, request, queryset):
        """Marcar habitaciones en mantenimiento"""
        updated = queryset.update(status='maintenance')
        self.message_user(
            request, 
            _('{} habitaciones marcadas en mantenimiento.').format(updated)
        )
    mark_as_maintenance.short_description = _('Marcar en mantenimiento')
    
    def mark_as_quarantine(self, request, queryset):
        """Marcar habitaciones en cuarentena"""
        updated = queryset.update(status='quarantine')
        self.message_user(
            request, 
            _('{} habitaciones marcadas en cuarentena.').format(updated)
        )
    mark_as_quarantine.short_description = _('Marcar en cuarentena') 