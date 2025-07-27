from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from datetime import date


class Staff(models.Model):
    """
    Modelo para gestionar el personal de la residencia
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
    ]
    
    EMPLOYMENT_STATUS_CHOICES = [
        ('active', _('Activo')),
        ('inactive', _('Inactivo')),
        ('suspended', _('Suspendido')),
        ('terminated', _('Terminado')),
    ]
    
    # Información Personal
    first_name = models.CharField(
        max_length=50,
        verbose_name=_('Nombre'),
        help_text=_('Nombre del empleado')
    )
    
    last_name = models.CharField(
        max_length=50,
        verbose_name=_('Apellido'),
        help_text=_('Apellido del empleado')
    )
    
    date_of_birth = models.DateField(
        verbose_name=_('Fecha de Nacimiento'),
        help_text=_('Fecha de nacimiento del empleado')
    )
    
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        verbose_name=_('Género'),
        help_text=_('Género del empleado')
    )
    
    marital_status = models.CharField(
        max_length=20,
        choices=MARITAL_STATUS_CHOICES,
        verbose_name=_('Estado Civil'),
        help_text=_('Estado civil del empleado')
    )
    
    # Información de Contacto
    phone = models.CharField(
        max_length=20,
        verbose_name=_('Teléfono'),
        help_text=_('Número de teléfono del empleado')
    )
    
    email = models.EmailField(
        verbose_name=_('Correo Electrónico'),
        help_text=_('Correo electrónico del empleado')
    )
    
    address = models.TextField(
        verbose_name=_('Dirección'),
        help_text=_('Dirección completa del empleado')
    )
    
    city = models.CharField(
        max_length=100,
        verbose_name=_('Ciudad'),
        help_text=_('Ciudad donde reside el empleado')
    )
    
    # Información Laboral
    employee_id = models.CharField(
        max_length=20,
        unique=True,
        verbose_name=_('ID de Empleado'),
        help_text=_('Identificador único del empleado')
    )
    
    position = models.CharField(
        max_length=100,
        verbose_name=_('Cargo'),
        help_text=_('Cargo o posición del empleado')
    )
    
    department = models.CharField(
        max_length=100,
        verbose_name=_('Departamento'),
        help_text=_('Departamento donde trabaja el empleado')
    )
    
    hire_date = models.DateField(
        verbose_name=_('Fecha de Contratación'),
        help_text=_('Fecha en que fue contratado el empleado')
    )
    
    employment_status = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_STATUS_CHOICES,
        default='active',
        verbose_name=_('Estado de Empleo'),
        help_text=_('Estado actual del empleado')
    )
    
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Salario'),
        help_text=_('Salario mensual del empleado')
    )
    
    # Información de Horarios
    work_schedule = models.CharField(
        max_length=100,
        verbose_name=_('Horario de Trabajo'),
        help_text=_('Horario de trabajo del empleado (ej: L-V 8:00-16:00)')
    )
    
    shift_type = models.CharField(
        max_length=50,
        verbose_name=_('Tipo de Turno'),
        help_text=_('Tipo de turno (mañana, tarde, noche, rotativo)')
    )
    
    # Información de Emergencia
    emergency_contact_name = models.CharField(
        max_length=100,
        verbose_name=_('Contacto de Emergencia'),
        help_text=_('Nombre del contacto de emergencia')
    )
    
    emergency_contact_relationship = models.CharField(
        max_length=50,
        verbose_name=_('Relación'),
        help_text=_('Relación con el contacto de emergencia')
    )
    
    emergency_contact_phone = models.CharField(
        max_length=20,
        verbose_name=_('Teléfono de Emergencia'),
        help_text=_('Teléfono del contacto de emergencia')
    )
    
    # Información Médica
    blood_type = models.CharField(
        max_length=5,
        blank=True,
        verbose_name=_('Tipo de Sangre'),
        help_text=_('Tipo de sangre del empleado')
    )
    
    allergies = models.TextField(
        blank=True,
        verbose_name=_('Alergias'),
        help_text=_('Alergias conocidas del empleado')
    )
    
    medical_conditions = models.TextField(
        blank=True,
        verbose_name=_('Condiciones Médicas'),
        help_text=_('Condiciones médicas relevantes')
    )
    
    # Información Adicional
    skills = models.TextField(
        blank=True,
        verbose_name=_('Habilidades'),
        help_text=_('Habilidades y certificaciones del empleado')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notas'),
        help_text=_('Notas adicionales sobre el empleado')
    )
    
    # Información del Sistema
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Fecha de Creación')
    )
    
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Fecha de Actualización')
    )
    
    class Meta:
        verbose_name = _('Empleado')
        verbose_name_plural = _('Empleados')
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.full_name} - {self.position}"
    
    @property
    def full_name(self):
        """Retorna el nombre completo del empleado"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calcula la edad del empleado"""
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def years_of_service(self):
        """Calcula los años de servicio"""
        today = date.today()
        return today.year - self.hire_date.year - (
            (today.month, today.day) < (self.hire_date.month, self.hire_date.day)
        )
    
    @property
    def is_active(self):
        """Retorna True si el empleado está activo"""
        return self.employment_status == 'active'
    
    def clean(self):
        """Validación personalizada del modelo"""
        from django.core.exceptions import ValidationError
        
        # Validar edad mínima (18 años)
        if self.age < 18:
            raise ValidationError({
                'date_of_birth': _('El empleado debe tener al menos 18 años.')
            })
        
        # Validar que la fecha de contratación no sea futura
        if self.hire_date > date.today():
            raise ValidationError({
                'hire_date': _('La fecha de contratación no puede ser futura.')
            })
        
        # Validar que la fecha de nacimiento no sea futura
        if self.date_of_birth > date.today():
            raise ValidationError({
                'date_of_birth': _('La fecha de nacimiento no puede ser futura.')
            })
        
        # Validar salario positivo
        if self.salary <= 0:
            raise ValidationError({
                'salary': _('El salario debe ser mayor a cero.')
            })
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para aplicar validaciones"""
        self.clean()
        super().save(*args, **kwargs) 