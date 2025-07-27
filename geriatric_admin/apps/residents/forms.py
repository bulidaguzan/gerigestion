from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Resident


class ResidentForm(forms.ModelForm):
    """
    Formulario para crear y editar residentes
    """
    
    class Meta:
        model = Resident
        fields = [
            'first_name', 'last_name', 'date_of_birth', 'gender',
            'phone', 'email', 'address', 'city',
            'marital_status', 'occupation',
            'blood_type', 'allergies', 'medical_conditions', 'medications',
            'emergency_contact_name', 'emergency_contact_relationship',
            'emergency_contact_phone', 'emergency_contact_email',
            'admission_date', 'room', 'notes'
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
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: +34 123 456 789')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('ejemplo@correo.com')
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
            'marital_status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'occupation': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ocupación anterior')
            }),
            'blood_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: A+, B-, O+, etc.')
            }),
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Lista de alergias conocidas')
            }),
            'medical_conditions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Condiciones médicas importantes')
            }),
            'medications': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Medicamentos que toma regularmente')
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nombre completo del contacto de emergencia')
            }),
            'emergency_contact_relationship': forms.Select(attrs={
                'class': 'form-control'
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Teléfono del contacto de emergencia')
            }),
            'emergency_contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Correo del contacto de emergencia')
            }),
            'admission_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'room': forms.Select(attrs={
                'class': 'form-control'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Notas adicionales sobre el residente')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar habitaciones disponibles para el campo room
        if 'room' in self.fields:
            from apps.facilities.models import Room
            available_rooms = Room.objects.filter(status='available')
            self.fields['room'].queryset = available_rooms
            self.fields['room'].empty_label = _("Seleccione una habitación")
    
    def clean_phone(self):
        """Validación personalizada para el teléfono"""
        phone = self.cleaned_data.get('phone')
        if phone:
            # Remover espacios y caracteres especiales
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 9:
                raise forms.ValidationError(_('El número de teléfono debe tener al menos 9 dígitos.'))
        return phone
    
    def clean_emergency_contact_phone(self):
        """Validación personalizada para el teléfono de emergencia"""
        phone = self.cleaned_data.get('emergency_contact_phone')
        if phone:
            # Remover espacios y caracteres especiales
            phone = ''.join(filter(str.isdigit, phone))
            if len(phone) < 9:
                raise forms.ValidationError(_('El número de teléfono debe tener al menos 9 dígitos.'))
        return phone 