from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Staff


class StaffForm(forms.ModelForm):
    """Formulario para crear y editar empleados"""
    
    class Meta:
        model = Staff
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender', 'marital_status',
            'phone', 'email', 'address', 'city',
            'employee_id', 'position', 'department', 'hire_date', 'employment_status', 'salary',
            'work_schedule', 'shift_type',
            'emergency_contact_name', 'emergency_contact_relationship', 'emergency_contact_phone',
            'blood_type', 'allergies', 'medical_conditions',
            'skills', 'notes'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el nombre')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ingrese el apellido')
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'gender': forms.Select(attrs={
                'class': 'form-control'
            }),
            'marital_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: +34 123 456 789')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('ejemplo@email.com')
            }),
            'address': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Dirección completa')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ciudad')
            }),
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('ID único del empleado')
            }),
            'position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: Enfermero/a, Médico, Cuidador/a')
            }),
            'department': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: Enfermería, Medicina, Cuidados')
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'employment_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'salary': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': _('Salario mensual')
            }),
            'work_schedule': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: L-V 8:00-16:00')
            }),
            'shift_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: Mañana, Tarde, Noche, Rotativo')
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nombre del contacto de emergencia')
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: Esposo/a, Hijo/a, Padre/Madre')
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Teléfono de emergencia')
            }),
            'blood_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: A+, B-, O+, AB+')
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Alergias conocidas (si las hay)')
            }),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Condiciones médicas relevantes')
            }),
            'skills': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Habilidades y certificaciones')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Notas adicionales')
            }),
        }
    
    def clean_phone(self):
        """Validar formato de teléfono"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remover espacios y caracteres especiales
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 9:
                raise forms.ValidationError(_('El número de teléfono debe tener al menos 9 dígitos.'))
        return phone
    
    def clean_emergency_contact_phone(self):
        """Validar formato de teléfono de emergencia"""
        phone = self.cleaned_data.get('emergency_contact_phone')
        if phone:
            # Remover espacios y caracteres especiales
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 9:
                raise forms.ValidationError(_('El número de teléfono debe tener al menos 9 dígitos.'))
        return phone
    
    def clean_employee_id(self):
        """Validar que el ID de empleado sea único"""
        employee_id = self.cleaned_data.get('employee_id')
        if employee_id:
            # Verificar si ya existe un empleado con este ID
            existing_staff = Staff.objects.filter(employee_id=employee_id)
            if self.instance.pk:
                existing_staff = existing_staff.exclude(pk=self.instance.pk)
            
            if existing_staff.exists():
                raise forms.ValidationError(_('Ya existe un empleado con este ID.'))
        return employee_id
    
    def clean_email(self):
        """Validar que el email sea único"""
        email = self.cleaned_data.get('email')
        if email:
            # Verificar si ya existe un empleado con este email
            existing_staff = Staff.objects.filter(email=email)
            if self.instance.pk:
                existing_staff = existing_staff.exclude(pk=self.instance.pk)
            
            if existing_staff.exists():
                raise forms.ValidationError(_('Ya existe un empleado con este email.'))
        return email 