from django.urls import path
from . import views

app_name = 'budget_basic'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transactions/', views.main, name='main'),
]