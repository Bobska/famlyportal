from django.contrib import admin
from django.utils.html import format_html


class FamilyScopedModelAdmin(admin.ModelAdmin):
    """Base admin class with family scoping and enhanced features"""
    
    def get_queryset(self, request):
        """Filter queryset to show only user's family data"""
        qs = super().get_queryset(request)
        
        # Superuser sees all data
        if request.user.is_superuser:
            return qs
        
        # Try to get user's family
        try:
            family_member = request.user.familymember_set.first()
            if family_member:
                # Filter by family field if it exists
                if hasattr(self.model, 'family'):
                    return qs.filter(family=family_member.family)
                # Filter by user field if it exists
                elif hasattr(self.model, 'user'):
                    # Get all family members for user filtering
                    family_users = family_member.family.familymember_set.values_list('user', flat=True)
                    return qs.filter(user__in=family_users)
        except:
            pass
        
        # Default: return full queryset for now (can be changed to qs.none() for stricter security)
        return qs
    
    def _check_family_access(self, request, obj):
        """Check if user has access to this object based on family membership"""
        if request.user.is_superuser:
            return True
            
        try:
            family_member = request.user.familymember_set.first()
            if not family_member:
                return False
            
            # Check family field
            if hasattr(obj, 'family'):
                return obj.family == family_member.family
            
            # Check user field  
            if hasattr(obj, 'user'):
                user_family_members = family_member.family.familymember_set.values_list('user', flat=True)
                return obj.user.id in user_family_members
            
            return True  # Allow access if no family relationship
        except:
            return True  # Allow access if error occurs
    
    def save_model(self, request, obj, form, change):
        """Auto-set family/user fields when saving"""
        if not change and not request.user.is_superuser:
            try:
                family_member = request.user.familymember_set.first()
                if family_member:
                    # Auto-set family field
                    if hasattr(obj, 'family') and not obj.family:
                        obj.family = family_member.family
                    
                    # Auto-set user field for user-scoped models
                    if hasattr(obj, 'user') and not obj.user:
                        obj.user = request.user
            except:
                pass
        
        super().save_model(request, obj, form, change)
    
    # Enhanced display methods
    def created_display(self, obj):
        """Display creation date"""
        if hasattr(obj, 'created_at') and obj.created_at:
            return format_html(
                '<span title="{}">{}</span>',
                obj.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                obj.created_at.strftime('%m/%d/%Y')
            )
        return '-'
    created_display.short_description = 'Created'
    created_display.admin_order_field = 'created_at'
