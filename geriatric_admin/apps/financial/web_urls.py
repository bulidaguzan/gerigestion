from django.urls import path
from . import views

app_name = 'financial_web'

urlpatterns = [
    # Dashboard
    path('', views.financial_dashboard, name='dashboard'),
    
    # Categorías
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:category_id>/update/', views.category_update, name='category_update'),
    path('categories/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    
    # Gastos
    path('expenses/', views.expense_list, name='expense_list'),
    path('expenses/create/', views.expense_create, name='expense_create'),
    path('expenses/<uuid:expense_id>/', views.expense_detail, name='expense_detail'),
    path('expenses/<uuid:expense_id>/update/', views.expense_update, name='expense_update'),
    path('expenses/<uuid:expense_id>/delete/', views.expense_delete, name='expense_delete'),
    
    # Ingresos
    path('income/', views.income_list, name='income_list'),
    path('income/create/', views.income_create, name='income_create'),
    path('income/<uuid:income_id>/', views.income_detail, name='income_detail'),
    path('income/<uuid:income_id>/update/', views.income_update, name='income_update'),
    path('income/<uuid:income_id>/delete/', views.income_delete, name='income_delete'),
    
    # Inversiones
    path('investments/', views.investment_list, name='investment_list'),
    path('investments/create/', views.investment_create, name='investment_create'),
    path('investments/<uuid:investment_id>/', views.investment_detail, name='investment_detail'),
    path('investments/<uuid:investment_id>/update/', views.investment_update, name='investment_update'),
    path('investments/<uuid:investment_id>/delete/', views.investment_delete, name='investment_delete'),
    
    # Presupuestos
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/create/', views.budget_create, name='budget_create'),
    path('budgets/<uuid:budget_id>/', views.budget_detail, name='budget_detail'),
    path('budgets/<uuid:budget_id>/update/', views.budget_update, name='budget_update'),
    path('budgets/<uuid:budget_id>/delete/', views.budget_delete, name='budget_delete'),
    
    # Flujo de Caja
    path('cash-flow/', views.cash_flow_list, name='cash_flow_list'),
    path('cash-flow/create/', views.cash_flow_create, name='cash_flow_create'),
    path('cash-flow/<uuid:cash_flow_id>/', views.cash_flow_detail, name='cash_flow_detail'),
    
    # Reportes
    path('reports/', views.financial_reports, name='reports'),
    
    # API endpoints
    path('api/stats/', views.financial_stats, name='financial_stats'),
] 