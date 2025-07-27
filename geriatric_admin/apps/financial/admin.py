from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import Category, Expense, Income, Investment, Budget, CashFlow


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'color_display', 'is_active', 'created_by', 'created_at']
    list_filter = ['category_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    
    def color_display(self, obj):
        return format_html(
            '<span style="background-color: {}; color: white; padding: 2px 8px; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_display.short_description = _('Color')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'status', 'expense_date', 'supplier', 'created_by']
    list_filter = ['status', 'category', 'payment_method', 'expense_date', 'created_at']
    search_fields = ['title', 'description', 'supplier', 'invoice_number']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    date_hierarchy = 'expense_date'
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('title', 'description', 'amount', 'category')
        }),
        (_('Fechas'), {
            'fields': ('expense_date', 'due_date', 'payment_date')
        }),
        (_('Estado y Pago'), {
            'fields': ('status', 'payment_method')
        }),
        (_('Proveedor'), {
            'fields': ('supplier', 'invoice_number', 'receipt_file')
        }),
        (_('Metadatos'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva instancia
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'category', 'status', 'income_date', 'client', 'created_by']
    list_filter = ['status', 'category', 'payment_method', 'income_date', 'created_at']
    search_fields = ['title', 'description', 'client', 'invoice_number']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    date_hierarchy = 'income_date'
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('title', 'description', 'amount', 'category')
        }),
        (_('Fechas'), {
            'fields': ('income_date', 'due_date', 'payment_date')
        }),
        (_('Estado y Pago'), {
            'fields': ('status', 'payment_method')
        }),
        (_('Cliente'), {
            'fields': ('client', 'invoice_number', 'receipt_file')
        }),
        (_('Metadatos'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva instancia
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'amount', 'investment_type', 'status', 'progress_percentage', 'planned_date', 'created_by']
    list_filter = ['status', 'investment_type', 'planned_date', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    date_hierarchy = 'planned_date'
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('title', 'description', 'amount', 'investment_type', 'category')
        }),
        (_('Fechas'), {
            'fields': ('planned_date', 'start_date', 'completion_date')
        }),
        (_('Estado y Progreso'), {
            'fields': ('status', 'progress_percentage')
        }),
        (_('Beneficios'), {
            'fields': ('expected_roi', 'expected_benefits')
        }),
        (_('Metadatos'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva instancia
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'period_type', 'total_budget', 'utilization_percentage', 'start_date', 'end_date', 'created_by']
    list_filter = ['period_type', 'start_date', 'end_date', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'utilization_percentage']
    date_hierarchy = 'start_date'
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('name', 'description', 'period_type')
        }),
        (_('Período'), {
            'fields': ('start_date', 'end_date')
        }),
        (_('Presupuesto'), {
            'fields': ('total_budget', 'allocated_budget', 'spent_budget')
        }),
        (_('Metadatos'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva instancia
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(CashFlow)
class CashFlowAdmin(admin.ModelAdmin):
    list_display = ['date', 'opening_balance', 'total_inflow', 'total_outflow', 'closing_balance', 'created_by']
    list_filter = ['date', 'created_at']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    date_hierarchy = 'date'
    
    fieldsets = (
        (_('Información Básica'), {
            'fields': ('date', 'opening_balance')
        }),
        (_('Flujos'), {
            'fields': ('total_inflow', 'total_outflow', 'closing_balance')
        }),
        (_('Transacciones'), {
            'fields': ('expenses', 'incomes')
        }),
        (_('Metadatos'), {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Si es una nueva instancia
            obj.created_by = request.user
        super().save_model(request, obj, form, change) 