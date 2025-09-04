from django.urls import path
from . import views

app_name = 'credit_cards'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('cards/', views.card_list, name='card_list'),
    path('cards/new/', views.card_create, name='card_create'),
    path('transactions/', views.transaction_list, name='transaction_list'),
]
