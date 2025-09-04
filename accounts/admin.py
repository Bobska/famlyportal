from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, Family, FamilyMember


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User Admin"""
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'profile_picture_preview')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('phone_number', 'date_of_birth', 'profile_picture')
        }),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('email', 'first_name', 'last_name', 'phone_number', 'date_of_birth', 'profile_picture')
        }),
    )
    
    def profile_picture_preview(self, obj):
        if obj.profile_picture:
            return format_html('<img src="{}" width="30" height="30" style="border-radius: 50%;" />', obj.profile_picture.url)
        return "No picture"
    profile_picture_preview.short_description = "Profile Picture"


@admin.register(Family)
class FamilyAdmin(admin.ModelAdmin):
    """Family Admin"""
    list_display = ('name', 'created_by', 'invite_code', 'member_count_display', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('name', 'invite_code', 'created_by__username')
    readonly_fields = ('invite_code', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'created_by')
        }),
        ('Invite Information', {
            'fields': ('invite_code',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def member_count_display(self, obj):
        return obj.member_count
    member_count_display.short_description = "Members"


@admin.register(FamilyMember)
class FamilyMemberAdmin(admin.ModelAdmin):
    """Family Member Admin"""
    list_display = ('user', 'family', 'role', 'joined_at', 'invited_by')
    list_filter = ('role', 'joined_at', 'family')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'family__name')
    ordering = ('-joined_at',)
    
    fieldsets = (
        (None, {
            'fields': ('user', 'family', 'role')
        }),
        ('Invitation Info', {
            'fields': ('invited_by', 'joined_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('joined_at',)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'family', 'invited_by')
