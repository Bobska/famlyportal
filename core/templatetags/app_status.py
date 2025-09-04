"""
Template tags for app status management

These template tags provide easy access to app status information
within Django templates, allowing for dynamic display of app
availability and status indicators.
"""

from django import template
from django.urls import reverse, NoReverseMatch
from core.utils.app_status import (
    get_app_status,
    get_app_status_message,
    get_app_status_class,
    is_app_active,
    get_app_config,
    get_all_apps,
    get_active_apps,
    get_inactive_apps,
    get_app_eta,
    get_app_features
)

register = template.Library()


@register.simple_tag
def app_status(app_name):
    """
    Get app status (active, coming_soon, maintenance, etc.)
    
    Usage:
        {% app_status 'timesheet' %}
    """
    return get_app_status(app_name)


@register.simple_tag
def app_status_message(app_name):
    """
    Get user-friendly status message for an app
    
    Usage:
        {% app_status_message 'timesheet' %}
    """
    return get_app_status_message(app_name)


@register.simple_tag
def app_status_class(app_name):
    """
    Get CSS classes for app status styling
    
    Usage:
        <span class="{% app_status_class 'timesheet' %}">Status</span>
    """
    return get_app_status_class(app_name)


@register.simple_tag
def is_app_available(app_name):
    """
    Check if an app is currently active and accessible
    
    Usage:
        {% is_app_available 'timesheet' as timesheet_available %}
        {% if timesheet_available %}...{% endif %}
    """
    return is_app_active(app_name)


@register.simple_tag
def app_config(app_name):
    """
    Get complete configuration for a specific app
    
    Usage:
        {% app_config 'timesheet' as timesheet_config %}
        {{ timesheet_config.name }}
    """
    return get_app_config(app_name)


@register.simple_tag
def app_icon(app_name):
    """
    Get Bootstrap icon class for an app
    
    Usage:
        <i class="{% app_icon 'timesheet' %}"></i>
    """
    config = get_app_config(app_name)
    if config:
        return config.get('icon', 'bi-app')
    return 'bi-app'


@register.simple_tag
def app_color(app_name):
    """
    Get app-specific color code
    
    Usage:
        <div style="color: {% app_color 'timesheet' %}">Content</div>
    """
    config = get_app_config(app_name)
    if config:
        return config.get('color', '#6c757d')
    return '#6c757d'


@register.simple_tag
def app_name(app_name):
    """
    Get display name for an app
    
    Usage:
        {% app_name 'timesheet' %}
    """
    config = get_app_config(app_name)
    if config:
        return config.get('name', app_name.replace('_', ' ').title())
    return app_name.replace('_', ' ').title()


@register.simple_tag
def app_description(app_name):
    """
    Get description for an app
    
    Usage:
        {% app_description 'timesheet' %}
    """
    config = get_app_config(app_name)
    if config:
        return config.get('description', '')
    return ''


@register.simple_tag
def app_eta(app_name):
    """
    Get estimated release date for an app
    
    Usage:
        {% app_eta 'daycare_invoices' %}
    """
    return get_app_eta(app_name)


@register.simple_tag
def app_features(app_name):
    """
    Get list of features for an app
    
    Usage:
        {% app_features 'timesheet' as features %}
        {% for feature in features %}...{% endfor %}
    """
    return get_app_features(app_name)


@register.simple_tag
def all_apps():
    """
    Get all app configurations
    
    Usage:
        {% all_apps as apps %}
        {% for app_name, config in apps.items %}...{% endfor %}
    """
    return get_all_apps()


@register.simple_tag
def active_apps():
    """
    Get only active app configurations
    
    Usage:
        {% active_apps as apps %}
        {% for app_name, config in apps.items %}...{% endfor %}
    """
    return get_active_apps()


@register.simple_tag
def inactive_apps():
    """
    Get only inactive app configurations
    
    Usage:
        {% inactive_apps as apps %}
        {% for app_name, config in apps.items %}...{% endfor %}
    """
    return get_inactive_apps()


@register.filter
def app_badge_class(status):
    """
    Get Bootstrap badge class for app status
    
    Usage:
        <span class="badge {% app_status 'timesheet'|app_badge_class %}">
    """
    badge_classes = {
        'active': 'bg-success',
        'complete': 'bg-success',
        'coming_soon': 'bg-secondary',
        'development': 'bg-info',
        'beta': 'bg-warning',
        'maintenance': 'bg-warning text-dark',
        'disabled': 'bg-danger'
    }
    return badge_classes.get(status, 'bg-secondary')


@register.filter
def can_access_app(app_name):
    """
    Check if user can access an app (for template conditions)
    
    Usage:
        {% if 'timesheet'|can_access_app %}...{% endif %}
    """
    return is_app_active(app_name)


@register.inclusion_tag('components/app_status_badge.html')
def app_status_badge(app_name, show_text=True):
    """
    Render app status badge component
    
    Usage:
        {% app_status_badge 'timesheet' %}
        {% app_status_badge 'daycare_invoices' show_text=False %}
    """
    return {
        'app_name': app_name,
        'status': get_app_status(app_name),
        'message': get_app_status_message(app_name),
        'class': get_app_status_class(app_name),
        'badge_class': app_badge_class(get_app_status(app_name)),
        'show_text': show_text
    }


@register.inclusion_tag('components/app_card.html')
def app_card(app_name, show_features=True, compact=False):
    """
    Render app information card
    
    Usage:
        {% app_card 'timesheet' %}
        {% app_card 'daycare_invoices' show_features=False compact=True %}
    """
    config = get_app_config(app_name)
    if not config:
        return {}
    
    return {
        'app_name': app_name,
        'config': config,
        'features': get_app_features(app_name) if show_features else [],
        'compact': compact,
        'active': is_app_active(app_name),
        'status': get_app_status(app_name),
        'eta': get_app_eta(app_name)
    }
