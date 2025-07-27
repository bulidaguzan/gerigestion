from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid


class Category(models.Model):
    """Categorías para gastos e ingresos"""
    
    CATEGORY_TYPES = [
        ('expense', _('Gasto')),
        ('income', _('Ingreso')),
        ('investment', _('Inversión')),
    ]
    
    name = models.CharField(_('Nombre'), max_length=100)
    description = models.TextField(_('Descripción'), blank=True)
    category_type = models.CharField(_('Tipo'), max_length=20, choices=CATEGORY_TYPES)
    color = models.CharField(_('Color'), max_length=7, default='#3498db', help_text=_('Color en formato hexadecimal'))
    is_active = models.BooleanField(_('Activo'), default=True)
    
    # Metadatos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Creado por'))
    created_at = models.DateTimeField(_('Creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado el'), auto_now=True)
    
    class Meta:
        verbose_name = _('Categoría')
        verbose_name_plural = _('Categorías')
        ordering = ['category_type', 'name']
        unique_together = ['name', 'category_type']
    
    def __str__(self):
        return f"{self.get_category_type_display()}: {self.name}"


class Expense(models.Model):
    """Modelo para gastos del geriátrico"""
    
    PAYMENT_METHODS = [
        ('cash', _('Efectivo')),
        ('card', _('Tarjeta')),
        ('transfer', _('Transferencia')),
        ('check', _('Cheque')),
        ('other', _('Otro')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pendiente')),
        ('paid', _('Pagado')),
        ('cancelled', _('Cancelado')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('Título'), max_length=200)
    description = models.TextField(_('Descripción'), blank=True)
    amount = models.DecimalField(_('Monto'), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name=_('Categoría'), limit_choices_to={'category_type': 'expense'})
    
    # Fechas
    expense_date = models.DateField(_('Fecha del Gasto'), default=timezone.now)
    due_date = models.DateField(_('Fecha de Vencimiento'), null=True, blank=True)
    payment_date = models.DateField(_('Fecha de Pago'), null=True, blank=True)
    
    # Información de pago
    payment_method = models.CharField(_('Método de Pago'), max_length=20, choices=PAYMENT_METHODS, default='cash')
    status = models.CharField(_('Estado'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Proveedor/Recibo
    supplier = models.CharField(_('Proveedor'), max_length=200, blank=True)
    invoice_number = models.CharField(_('Número de Factura'), max_length=100, blank=True)
    receipt_file = models.FileField(_('Comprobante'), upload_to='financial/receipts/', blank=True)
    
    # Metadatos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Creado por'))
    created_at = models.DateTimeField(_('Creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado el'), auto_now=True)
    
    class Meta:
        verbose_name = _('Gasto')
        verbose_name_plural = _('Gastos')
        ordering = ['-expense_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - €{self.amount}"
    
    @property
    def is_overdue(self):
        """Verifica si el gasto está vencido"""
        if self.due_date and self.status == 'pending':
            return self.due_date < timezone.now().date()
        return False
    
    @property
    def days_overdue(self):
        """Retorna los días de atraso"""
        if self.is_overdue:
            return (timezone.now().date() - self.due_date).days
        return 0


class Income(models.Model):
    """Modelo para ingresos del geriátrico"""
    
    PAYMENT_METHODS = [
        ('cash', _('Efectivo')),
        ('card', _('Tarjeta')),
        ('transfer', _('Transferencia')),
        ('check', _('Cheque')),
        ('other', _('Otro')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pendiente')),
        ('received', _('Recibido')),
        ('cancelled', _('Cancelado')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('Título'), max_length=200)
    description = models.TextField(_('Descripción'), blank=True)
    amount = models.DecimalField(_('Monto'), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name=_('Categoría'), limit_choices_to={'category_type': 'income'})
    
    # Fechas
    income_date = models.DateField(_('Fecha del Ingreso'), default=timezone.now)
    due_date = models.DateField(_('Fecha de Vencimiento'), null=True, blank=True)
    payment_date = models.DateField(_('Fecha de Pago'), null=True, blank=True)
    
    # Información de pago
    payment_method = models.CharField(_('Método de Pago'), max_length=20, choices=PAYMENT_METHODS, default='transfer')
    status = models.CharField(_('Estado'), max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Cliente/Recibo
    client = models.CharField(_('Cliente'), max_length=200, blank=True)
    invoice_number = models.CharField(_('Número de Factura'), max_length=100, blank=True)
    receipt_file = models.FileField(_('Comprobante'), upload_to='financial/receipts/', blank=True)
    
    # Metadatos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Creado por'))
    created_at = models.DateTimeField(_('Creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado el'), auto_now=True)
    
    class Meta:
        verbose_name = _('Ingreso')
        verbose_name_plural = _('Ingresos')
        ordering = ['-income_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - €{self.amount}"
    
    @property
    def is_overdue(self):
        """Verifica si el ingreso está vencido"""
        if self.due_date and self.status == 'pending':
            return self.due_date < timezone.now().date()
        return False


class Investment(models.Model):
    """Modelo para inversiones del geriátrico"""
    
    INVESTMENT_TYPES = [
        ('equipment', _('Equipamiento')),
        ('infrastructure', _('Infraestructura')),
        ('technology', _('Tecnología')),
        ('marketing', _('Marketing')),
        ('training', _('Capacitación')),
        ('other', _('Otro')),
    ]
    
    STATUS_CHOICES = [
        ('planned', _('Planificado')),
        ('in_progress', _('En Progreso')),
        ('completed', _('Completado')),
        ('cancelled', _('Cancelado')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(_('Título'), max_length=200)
    description = models.TextField(_('Descripción'), blank=True)
    amount = models.DecimalField(_('Monto'), max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    investment_type = models.CharField(_('Tipo de Inversión'), max_length=20, choices=INVESTMENT_TYPES)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, verbose_name=_('Categoría'), limit_choices_to={'category_type': 'investment'})
    
    # Fechas
    planned_date = models.DateField(_('Fecha Planificada'), default=timezone.now)
    start_date = models.DateField(_('Fecha de Inicio'), null=True, blank=True)
    completion_date = models.DateField(_('Fecha de Finalización'), null=True, blank=True)
    
    # Estado y progreso
    status = models.CharField(_('Estado'), max_length=20, choices=STATUS_CHOICES, default='planned')
    progress_percentage = models.IntegerField(_('Porcentaje de Progreso'), default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    
    # Beneficios esperados
    expected_roi = models.DecimalField(_('ROI Esperado (%)'), max_digits=5, decimal_places=2, null=True, blank=True)
    expected_benefits = models.TextField(_('Beneficios Esperados'), blank=True)
    
    # Metadatos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Creado por'))
    created_at = models.DateTimeField(_('Creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado el'), auto_now=True)
    
    class Meta:
        verbose_name = _('Inversión')
        verbose_name_plural = _('Inversiones')
        ordering = ['-planned_date', '-created_at']
    
    def __str__(self):
        return f"{self.title} - €{self.amount}"


class CashFlow(models.Model):
    """Modelo para el flujo de caja"""
    
    FLOW_TYPES = [
        ('inflow', _('Entrada')),
        ('outflow', _('Salida')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    date = models.DateField(_('Fecha'), default=timezone.now)
    flow_type = models.CharField(_('Tipo de Flujo'), max_length=10, choices=FLOW_TYPES)
    
    # Montos
    opening_balance = models.DecimalField(_('Saldo Inicial'), max_digits=12, decimal_places=2, default=0)
    total_inflow = models.DecimalField(_('Total Entradas'), max_digits=12, decimal_places=2, default=0)
    total_outflow = models.DecimalField(_('Total Salidas'), max_digits=12, decimal_places=2, default=0)
    closing_balance = models.DecimalField(_('Saldo Final'), max_digits=12, decimal_places=2, default=0)
    
    # Referencias a transacciones
    expenses = models.ManyToManyField(Expense, blank=True, verbose_name=_('Gastos'))
    incomes = models.ManyToManyField(Income, blank=True, verbose_name=_('Ingresos'))
    
    # Metadatos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Creado por'))
    created_at = models.DateTimeField(_('Creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado el'), auto_now=True)
    
    class Meta:
        verbose_name = _('Flujo de Caja')
        verbose_name_plural = _('Flujos de Caja')
        ordering = ['-date']
        unique_together = ['date']
    
    def __str__(self):
        return f"Flujo de Caja - {self.date} - Saldo: €{self.closing_balance}"
    
    def calculate_balances(self):
        """Calcula los saldos basándose en las transacciones"""
        self.total_inflow = sum(income.amount for income in self.incomes.all())
        self.total_outflow = sum(expense.amount for expense in self.expenses.all())
        self.closing_balance = self.opening_balance + self.total_inflow - self.total_outflow
        self.save()


class Budget(models.Model):
    """Modelo para presupuestos"""
    
    PERIOD_TYPES = [
        ('monthly', _('Mensual')),
        ('quarterly', _('Trimestral')),
        ('yearly', _('Anual')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nombre'), max_length=200)
    description = models.TextField(_('Descripción'), blank=True)
    period_type = models.CharField(_('Tipo de Período'), max_length=20, choices=PERIOD_TYPES)
    
    # Fechas
    start_date = models.DateField(_('Fecha de Inicio'))
    end_date = models.DateField(_('Fecha de Fin'))
    
    # Montos presupuestados
    total_budget = models.DecimalField(_('Presupuesto Total'), max_digits=12, decimal_places=2)
    allocated_budget = models.DecimalField(_('Presupuesto Asignado'), max_digits=12, decimal_places=2, default=0)
    spent_budget = models.DecimalField(_('Presupuesto Gastado'), max_digits=12, decimal_places=2, default=0)
    
    # Metadatos
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_('Creado por'))
    created_at = models.DateTimeField(_('Creado el'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Actualizado el'), auto_now=True)
    
    class Meta:
        verbose_name = _('Presupuesto')
        verbose_name_plural = _('Presupuestos')
        ordering = ['-start_date']
    
    def __str__(self):
        return f"{self.name} - €{self.total_budget}"
    
    @property
    def remaining_budget(self):
        """Retorna el presupuesto restante"""
        return self.total_budget - self.spent_budget
    
    @property
    def utilization_percentage(self):
        """Retorna el porcentaje de utilización del presupuesto"""
        if self.total_budget > 0:
            return (self.spent_budget / self.total_budget) * 100
        return 0 