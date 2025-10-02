"""
AI Hub URLs
"""
from django.urls import path
from . import views

app_name = 'ai'

urlpatterns = [
    # Dashboard
    path('', views.dashboard, name='dashboard'),
    path('statistics/', views.statistics, name='statistics'),
    
    # Models
    path('models/', views.model_list, name='model_list'),
    path('models/<int:model_id>/', views.model_detail, name='model_detail'),
    path('models/<int:model_id>/activate/', views.activate_model, name='activate_model'),
    
    # Datasets
    path('datasets/', views.dataset_list, name='dataset_list'),
    
    # Predictions
    path('predictions/', views.prediction_list, name='prediction_list'),
    path('predictions/<int:prediction_id>/confirm/', views.confirm_prediction, name='confirm_prediction'),
    path('predictions/<int:prediction_id>/reject/', views.reject_prediction, name='reject_prediction'),
    
    # Email Classification Views
    path('emails/review/', views.email_review_view, name='email_review'),
    path('emails/manual-select/', views.manual_selection_view, name='manual_selection'),
    path('emails/training-dashboard/', views.training_dashboard_view, name='training_dashboard'),
    
    # Email Classification AJAX Endpoints
    path('emails/classify/<int:email_id>/', views.classify_single_email, name='classify_single_email'),
    path('emails/classify-all/', views.classify_all_emails_view, name='classify_all_emails'),
    path('emails/predictions/<int:prediction_id>/confirm/', views.confirm_email_prediction, name='confirm_email_prediction'),
    path('emails/predictions/<int:prediction_id>/reject/', views.reject_email_prediction, name='reject_email_prediction'),
    path('emails/train/', views.train_model_view, name='train_model'),
]
