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
    
    TREATMENT_TYPE_CHOICES = [
        ('physical_therapy', _('Fisioterapia')),
        ('occupational_therapy', _('Terapia Ocupacional')),
        ('speech_therapy', _('Terapia del Habla')),
        ('psychological_therapy', _('Terapia Psicológica')),
        ('medical_treatment', _('Tratamiento Médico')),
        ('rehabilitation', _('Rehabilitación')),
        ('pain_management', _('Manejo del Dolor')),
        ('cardiac_rehabilitation', _('Rehabilitación Cardíaca')),
        ('respiratory_therapy', _('Terapia Respiratoria')),
        ('nutritional_therapy', _('Terapia Nutricional')),
        ('social_work', _('Trabajo Social')),
        ('recreational_therapy', _('Terapia Recreativa')),
        ('cognitive_therapy', _('Terapia Cognitiva')),
        ('other', _('Otro')),
    ]
    
    TREATMENT_STATUS_CHOICES = [
        ('active', _('Activo')),
        ('completed', _('Completado')),
        ('suspended', _('Suspendido')),
        ('discontinued', _('Discontinuado')),
        ('maintenance', _('Mantenimiento')),
        ('evaluation', _('En Evaluación')),
    ]
    
    treatment_type = models.CharField(
        max_length=50,
        choices=TREATMENT_TYPE_CHOICES,
        blank=True,
        verbose_name=_('Tipo de Tratamiento'),
        help_text=_('Tipo específico de tratamiento que está recibiendo')
    )
    
    treatment_status = models.CharField(
        max_length=20,
        choices=TREATMENT_STATUS_CHOICES,
        blank=True,
        verbose_name=_('Estado del Tratamiento'),
        help_text=_('Estado actual del tratamiento')
    )
    
    treatment_start_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de Inicio del Tratamiento'),
        help_text=_('Fecha en que comenzó el tratamiento actual')
    )
    
    treatment_end_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Fecha de Finalización del Tratamiento'),
        help_text=_('Fecha en que finalizó o se espera que finalice el tratamiento')
    )
    
    treatment_frequency = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Frecuencia del Tratamiento'),
        help_text=_('Frecuencia del tratamiento (ej: diario, 3 veces por semana, etc.)')
    )
    
    treatment_provider = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('Proveedor del Tratamiento'),
        help_text=_('Nombre del profesional o institución que proporciona el tratamiento')
    )
    
    treatment_goals = models.TextField(
        blank=True,
        verbose_name=_('Objetivos del Tratamiento'),
        help_text=_('Objetivos específicos del tratamiento actual')
    )
    
    treatment_progress = models.TextField(
        blank=True,
        verbose_name=_('Progreso del Tratamiento'),
        help_text=_('Evaluación del progreso del tratamiento')
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


class ResidentReport(models.Model):
    """
    Modelo para informes periódicos de residentes
    """
    REPORT_TYPES = [
        ('weekly', _('Semanal')),
        ('monthly', _('Mensual')),
        ('quarterly', _('Trimestral')),
        ('custom', _('Personalizado')),
    ]
    
    STATUS_CHOICES = [
        ('draft', _('Borrador')),
        ('completed', _('Completado')),
        ('archived', _('Archivado')),
    ]
    
    # Información básica
    resident = models.ForeignKey(
        Resident,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Residente'),
        help_text=_('Residente al que pertenece este informe')
    )
    
    report_type = models.CharField(
        max_length=20,
        choices=REPORT_TYPES,
        default='monthly',
        verbose_name=_('Tipo de Informe'),
        help_text=_('Tipo de informe periódico')
    )
    
    report_date = models.DateField(
        verbose_name=_('Fecha del Informe'),
        help_text=_('Fecha en que se realiza el informe')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Estado'),
        help_text=_('Estado actual del informe')
    )
    
    # Contenido del informe
    physical_condition = models.TextField(
        blank=True,
        verbose_name=_('Estado Físico'),
        help_text=_('Evaluación del estado físico del residente')
    )
    
    mental_condition = models.TextField(
        blank=True,
        verbose_name=_('Estado Mental'),
        help_text=_('Evaluación del estado mental y emocional')
    )
    
    social_activity = models.TextField(
        blank=True,
        verbose_name=_('Actividad Social'),
        help_text=_('Participación en actividades sociales y recreativas')
    )
    
    medical_treatment = models.TextField(
        blank=True,
        verbose_name=_('Tratamiento Médico'),
        help_text=_('Información sobre tratamientos médicos actuales')
    )
    
    medication_changes = models.TextField(
        blank=True,
        verbose_name=_('Cambios en Medicación'),
        help_text=_('Cambios en la medicación durante el período')
    )
    
    incidents = models.TextField(
        blank=True,
        verbose_name=_('Incidentes'),
        help_text=_('Incidentes o eventos importantes durante el período')
    )
    
    goals_achieved = models.TextField(
        blank=True,
        verbose_name=_('Metas Alcanzadas'),
        help_text=_('Metas alcanzadas durante el período')
    )
    
    next_goals = models.TextField(
        blank=True,
        verbose_name=_('Próximas Metas'),
        help_text=_('Metas para el próximo período')
    )
    
    recommendations = models.TextField(
        blank=True,
        verbose_name=_('Recomendaciones'),
        help_text=_('Recomendaciones para el cuidado del residente')
    )
    
    # Metadatos
    created_by = models.ForeignKey(
        'core.User',
        on_delete=models.CASCADE,
        verbose_name=_('Creado por'),
        help_text=_('Usuario que creó el informe')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de Actualización')
    )
    
    class Meta:
        verbose_name = _('Informe de Residente')
        verbose_name_plural = _('Informes de Residentes')
        ordering = ['-report_date', '-created_at']
        unique_together = ['resident', 'report_date', 'report_type']
    
    def __str__(self):
        return f"Informe de {self.resident.full_name} - {self.get_report_type_display()} - {self.report_date}"
    
    @property
    def is_completed(self):
        """Retorna True si el informe está completado"""
        return self.status == 'completed'
    
    @property
    def is_draft(self):
        """Retorna True si el informe está en borrador"""
        return self.status == 'draft'
    
    def clean(self):
        """Validación personalizada del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar que la fecha del informe no sea en el futuro
        if self.report_date and self.report_date > date.today():
            raise ValidationError({
                'report_date': _('La fecha del informe no puede ser en el futuro.')
            })
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para aplicar validaciones"""
        self.clean()
        super().save(*args, **kwargs) 