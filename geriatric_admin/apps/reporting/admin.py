from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from .models import Report, ReportTemplate, DashboardWidget


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'report_type_display', 'format', 'status_display', 
        'created_by', 'created_at', 'file_size_display'
    ]
    list_filter = [
        'report_type', 'status', 'format', 'created_at', 'generated_at'
    ]
    search_fields = ['title', 'description', 'created_by__username']
    readonly_fields = [
        'created_by', 'created_at', 'updated_at', 'generated_at', 
        'file_size', 'file_size_mb'
    ]
    date_hierarchy = 'created_at'
    ordering = ['-created_at']
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('title', 'description', 'report_type', 'format', 'status')
        }),
        (_('Filtros y Parámetros'), {
            'fields': ('date_from', 'date_to', 'filters'),
            'classes': ('collapse',)
        }),
        (_('Resultados'), {
            'fields': ('file_path', 'file_size', 'file_size_mb', 'generated_at'),
            'classes': ('collapse',)
        }),
        (_('Metadatos'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def report_type_display(self, obj):
        return obj.get_report_type_display()
    report_type_display.short_description = _('Tipo de Reporte')
    
    def status_display(self, obj):
        status_colors = {
            'pending': 'orange',
            'processing': 'blue',
            'completed': 'green',
            'failed': 'red'
        }
        color = status_colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = _('Estado')
    
    def file_size_display(self, obj):
        if obj.file_size:
            return f"{obj.file_size_mb} MB"
        return _('No disponible')
    file_size_display.short_description = _('Tamaño')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo reporte
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ReportTemplate)
class ReportTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'template_type_display', 'is_active', 'default_format',
        'created_by', 'created_at'
    ]
    list_filter = ['template_type', 'is_active', 'default_format', 'created_at']
    search_fields = ['name', 'description', 'created_by__username']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('name', 'description', 'template_type', 'is_active')
        }),
        (_('Configuración'), {
            'fields': ('default_filters', 'default_format'),
            'classes': ('collapse',)
        }),
        (_('Metadatos'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def template_type_display(self, obj):
        return obj.get_template_type_display()
    template_type_display.short_description = _('Tipo de Plantilla')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva plantilla
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'widget_type_display', 'chart_type_display', 'is_active',
        'position_display', 'created_by'
    ]
    list_filter = [
        'widget_type', 'chart_type', 'is_active', 'refresh_interval', 'created_at'
    ]
    search_fields = ['name', 'description', 'data_source', 'created_by__username']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('name', 'description', 'widget_type', 'chart_type')
        }),
        (_('Configuración'), {
            'fields': ('data_source', 'refresh_interval', 'is_active')
        }),
        (_('Posición y Tamaño'), {
            'fields': ('position_x', 'position_y', 'width', 'height'),
            'classes': ('collapse',)
        }),
        (_('Metadatos'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def widget_type_display(self, obj):
        return obj.get_widget_type_display()
    widget_type_display.short_description = _('Tipo de Widget')
    
    def chart_type_display(self, obj):
        if obj.chart_type:
            return obj.get_chart_type_display()
        return _('N/A')
    chart_type_display.short_description = _('Tipo de Gráfico')
    
    def position_display(self, obj):
        return f"({obj.position_x}, {obj.position_y}) - {obj.width}x{obj.height}"
    position_display.short_description = _('Posición y Tamaño')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es un nuevo widget
            obj.created_by = request.user
        super().save_model(request, obj, form, change) 