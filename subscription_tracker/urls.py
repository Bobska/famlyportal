"""
Subscription Tracker URLs

RESTful URL patterns for subscription management functionality.
"""

from django.urls import path
from . import views

app_name = 'subscription_tracker'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Subscription Management
    path('subscriptions/', views.subscription_list, name='subscription_list'),
    path('subscriptions/new/', views.subscription_create, name='subscription_create'),
    path('subscriptions/<int:pk>/', views.subscription_detail, name='subscription_detail'),
    path('subscriptions/<int:pk>/edit/', views.subscription_update, name='subscription_update'),
    path('subscriptions/<int:pk>/cancel/', views.subscription_delete, name='subscription_delete'),
    
    # Category Management
    path('categories/', views.category_list, name='category_list'),
    
    # Analytics and Reporting
    path('analytics/', views.cost_analysis, name='cost_analysis'),
    path('export/csv/', views.export_csv, name='export_csv'),
    
    # AJAX Endpoints
    path('api/quick-add/', views.quick_add_subscription, name='quick_add_subscription'),
    path('api/mark-payment/<int:pk>/', views.mark_payment, name='mark_payment'),
    path('api/bulk-actions/', views.bulk_actions, name='bulk_actions'),
]
