from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import Category, Expense, Income, Investment, Budget, CashFlow


class CategoryForm(forms.ModelForm):
    """Formulario para categorías"""
    
    class Meta:
        model = Category
        fields = ['name', 'description', 'category_type', 'color', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nombre de la categoría')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Descripción de la categoría')
            }),
            'category_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'color': forms.TextInput(attrs={
                'class': 'form-control',
                'type': 'color'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }


class ExpenseForm(forms.ModelForm):
    """Formulario para gastos"""
    
    class Meta:
        model = Expense
        fields = [
            'title', 'description', 'amount', 'category', 'expense_date',
            'due_date', 'payment_date', 'payment_method', 'status',
            'supplier', 'invoice_number', 'receipt_file'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Título del gasto')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Descripción del gasto')
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'expense_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'supplier': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nombre del proveedor')
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Número de factura')
            }),
            'receipt_file': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar categorías solo de gastos
        self.fields['category'].queryset = Category.objects.filter(
            category_type='expense',
            is_active=True
        )


class IncomeForm(forms.ModelForm):
    """Formulario para ingresos"""
    
    class Meta:
        model = Income
        fields = [
            'title', 'description', 'amount', 'category', 'income_date',
            'due_date', 'payment_date', 'payment_method', 'status',
            'client', 'invoice_number', 'receipt_file'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Título del ingreso')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Descripción del ingreso')
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'income_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'payment_method': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'client': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nombre del cliente')
            }),
            'invoice_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Número de factura')
            }),
            'receipt_file': forms.FileInput(attrs={
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar categorías solo de ingresos
        self.fields['category'].queryset = Category.objects.filter(
            category_type='income',
            is_active=True
        )


class InvestmentForm(forms.ModelForm):
    """Formulario para inversiones"""
    
    class Meta:
        model = Investment
        fields = [
            'title', 'description', 'amount', 'investment_type', 'category',
            'planned_date', 'start_date', 'completion_date', 'status',
            'progress_percentage', 'expected_roi', 'expected_benefits'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Título de la inversión')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Descripción de la inversión')
            }),
            'amount': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            }),
            'investment_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'planned_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'completion_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
            'progress_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100'
            }),
            'expected_roi': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0'
            }),
            'expected_benefits': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Beneficios esperados de la inversión')
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar categorías solo de inversiones
        self.fields['category'].queryset = Category.objects.filter(
            category_type='investment',
            is_active=True
        )


class BudgetForm(forms.ModelForm):
    """Formulario para presupuestos"""
    
    class Meta:
        model = Budget
        fields = [
            'name', 'description', 'period_type', 'start_date',
            'end_date', 'total_budget'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Nombre del presupuesto')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Descripción del presupuesto')
            }),
            'period_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'total_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0.01'
            })
        }
    
    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date >= end_date:
            raise forms.ValidationError(
                _('La fecha de inicio debe ser anterior a la fecha de fin.')
            )
        
        return cleaned_data


class CashFlowForm(forms.ModelForm):
    """Formulario para flujo de caja"""
    
    class Meta:
        model = CashFlow
        fields = ['date', 'opening_balance']
        widgets = {
            'date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'opening_balance': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01'
            })
        }


class FinancialReportForm(forms.Form):
    """Formulario para reportes financieros"""
    
    REPORT_TYPES = [
        ('cash_flow', _('Flujo de Caja')),
        ('income_statement', _('Estado de Resultados')),
        ('budget_vs_actual', _('Presupuesto vs Real')),
        ('expense_analysis', _('Análisis de Gastos')),
        ('income_analysis', _('Análisis de Ingresos')),
        ('investment_summary', _('Resumen de Inversiones')),
    ]
    
    PERIOD_CHOICES = [
        ('today', _('Hoy')),
        ('week', _('Esta Semana')),
        ('month', _('Este Mes')),
        ('quarter', _('Este Trimestre')),
        ('year', _('Este Año')),
        ('custom', _('Período Personalizado')),
    ]
    
    FORMAT_CHOICES = [
        ('pdf', 'PDF'),
        ('excel', 'Excel'),
        ('csv', 'CSV'),
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
    
    format = forms.ChoiceField(
        choices=FORMAT_CHOICES,
        label=_('Formato'),
        initial='pdf',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    include_charts = forms.BooleanField(
        label=_('Incluir Gráficos'),
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def clean(self):
        cleaned_data = super().clean()
        period = cleaned_data.get('period')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if period == 'custom':
            if not date_from or not date_to:
                raise forms.ValidationError(
                    _('Para períodos personalizados debe especificar fecha desde y hasta.')
                )
            if date_from >= date_to:
                raise forms.ValidationError(
                    _('La fecha desde debe ser anterior a la fecha hasta.')
                )
        
        return cleaned_data 