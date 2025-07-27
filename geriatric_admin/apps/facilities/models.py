from django.db import models
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _


class Room(models.Model):
    """
    Modelo para gestionar habitaciones del geriátrico
    """
    ROOM_STATUS_CHOICES = [
        ('available', _('Disponible')),
        ('maintenance', _('En Mantenimiento')),
        ('quarantine', _('En Cuarentena')),
    ]
    
    room_number = models.CharField(
        max_length=10,
        unique=True,
        verbose_name=_('Número de Habitación'),
        help_text=_('Número único de la habitación')
    )
    
    floor = models.PositiveIntegerField(
        verbose_name=_('Piso'),
        help_text=_('Piso donde se encuentra la habitación')
    )
    
    total_beds = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Total de Camas'),
        help_text=_('Número total de camas en la habitación')
    )
    
    occupied_beds = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Camas Ocupadas'),
        help_text=_('Número de camas actualmente ocupadas')
    )
    
    status = models.CharField(
        max_length=20,
        choices=ROOM_STATUS_CHOICES,
        default='available',
        verbose_name=_('Estado'),
        help_text=_('Estado actual de la habitación')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('Descripción'),
        help_text=_('Descripción adicional de la habitación')
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
        verbose_name = _('Habitación')
        verbose_name_plural = _('Habitaciones')
        ordering = ['floor', 'room_number']
    
    def __str__(self):
        return f"Habitación {self.room_number} - Piso {self.floor}"
    
    @property
    def available_beds(self):
        """Retorna el número de camas disponibles"""
        return self.total_beds - self.occupied_beds
    
    @property
    def occupancy_rate(self):
        """Retorna el porcentaje de ocupación de la habitación"""
        if self.total_beds == 0:
            return 0
        return round((self.occupied_beds / self.total_beds) * 100, 1)
    
    @property
    def is_full(self):
        """Retorna True si la habitación está completamente ocupada"""
        return self.occupied_beds >= self.total_beds
    
    @property
    def is_available(self):
        """Retorna True si hay camas disponibles"""
        return self.available_beds > 0 and self.status == 'available'
    
    @property
    def residents(self):
        """Retorna los residentes asignados a esta habitación"""
        from apps.residents.models import Resident
        return Resident.objects.filter(room=self)
    
    @property
    def residents_count(self):
        """Retorna el número de residentes asignados"""
        return self.residents.count()
    
    def clean(self):
        """Validación personalizada del modelo"""
        from django.core.exceptions import ValidationError
        
        if self.occupied_beds > self.total_beds:
            raise ValidationError({
                'occupied_beds': _('El número de camas ocupadas no puede ser mayor al total de camas.')
            })
    
    def save(self, *args, **kwargs):
        """Sobrescribir save para aplicar validaciones"""
        self.clean()
        super().save(*args, **kwargs) 