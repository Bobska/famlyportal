from django.urls import path
from . import views

app_name = 'household_budget'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Budget Management
    path('budget/', views.budget_overview, name='budget_overview'),
    path('budget/new/', views.BudgetCreateView.as_view(), name='budget_create'),
    path('budget/<int:pk>/edit/', views.BudgetUpdateView.as_view(), name='budget_update'),
    
    # Transaction Management
    path('transactions/', views.transaction_list, name='transaction_list'),
    path('transactions/new/', views.TransactionCreateView.as_view(), name='transaction_create'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_update'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    
    # Category Management
    path('categories/', views.category_management, name='category_management'),
    path('categories/new/', views.CategoryCreateView.as_view(), name='category_create'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_update'),
    
    # Savings Goals
    path('savings-goals/', views.savings_goals, name='savings_goals'),
    path('savings-goals/new/', views.SavingsGoalCreateView.as_view(), name='savings_goal_create'),
    path('savings-goals/<int:pk>/edit/', views.SavingsGoalUpdateView.as_view(), name='savings_goal_update'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    
    # AJAX API Endpoints
    path('api/quick-transaction/', views.quick_transaction, name='quick_transaction'),
    path('api/chart-data/', views.budget_chart_data, name='budget_chart_data'),
]
