from django.urls import path
from . import views

app_name = 'household_budget'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('budgets/', views.budget_list, name='budget_list'),
    path('budgets/new/', views.budget_create, name='budget_create'),
    path('expenses/', views.expense_list, name='expense_list'),
    path('income/', views.income_list, name='income_list'),
]
