from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.utils import timezone
from .models import Expense, Income, CashFlow


@receiver(post_save, sender=Expense)
def update_cash_flow_on_expense_save(sender, instance, created, **kwargs):
    """Actualizar flujo de caja cuando se crea o actualiza un gasto"""
    try:
        # Buscar o crear flujo de caja para la fecha del gasto
        cash_flow, created_cf = CashFlow.objects.get_or_create(
            date=instance.expense_date,
            defaults={
                'opening_balance': 0,
                'total_inflow': 0,
                'total_outflow': 0,
                'closing_balance': 0,
                'created_by': instance.created_by
            }
        )
        
        # Recalcular saldos
        cash_flow.calculate_balances()
        
    except Exception as e:
        # Log error si es necesario
        pass


@receiver(post_save, sender=Income)
def update_cash_flow_on_income_save(sender, instance, created, **kwargs):
    """Actualizar flujo de caja cuando se crea o actualiza un ingreso"""
    try:
        # Buscar o crear flujo de caja para la fecha del ingreso
        cash_flow, created_cf = CashFlow.objects.get_or_create(
            date=instance.income_date,
            defaults={
                'opening_balance': 0,
                'total_inflow': 0,
                'total_outflow': 0,
                'closing_balance': 0,
                'created_by': instance.created_by
            }
        )
        
        # Recalcular saldos
        cash_flow.calculate_balances()
        
    except Exception as e:
        # Log error si es necesario
        pass


@receiver(post_delete, sender=Expense)
def update_cash_flow_on_expense_delete(sender, instance, **kwargs):
    """Actualizar flujo de caja cuando se elimina un gasto"""
    try:
        # Buscar flujo de caja para la fecha del gasto
        cash_flow = CashFlow.objects.filter(date=instance.expense_date).first()
        if cash_flow:
            cash_flow.calculate_balances()
            
    except Exception as e:
        # Log error si es necesario
        pass


@receiver(post_delete, sender=Income)
def update_cash_flow_on_income_delete(sender, instance, **kwargs):
    """Actualizar flujo de caja cuando se elimina un ingreso"""
    try:
        # Buscar flujo de caja para la fecha del ingreso
        cash_flow = CashFlow.objects.filter(date=instance.income_date).first()
        if cash_flow:
            cash_flow.calculate_balances()
            
    except Exception as e:
        # Log error si es necesario
        pass 