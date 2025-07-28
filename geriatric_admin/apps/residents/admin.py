from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Resident, ResidentReport


@admin.register(Resident)
class ResidentAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'age', 'gender_display', 'room_display', 
        'admission_date', 'length_of_stay_display', 'treatment_status_display', 'emergency_contact'
    ]
    list_filter = [
        'gender', 'marital_status', 'admission_date', 'room__floor',
        'is_in_treatment', 'treatment_type', 'treatment_status',
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
        (_('Estado de Tratamiento'), {
            'fields': (
                'is_in_treatment', 
                'treatment_type', 
                'treatment_status',
                'treatment_start_date', 
                'treatment_end_date',
                'treatment_frequency',
                'treatment_provider',
                'treatment_goals',
                'treatment_progress',
                'treatment_notes'
            ),
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
    
    def treatment_status_display(self, obj):
        if obj.is_in_treatment:
            return format_html('<span style="color: #28a745;">{}</span>', _('En Tratamiento'))
        else:
            return format_html('<span style="color: #6c757d;">{}</span>', _('Sin Tratamiento'))
    treatment_status_display.short_description = _('Estado de Tratamiento')
    
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


@admin.register(ResidentReport)
class ResidentReportAdmin(admin.ModelAdmin):
    list_display = [
        'resident_name', 'report_type_display', 'report_date', 
        'status_display', 'created_by', 'created_at'
    ]
    list_filter = [
        'report_type', 'status', 'report_date', 'resident__is_in_treatment',
        'created_by'
    ]
    search_fields = [
        'resident__first_name', 'resident__last_name', 
        'physical_condition', 'mental_condition', 'recommendations'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('resident', 'report_type', 'report_date', 'status')
        }),
        (_('Evaluación Física'), {
            'fields': ('physical_condition', 'medical_treatment', 'medication_changes'),
            'classes': ('collapse',)
        }),
        (_('Evaluación Mental y Social'), {
            'fields': ('mental_condition', 'social_activity'),
            'classes': ('collapse',)
        }),
        (_('Eventos y Metas'), {
            'fields': ('incidents', 'goals_achieved', 'next_goals'),
            'classes': ('collapse',)
        }),
        (_('Recomendaciones'), {
            'fields': ('recommendations',)
        }),
        (_('Metadatos'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def resident_name(self, obj):
        return obj.resident.full_name
    resident_name.short_description = _('Residente')
    resident_name.admin_order_field = 'resident__last_name'
    
    def report_type_display(self, obj):
        return obj.get_report_type_display()
    report_type_display.short_description = _('Tipo de Informe')
    
    def status_display(self, obj):
        if obj.status == 'completed':
            return format_html('<span style="color: #28a745;">{}</span>', _('Completado'))
        elif obj.status == 'draft':
            return format_html('<span style="color: #ffc107;">{}</span>', _('Borrador'))
        else:
            return format_html('<span style="color: #6c757d;">{}</span>', _('Archivado'))
    status_display.short_description = _('Estado')
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('resident', 'created_by')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo informe
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    class Media:
        css = {
            'all': ('admin/css/resident_report_admin.css',)
        }
        js = ('admin/js/resident_report_admin.js',) 