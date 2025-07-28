from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Room


class RoomForm(forms.ModelForm):
    """Formulario para crear y editar habitaciones"""
    
    class Meta:
        model = Room
        fields = [
            'room_number',
            'floor',
            'total_beds',
            'status',
            'description'
        ]
        widgets = {
            'room_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Ej: 101, A-1, etc.')
            }),
            'floor': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': _('Número de piso')
            }),
            'total_beds': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '1',
                'placeholder': _('Total de camas')
            }),

            'status': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': '3',
                'placeholder': _('Descripción adicional de la habitación')
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Personalizar etiquetas
        self.fields['room_number'].label = _('Número de Habitación')
        self.fields['floor'].label = _('Piso')
        self.fields['total_beds'].label = _('Total de Camas')
        self.fields['status'].label = _('Estado')
        self.fields['description'].label = _('Descripción')
        
        # Agregar ayuda
        self.fields['room_number'].help_text = _('Número único de la habitación')
        self.fields['floor'].help_text = _('Piso donde se encuentra la habitación')
        self.fields['total_beds'].help_text = _('Número total de camas en la habitación')
        self.fields['status'].help_text = _('Estado actual de la habitación')
        self.fields['description'].help_text = _('Descripción adicional de la habitación')
    
    def clean(self):
        """Validación personalizada del formulario"""
        cleaned_data = super().clean()
        # La validación de ocupación ahora se maneja en el modelo
        return cleaned_data


class RoomSearchForm(forms.Form):
    """Formulario para buscar y filtrar habitaciones"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Buscar por número o descripción...')
        }),
        label=_('Buscar')
    )
    
    floor = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': _('Filtrar por piso')
        }),
        label=_('Piso')
    )
    
    status = forms.ChoiceField(
        choices=[('', _('Todos los estados'))] + Room.ROOM_STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control'
        }),
        label=_('Estado')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Hacer el campo de piso opcional
        self.fields['floor'].required = False 