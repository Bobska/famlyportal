from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
from core.admin import FamilyScopedModelAdmin
from .models import Family, FamilyMember

# Check if AppPermission exists in the current model structure
try:
    from .models import AppPermission
    HAS_APP_PERMISSION = True
except ImportError:
    HAS_APP_PERMISSION = False

User = get_user_model()


class FamilyMemberInline(admin.TabularInline):
    """Inline for family members"""
    model = FamilyMember
    extra = 0
    fields = ['user', 'role', 'joined_at']
    readonly_fields = ['joined_at']
    raw_id_fields = ['user']


if HAS_APP_PERMISSION:
    class AppPermissionInline(admin.TabularInline):
        """Inline for app permissions"""
        model = AppPermission
        extra = 0
        fields = ['app_name', 'can_view', 'can_add', 'can_change', 'can_delete']


@admin.register(Family)
class FamilyAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for Family model"""
    
    list_display = [
        'name', 
        'created_by',
        'member_count_display', 
        'invite_code',
        'created_display'
    ]
    list_filter = ['created_at']
    search_fields = ['name', 'invite_code', 'created_by__username']
    readonly_fields = ['invite_code', 'created_at', 'updated_at']
    inlines = [FamilyMemberInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'created_by')
        }),
        ('Family Access', {
            'fields': ('invite_code',),
            'description': 'Share this invite code with family members to join'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with member counts"""
        qs = super().get_queryset(request)
        return qs.annotate(
            member_count_annotated=Count('familymember')
        ).select_related('created_by')
    
    def member_count_display(self, obj):
        """Display member count with link"""
        count = getattr(obj, 'member_count_annotated', obj.familymember_set.count())
        return format_html(
            '<a href="{}?family__id__exact={}">{} members</a>',
            reverse('admin:accounts_familymember_changelist'),
            obj.id,
            count
        )
    member_count_display.short_description = 'Members'
    member_count_display.admin_order_field = 'member_count_annotated'
    
    def regenerate_invite_code(self, request, queryset):
        """Bulk action to regenerate invite codes"""
        for family in queryset:
            family.generate_invite_code()
            family.save()
        count = queryset.count()
        self.message_user(request, f'Regenerated invite codes for {count} families.')
    regenerate_invite_code.short_description = "Regenerate invite codes"
    
    def get_actions(self, request):
        """Add custom actions"""
        actions = super().get_actions(request)
        actions['regenerate_invite_code'] = (
            self.regenerate_invite_code, 
            'regenerate_invite_code', 
            self.regenerate_invite_code.short_description
        )
        return actions


