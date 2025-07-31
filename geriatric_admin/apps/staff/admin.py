from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from .models import Staff


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = [
        'full_name_display',
        'employee_id',
        'position',
        'department',
        'employment_status_display',
        'hire_date',
        'years_of_service_display',
        'salary_display',
        'contact_info'
    ]
    
    list_filter = [
        'department',
        'position',
        'employment_status',
        'gender',
        'marital_status',
        'hire_date',
        'shift_type',
    ]
    
    search_fields = [
        'first_name',
        'last_name',
        'employee_id',
        'email',
        'phone',
        'position',
        'department'
    ]
    
    # list_editable = [
    #     'employment_status'
    # ]
    
    readonly_fields = [
        'age',
        'years_of_service',
        'is_active',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        (_('Información Personal'), {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'marital_status')
        }),
        (_('Información de Contacto'), {
            'fields': ('phone', 'email', 'address', 'city')
        }),
        (_('Información Laboral'), {
            'fields': ('employee_id', 'position', 'department', 'hire_date', 'employment_status', 'salary')
        }),
        (_('Horarios'), {
            'fields': ('work_schedule', 'shift_type')
        }),
        (_('Contacto de Emergencia'), {
            'fields': ('emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone')
        }),
        (_('Información Médica'), {
            'fields': ('blood_type', 'allergies', 'medical_conditions'),
            'classes': ('collapse',)
        }),
        (_('Información Adicional'), {
            'fields': ('skills', 'notes'),
            'classes': ('collapse',)
        }),
        (_('Información del Sistema'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    ordering = ['last_name', 'first_name']
    
    def full_name_display(self, obj):
        """Muestra el nombre completo con enlace"""
        url = reverse('admin:staff_staff_change', args=[obj.id])
        return format_html('<a href="{}">{}</a>', url, obj.full_name)
    full_name_display.short_description = _('Nombre Completo')
    full_name_display.admin_order_field = 'last_name'
    
    def employment_status_display(self, obj):
        """Muestra el estado de empleo con color"""
        status_colors = {
            'active': 'green',
            'inactive': 'gray',
            'suspended': 'orange',
            'terminated': 'red'
        }
        color = status_colors.get(obj.employment_status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>', 
            color, 
            obj.get_employment_status_display()
        )
    employment_status_display.short_description = _('Estado')
    
    def years_of_service_display(self, obj):
        """Muestra los años de servicio"""
        years = obj.years_of_service
        if years == 0:
            return _('Menos de 1 año')
        elif years == 1:
            return _('1 año')
        else:
            return _('{} años').format(years)
    years_of_service_display.short_description = _('Años de Servicio')
    years_of_service_display.admin_order_field = 'hire_date'
    
    def salary_display(self, obj):
        """Muestra el salario formateado"""
        return format_html('${:,.2f}', obj.salary)
    salary_display.short_description = _('Salario')
    salary_display.admin_order_field = 'salary'
    
    def contact_info(self, obj):
        """Muestra información de contacto resumida"""
        return format_html(
            '<div><strong>📧</strong> {}</div><div><strong>📞</strong> {}</div>',
            obj.email,
            obj.phone
        )
    contact_info.short_description = _('Contacto')
    
    def get_queryset(self, request):
        """Optimizar consultas"""
        return super().get_queryset(request)
    
    def save_model(self, request, obj, form, change):
        """Validar antes de guardar"""
        obj.full_clean()
        super().save_model(request, obj, form, change)
    
    actions = ['activate_staff', 'deactivate_staff', 'suspend_staff']
    
    def activate_staff(self, request, queryset):
        """Activar empleados seleccionados"""
        updated = queryset.update(employment_status='active')
        self.message_user(
            request, 
            _('{} empleados activados exitosamente.').format(updated)
        )
    activate_staff.short_description = _('Activar empleados seleccionados')
    
    def deactivate_staff(self, request, queryset):
        """Desactivar empleados seleccionados"""
        updated = queryset.update(employment_status='inactive')
        self.message_user(
            request, 
            _('{} empleados desactivados exitosamente.').format(updated)
        )
    deactivate_staff.short_description = _('Desactivar empleados seleccionados')
    
    def suspend_staff(self, request, queryset):
        """Suspender empleados seleccionados"""
        updated = queryset.update(employment_status='suspended')
        self.message_user(
            request, 
            _('{} empleados suspendidos exitosamente.').format(updated)
        )
    suspend_staff.short_description = _('Suspender empleados seleccionados') 