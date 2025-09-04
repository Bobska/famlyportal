"""
URL patterns for core app functionality including coming soon pages
"""

from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # Coming soon pages
    path('coming-soon/<str:app_name>/', views.coming_soon, name='coming_soon'),
    
    # API endpoints
    path('api/notify-when-ready/', views.notify_when_ready, name='notify_when_ready'),
    path('api/app-status/<str:app_name>/', views.app_status_api, name='app_status_api'),
    path('api/all-apps-status/', views.all_apps_status_api, name='all_apps_status_api'),
]
