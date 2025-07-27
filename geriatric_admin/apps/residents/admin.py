from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Resident


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'age', 'gender_display', 'room_display', 
        'admission_date', 'length_of_stay_display', 'emergency_contact'
    ]
    list_filter = [
        'gender', 'marital_status', 'admission_date', 'room__floor',
        ('room', admin.EmptyFieldListFilter),
    ]
    search_fields = [
        'first_name', 'last_name', 'phone', 'email', 
        'emergency_contact_name', 'emergency_contact_phone'
    ]
    readonly_fields = ['age', 'length_of_stay', 'created_at', 'updated_at']
    
    fieldsets = (
        (_('Información Personal'), {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'marital_status', 'occupation')
        }),
        (_('Información de Contacto'), {
            'fields': ('phone', 'email', 'address', 'city')
        }),
        (_('Información Médica'), {
            'fields': ('blood_type', 'allergies', 'medical_conditions', 'medications'),
            'classes': ('collapse',)
        }),
        (_('Contacto de Emergencia'), {
            'fields': (
                'emergency_contact_name', 'emergency_contact_relationship',
                'emergency_contact_phone', 'emergency_contact_email'
            )
        }),
        (_('Información de Admisión'), {
            'fields': ('admission_date', 'room')
        }),
        (_('Información Adicional'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Información de Auditoría'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = _('Nombre Completo')
    full_name.admin_order_field = 'last_name'
    
    def age(self, obj):
        return f"{obj.age} años"
    age.short_description = _('Edad')
    
    def gender_display(self, obj):
        if obj.gender == 'M':
            return format_html('<span style="color: #007bff;">{}</span>', _('Masculino'))
        elif obj.gender == 'F':
            return format_html('<span style="color: #17a2b8;">{}</span>', _('Femenino'))
        else:
            return format_html('<span style="color: #6c757d;">{}</span>', _('Otro'))
    gender_display.short_description = _('Género')
    
    def room_display(self, obj):
        if obj.room:
            return format_html(
                '<a href="{}">{}</a>',
                reverse('admin:facilities_room_change', args=[obj.room.id]),
                obj.room.room_number
            )
        else:
            return format_html('<span style="color: #ffc107;">{}</span>', _('Sin asignar'))
    room_display.short_description = _('Habitación')
    
    def length_of_stay_display(self, obj):
        return f"{obj.length_of_stay} días"
    length_of_stay_display.short_description = _('Tiempo de Estancia')
    
    def emergency_contact(self, obj):
        return f"{obj.emergency_contact_name} ({obj.get_emergency_contact_relationship_display()})"
    emergency_contact.short_description = _('Contacto de Emergencia')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('room')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo residente
            # Aquí podrías agregar lógica adicional para nuevos residentes
            pass
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/resident_admin.css',)
        }
        js = ('admin/js/resident_admin.js',) 