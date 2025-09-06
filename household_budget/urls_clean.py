from django.urls import path
from . import views

app_name = 'household_budget'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Transaction Management
    path('transactions/', views.TransactionListView.as_view(), name='transaction_list'),
    path('transactions/add/', views.TransactionCreateView.as_view(), name='transaction_add'),
    path('transactions/<int:pk>/edit/', views.TransactionUpdateView.as_view(), name='transaction_edit'),
    path('transactions/<int:pk>/delete/', views.TransactionDeleteView.as_view(), name='transaction_delete'),
    
    # Category Management
    path('categories/', views.category_tree, name='category_tree'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
]
