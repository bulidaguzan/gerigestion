from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.utils.translation import gettext as _
from datetime import datetime, timedelta
import json

from .models import Category, Expense, Income, Investment, Budget, CashFlow
from .forms import (
    CategoryForm, ExpenseForm, IncomeForm, InvestmentForm,
    BudgetForm, CashFlowForm, FinancialReportForm
)


@login_required
def financial_dashboard(request):
    """Dashboard principal de gestión financiera"""
    
    # Estadísticas generales
    today = timezone.now().date()
    current_month = today.replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    # Gastos del mes actual
    monthly_expenses = Expense.objects.filter(
        expense_date__gte=current_month,
        expense_date__lt=next_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Ingresos del mes actual
    monthly_income = Income.objects.filter(
        income_date__gte=current_month,
        income_date__lt=next_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Balance del mes
    monthly_balance = monthly_income - monthly_expenses
    
    # Gastos del año actual
    yearly_expenses = Expense.objects.filter(
        expense_date__year=today.year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Ingresos del año actual
    yearly_income = Income.objects.filter(
        income_date__year=today.year
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Balance del año
    yearly_balance = yearly_income - yearly_expenses
    
    # Nombre del mes actual
    month_names = {
        1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio',
        7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
    }
    current_month_name = month_names[today.month]
    
    # Gastos pendientes
    pending_expenses = Expense.objects.filter(status='pending').count()
    overdue_expenses = Expense.objects.filter(
        status='pending',
        due_date__lt=today
    ).count()
    
    # Ingresos pendientes
    pending_income = Income.objects.filter(status='pending').count()
    overdue_income = Income.objects.filter(
        status='pending',
        due_date__lt=today
    ).count()
    
    # Inversiones activas
    active_investments = Investment.objects.filter(status='in_progress').count()
    total_investment_amount = Investment.objects.filter(
        status__in=['planned', 'in_progress']
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Gastos recientes
    recent_expenses = Expense.objects.order_by('-expense_date')[:5]
    
    # Ingresos recientes
    recent_income = Income.objects.order_by('-income_date')[:5]
    
    # Gastos por categoría (último mes)
    expenses_by_category = Expense.objects.filter(
        expense_date__gte=current_month,
        expense_date__lt=next_month
    ).values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Ingresos por categoría (último mes)
    income_by_category = Income.objects.filter(
        income_date__gte=current_month,
        income_date__lt=next_month
    ).values('category__name').annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Cálculos adicionales para el template
    net_balance = monthly_income - monthly_expenses
    
    # Total de ingresos y gastos (histórico)
    total_income = Income.objects.aggregate(total=Sum('amount'))['total'] or 0
    total_expenses = Expense.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    # Total de inversiones
    total_investments = Investment.objects.aggregate(total=Sum('amount'))['total'] or 0
    
    # Cálculo del margen de beneficio
    profit_margin = 0
    if total_income > 0:
        profit_margin = round(((total_income - total_expenses) / total_income) * 100, 1)
    
    # Montos pendientes
    pending_amount = (Expense.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0) + \
                    (Income.objects.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0)
    
    # Transacciones recientes combinadas
    recent_transactions = []
    
    # Agregar ingresos recientes
    for income in recent_income:
        recent_transactions.append({
            'id': income.id,
            'description': income.description,
            'type': 'income',
            'amount': income.amount,
            'date': income.income_date,
            'category': income.category
        })
    
    # Agregar gastos recientes
    for expense in recent_expenses:
        recent_transactions.append({
            'id': expense.id,
            'description': expense.description,
            'type': 'expense',
            'amount': expense.amount,
            'date': expense.expense_date,
            'category': expense.category
        })
    
    # Ordenar por fecha (más recientes primero)
    recent_transactions.sort(key=lambda x: x['date'], reverse=True)
    recent_transactions = recent_transactions[:10]  # Limitar a 10 transacciones
    
    # Acciones rápidas para el dashboard
    quick_actions = [
        {
            'url': '/financial/income/create/',
            'icon': 'add',
            'text': 'Nuevo Ingreso',
            'bg_color': 'bg-emerald-600',
            'hover_color': 'hover:bg-emerald-700'
        },
        {
            'url': '/financial/expenses/create/',
            'icon': 'remove',
            'text': 'Nuevo Gasto',
            'bg_color': 'bg-red-600',
            'hover_color': 'hover:bg-red-700'
        },
        {
            'url': '/financial/reports/',
            'icon': 'assessment',
            'text': 'Reportes',
            'bg_color': 'bg-indigo-600',
            'hover_color': 'hover:bg-indigo-700'
        },
        {
            'url': '/financial/categories/',
            'icon': 'category',
            'text': 'Categorías',
            'bg_color': 'bg-amber-600',
            'hover_color': 'hover:bg-amber-700'
        }
    ]
    
    context = {
        'monthly_expenses': monthly_expenses,
        'monthly_income': monthly_income,
        'monthly_balance': monthly_balance,
        'yearly_expenses': yearly_expenses,
        'yearly_income': yearly_income,
        'yearly_balance': yearly_balance,
        'current_month_name': current_month_name,
        'net_balance': net_balance,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'total_investments': total_investments,
        'profit_margin': profit_margin,
        'pending_amount': pending_amount,
        'recent_transactions': recent_transactions,
        'pending_expenses': pending_expenses,
        'overdue_expenses': overdue_expenses,
        'pending_income': pending_income,
        'overdue_income': overdue_income,
        'active_investments': active_investments,
        'total_investment_amount': total_investment_amount,
        'recent_expenses': recent_expenses,
        'recent_income': recent_income,
        'expenses_by_category': expenses_by_category,
        'income_by_category': income_by_category,
        'quick_actions': quick_actions,
    }
    
    return render(request, 'financial/dashboard.html', context)


# Gestión de Categorías
@login_required
def category_list(request):
    """Lista de categorías"""
    categories = Category.objects.all()
    
    # Filtros
    category_type = request.GET.get('type', '')
    if category_type:
        categories = categories.filter(category_type=category_type)
    
    # Estadísticas por tipo
    expense_categories = Category.objects.filter(category_type='expense')
    income_categories = Category.objects.filter(category_type='income')
    investment_categories = Category.objects.filter(category_type='investment')
    
    # Contadores
    expense_categories_count = expense_categories.count()
    income_categories_count = income_categories.count()
    investment_categories_count = investment_categories.count()
    total_categories_count = categories.count()
    
    context = {
        'categories': categories,
        'expense_categories': expense_categories,
        'income_categories': income_categories,
        'investment_categories': investment_categories,
        'expense_categories_count': expense_categories_count,
        'income_categories_count': income_categories_count,
        'investment_categories_count': investment_categories_count,
        'total_categories_count': total_categories_count,
        'category_types': Category.CATEGORY_TYPES
    }
    
    return render(request, 'financial/categories/list.html', context)


@login_required
def category_create(request):
    """Crear nueva categoría"""
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            category = form.save(commit=False)
            category.created_by = request.user
            category.save()
            
            messages.success(request, _('Categoría creada exitosamente.'))
            return redirect('financial_web:category_list')
    else:
        form = CategoryForm()
    
    context = {
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'financial/categories/form.html', context)


@login_required
def category_update(request, category_id):
    """Actualizar categoría"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        form = CategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, _('Categoría actualizada exitosamente.'))
            return redirect('financial_web:category_list')
    else:
        form = CategoryForm(instance=category)
    
    context = {
        'form': form,
        'category': category,
        'action': 'update'
    }
    
    return render(request, 'financial/categories/form.html', context)


@login_required
def category_delete(request, category_id):
    """Eliminar categoría"""
    category = get_object_or_404(Category, id=category_id)
    
    if request.method == 'POST':
        category.delete()
        messages.success(request, _('Categoría eliminada exitosamente.'))
        return redirect('financial_web:category_list')
    
    context = {
        'category': category
    }
    
    return render(request, 'financial/categories/delete.html', context)


# Gestión de Gastos
@login_required
def expense_list(request):
    """Lista de gastos"""
    expenses = Expense.objects.all()
    
    # Filtros
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    if status:
        expenses = expenses.filter(status=status)
    
    if category:
        expenses = expenses.filter(category_id=category)
    
    if date_from:
        expenses = expenses.filter(expense_date__gte=date_from)
    
    if date_to:
        expenses = expenses.filter(expense_date__lte=date_to)
    
    if search:
        expenses = expenses.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(supplier__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(expenses, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_amount = expenses.aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = expenses.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    paid_count = expenses.filter(status='paid').count()
    pending_count = expenses.filter(status='pending').count()
    overdue_count = expenses.filter(
        status='pending',
        due_date__lt=timezone.now().date()
    ).count()
    
    context = {
        'page_obj': page_obj,
        'total_amount': total_amount,
        'pending_amount': pending_amount,
        'paid_count': paid_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'categories': Category.objects.filter(category_type='expense', is_active=True),
        'status_choices': Expense.STATUS_CHOICES
    }
    
    return render(request, 'financial/expenses/list.html', context)


@login_required
def expense_create(request):
    """Crear nuevo gasto"""
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES)
        if form.is_valid():
            expense = form.save(commit=False)
            expense.created_by = request.user
            expense.save()
            
            messages.success(request, _('Gasto creado exitosamente.'))
            return redirect('financial:expense_list')
    else:
        form = ExpenseForm()
    
    context = {
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'financial/expenses/form.html', context)


@login_required
def expense_update(request, expense_id):
    """Actualizar gasto"""
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        form = ExpenseForm(request.POST, request.FILES, instance=expense)
        if form.is_valid():
            form.save()
            messages.success(request, _('Gasto actualizado exitosamente.'))
            return redirect('financial:expense_list')
    else:
        form = ExpenseForm(instance=expense)
    
    context = {
        'form': form,
        'expense': expense,
        'action': 'update'
    }
    
    return render(request, 'financial/expenses/form.html', context)


@login_required
def expense_delete(request, expense_id):
    """Eliminar gasto"""
    expense = get_object_or_404(Expense, id=expense_id)
    
    if request.method == 'POST':
        expense.delete()
        messages.success(request, _('Gasto eliminado exitosamente.'))
        return redirect('financial_web:expense_list')
    
    context = {
        'expense': expense
    }
    
    return render(request, 'financial/expenses/delete.html', context)


@login_required
def expense_detail(request, expense_id):
    """Detalle del gasto"""
    expense = get_object_or_404(Expense, id=expense_id)
    
    context = {
        'expense': expense
    }
    
    return render(request, 'financial/expenses/detail.html', context)


# Gestión de Ingresos
@login_required
def income_list(request):
    """Lista de ingresos"""
    incomes = Income.objects.all()
    
    # Filtros
    status = request.GET.get('status', '')
    category = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    search = request.GET.get('search', '')
    
    if status:
        incomes = incomes.filter(status=status)
    
    if category:
        incomes = incomes.filter(category_id=category)
    
    if date_from:
        incomes = incomes.filter(income_date__gte=date_from)
    
    if date_to:
        incomes = incomes.filter(income_date__lte=date_to)
    
    if search:
        incomes = incomes.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(client__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(incomes, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_amount = incomes.aggregate(total=Sum('amount'))['total'] or 0
    pending_amount = incomes.filter(status='pending').aggregate(total=Sum('amount'))['total'] or 0
    received_count = incomes.filter(status='received').count()
    pending_count = incomes.filter(status='pending').count()
    overdue_count = incomes.filter(
        status='pending',
        due_date__lt=timezone.now().date()
    ).count()
    
    context = {
        'page_obj': page_obj,
        'total_amount': total_amount,
        'pending_amount': pending_amount,
        'received_count': received_count,
        'pending_count': pending_count,
        'overdue_count': overdue_count,
        'categories': Category.objects.filter(category_type='income', is_active=True),
        'status_choices': Income.STATUS_CHOICES
    }
    
    return render(request, 'financial/income/list.html', context)


@login_required
def income_create(request):
    """Crear nuevo ingreso"""
    if request.method == 'POST':
        form = IncomeForm(request.POST, request.FILES)
        if form.is_valid():
            income = form.save(commit=False)
            income.created_by = request.user
            income.save()
            
            messages.success(request, _('Ingreso creado exitosamente.'))
            return redirect('financial:income_list')
    else:
        form = IncomeForm()
    
    context = {
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'financial/income/form.html', context)


@login_required
def income_update(request, income_id):
    """Actualizar ingreso"""
    income = get_object_or_404(Income, id=income_id)
    
    if request.method == 'POST':
        form = IncomeForm(request.POST, request.FILES, instance=income)
        if form.is_valid():
            form.save()
            messages.success(request, _('Ingreso actualizado exitosamente.'))
            return redirect('financial:income_list')
    else:
        form = IncomeForm(instance=income)
    
    context = {
        'form': form,
        'income': income,
        'action': 'update'
    }
    
    return render(request, 'financial/income/form.html', context)


@login_required
def income_delete(request, income_id):
    """Eliminar ingreso"""
    income = get_object_or_404(Income, id=income_id)
    
    if request.method == 'POST':
        income.delete()
        messages.success(request, _('Ingreso eliminado exitosamente.'))
        return redirect('financial_web:income_list')
    
    context = {
        'income': income
    }
    
    return render(request, 'financial/income/delete.html', context)


@login_required
def income_detail(request, income_id):
    """Detalle del ingreso"""
    income = get_object_or_404(Income, id=income_id)
    
    context = {
        'income': income
    }
    
    return render(request, 'financial/income/detail.html', context)


# Gestión de Inversiones
@login_required
def investment_list(request):
    """Lista de inversiones"""
    investments = Investment.objects.all()
    
    # Filtros
    status = request.GET.get('status', '')
    investment_type = request.GET.get('type', '')
    search = request.GET.get('search', '')
    
    if status:
        investments = investments.filter(status=status)
    
    if investment_type:
        investments = investments.filter(investment_type=investment_type)
    
    if search:
        investments = investments.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Paginación
    paginator = Paginator(investments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Estadísticas
    total_amount = investments.aggregate(total=Sum('amount'))['total'] or 0
    active_amount = investments.filter(status='in_progress').aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'page_obj': page_obj,
        'total_amount': total_amount,
        'active_amount': active_amount,
        'investment_types': Investment.INVESTMENT_TYPES,
        'status_choices': Investment.STATUS_CHOICES
    }
    
    return render(request, 'financial/investments/list.html', context)


@login_required
def investment_create(request):
    """Crear nueva inversión"""
    if request.method == 'POST':
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.created_by = request.user
            investment.save()
            
            messages.success(request, _('Inversión creada exitosamente.'))
            return redirect('financial_web:investment_list')
    else:
        form = InvestmentForm()
    
    context = {
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'financial/investments/form.html', context)


@login_required
def investment_update(request, investment_id):
    """Actualizar inversión"""
    investment = get_object_or_404(Investment, id=investment_id)
    
    if request.method == 'POST':
        form = InvestmentForm(request.POST, instance=investment)
        if form.is_valid():
            form.save()
            messages.success(request, _('Inversión actualizada exitosamente.'))
            return redirect('financial_web:investment_list')
    else:
        form = InvestmentForm(instance=investment)
    
    context = {
        'form': form,
        'investment': investment,
        'action': 'update'
    }
    
    return render(request, 'financial/investments/form.html', context)


@login_required
def investment_delete(request, investment_id):
    """Eliminar inversión"""
    investment = get_object_or_404(Investment, id=investment_id)
    
    if request.method == 'POST':
        investment.delete()
        messages.success(request, _('Inversión eliminada exitosamente.'))
        return redirect('financial_web:investment_list')
    
    context = {
        'investment': investment
    }
    
    return render(request, 'financial/investments/delete.html', context)


@login_required
def investment_detail(request, investment_id):
    """Detalle de la inversión"""
    investment = get_object_or_404(Investment, id=investment_id)
    
    context = {
        'investment': investment
    }
    
    return render(request, 'financial/investments/detail.html', context)


# Gestión de Presupuestos
@login_required
def budget_list(request):
    """Lista de presupuestos"""
    budgets = Budget.objects.all()
    
    # Paginación
    paginator = Paginator(budgets, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj
    }
    
    return render(request, 'financial/budget_list.html', context)


@login_required
def budget_create(request):
    """Crear nuevo presupuesto"""
    if request.method == 'POST':
        form = BudgetForm(request.POST)
        if form.is_valid():
            budget = form.save(commit=False)
            budget.created_by = request.user
            budget.save()
            
            messages.success(request, _('Presupuesto creado exitosamente.'))
            return redirect('financial_web:budget_list')
    else:
        form = BudgetForm()
    
    context = {
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'financial/budget_form.html', context)


@login_required
def budget_update(request, budget_id):
    """Actualizar presupuesto"""
    budget = get_object_or_404(Budget, id=budget_id)
    
    if request.method == 'POST':
        form = BudgetForm(request.POST, instance=budget)
        if form.is_valid():
            form.save()
            messages.success(request, _('Presupuesto actualizado exitosamente.'))
            return redirect('financial_web:budget_list')
    else:
        form = BudgetForm(instance=budget)
    
    context = {
        'form': form,
        'budget': budget,
        'action': 'update'
    }
    
    return render(request, 'financial/budget_form.html', context)


@login_required
def budget_delete(request, budget_id):
    """Eliminar presupuesto"""
    budget = get_object_or_404(Budget, id=budget_id)
    
    if request.method == 'POST':
        budget.delete()
        messages.success(request, _('Presupuesto eliminado exitosamente.'))
        return redirect('financial_web:budget_list')
    
    context = {
        'budget': budget
    }
    
    return render(request, 'financial/budget_delete.html', context)


@login_required
def budget_detail(request, budget_id):
    """Detalle del presupuesto"""
    budget = get_object_or_404(Budget, id=budget_id)
    
    context = {
        'budget': budget
    }
    
    return render(request, 'financial/budget_detail.html', context)


# Flujo de Caja
@login_required
def cash_flow_list(request):
    """Lista de flujos de caja"""
    cash_flows = CashFlow.objects.all()
    
    # Paginación
    paginator = Paginator(cash_flows, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj
    }
    
    return render(request, 'financial/cash_flow_list.html', context)


@login_required
def cash_flow_create(request):
    """Crear nuevo flujo de caja"""
    if request.method == 'POST':
        form = CashFlowForm(request.POST)
        if form.is_valid():
            cash_flow = form.save(commit=False)
            cash_flow.created_by = request.user
            cash_flow.save()
            
            messages.success(request, _('Flujo de caja creado exitosamente.'))
            return redirect('financial_web:cash_flow_list')
    else:
        form = CashFlowForm()
    
    context = {
        'form': form,
        'action': 'create'
    }
    
    return render(request, 'financial/cash_flow_form.html', context)


@login_required
def cash_flow_detail(request, cash_flow_id):
    """Detalle del flujo de caja"""
    cash_flow = get_object_or_404(CashFlow, id=cash_flow_id)
    
    context = {
        'cash_flow': cash_flow
    }
    
    return render(request, 'financial/cash_flow_detail.html', context)


# Reportes Financieros
@login_required
def financial_reports(request):
    """Generar reportes financieros"""
    if request.method == 'POST':
        form = FinancialReportForm(request.POST)
        if form.is_valid():
            # Aquí se implementaría la generación de reportes
            messages.success(request, _('Reporte generado exitosamente.'))
            return redirect('financial_web:financial_dashboard')
    else:
        form = FinancialReportForm()
    
    context = {
        'form': form
    }
    
    return render(request, 'financial/reports.html', context)


# API endpoints para AJAX
@login_required
def financial_stats(request):
    """Estadísticas financieras para AJAX"""
    today = timezone.now().date()
    current_month = today.replace(day=1)
    next_month = (current_month + timedelta(days=32)).replace(day=1)
    
    # Estadísticas del mes
    monthly_expenses = Expense.objects.filter(
        expense_date__gte=current_month,
        expense_date__lt=next_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_income = Income.objects.filter(
        income_date__gte=current_month,
        income_date__lt=next_month
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Gastos por categoría
    expenses_by_category = Expense.objects.filter(
        expense_date__gte=current_month,
        expense_date__lt=next_month
    ).values('category__name').annotate(total=Sum('amount'))
    
    # Ingresos por categoría
    income_by_category = Income.objects.filter(
        income_date__gte=current_month,
        income_date__lt=next_month
    ).values('category__name').annotate(total=Sum('amount'))
    
    data = {
        'monthly_expenses': float(monthly_expenses),
        'monthly_income': float(monthly_income),
        'monthly_balance': float(monthly_income - monthly_expenses),
        'expenses_by_category': list(expenses_by_category),
        'income_by_category': list(income_by_category),
    }
    
    return JsonResponse(data) 