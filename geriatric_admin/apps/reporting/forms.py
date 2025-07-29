from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from .models import Report
from apps.residents.models import Resident
from apps.staff.models import Staff
from apps.facilities.models import Room
from datetime import datetime, timedelta
from django.utils import timezone


class ReportForm(forms.ModelForm):
    """Formulario para crear y editar reportes"""
    
    class Meta:
        model = Report
        fields = [
            'title', 'description', 'report_type', 'format',
            'date_from', 'date_to', 'filters'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el título del reporte')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Descripción opcional del reporte')
            }),
            'report_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'format': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'date_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Establecer fechas por defecto (último mes)
        if not self.instance.pk:
            today = timezone.now().date()
            self.fields['date_from'].initial = today - timedelta(days=30)
            self.fields['date_to'].initial = today
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise forms.ValidationError(
                _('La fecha de inicio no puede ser posterior a la fecha de fin.')
            )
        
        return cleaned_data


class QuickReportForm(forms.Form):
    """Formulario para reportes rápidos"""
    
    REPORT_TYPES = [
        ('residents', _('Residentes')),
        ('staff', _('Personal')),
        ('facilities', _('Instalaciones')),
        ('financial', _('Financiero')),
        ('medical', _('Médico')),
        ('occupancy', _('Ocupación')),
        ('custom', _('Personalizado')),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('json', 'JSON'),
        ('csv', 'CSV'),
    ]
    
    PERIOD_CHOICES = [
        ('today', _('Hoy')),
        ('week', _('Esta Semana')),
        ('month', _('Este Mes')),
        ('quarter', _('Este Trimestre')),
        ('year', _('Este Año')),
        ('custom', _('Personalizado')),
    ]
    
    report_type = forms.ChoiceField(
        choices=REPORT_TYPES,
        label=_('Tipo de Reporte'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    period = forms.ChoiceField(
        choices=PERIOD_CHOICES,
        label=_('Período'),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        label=_('Formato'),
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        label=_('Fecha Desde'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        label=_('Fecha Hasta'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if period == 'custom':
            if not date_from or not date_to:
                raise forms.ValidationError(
                    _('Para períodos personalizados, debe especificar las fechas de inicio y fin.')
                )
            if date_from > date_to:
                raise forms.ValidationError(
                    _('La fecha de inicio no puede ser posterior a la fecha de fin.')
                )
        
        return cleaned_data
    
    def get_report_type_display(self):
        """Retorna el nombre legible del tipo de reporte seleccionado"""
        report_type = self.cleaned_data.get('report_type')
        if report_type:
            for choice_value, choice_label in self.REPORT_TYPES:
                if choice_value == report_type:
                    return choice_label
        return report_type or ''
    
    def get_date_range(self):
        """Retorna el rango de fechas basado en el período seleccionado"""
        period = self.cleaned_data.get('period')
        today = timezone.now().date()
        
        if period == 'custom':
            return self.cleaned_data.get('date_from'), self.cleaned_data.get('date_to')
        elif period == 'today':
            return today, today
        elif period == 'week':
            start = today - timedelta(days=today.weekday())
            return start, today
        elif period == 'month':
            start = today.replace(day=1)
            return start, today
        elif period == 'quarter':
            quarter = (today.month - 1) // 3
            start = today.replace(month=quarter * 3 + 1, day=1)
            return start, today
        elif period == 'year':
            start = today.replace(month=1, day=1)
            return start, today
        
        return None, None


class ResidentReportForm(forms.Form):
    """Formulario específico para reportes de residentes"""
    
    STATUS_CHOICES = [
        ('', _('Todos')),
        ('active', _('Activos')),
        ('inactive', _('Inactivos')),
    ]
    
    GENDER_CHOICES = [
        ('', _('Todos')),
        ('M', _('Masculino')),
        ('F', _('Femenino')),
    ]
    
    ROOM_STATUS_CHOICES = [
        ('', _('Todos')),
        ('assigned', _('Con Habitación')),
        ('unassigned', _('Sin Habitación')),
    ]
    
    date_from = forms.DateField(
        label=_('Fecha Desde'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        label=_('Fecha Hasta'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label=_('Estado'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    gender = forms.ChoiceField(
        choices=GENDER_CHOICES,
        label=_('Género'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    room_status = forms.ChoiceField(
        choices=ROOM_STATUS_CHOICES,
        label=_('Estado de Habitación'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_age = forms.IntegerField(
        label=_('Edad Mínima'),
        required=False,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ej: 65')
        })
    )
    
    max_age = forms.IntegerField(
        label=_('Edad Máxima'),
        required=False,
        min_value=0,
        max_value=120,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ej: 85')
        })
    )
    
    include_medical_info = forms.BooleanField(
        label=_('Incluir Información Médica'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_emergency_contacts = forms.BooleanField(
        label=_('Incluir Contactos de Emergencia'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    format = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('json', 'JSON'),
            ('csv', 'CSV'),
        ],
        label=_('Formato'),
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


class StaffReportForm(forms.Form):
    """Formulario específico para reportes de personal"""
    
    STATUS_CHOICES = [
        ('', _('Todos')),
        ('active', _('Activos')),
        ('inactive', _('Inactivos')),
        ('suspended', _('Suspendidos')),
    ]
    
    DEPARTMENT_CHOICES = [
        ('', _('Todos')),
        ('nursing', _('Enfermería')),
        ('medical', _('Médico')),
        ('administrative', _('Administrativo')),
        ('maintenance', _('Mantenimiento')),
        ('kitchen', _('Cocina')),
        ('cleaning', _('Limpieza')),
    ]
    
    date_from = forms.DateField(
        label=_('Fecha Desde'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        label=_('Fecha Hasta'),
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        label=_('Estado'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    department = forms.ChoiceField(
        choices=DEPARTMENT_CHOICES,
        label=_('Departamento'),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    min_salary = forms.DecimalField(
        label=_('Salario Mínimo'),
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ej: 1500.00')
        })
    )
    
    max_salary = forms.DecimalField(
        label=_('Salario Máximo'),
        required=False,
        min_value=0,
        decimal_places=2,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Ej: 3000.00')
        })
    )
    
    include_salary_info = forms.BooleanField(
        label=_('Incluir Información Salarial'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    include_schedule_info = forms.BooleanField(
        label=_('Incluir Información de Horarios'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    format = forms.ChoiceField(
        choices=[
            ('pdf', 'PDF'),
            ('json', 'JSON'),
            ('csv', 'CSV'),
        ],
        label=_('Formato'),
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-select'})
    )


# Formularios de plantillas y widgets eliminados para simplificar el sistema 