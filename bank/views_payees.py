"""
Payee/Merchant Management Views for Bank App
Handles CRUD operations for payees/merchants
"""
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_http_methods
from django.http import JsonResponse
from django.core.exceptions import ValidationError
from django.db.models import Count, Q
from django.template.loader import render_to_string
from .models import Payee, Category, Income, Expense
import logging

logger = logging.getLogger(__name__)


@login_required
def payee_list(request):
    """Display all payees for the current user."""
    from .views import build_sidebar_summary_context
    
    payees = Payee.objects.filter(user=request.user).prefetch_related('categories')
    context = {
        'payees': payees,
        **build_sidebar_summary_context(request),
    }
    return render(request, 'bank/payees.html', context)


@login_required  
@require_POST
def payee_create(request):
    """Create a new payee via AJAX."""
    try:
        name = request.POST.get('name', '').strip()
        transaction_type = request.POST.get('transaction_type', 'expense').strip()
        category_ids = request.POST.getlist('categories', [])
        
        if not name:
            return JsonResponse({
                'success': False, 
                'error': 'Payee/Merchant name is required.'
            })
        
        # Check for duplicate payee names (case-insensitive)
        if Payee.objects.filter(user=request.user, name__iexact=name).exists():
            return JsonResponse({
                'success': False,
                'error': f'Payee "{name}" already exists.'
            })
        
        # Create new payee
        payee = Payee.objects.create(
            user=request.user,
            name=name,
            transaction_type=transaction_type
        )
        
        # Add categories if provided
        if category_ids:
            categories = Category.objects.filter(
                user=request.user, 
                id__in=category_ids
            )
            payee.categories.set(categories)
        
        return JsonResponse({
            'success': True,
            'message': f'Payee "{name}" created successfully!',
            'payee': {
                'id': payee.id,
                'name': payee.name,
                'transaction_type': payee.transaction_type,
                'transaction_type_display': payee.get_transaction_type_display(),
                'categories_count': payee.categories.count(),
                'categories_display': ', '.join([c.name for c in payee.categories.all()]) or 'None',
                'created_at': payee.created_at.isoformat(),
            }
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': f'Validation error: {e.message}'
        })
    except Exception as e:
        logger.error(f"Error creating payee: {e}")
        return JsonResponse({
            'success': False, 
            'error': f'Error creating payee: {str(e)}'
        })


@login_required
@require_POST  
def payee_update(request, payee_id):
    """Update an existing payee via AJAX."""
    try:
        payee = get_object_or_404(Payee, id=payee_id, user=request.user)
        
        name = request.POST.get('name', '').strip()
        transaction_type = request.POST.get('transaction_type', '').strip()
        category_ids = request.POST.getlist('categories', [])
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Payee name is required.'
            })
        
        # Check for duplicate names (excluding current payee)
        if Payee.objects.filter(
            user=request.user, 
            name__iexact=name
        ).exclude(id=payee_id).exists():
            return JsonResponse({
                'success': False,
                'error': f'Another payee with name "{name}" already exists.'
            })
        
        # Update payee
        payee.name = name
        if transaction_type:
            payee.transaction_type = transaction_type
        payee.save()
        
        # Update categories
        if category_ids:
            categories = Category.objects.filter(
                user=request.user, 
                id__in=category_ids
            )
            payee.categories.set(categories)
        else:
            payee.categories.clear()
        
        return JsonResponse({
            'success': True,
            'message': f'Payee "{name}" updated successfully!',
            'payee': {
                'id': payee.id,
                'name': payee.name,
                'transaction_type': payee.transaction_type,
                'transaction_type_display': payee.get_transaction_type_display(),
                'categories_count': payee.categories.count(),
                'categories_display': ', '.join([c.name for c in payee.categories.all()]) or 'None',
                'updated_at': payee.updated_at.isoformat(),
            }
        })
        
    except Payee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Payee not found.'
        })
    except Exception as e:
        logger.error(f"Error updating payee: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error updating payee: {str(e)}'
        })


@login_required
@require_POST
def payee_delete(request, payee_id):
    """Delete a payee via AJAX."""
    try:
        payee = get_object_or_404(Payee, id=payee_id, user=request.user)
        
        # Check if payee is used in transactions (both income and expense)
        income_count = Income.objects.filter(
            user=request.user,
            payee=payee.name
        ).count()
        
        expense_count = Expense.objects.filter(
            user=request.user,
            payee=payee.name
        ).count()
        
        transaction_count = income_count + expense_count
        
        if transaction_count > 0:
            return JsonResponse({
                'success': False,
                'error': f'Cannot delete payee "{payee.name}" because it is used in {transaction_count} transaction(s). Please reassign or delete those transactions first.'
            })
        
        payee_name = payee.name
        payee.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Payee "{payee_name}" deleted successfully!'
        })
        
    except Payee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Payee not found.'
        })
    except Exception as e:
        logger.error(f"Error deleting payee: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error deleting payee: {str(e)}'
        })


@login_required
def payee_search(request):
    """Search payees by name (AJAX endpoint)."""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'payees': []})
    
    payees = Payee.objects.filter(
        user=request.user,
        name__icontains=query
    ).values('id', 'name', 'transaction_type')[:10]
    
    return JsonResponse({
        'payees': list(payees)
    })
