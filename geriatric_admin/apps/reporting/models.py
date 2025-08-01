from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from datetime import datetime, timedelta
import json


class Report(models.Model):
    """Modelo para almacenar reportes generados del sistema"""
    
    REPORT_TYPES = [
        ('residents', _('Residentes')),
        ('staff', _('Personal')),
        ('facilities', _('Instalaciones')),
        ('financial', _('Financiero')),
        ('medical', _('Médico')),
        ('occupancy', _('Ocupación')),
        ('custom', _('Personalizado')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pendiente')),
        ('processing', _('Procesando')),
        ('completed', _('Completado')),
        ('failed', _('Fallido')),
    ]
    
    FORMAT_CHOICES = [
        ('csv', 'CSV'),
    ]
    
    # Información básica
    title = models.CharField(_('Título'), max_length=200)
    description = models.TextField(_('Descripción'), blank=True)
    report_type = models.CharField(_('Tipo de Reporte'), max_length=20, choices=REPORT_TYPES)
    format = models.CharField(_('Formato'), max_length=10, choices=FORMAT_CHOICES, default='csv')
    status = models.CharField(_('Estado'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Filtros y parámetros
    date_from = models.DateField(_('Fecha Desde'), null=True, blank=True)
    date_to = models.DateField(_('Fecha Hasta'), null=True, blank=True)
    filters = models.JSONField(_('Filtros'), default=dict, blank=True)
    
    # Resultados
    file_path = models.CharField(_('Ruta del Archivo'), max_length=500, blank=True)
    file_size = models.IntegerField(_('Tamaño del Archivo (bytes)'), default=0)
    generated_at = models.DateTimeField(_('Generado el'), null=True, blank=True)
    
    # Metadatos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Creado por'))
    created_at = models.DateTimeField(_('Creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado el'), auto_now=True)
    
    class Meta:
        verbose_name = _('Reporte')
        verbose_name_plural = _('Reportes')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.get_report_type_display()}"
    
    @property
    def is_completed(self):
        return self.status == 'completed'
    
    @property
    def is_failed(self):
        return self.status == 'failed'
    
    @property
    def file_size_mb(self):
        """Retorna el tamaño del archivo en MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def get_filters_display(self):
        """Retorna los filtros en formato legible"""
        if not self.filters:
            return _('Sin filtros')
        
        filter_display = []
        for key, value in self.filters.items():
            if isinstance(value, list):
                filter_display.append(f"{key}: {', '.join(map(str, value))}")
            else:
                filter_display.append(f"{key}: {value}")
        
        return '; '.join(filter_display)


class ReportTemplate(models.Model):
    """Modelo para plantillas de reportes reutilizables"""
    
    TEMPLATE_TYPES = [
        ('residents_monthly', _('Residentes Mensual')),
        ('staff_attendance', _('Asistencia del Personal')),
        ('facilities_occupancy', _('Ocupación de Instalaciones')),
        ('financial_summary', _('Resumen Financiero')),
        ('medical_records', _('Registros Médicos')),
        ('custom', _('Personalizado')),
    ]
    
    name = models.CharField(_('Nombre'), max_length=200)
    description = models.TextField(_('Descripción'), blank=True)
    template_type = models.CharField(_('Tipo de Plantilla'), max_length=30, choices=TEMPLATE_TYPES)
    is_active = models.BooleanField(_('Activo'), default=True)
    
    # Configuración del reporte
    default_filters = models.JSONField(_('Filtros por Defecto'), default=dict, blank=True)
    default_format = models.CharField(_('Formato por Defecto'), max_length=10, choices=Report.FORMAT_CHOICES, default='csv')
    
    # Metadatos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Creado por'))
    created_at = models.DateTimeField(_('Creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado el'), auto_now=True)
    
    class Meta:
        verbose_name = _('Plantilla de Reporte')
        verbose_name_plural = _('Plantillas de Reportes')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def create_report(self, user, **kwargs):
        """Crea un nuevo reporte basado en esta plantilla"""
        filters = self.default_filters.copy()
        filters.update(kwargs.get('filters', {}))
        
        return Report.objects.create(
            title=f"{self.name} - {timezone.now().strftime('%d/%m/%Y')}",
            description=self.description,
            report_type=self.template_type.split('_')[0],
            format=kwargs.get('format', self.default_format),
            filters=filters,
            date_from=kwargs.get('date_from'),
            date_to=kwargs.get('date_to'),
            created_by=user
        )


class DashboardWidget(models.Model):
    """Modelo para widgets del dashboard de reportes"""
    
    WIDGET_TYPES = [
        ('chart', _('Gráfico')),
        ('metric', _('Métrica')),
        ('table', _('Tabla')),
        ('list', _('Lista')),
    ]
    
    CHART_TYPES = [
        ('line', _('Línea')),
        ('bar', _('Barras')),
        ('pie', _('Circular')),
        ('doughnut', _('Dona')),
        ('area', _('Área')),
    ]
    
    name = models.CharField(_('Nombre'), max_length=200)
    description = models.TextField(_('Descripción'), blank=True)
    widget_type = models.CharField(_('Tipo de Widget'), max_length=20, choices=WIDGET_TYPES)
    chart_type = models.CharField(_('Tipo de Gráfico'), max_length=20, choices=CHART_TYPES, blank=True)
    
    # Configuración
    data_source = models.CharField(_('Fuente de Datos'), max_length=100)
    refresh_interval = models.IntegerField(_('Intervalo de Actualización (minutos)'), default=60)
    is_active = models.BooleanField(_('Activo'), default=True)
    
    # Posición y tamaño
    position_x = models.IntegerField(_('Posición X'), default=0)
    position_y = models.IntegerField(_('Posición Y'), default=0)
    width = models.IntegerField(_('Ancho'), default=6)
    height = models.IntegerField(_('Alto'), default=4)
    
    # Metadatos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Creado por'))
    created_at = models.DateTimeField(_('Creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado el'), auto_now=True)
    
    class Meta:
        verbose_name = _('Widget del Dashboard')
        verbose_name_plural = _('Widgets del Dashboard')
        ordering = ['position_y', 'position_x']
    
    def __str__(self):
        return self.name
    
    @property
    def is_chart(self):
        return self.widget_type == 'chart'
    
    @property
    def is_metric(self):
        return self.widget_type == 'metric'
    
    @property
    def is_table(self):
        return self.widget_type == 'table'
    
    @property
    def is_list(self):
        return self.widget_type == 'list' 