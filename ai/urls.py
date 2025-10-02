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
]
