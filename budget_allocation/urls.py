# Budget Allocation App URLs
from django.urls import path
from . import views

app_name = 'budget_allocation'

urlpatterns = [
    # Dashboard and main views
    path('', views.dashboard, name='dashboard'),
    
    # URL patterns will be added as views are implemented
]
