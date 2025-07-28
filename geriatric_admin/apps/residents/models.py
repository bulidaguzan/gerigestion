from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date


class Resident(models.Model):
    """
    Modelo para gestionar residentes del geriátrico
    """
    GENDER_CHOICES = [
        ('M', _('Masculino')),
        ('F', _('Femenino')),
        ('O', _('Otro')),
    ]
    
    MARITAL_STATUS_CHOICES = [
        ('single', _('Soltero/a')),
        ('married', _('Casado/a')),
        ('divorced', _('Divorciado/a')),
        ('widowed', _('Viudo/a')),
        ('separated', _('Separado/a')),
    ]
    
    EMERGENCY_CONTACT_RELATIONSHIP_CHOICES = [
        ('spouse', _('Cónyuge')),
        ('child', _('Hijo/a')),
        ('parent', _('Padre/Madre')),
        ('sibling', _('Hermano/a')),
        ('friend', _('Amigo/a')),
        ('other', _('Otro')),
    ]
    
    # Información personal básica
    first_name = models.CharField(
        max_length=50,
        verbose_name=_('Nombre'),
        help_text=_('Primer nombre del residente')
    )
    
    last_name = models.CharField(
        max_length=50,
        verbose_name=_('Apellido'),
        help_text=_('Apellido del residente')
    )
    
    date_of_birth = models.DateField(
        verbose_name=_('Fecha de Nacimiento'),
        help_text=_('Fecha de nacimiento del residente')
    )
    
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name=_('Género'),
        help_text=_('Género del residente')
    )
    
    # Información de contacto
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Teléfono'),
        help_text=_('Número de teléfono del residente')
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name=_('Correo Electrónico'),
        help_text=_('Dirección de correo electrónico del residente')
    )
    
    # Información de dirección
    address = models.TextField(
        blank=True,
        verbose_name=_('Dirección'),
        help_text=_('Dirección de residencia anterior')
    )
    
    city = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Ciudad'),
        help_text=_('Ciudad de residencia anterior')
    )
    
    # Información médica y personal
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        blank=True,
        verbose_name=_('Estado Civil'),
        help_text=_('Estado civil del residente')
    )
    
    occupation = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Ocupación'),
        help_text=_('Ocupación anterior del residente')
    )
    
    # Información médica
    blood_type = models.CharField(
        max_length=5,
        blank=True,
        verbose_name=_('Tipo de Sangre'),
        help_text=_('Tipo de sangre del residente')
    )
    
    allergies = models.TextField(
        blank=True,
        verbose_name=_('Alergias'),
        help_text=_('Lista de alergias conocidas')
    )
    
    medical_conditions = models.TextField(
        blank=True,
        verbose_name=_('Condiciones Médicas'),
        help_text=_('Condiciones médicas crónicas o importantes')
    )
    
    medications = models.TextField(
        blank=True,
        verbose_name=_('Medicamentos'),
        help_text=_('Medicamentos que toma regularmente')
    )
    
    # Estado de tratamiento
    is_in_treatment = models.BooleanField(
        default=False,
        verbose_name=_('En Tratamiento'),
        help_text=_('Indica si el residente está actualmente en tratamiento médico')
    )
    
    treatment_type = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Tipo de Tratamiento'),
        help_text=_('Tipo de tratamiento que está recibiendo (ej: fisioterapia, terapia ocupacional, etc.)')
    )
    
    treatment_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de Inicio del Tratamiento'),
        help_text=_('Fecha en que comenzó el tratamiento actual')
    )
    
    treatment_notes = models.TextField(
        blank=True,
        verbose_name=_('Notas del Tratamiento'),
        help_text=_('Notas adicionales sobre el tratamiento actual')
    )
    
    # Información de emergencia
    emergency_contact_name = models.CharField(
        max_length=100,
        verbose_name=_('Nombre del Contacto de Emergencia'),
        help_text=_('Nombre completo del contacto de emergencia')
    )
    
    emergency_contact_relationship = models.CharField(
        max_length=20,
        choices=EMERGENCY_CONTACT_RELATIONSHIP_CHOICES,
        verbose_name=_('Relación con el Contacto de Emergencia'),
        help_text=_('Relación del contacto de emergencia con el residente')
    )
    
    emergency_contact_phone = models.CharField(
        max_length=20,
        verbose_name=_('Teléfono del Contacto de Emergencia'),
        help_text=_('Número de teléfono del contacto de emergencia')
    )
    
    emergency_contact_email = models.EmailField(
        blank=True,
        verbose_name=_('Correo del Contacto de Emergencia'),
        help_text=_('Correo electrónico del contacto de emergencia')
    )
    
    # Información de admisión
    admission_date = models.DateField(
        verbose_name=_('Fecha de Admisión'),
        help_text=_('Fecha en que el residente fue admitido')
    )
    
    room = models.ForeignKey(
        'facilities.Room',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Habitación'),
        help_text=_('Habitación asignada al residente')
    )
    
    # Información adicional
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notas'),
        help_text=_('Notas adicionales sobre el residente')
    )
    
    # Campos de auditoría
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de Actualización')
    )
    
    class Meta:
        verbose_name = _('Residente')
        verbose_name_plural = _('Residentes')
        ordering = ['last_name', 'first_name']
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['admission_date']),
            models.Index(fields=['room']),
        ]
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Retorna el nombre completo del residente"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calcula la edad del residente"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def length_of_stay(self):
        """Calcula el tiempo de estancia en días"""
        today = date.today()
        return (today - self.admission_date).days
    
    def clean(self):
        """Validación personalizada del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar que la fecha de nacimiento no sea en el futuro
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValidationError({
                'date_of_birth': _('La fecha de nacimiento no puede ser en el futuro.')
            })
        
        # Validar que la fecha de admisión no sea en el futuro
        if self.admission_date and self.admission_date > date.today():
            raise ValidationError({
                'admission_date': _('La fecha de admisión no puede ser en el futuro.')
            })
        
        # Validar que la fecha de nacimiento sea anterior a la fecha de admisión
        if self.date_of_birth and self.admission_date and self.date_of_birth >= self.admission_date:
            raise ValidationError({
                'admission_date': _('La fecha de admisión debe ser posterior a la fecha de nacimiento.')
            })
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para aplicar validaciones"""
        self.clean()
        super().save(*args, **kwargs) 