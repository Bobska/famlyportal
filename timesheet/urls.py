from django.urls import path
from . import views

app_name = 'timesheet'

urlpatterns = [
    # Main dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Time entries
    path('entries/', views.time_entries, name='entries'),
    path('entries/create/', views.create_entry, name='create_entry'),
    path('entries/<int:entry_id>/edit/', views.edit_entry, name='edit_entry'),
    path('entries/<int:entry_id>/delete/', views.delete_entry, name='delete_entry'),
    
    # Projects
    path('projects/', views.projects, name='projects'),
    path('projects/create/', views.create_project, name='create_project'),
    path('projects/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    
    # Reports
    path('reports/', views.reports, name='reports'),
    path('export/csv/', views.export_csv, name='export_csv'),
    
    # API endpoints for AJAX functionality
    path('api/quick-entry/', views.quick_entry_api, name='quick_entry_api'),
    path('api/timer/start/', views.start_timer_api, name='start_timer_api'),
    path('api/timer/stop/', views.stop_timer_api, name='stop_timer_api'),
    path('api/timer/status/', views.get_timer_status_api, name='timer_status_api'),
    
    # Legacy URLs for compatibility
    path('entry-list/', views.entry_list, name='entry_list'),
    path('entry-create/', views.entry_create, name='entry_create'),
    path('entry-detail/<int:pk>/', views.entry_detail, name='entry_detail'),
    path('entry-update/<int:pk>/', views.entry_update, name='entry_update'),
    path('entry-delete/<int:pk>/', views.entry_delete, name='entry_delete'),
    path('job-list/', views.job_list, name='job_list'),
    path('job-create/', views.job_create, name='job_create'),
]
