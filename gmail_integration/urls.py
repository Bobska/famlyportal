"""
Gmail Integration URLs
"""
from django.urls import path
from . import views

app_name = 'gmail_integration'

urlpatterns = [
    # Account management
    path('', views.account_list, name='account_list'),
    path('add/', views.add_account, name='add_account'),
    path('oauth/callback/', views.oauth_callback, name='oauth_callback'),
    path('account/<int:account_id>/', views.account_detail, name='account_detail'),
    path('account/<int:account_id>/toggle/', views.toggle_account, name='toggle_account'),
    path('account/<int:account_id>/delete/', views.delete_account, name='delete_account'),
    
    # Email management
    path('account/<int:account_id>/emails/', views.email_list, name='email_list'),
    path('account/<int:account_id>/email/<int:email_id>/', views.email_detail, name='email_detail'),
    
    # Sync operations
    path('account/<int:account_id>/sync/', views.sync_emails, name='sync_emails'),
    path('account/<int:account_id>/sync-logs/', views.sync_logs, name='sync_logs'),
    path('sync/<int:sync_log_id>/status/', views.sync_status, name='sync_status'),
    
    # API endpoints
    path('api/accounts/', views.api_accounts, name='api_accounts'),
    path('api/account/<int:account_id>/search/', views.api_search_emails, name='api_search_emails'),
]