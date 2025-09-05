"""
Django template filters for form field manipulation
"""

from django import template
from django.forms import BoundField
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def add_class(field, css_class):
    """
    Add CSS class(es) to a form field widget.
    
    Usage in templates:
    {{ form.field|add_class:"form-control" }}
    {{ form.field|add_class:"form-control is-invalid" }}
    """
    if isinstance(field, BoundField):
        # Get the widget and copy its attributes
        widget = field.field.widget
        attrs = widget.attrs.copy() if hasattr(widget, 'attrs') else {}
        
        # Add or append the CSS class
        existing_classes = attrs.get('class', '')
        if existing_classes:
            attrs['class'] = f"{existing_classes} {css_class}"
        else:
            attrs['class'] = css_class
        
        # Create new widget with updated attributes
        widget.attrs = attrs
        return field
    
    return field


@register.filter
def add_attr(field, attr_value):
    """
    Add an attribute to a form field widget.
    
    Usage in templates:
    {{ form.field|add_attr:"placeholder:Enter your name" }}
    {{ form.field|add_attr:"data-toggle:tooltip" }}
    """
    if isinstance(field, BoundField) and ':' in attr_value:
        attr_name, attr_val = attr_value.split(':', 1)
        widget = field.field.widget
        attrs = widget.attrs.copy() if hasattr(widget, 'attrs') else {}
        attrs[attr_name] = attr_val
        widget.attrs = attrs
        return field
    
    return field


@register.filter
def field_type(field):
    """
    Get the widget type of a form field.
    
    Usage in templates:
    {% if form.field|field_type == "EmailInput" %}
        <i class="fas fa-envelope"></i>
    {% endif %}
    """
    if isinstance(field, BoundField):
        widget = field.field.widget
        return type(widget).__name__
    return ""


@register.filter
def has_error(field):
    """
    Check if a form field has errors.
    
    Usage in templates:
    {% if form.field|has_error %}
        <div class="error">{{ form.field.errors }}</div>
    {% endif %}
    """
    if isinstance(field, BoundField):
        return bool(field.errors)
    return False
