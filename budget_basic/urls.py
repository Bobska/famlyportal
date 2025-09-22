from django.urls import path
from . import views

app_name = 'budget_basic'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transactions/', views.main, name='main'),
    path('week-data/', views.get_week_data, name='get_week_data'),
    # Payee URLs
    path('payees/', views.get_payees, name='get_payees'),
    path('payee/add/', views.add_payee, name='add_payee'),
    path('auto-date/', views.get_auto_date, name='get_auto_date'),
    # Income URLs
    path('income/add/', views.add_income, name='add_income'),
    path('income/<int:income_id>/edit/', views.edit_income, name='edit_income'),
    path('income/<int:income_id>/get/', views.get_income, name='get_income'),
    path('income/<int:income_id>/delete/', views.delete_income, name='delete_income'),
    # Expense URLs
    path('expense/add/', views.add_expense, name='add_expense'),
    path('expense/<int:expense_id>/edit/', views.edit_expense, name='edit_expense'),
    path('expense/<int:expense_id>/get/', views.get_expense, name='get_expense'),
    path('expense/<int:expense_id>/delete/', views.delete_expense, name='delete_expense'),
]