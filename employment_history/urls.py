from django.urls import path
from . import views

app_name = 'employment_history'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('positions/', views.position_list, name='position_list'),
    path('positions/new/', views.position_create, name='position_create'),
    path('positions/<int:pk>/', views.position_detail, name='position_detail'),
    path('skills/', views.skill_list, name='skill_list'),
]
