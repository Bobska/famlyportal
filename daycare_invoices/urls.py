"""
Daycare Invoice Tracker URL Configuration

Defines URL patterns for all daycare provider, child, invoice and payment 
management features with clean hierarchical organization.
"""

from django.urls import path
from . import views

app_name = 'daycare_invoices'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Provider Management
    path('providers/', views.provider_list, name='provider_list'),
    path('providers/add/', views.provider_create, name='provider_create'),
    path('providers/<int:pk>/', views.provider_detail, name='provider_detail'),
    path('providers/<int:pk>/edit/', views.provider_update, name='provider_update'),
    
    # Child Management (these will be added when child views are created)
    # path('children/', views.child_list, name='child_list'),
    # path('children/add/', views.child_create, name='child_create'),
    # path('children/<int:pk>/', views.child_detail, name='child_detail'),
    # path('children/<int:pk>/edit/', views.child_update, name='child_update'),
    
    # Invoice Management
    path('invoices/', views.invoice_list, name='invoice_list'),
    path('invoices/add/', views.invoice_create, name='invoice_create'),
    path('invoices/<int:pk>/', views.invoice_detail, name='invoice_detail'),
    path('invoices/<int:pk>/edit/', views.invoice_update, name='invoice_update'),
    
    # Payment Management
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/add/', views.payment_create, name='payment_create'),
    path('payments/add/<int:invoice_pk>/', views.payment_create, name='payment_create_for_invoice'),
    path('payments/<int:pk>/', views.payment_detail, name='payment_detail'),
    
    # Reporting
    path('reports/', views.financial_report, name='financial_report'),
    
    # AJAX Endpoints
    path('ajax/quick-invoice/', views.quick_invoice_ajax, name='quick_invoice_ajax'),
    path('ajax/mark-paid/<int:pk>/', views.mark_as_paid_ajax, name='mark_as_paid_ajax'),
]
