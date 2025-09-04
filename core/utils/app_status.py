"""
App Status Management for FamlyPortal

This module provides utilities for managing app status and availability
across the FamlyPortal platform. It handles active/inactive states,
coming soon indicators, and maintenance mode.
"""

from typing import Dict, Any, Optional
from django.utils import timezone
from datetime import datetime

# Configuration for app status and availability
APP_STATUS_CONFIG = {
    'timesheet': {
        'active': True,
        'status': 'complete',
        'name': 'Time Tracking',
        'description': 'Track work hours and manage projects',
        'icon': 'bi-clock',
        'color': '#007bff',
        'order': 1,
        'features': [
            'Time entry tracking',
            'Project management',
            'Reporting and analytics',
            'Timer functionality'
        ]
    },
    'household_budget': {
        'active': True,
        'status': 'complete',
        'name': 'Household Budget',
        'description': 'Manage family finances and track expenses',
        'icon': 'bi-piggy-bank',
        'color': '#28a745',
        'order': 2,
        'features': [
            'Budget tracking',
            'Expense categorization',
            'Savings goals',
            'Financial reports'
        ]
    },
    'daycare_invoices': {
        'active': False,
        'status': 'coming_soon',
        'name': 'Daycare Invoices',
        'description': 'Track daycare expenses and invoices',
        'icon': 'bi-building',
        'color': '#fd7e14',
        'order': 3,
        'eta': 'Q4 2025',
        'features': [
            'Invoice management',
            'Provider tracking',
            'Payment history',
            'Child enrollment'
        ]
    },
    'employment_history': {
        'active': False,
        'status': 'coming_soon',
        'name': 'Employment History',
        'description': 'Manage career history and skills',
        'icon': 'bi-briefcase',
        'color': '#6f42c1',
        'order': 4,
        'eta': 'Q1 2026',
        'features': [
            'Position tracking',
            'Skills management',
            'Company profiles',
            'Career timeline'
        ]
    },
    'upcoming_payments': {
        'active': False,
        'status': 'coming_soon',
        'name': 'Upcoming Payments',
        'description': 'Track and schedule recurring payments',
        'icon': 'bi-calendar-check',
        'color': '#dc3545',
        'order': 5,
        'eta': 'Q1 2026',
        'features': [
            'Payment scheduling',
            'Recurring payments',
            'Payment reminders',
            'Category management'
        ]
    },
    'credit_cards': {
        'active': False,
        'status': 'coming_soon',
        'name': 'Credit Cards',
        'description': 'Manage credit cards and payments',
        'icon': 'bi-credit-card',
        'color': '#343a40',
        'order': 6,
        'eta': 'Q2 2026',
        'features': [
            'Card management',
            'Transaction tracking',
            'Payment scheduling',
            'Balance monitoring'
        ]
    },
    'autocraftcv': {
        'active': False,
        'status': 'coming_soon',
        'name': 'AutoCraftCV',
        'description': 'AI-powered CV and cover letter generation',
        'icon': 'bi-file-text',
        'color': '#20c997',
        'order': 7,
        'eta': 'Q2 2026',
        'features': [
            'AI CV generation',
            'Job matching',
            'Cover letters',
            'Template library'
        ]
    },
    'subscription_tracker': {
        'active': False,
        'status': 'coming_soon',
        'name': 'Subscription Tracker',
        'description': 'Track and manage subscriptions',
        'icon': 'bi-arrow-repeat',
        'color': '#e83e8c',
        'order': 8,
        'eta': 'Q3 2026',
        'features': [
            'Subscription tracking',
            'Renewal alerts',
            'Cost analysis',
            'Cancellation management'
        ]
    }
}

# Status messages for user display
STATUS_MESSAGES = {
    'active': 'Available',
    'complete': 'Available',
    'coming_soon': 'Coming Soon',
    'development': 'In Development',
    'beta': 'Beta Testing',
    'maintenance': 'Under Maintenance',
    'disabled': 'Temporarily Disabled'
}

# CSS classes for status styling
STATUS_CLASSES = {
    'active': 'text-success',
    'complete': 'text-success',
    'coming_soon': 'text-secondary',
    'development': 'text-info',
    'beta': 'text-warning',
    'maintenance': 'text-warning',
    'disabled': 'text-danger'
}


