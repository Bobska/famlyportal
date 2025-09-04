"""
Views for coming soon pages and app status management
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from core.utils.app_status import (
    get_app_config,
    is_app_active,
    get_app_features,
    get_app_eta
)


@login_required
def coming_soon(request, app_name):
    """
    Display coming soon page for inactive apps
    
    Args:
        request: HTTP request object
        app_name: Name of the app to display
        
    Returns:
        Rendered coming soon template
    """
    # Get app configuration
    app_config = get_app_config(app_name)
    if not app_config:
        messages.error(request, f"App '{app_name}' not found.")
        return redirect('accounts:dashboard')
    
    # If app is active, redirect to app dashboard
    if is_app_active(app_name):
        try:
            return redirect(f'{app_name}:dashboard')
        except:
            # If URL doesn't exist, fall through to coming soon page
            pass
    
    # Handle notification signup
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # TODO: Implement email notification system
            messages.success(
                request, 
                f"Thanks! We'll notify you at {email} when {app_config['name']} launches."
            )
        else:
            messages.error(request, "Please provide a valid email address.")
    
    context = {
        'app_name': app_name,
        'app_config': app_config,
        'features': get_app_features(app_name),
        'eta': get_app_eta(app_name),
        'page_title': f"{app_config['name']} - Coming Soon"
    }
    
    return render(request, 'coming_soon/app_placeholder.html', context)


@login_required
@require_http_methods(["POST"])
def notify_when_ready(request):
    """
    AJAX endpoint for email notification signup
    
    Returns:
        JSON response with success/error status
    """
    app_name = request.POST.get('app_name')
    email = request.POST.get('email')
    
    if not app_name or not email:
        return JsonResponse({
            'success': False,
            'message': 'App name and email are required.'
        })
    
    app_config = get_app_config(app_name)
    if not app_config:
        return JsonResponse({
            'success': False,
            'message': 'Invalid app name.'
        })
    
    # TODO: Implement email notification system
    # For now, just return success
    
    return JsonResponse({
        'success': True,
        'message': f"We'll notify you when {app_config['name']} is ready!"
    })


def app_status_api(request, app_name):
    """
    API endpoint to get app status information
    
    Args:
        request: HTTP request object
        app_name: Name of the app to check
        
    Returns:
        JSON response with app status
    """
    app_config = get_app_config(app_name)
    if not app_config:
        return JsonResponse({'error': 'App not found'}, status=404)
    
    return JsonResponse({
        'app_name': app_name,
        'name': app_config['name'],
        'active': app_config['active'],
        'status': app_config['status'],
        'description': app_config['description'],
        'icon': app_config['icon'],
        'color': app_config['color'],
        'eta': get_app_eta(app_name),
        'features': get_app_features(app_name)
    })


def all_apps_status_api(request):
    """
    API endpoint to get status of all apps
    
    Returns:
        JSON response with all app statuses
    """
    from core.utils.app_status import get_all_apps
    
    apps = get_all_apps()
    app_statuses = {}
    
    for app_name, config in apps.items():
        app_statuses[app_name] = {
            'name': config['name'],
            'active': config['active'],
            'status': config['status'],
            'description': config['description'],
            'icon': config['icon'],
            'color': config['color'],
            'order': config['order'],
            'eta': get_app_eta(app_name),
            'features': get_app_features(app_name)
        }
    
    return JsonResponse({'apps': app_statuses})