@admin.register(FamilyMember)
class FamilyMemberAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for FamilyMember model"""
    
    list_display = [
        'user_display', 
        'family',
        'role_display', 
        'joined_at',
        'invited_by'
    ]
    list_filter = ['role', 'joined_at', 'family']
    search_fields = ['user__username', 'user__email', 'user__first_name', 'user__last_name', 'family__name']
    raw_id_fields = ['user', 'family', 'invited_by']
    date_hierarchy = 'joined_at'
    
    if HAS_APP_PERMISSION:
        inlines = [AppPermissionInline]
    
    fieldsets = (
        ('Member Information', {
            'fields': ('user', 'family', 'role')
        }),
        ('Invitation Info', {
            'fields': ('invited_by', 'joined_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['joined_at']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'family', 'invited_by')
    
    def user_display(self, obj):
        """Display user information with link"""
        user = obj.user
        name = f"{user.first_name} {user.last_name}".strip() or user.username
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            reverse('admin:accounts_user_change', args=[user.id]),
            user.email,
            name
        )
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user__username'
    
    def role_display(self, obj):
        """Display role with color coding"""
        role_colors = {
            'admin': 'red',
            'parent': 'blue',
            'child': 'green',
            'other': 'gray'
        }
        color = role_colors.get(obj.role, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_display.short_description = 'Role'
    role_display.admin_order_field = 'role'
    
    def promote_to_admin(self, request, queryset):
        """Bulk action to promote members to admin"""
        updated = queryset.update(role='admin')
        self.message_user(request, f'Promoted {updated} members to admin.')
    promote_to_admin.short_description = "Promote to admin"
    
    def demote_from_admin(self, request, queryset):
        """Bulk action to demote admins to parent"""
        updated = queryset.filter(role='admin').update(role='parent')
        self.message_user(request, f'Demoted {updated} admins to parent.')
    demote_from_admin.short_description = "Demote from admin"
    
    def get_actions(self, request):
        """Add role management actions"""
        actions = super().get_actions(request)
        actions['promote_to_admin'] = (
            self.promote_to_admin, 
            'promote_to_admin', 
            self.promote_to_admin.short_description
        )
        actions['demote_from_admin'] = (
            self.demote_from_admin, 
            'demote_from_admin', 
            self.demote_from_admin.short_description
        )
        return actions


if HAS_APP_PERMISSION:
    @admin.register(AppPermission)
    class AppPermissionAdmin(FamilyScopedModelAdmin):
        """Enhanced admin for AppPermission model"""
        
        list_display = [
            'family_member_display',
            'app_name',
            'permissions_summary',
            'created_display'
        ]
        list_filter = ['app_name', 'can_view', 'can_add', 'can_change', 'can_delete']
        search_fields = [
            'family_member__user__username',
            'family_member__user__email', 
            'family_member__family__name',
            'app_name'
        ]
        raw_id_fields = ['family_member']
        
        fieldsets = (
            ('Permission Details', {
                'fields': ('family_member', 'app_name')
            }),
            ('Permissions', {
                'fields': ('can_view', 'can_add', 'can_change', 'can_delete'),
                'description': 'Set specific permissions for this app'
            }),
            ('Timestamps', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )
        
        def get_queryset(self, request):
            """Optimize queryset"""
            qs = super().get_queryset(request)
            return qs.select_related('family_member__user', 'family_member__family')
        
        def family_member_display(self, obj):
            """Display family member with family info"""
            user = obj.family_member.user
            name = f"{user.first_name} {user.last_name}".strip() or user.username
            return format_html(
                '{} <small>({})</small>',
                name,
                obj.family_member.family.name
            )
        family_member_display.short_description = 'Family Member'
        family_member_display.admin_order_field = 'family_member__user__username'
        
        def permissions_summary(self, obj):
            """Display permissions summary"""
            perms = []
            if obj.can_view: perms.append('View')
            if obj.can_add: perms.append('Add')
            if obj.can_change: perms.append('Change')
            if obj.can_delete: perms.append('Delete')
            
            if perms:
                return format_html(
                    '<span style="color: green;">{}</span>',
                    ', '.join(perms)
                )
            return format_html('<span style="color: red;">No permissions</span>')
        permissions_summary.short_description = 'Permissions'


class FamilyMembershipInline(admin.TabularInline):
    """Inline for user's family memberships"""
    model = FamilyMember
    fk_name = 'user'  # Specify which foreign key to use
    extra = 0
    fields = ['family', 'role', 'joined_at']
    readonly_fields = ['joined_at']
    raw_id_fields = ['family']


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Enhanced user admin with family information"""
    
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'date_joined', 'family_info', 'profile_picture_preview')
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
    
    inlines = [FamilyMembershipInline]
    
    def profile_picture_preview(self, obj):
        """Display profile picture preview"""
        if obj.profile_picture:
            return format_html('<img src="{}" width="30" height="30" style="border-radius: 50%;" />', obj.profile_picture.url)
        return "No picture"
    profile_picture_preview.short_description = "Profile Picture"
    
    def family_info(self, obj):
        """Display family membership info"""
        memberships = obj.familymember_set.all()
        if not memberships:
            return format_html('<span style="color: red;">No family</span>')
        
        info = []
        for membership in memberships:
            color = 'green'
            info.append(format_html(
                '<span style="color: {};">{} ({})</span>',
                color,
                membership.family.name,
                membership.get_role_display()
            ))
        
        return format_html('<br>'.join(info))
    family_info.short_description = 'Family Memberships'
