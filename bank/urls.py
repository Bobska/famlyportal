from django.urls import path
from . import views
from . import views_payees

app_name = 'bank'

urlpatterns = [
    # Navigation Shell (new unified entry point)
    path('shell/', views.shell, name='shell'),
    
    # Initialization page
    path('init/', views.initialize_bank, name='initialize'),
    
    # Traditional page routes (kept for backwards compatibility)
    path('', views.dashboard, name='dashboard'),
    path('accounts/', views.accounts, name='accounts'),
    path('transactions/', views.transactions, name='transactions'),
    path('transactions-tactical/', views.transactions, name='transactions_tactical'),
    path('maintenance/', views.maintenance, name='maintenance'),
    path('weekly/', views.weekly, name='weekly'),
    path('weekly-expanse/', views.weekly_expanse, name='weekly_expanse'),
    path('week-data/', views.get_week_data, name='get_week_data'),
    
    # AJAX Content Loading Endpoints for Navigation Shell
    path('ajax/dashboard/', views.ajax_dashboard_content, name='ajax_dashboard'),
    path('ajax/accounts/', views.ajax_accounts_content, name='ajax_accounts'),
    path('ajax/weekly/', views.ajax_weekly_content, name='ajax_weekly'),
    path('ajax/transactions/', views.ajax_transactions_content, name='ajax_transactions'),
    path('ajax/payees/', views.ajax_payees_content, name='ajax_payees'),
    path('ajax/categories/', views.ajax_categories_content, name='ajax_categories'),
    
    # API Endpoints for Quick Add
    path('api/add-payee/', views.api_add_payee, name='api_add_payee'),
    path('api/add-category/', views.api_add_category, name='api_add_category'),
    path('api/link-payee-category/', views.api_link_payee_category, name='api_link_payee_category'),
    path('api/payee-categories/<str:payee_name>/', views.api_get_payee_categories, name='api_get_payee_categories'),
    path('api/category-payees/<int:category_id>/', views.api_get_category_payees, name='api_get_category_payees'),
    
    # Payee URLs (existing)
    path('payees/', views.get_payees, name='get_payees'),
    path('payee/add/', views.add_payee, name='add_payee'),
    path('payee/link-categories/', views.link_categories_to_payee, name='link_categories_to_payee'),
    
    # Payee Management URLs (new)
    path('payees-manage/', views_payees.payee_list, name='payee_list'),
    path('payee/create/', views_payees.payee_create, name='payee_create'),
    path('payee/<int:payee_id>/update/', views_payees.payee_update, name='payee_update'),
    path('payee/<int:payee_id>/delete/', views_payees.payee_delete, name='payee_delete'),
    path('payee/search/', views_payees.payee_search, name='payee_search'),
    
    # Category URLs (existing)
    path('categories-list/', views.get_categories, name='get_categories'),
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
    
    # Example pages
    path('dropdown-example/', views.dropdown_example, name='dropdown_example'),
    path('datepicker-example/', views.datepicker_example, name='datepicker_example'),
]