def get_app_config(app_name: str) -> Optional[Dict[str, Any]]:
    """
    Get complete configuration for a specific app
    
    Args:
        app_name: The name of the app to get config for
        
    Returns:
        Dictionary containing app configuration or None if not found
    """
    return APP_STATUS_CONFIG.get(app_name)


def get_app_status(app_name: str) -> str:
    """
    Get the current status of an app
    
    Args:
        app_name: The name of the app to check
        
    Returns:
        Status string (active, coming_soon, maintenance, etc.)
    """
    config = get_app_config(app_name)
    if not config:
        return 'unknown'
    return config.get('status', 'unknown')


def is_app_active(app_name: str) -> bool:
    """
    Check if an app is currently active and accessible
    
    Args:
        app_name: The name of the app to check
        
    Returns:
        True if app is active, False otherwise
    """
    config = get_app_config(app_name)
    if not config:
        return False
    return config.get('active', False)


def get_app_status_message(app_name: str) -> str:
    """
    Get user-friendly status message for an app
    
    Args:
        app_name: The name of the app
        
    Returns:
        Human-readable status message
    """
    status = get_app_status(app_name)
    return STATUS_MESSAGES.get(status, 'Unknown')


def get_app_status_class(app_name: str) -> str:
    """
    Get CSS classes for styling app status
    
    Args:
        app_name: The name of the app
        
    Returns:
        CSS classes for status styling
    """
    status = get_app_status(app_name)
    return STATUS_CLASSES.get(status, 'text-muted')


def get_all_apps() -> Dict[str, Dict[str, Any]]:
    """
    Get configuration for all apps, sorted by order
    
    Returns:
        Dictionary of all app configurations
    """
    return dict(sorted(
        APP_STATUS_CONFIG.items(),
        key=lambda item: item[1].get('order', 999)
    ))


def get_active_apps() -> Dict[str, Dict[str, Any]]:
    """
    Get only active apps
    
    Returns:
        Dictionary of active app configurations
    """
    return {
        name: config for name, config in get_all_apps().items()
        if config.get('active', False)
    }


def get_inactive_apps() -> Dict[str, Dict[str, Any]]:
    """
    Get only inactive apps
    
    Returns:
        Dictionary of inactive app configurations
    """
    return {
        name: config for name, config in get_all_apps().items()
        if not config.get('active', False)
    }


