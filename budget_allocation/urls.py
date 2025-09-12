# Budget Allocation App URLs
from django.urls import path
from . import views

app_name = 'budget_allocation'

urlpatterns = [
    # Dashboard and main views
    path('', views.dashboard, name='dashboard'),
    
    # Account management
    path('accounts/', views.account_list, name='account_list'),
    path('accounts/create/', views.account_create, name='account_create'),
    path('account/<int:account_id>/', views.account_detail, name='account_detail'),
    path('account/<int:account_id>/edit/', views.edit_account, name='edit_account'),
    path('account/<int:account_id>/toggle-status/', views.toggle_account_status_api, name='toggle_account_status'),
    path('account/<int:parent_id>/add-child/', views.add_child_account, name='add_child_account'),
    
    # Allocation management
    path('allocation/', views.allocation_dashboard, name='allocation_dashboard'),
    path('allocation/create/', views.create_allocation, name='create_allocation'),
    
    # Transaction management
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/create/', views.transaction_create, name='transaction_create'),
    path('transactions/<int:pk>/delete/', views.transaction_delete, name='transaction_delete'),
    # path('transactions/<int:pk>/', views.transaction_detail, name='transaction_detail'),
    # path('transactions/<int:pk>/edit/', views.transaction_update, name='transaction_update'),
    
    # Budget template management
    path('budget-templates/', views.budget_template_list, name='budget_template_list'),
    path('budget-templates/create/', views.budget_template_create, name='budget_template_create'),
    
    # Settings
    path('settings/', views.family_settings, name='family_settings'),
    
    # API Endpoints
    path('api/accounts/', views.accounts_api, name='accounts_api'),
    path('api/accounts/create/', views.create_account_ajax, name='create_account_ajax'),
    path('api/account/<int:account_id>/balance/', views.account_balance_api, name='account_balance_api'),
    path('api/account/<int:account_id>/toggle-status/', views.toggle_account_status_api, name='toggle_account_status_api'),
    path('api/allocation-suggestions/', views.allocation_suggestions_api, name='allocation_suggestions_api'),
    path('api/week-summary/', views.week_summary_api, name='week_summary_api'),
]
