from functools import wraps
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.http import Http404
from .models import Family, FamilyMember


def family_required(function=None, redirect_url='/accounts/dashboard/'):
    """
    Decorator to ensure user belongs to at least one family.
    If user has no family, redirects them to dashboard with a message.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.familymember_set.exists():
                messages.warning(request, "You need to be part of a family to access this feature.")
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator


def family_admin_required(function=None, redirect_url='/accounts/dashboard/'):
    """
    Decorator to ensure user is an admin of at least one family.
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_family_admin():
                messages.error(request, "You need to be a family admin to access this feature.")
                return redirect(redirect_url)
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    
    if function:
        return decorator(function)
    return decorator


def specific_family_admin_required(family_pk_param='family_pk'):
    """
    Decorator to ensure user is an admin of a specific family.
    
    Args:
        family_pk_param: The name of the URL parameter containing the family ID
    """
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def _wrapped_view(request, *args, **kwargs):
            family_pk = kwargs.get(family_pk_param)
            if not family_pk:
                raise Http404("Family not specified")
            
            family = get_object_or_404(Family, pk=family_pk)
            
            if not request.user.is_family_admin(family):
                messages.error(request, f"You need to be an admin of {family.name} to access this feature.")
                return redirect('/accounts/dashboard/')
            
            # Add family to request for easy access in view
            request.current_family = family
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def get_user_families(user):
    """
    Get all families that a user belongs to.
    Returns a queryset of Family objects.
    """
    return Family.objects.filter(familymember__user=user).distinct()


def get_user_family_context(user):
    """
    Get family context data for templates.
    Returns a dictionary with family information.
    """
    families = get_user_families(user)
    primary_family = user.primary_family
    
    context = {
        'user_families': families,
        'primary_family': primary_family,
        'is_family_admin': user.is_family_admin(),
        'family_count': families.count(),
    }
    
    if primary_family:
        context.update({
            'primary_family_member': primary_family.get_member_by_user(user),
            'primary_family_members': primary_family.familymember_set.select_related('user').all(),
        })
    
    return context


class FamilyPermissionMixin:
    """
    Mixin for class-based views that require family membership.
    """
    family_required = True
    admin_required = False
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')
        
        if self.family_required and not request.user.familymember_set.exists():
            messages.warning(request, "You need to be part of a family to access this feature.")
            return redirect('accounts:dashboard')
        
        if self.admin_required and not request.user.is_family_admin():
            messages.error(request, "You need to be a family admin to access this feature.")
            return redirect('accounts:dashboard')
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            context.update(get_user_family_context(self.request.user))
        return context


def can_user_access_family(user, family):
    """
    Check if a user can access a specific family's data.
    Returns True if user is a member of the family.
    """
    return FamilyMember.objects.filter(user=user, family=family).exists()


def can_user_manage_family_member(user, target_member):
    """
    Check if a user can manage another family member.
    Only family admins can manage other members.
    """
    if not isinstance(target_member, FamilyMember):
        return False
    
    # Users can always manage themselves
    if user == target_member.user:
        return True
    
    # Check if user is admin of the same family
    return user.is_family_admin(target_member.family)
