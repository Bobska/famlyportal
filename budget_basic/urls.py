from django.urls import path
from . import views

app_name = 'budget_basic'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions, name='transactions'),
    path('weekly/', views.weekly, name='weekly'),
    path('week-data/', views.get_week_data, name='get_week_data'),
    # Payee URLs (existing)
    path('payees/', views.get_payees, name='get_payees'),
    path('payee/add/', views.add_payee, name='add_payee'),
    # Payee Management URLs (new)
    path('payees-manage/', views.payee_list, name='payee_list'),
    path('payee/create/', views.payee_create, name='payee_create'),
    path('payee/<int:payee_id>/update/', views.payee_update, name='payee_update'),
    path('payee/<int:payee_id>/delete/', views.payee_delete, name='payee_delete'),
    path('payee/search/', views.payee_search, name='payee_search'),
    # Other URLs
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
    # Category Management URLs
    path('categories/', views.category_list, name='category_list'),
    path('category/create/', views.category_create, name='category_create'),
    path('category/<int:category_id>/update/', views.category_update, name='category_update'),
    path('category/<int:category_id>/delete/', views.category_delete, name='category_delete'),
    path('category/search/', views.category_search, name='category_search'),
    path('category/<int:category_id>/payees/', views.category_payees, name='category_payees'),
]
