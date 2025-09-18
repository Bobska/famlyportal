from django.urls import path
from . import views

app_name = 'budget_basic'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('transactions/', views.main, name='main'),
    path('income/add/', views.add_income, name='add_income'),
    path('income/<int:income_id>/edit/', views.edit_income, name='edit_income'),
    path('income/<int:income_id>/get/', views.get_income, name='get_income'),
    path('income/<int:income_id>/delete/', views.delete_income, name='delete_income'),
]