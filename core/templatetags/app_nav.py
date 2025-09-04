"""
Template tags for app-specific navigation

These template tags provide dynamic navigation functionality
for individual apps within the FamlyPortal platform.
"""

from django import template
from django.urls import reverse, NoReverseMatch
from django.http import Http404
from core.utils.app_status import (
    get_app_navigation_config,
    is_app_active,
    get_app_config
)

register = template.Library()


@register.inclusion_tag('components/app_nav.html', takes_context=True)
def app_navigation(context, app_name):
    """
    Generate secondary navigation for specific app
    
    Usage:
        {% load app_nav %}
        {% app_navigation 'timesheet' %}
    """
    request = context.get('request')
    if not request:
        return {}
    
    # Check if app is active
    if not is_app_active(app_name):
        return {}
    
    # Get navigation configuration
    nav_config = get_app_navigation_config(app_name)
    if not nav_config:
        return {}
    
    # Get app configuration for styling
    app_config = get_app_config(app_name)
    
    # Build navigation items with URL resolution and active state
    nav_items = []
    current_url_name = None
    
    # Try to get the current URL name
    if hasattr(request, 'resolver_match') and request.resolver_match:
        current_url_name = request.resolver_match.url_name
        current_namespace = getattr(request.resolver_match, 'namespace', '')
        if current_namespace:
            current_url_name = f"{current_namespace}:{current_url_name}"
    
    for item in nav_config.get('items', []):
        nav_item = {
            'name': item['name'],
            'icon': item['icon'],
            'url': '#',  # Default fallback
            'active': False
        }
        
        # Try to resolve URL
        try:
            nav_item['url'] = reverse(item['url'])
        except NoReverseMatch:
            # URL doesn't exist yet, keep as placeholder
            nav_item['url'] = '#'
            nav_item['disabled'] = True
        
        # Check if this is the active navigation item
        if current_url_name and item['url'] == current_url_name:
            nav_item['active'] = True
        
        nav_items.append(nav_item)
    
    return {
        'app_name': app_name,
        'app_config': app_config,
        'nav_items': nav_items,
        'current_url': request.path if request else ''
    }


@register.simple_tag(takes_context=True)
def is_active_nav(context, url_name, app_name=None):
    """
    Check if current navigation item is active
    
    Usage:
        {% is_active_nav 'timesheet:dashboard' 'timesheet' as is_active %}
        <li class="{% if is_active %}active{% endif %}">
    """
    request = context.get('request')
    if not request or not hasattr(request, 'resolver_match'):
        return False
    
    resolver_match = request.resolver_match
    if not resolver_match:
        return False
    
    current_url_name = resolver_match.url_name
    current_namespace = getattr(resolver_match, 'namespace', '')
    
    # Build full URL name
    if current_namespace:
        full_current_name = f"{current_namespace}:{current_url_name}"
    else:
        full_current_name = current_url_name
    
    # Check exact match
    if url_name == full_current_name:
        return True
    
    # Check namespace match for app-level navigation
    if app_name and current_namespace == app_name:
        return True
    
    return False


@register.simple_tag
def get_app_nav_config(app_name):
    """
    Get navigation configuration for specific app
    
    Usage:
        {% get_app_nav_config 'timesheet' as nav_config %}
        {% for item in nav_config.items %}...{% endfor %}
    """
    return get_app_navigation_config(app_name)


@register.simple_tag(takes_context=True)
def current_app_name(context):
    """
    Get the current app name based on URL namespace
    
    Usage:
        {% current_app_name as app_name %}
        {% if app_name %}App: {{ app_name }}{% endif %}
    """
    request = context.get('request')
    if not request or not hasattr(request, 'resolver_match'):
        return None
    
    resolver_match = request.resolver_match
    if not resolver_match:
        return None
    
    return getattr(resolver_match, 'namespace', None)


@register.inclusion_tag('components/app_breadcrumb.html', takes_context=True)
def app_breadcrumb(context, app_name, page_title=None):
    """
    Generate breadcrumb navigation for app pages
    
    Usage:
        {% app_breadcrumb 'timesheet' 'Dashboard' %}
        {% app_breadcrumb 'household_budget' %}
    """
    request = context.get('request')
    app_config = get_app_config(app_name)
    
    breadcrumbs = [
        {'name': 'Home', 'url': reverse('accounts:dashboard')},
    ]
    
    if app_config:
        # Add app home
        try:
            app_url = reverse(f"{app_name}:dashboard")
        except NoReverseMatch:
            app_url = '#'
        
        breadcrumbs.append({
            'name': app_config.get('name', app_name.replace('_', ' ').title()),
            'url': app_url,
            'icon': app_config.get('icon', '')
        })
    
    # Add current page if specified
    if page_title:
        breadcrumbs.append({
            'name': page_title,
            'url': request.path if request else '#',
            'active': 'true'
        })
    
    return {
        'breadcrumbs': breadcrumbs,
        'app_config': app_config
    }


@register.filter
def nav_url_exists(url_name):
    """
    Check if a URL name exists and can be reversed
    
    Usage:
        {% if 'timesheet:reports'|nav_url_exists %}
            <a href="{% url 'timesheet:reports' %}">Reports</a>
        {% else %}
            <span class="text-muted">Reports (Coming Soon)</span>
        {% endif %}
    """
    try:
        reverse(url_name)
        return True
    except NoReverseMatch:
        return False


@register.simple_tag
def nav_url_safe(url_name, fallback='#'):
    """
    Safely reverse a URL, returning fallback if URL doesn't exist
    
    Usage:
        <a href="{% nav_url_safe 'timesheet:reports' %}">Reports</a>
    """
    try:
        return reverse(url_name)
    except NoReverseMatch:
        return fallback


@register.inclusion_tag('components/mobile_app_nav.html', takes_context=True)
def mobile_app_navigation(context, app_name):
    """
    Generate mobile-optimized navigation for specific app
    
    Usage:
        {% mobile_app_navigation 'timesheet' %}
    """
    request = context.get('request')
    if not request:
        return {}
    
    # Check if app is active
    if not is_app_active(app_name):
        return {}
    
    # Get navigation configuration
    nav_config = get_app_navigation_config(app_name)
    if not nav_config:
        return {}
    
    # Get app configuration
    app_config = get_app_config(app_name)
    
    # Get current URL for active state
    current_url_name = None
    if hasattr(request, 'resolver_match') and request.resolver_match:
        current_url_name = request.resolver_match.url_name
        current_namespace = getattr(request.resolver_match, 'namespace', '')
        if current_namespace:
            current_url_name = f"{current_namespace}:{current_url_name}"
    
    # Build mobile navigation items
    nav_items = []
    for item in nav_config.get('items', []):
        nav_item = {
            'name': item['name'],
            'icon': item['icon'],
            'url': '#',
            'active': False
        }
        
        # Try to resolve URL
        try:
            nav_item['url'] = reverse(item['url'])
        except NoReverseMatch:
            nav_item['url'] = '#'
            nav_item['disabled'] = True
        
        # Check active state
        if current_url_name and item['url'] == current_url_name:
            nav_item['active'] = True
        
        nav_items.append(nav_item)
    
    return {
        'app_name': app_name,
        'app_config': app_config,
        'nav_items': nav_items,
        'current_url': request.path if request else ''
    }
