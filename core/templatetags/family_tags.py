"""
FamlyPortal template tags for family context and permissions.
"""
from django import template
from django.contrib.auth.models import User
from accounts.models import FamilyMember

register = template.Library()


@register.inclusion_tag('core/family_context.html', takes_context=True)
def family_context(context):
    """
    Provides family context information for templates.
    Returns family name, member count, and current user's role.
    """
    request = context['request']
    user = request.user
    
    if not user.is_authenticated:
        return {'family': None, 'member': None}
    
    try:
        family_member = user.familymember_set.first()
        if family_member:
            family = family_member.family
            member_count = family.familymember_set.count()
            return {
                'family': family,
                'member': family_member,
                'member_count': member_count,
                'role_display': family_member.get_role_display()
            }
    except FamilyMember.DoesNotExist:
        pass
    
    return {'family': None, 'member': None}


@register.simple_tag(takes_context=True)
def has_app_permission(context, app_name):
    """
    Check if the current user has permission to access a specific app.
    Usage: {% has_app_permission 'timesheet' as can_access_timesheet %}
    """
    request = context['request']
    user = request.user
    
    if not user.is_authenticated:
        return False
    
    try:
        family_member = user.familymember_set.first()
        if not family_member:
            return False
        
        # Family admins have access to all apps
        if family_member.role == 'admin':
            return True
        
        # Parents have access to most apps except admin-only
        if family_member.role == 'parent':
            admin_only_apps = ['household_budget', 'credit_cards', 'budget_allocation']
            return app_name not in admin_only_apps
        
        # Children have limited access
        if family_member.role == 'child':
            allowed_apps = ['timesheet', 'employment_history', 'autocraftcv']
            return app_name in allowed_apps
        
        # Others have basic access
        if family_member.role == 'other':
            allowed_apps = ['timesheet']
            return app_name in allowed_apps
            
        return False
    except FamilyMember.DoesNotExist:
        return False


@register.filter
def user_display_name(user):
    """
    Return the best display name for a user.
    Usage: {{ user|user_display_name }}
    """
    if user.first_name and user.last_name:
        return f"{user.first_name} {user.last_name}"
    elif user.first_name:
        return user.first_name
    elif user.last_name:
        return user.last_name
    else:
        return user.username


@register.filter
def family_role_badge(role):
    """
    Return a Bootstrap badge class for family roles.
    Usage: {{ member.role|family_role_badge }}
    """
    role_badges = {
        'admin': 'bg-danger',
        'parent': 'bg-primary', 
        'child': 'bg-success',
        'other': 'bg-secondary'
    }
    return role_badges.get(role, 'bg-secondary')


@register.simple_tag
def app_icon(app_name):
    """
    Return the appropriate Bootstrap icon for each app.
    Usage: {% app_icon 'timesheet' %}
    """
    app_icons = {
        'timesheet': 'bi-clock',
        'daycare_invoices': 'bi-receipt',
        'employment_history': 'bi-briefcase',
        'upcoming_payments': 'bi-calendar-check',
        'credit_cards': 'bi-credit-card',
        'household_budget': 'bi-piggy-bank',
        'budget_allocation': 'bi-pie-chart',
        'autocraftcv': 'bi-file-text'
    }
    return app_icons.get(app_name, 'bi-app')


@register.inclusion_tag('core/app_card.html', takes_context=True)
def app_card(context, app_name, app_title, app_description, dashboard_url):
    """
    Render an app card for the dashboard.
    Usage: {% app_card 'timesheet' 'Time Tracking' 'Track your work hours' 'timesheet:dashboard' %}
    """
    request = context['request']
    
    # Check if user has permission for this app
    has_permission = has_app_permission(context, app_name)
    icon = app_icon(app_name)
    
    return {
        'app_name': app_name,
        'app_title': app_title,
        'app_description': app_description,
        'dashboard_url': dashboard_url,
        'has_permission': has_permission,
        'icon': icon,
        'request': request
    }


@register.simple_tag(takes_context=True)
def get_family_member_count(context):
    """
    Get the count of family members for the current user's family.
    Usage: {% get_family_member_count as member_count %}
    """
    request = context['request']
    user = request.user
    
    if not user.is_authenticated:
        return 0
    
    try:
        family_member = user.familymember_set.first()
        if family_member:
            return family_member.family.familymember_set.count()
    except FamilyMember.DoesNotExist:
        pass
    
    return 0


@register.filter
def format_currency(value):
    """
    Format a decimal value as currency.
    Usage: {{ amount|format_currency }}
    """
    if value is None:
        return "$0.00"
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError):
        return "$0.00"


@register.filter
def truncate_smart(value, length=50):
    """
    Smart truncation that doesn't cut words in half.
    Usage: {{ description|truncate_smart:100 }}
    """
    if not value:
        return ""
    
    if len(value) <= length:
        return value
    
    # Find the last space before the length limit
    truncated = value[:length]
    last_space = truncated.rfind(' ')
    
    if last_space > 0:
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."


@register.simple_tag
def current_year():
    """
    Get the current year for copyright notices.
    Usage: {% current_year %}
    """
    from datetime import datetime
    return datetime.now().year
