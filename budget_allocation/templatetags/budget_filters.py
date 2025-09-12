from django import template

register = template.Library()

@register.filter
def order_by_children_count(queryset):
    """
    Custom template filter to order accounts by number of children (descending), then by name.
    """
    if not queryset:
        return queryset
    
    # Convert QuerySet to list and sort by children count (descending), then by name
    accounts_list = list(queryset)
    
    def get_children_count(account):
        """Get count of active children for an account"""
        return account.children.filter(is_active=True).count()
    
    # Sort by children count (descending), then by name (ascending)
    accounts_list.sort(key=lambda account: (-get_children_count(account), account.name.lower()))
    
    return accounts_list

@register.filter
def active_children_ordered(account):
    """
    Get active children of an account ordered by children count (descending), then by name.
    """
    active_children = account.children.filter(is_active=True)
    return order_by_children_count(active_children)