def get_app_navigation_config(app_name: str) -> Optional[Dict[str, Any]]:
    """
    Get navigation configuration for a specific app
    
    Args:
        app_name: The name of the app
        
    Returns:
        Navigation configuration dictionary or None
    """
    # Navigation configurations for each app
    nav_configs = {
        'timesheet': {
            'items': [
                {'name': 'Dashboard', 'url': 'timesheet:dashboard', 'icon': 'bi-house'},
                {'name': 'Time Entries', 'url': 'timesheet:entry_list', 'icon': 'bi-clock'},
                {'name': 'Projects', 'url': 'timesheet:job_list', 'icon': 'bi-folder'},
                {'name': 'Reports', 'url': 'timesheet:reports', 'icon': 'bi-bar-chart'},
                {'name': 'Settings', 'url': 'timesheet:settings', 'icon': 'bi-gear'}
            ]
        },
        'household_budget': {
            'items': [
                {'name': 'Dashboard', 'url': 'household_budget:dashboard', 'icon': 'bi-house'},
                {'name': 'Budget Overview', 'url': 'household_budget:budget_overview', 'icon': 'bi-pie-chart'},
                {'name': 'Transactions', 'url': 'household_budget:transaction_list', 'icon': 'bi-list-ul'},
                {'name': 'Categories', 'url': 'household_budget:category_management', 'icon': 'bi-tags'},
                {'name': 'Savings Goals', 'url': 'household_budget:savings_goals', 'icon': 'bi-target'},
                {'name': 'Reports', 'url': 'household_budget:reports', 'icon': 'bi-bar-chart'}
            ]
        },
        'daycare_invoices': {
            'items': [
                {'name': 'Dashboard', 'url': 'daycare_invoices:dashboard', 'icon': 'bi-house'},
                {'name': 'Invoices', 'url': 'daycare_invoices:invoice_list', 'icon': 'bi-file-text'},
                {'name': 'Providers', 'url': 'daycare_invoices:provider_list', 'icon': 'bi-building'},
                {'name': 'Children', 'url': 'daycare_invoices:child_list', 'icon': 'bi-people'},
                {'name': 'Payments', 'url': 'daycare_invoices:payment_list', 'icon': 'bi-credit-card'}
            ]
        },
        'employment_history': {
            'items': [
                {'name': 'Dashboard', 'url': 'employment_history:dashboard', 'icon': 'bi-house'},
                {'name': 'Positions', 'url': 'employment_history:position_list', 'icon': 'bi-briefcase'},
                {'name': 'Companies', 'url': 'employment_history:company_list', 'icon': 'bi-building'},
                {'name': 'Skills', 'url': 'employment_history:skill_list', 'icon': 'bi-award'},
                {'name': 'Education', 'url': 'employment_history:education_list', 'icon': 'bi-book'}
            ]
        },
        'upcoming_payments': {
            'items': [
                {'name': 'Dashboard', 'url': 'upcoming_payments:dashboard', 'icon': 'bi-house'},
                {'name': 'Schedule', 'url': 'upcoming_payments:schedule', 'icon': 'bi-calendar'},
                {'name': 'Recurring', 'url': 'upcoming_payments:recurring', 'icon': 'bi-arrow-repeat'},
                {'name': 'Categories', 'url': 'upcoming_payments:category_list', 'icon': 'bi-tags'}
            ]
        },
        'credit_cards': {
            'items': [
                {'name': 'Dashboard', 'url': 'credit_cards:dashboard', 'icon': 'bi-house'},
                {'name': 'Cards', 'url': 'credit_cards:card_list', 'icon': 'bi-credit-card'},
                {'name': 'Transactions', 'url': 'credit_cards:transaction_list', 'icon': 'bi-list-ul'},
                {'name': 'Payments', 'url': 'credit_cards:payment_list', 'icon': 'bi-currency-dollar'}
            ]
        },
        'autocraftcv': {
            'items': [
                {'name': 'Dashboard', 'url': 'autocraftcv:dashboard', 'icon': 'bi-house'},
                {'name': 'Job Search', 'url': 'autocraftcv:job_search', 'icon': 'bi-search'},
                {'name': 'CV Templates', 'url': 'autocraftcv:template_list', 'icon': 'bi-file-text'},
                {'name': 'Generated CVs', 'url': 'autocraftcv:cv_list', 'icon': 'bi-download'},
                {'name': 'Cover Letters', 'url': 'autocraftcv:cover_letter_list', 'icon': 'bi-envelope'}
            ]
        },
        'subscription_tracker': {
            'items': [
                {'name': 'Dashboard', 'url': 'subscription_tracker:dashboard', 'icon': 'bi-house'},
                {'name': 'Subscriptions', 'url': 'subscription_tracker:subscription_list', 'icon': 'bi-check-circle'},
                {'name': 'Categories', 'url': 'subscription_tracker:category_list', 'icon': 'bi-tags'},
                {'name': 'Calendar', 'url': 'subscription_tracker:calendar', 'icon': 'bi-calendar'},
                {'name': 'Analytics', 'url': 'subscription_tracker:analytics', 'icon': 'bi-graph-up'}
            ]
        }
    }
    
    return nav_configs.get(app_name)


def update_app_status(app_name: str, status: str, active: Optional[bool] = None) -> bool:
    """
    Update the status of an app (for admin/management use)
    
    Args:
        app_name: The name of the app to update
        status: New status for the app
        active: Whether the app should be active (optional)
        
    Returns:
        True if update was successful, False otherwise
    """
    if app_name not in APP_STATUS_CONFIG:
        return False
    
    APP_STATUS_CONFIG[app_name]['status'] = status
    if active is not None:
        APP_STATUS_CONFIG[app_name]['active'] = active
        
    # In a real implementation, this would save to database
    # For now, we're using in-memory configuration
    
    return True


def get_app_eta(app_name: str) -> Optional[str]:
    """
    Get estimated time of arrival (release date) for an app
    
    Args:
        app_name: The name of the app
        
    Returns:
        ETA string or None if not available
    """
    config = get_app_config(app_name)
    if not config:
        return None
    return config.get('eta')


def get_app_features(app_name: str) -> list:
    """
    Get list of features for an app
    
    Args:
        app_name: The name of the app
        
    Returns:
        List of feature descriptions
    """
    config = get_app_config(app_name)
    if not config:
        return []
    return config.get('features', [])
