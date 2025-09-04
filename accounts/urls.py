from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    # Authentication
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('register/', views.user_register, name='register'),
    
    # Dashboard and Profile
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.user_profile, name='profile'),
    
    # Family Management
    path('join-family/', views.join_family, name='join_family'),
    path('family/', views.family_management, name='family'),
    path('family/<int:family_pk>/members/', views.family_members, name='family_members'),
    path('family/<int:family_pk>/members/add/', views.add_family_member, name='add_family_member'),
    path('family/<int:family_pk>/members/<int:member_pk>/role/', views.update_member_role, name='update_member_role'),
    path('family/<int:family_pk>/members/<int:member_pk>/remove/', views.remove_family_member, name='remove_member'),
    
    # AJAX endpoints
    path('family/<int:family_pk>/invite-code/', views.family_invite_code, name='family_invite_code'),
]
