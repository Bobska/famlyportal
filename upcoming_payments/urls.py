from django.urls import path
from . import views

app_name = 'upcoming_payments'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('payments/', views.payment_list, name='payment_list'),
    path('payments/new/', views.payment_create, name='payment_create'),
    path('reminders/', views.reminder_list, name='reminder_list'),
]
