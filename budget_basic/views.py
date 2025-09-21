from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from datetime import datetime, date
from django.db.models import Sum
from .models import Income, Expense


@login_required
def dashboard(request):
    """Budget Basic main dashboard view."""
    context = {
        'page_title': 'Budget Basic',
        'app_name': 'budget_basic',
    }
    return render(request, 'budget_basic/dashboard.html', context)


@login_required
def main(request):
    """Budget Basic main transactions view."""
    # Get current month and year
    current_month = date.today().month
    current_year = date.today().year
    
    # Get income and expense entries for the current user
    income_entries = Income.objects.filter(user=request.user).order_by('-date', '-created_at')
    expense_entries = Expense.objects.filter(user=request.user).order_by('-date', '-created_at')
    
    # Calculate monthly totals for current month
    monthly_income = Income.objects.filter(
        user=request.user,
        date__month=current_month,
        date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    monthly_expenses = Expense.objects.filter(
        user=request.user,
        date__month=current_month,
        date__year=current_year
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Calculate balance
    monthly_balance = monthly_income - monthly_expenses
    
    context = {
        'page_title': 'Transactions',
        'app_name': 'budget_basic',
        'income_entries': income_entries,
        'expense_entries': expense_entries,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_balance,
    }
    return render(request, 'budget_basic/main.html', context)


@login_required
@require_POST
def add_income(request):
    """Add new income entry via AJAX."""
    try:
        # Get form data
        date_str = request.POST.get('date')
        payee = request.POST.get('payee', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validate required fields
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date is required'})
        
        if not payee:
            return JsonResponse({'success': False, 'error': 'Payee is required'})
        
        if not amount_str:
            return JsonResponse({'success': False, 'error': 'Amount is required'})
        
        # Parse date
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})
        
        # Parse amount
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Amount must be positive'})
        except (ValueError, InvalidOperation):
            return JsonResponse({'success': False, 'error': 'Invalid amount format'})
        
        # Create income entry
        income = Income.objects.create(
            user=request.user,
            date=date,
            payee=payee,
            amount=amount,
            notes=notes
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Income of ${amount} from {payee} added successfully',
            'income_id': income.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
@require_POST
def edit_income(request, income_id):
    """Edit existing income entry via AJAX."""
    try:
        # Get the income entry and verify ownership
        try:
            income = Income.objects.get(id=income_id, user=request.user)
        except Income.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Income entry not found or access denied'})
        
        # Get form data
        date_str = request.POST.get('date')
        payee = request.POST.get('payee', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validate required fields
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date is required'})
        
        if not payee:
            return JsonResponse({'success': False, 'error': 'Payee is required'})
        
        if not amount_str:
            return JsonResponse({'success': False, 'error': 'Amount is required'})
        
        # Parse date
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})
        
        # Parse amount
        try:
            amount = Decimal(amount_str)
            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Amount must be positive'})
        except (ValueError, InvalidOperation):
            return JsonResponse({'success': False, 'error': 'Invalid amount format'})
        
        # Update income entry
        income.date = date
        income.payee = payee
        income.amount = amount
        income.notes = notes
        income.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Income entry updated successfully: ${amount} from {payee}',
            'income_id': income.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
def get_income(request, income_id):
    """Get income entry data for editing via AJAX."""
    try:
        # Get the income entry and verify ownership
        try:
            income = Income.objects.get(id=income_id, user=request.user)
        except Income.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Income entry not found or access denied'})
        
        return JsonResponse({
            'success': True,
            'income': {
                'id': income.id,
                'date': income.date.strftime('%Y-%m-%d'),
                'payee': income.payee,
                'amount': str(income.amount),
                'notes': income.notes or ''
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
@require_POST
def delete_income(request, income_id):
    """Delete income entry via AJAX."""
    try:
        # Get the income entry and verify ownership
        try:
            income = Income.objects.get(id=income_id, user=request.user)
        except Income.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Income entry not found or access denied'})
        
        # Store details for success message before deletion
        payee = income.payee
        amount = income.amount
        
        # Delete the income entry
        income.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Income entry deleted successfully: ${amount} from {payee}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


# ===== EXPENSE VIEWS =====

@login_required
@require_POST
def add_expense(request):
    """Add new expense entry via AJAX."""
    try:
        # Get form data
        date_str = request.POST.get('date')
        payee = request.POST.get('payee', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validate required fields
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date is required'})
        
        if not payee:
            return JsonResponse({'success': False, 'error': 'Payee is required'})
        
        if not amount_str:
            return JsonResponse({'success': False, 'error': 'Amount is required'})
        
        # Parse date
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})
        
        # Parse amount - remove commas first
        try:
            amount_clean = amount_str.replace(',', '')
            amount = Decimal(amount_clean)
            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Amount must be positive'})
        except (ValueError, InvalidOperation):
            return JsonResponse({'success': False, 'error': 'Invalid amount format'})
        
        # Create expense entry
        expense = Expense.objects.create(
            user=request.user,
            date=date,
            payee=payee,
            amount=amount,
            notes=notes
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Expense of ${amount} to {payee} added successfully',
            'expense_id': expense.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
@require_POST
def edit_expense(request, expense_id):
    """Edit existing expense entry via AJAX."""
    try:
        # Get the expense entry and verify ownership
        try:
            expense = Expense.objects.get(id=expense_id, user=request.user)
        except Expense.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Expense entry not found or access denied'})
        
        # Get form data
        date_str = request.POST.get('date')
        payee = request.POST.get('payee', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validate required fields
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date is required'})
        
        if not payee:
            return JsonResponse({'success': False, 'error': 'Payee is required'})
        
        if not amount_str:
            return JsonResponse({'success': False, 'error': 'Amount is required'})
        
        # Parse date
        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({'success': False, 'error': 'Invalid date format'})
        
        # Parse amount
        try:
            amount_clean = amount_str.replace(',', '')
            amount = Decimal(amount_clean)
            if amount <= 0:
                return JsonResponse({'success': False, 'error': 'Amount must be positive'})
        except (ValueError, InvalidOperation):
            return JsonResponse({'success': False, 'error': 'Invalid amount format'})
        
        # Update expense entry
        expense.date = date
        expense.payee = payee
        expense.amount = amount
        expense.notes = notes
        expense.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Expense entry updated successfully: ${amount} to {payee}',
            'expense_id': expense.id
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
def get_expense(request, expense_id):
    """Get expense entry data for editing via AJAX."""
    try:
        # Get the expense entry and verify ownership
        try:
            expense = Expense.objects.get(id=expense_id, user=request.user)
        except Expense.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Expense entry not found or access denied'})
        
        return JsonResponse({
            'success': True,
            'expense': {
                'id': expense.id,
                'date': expense.date.strftime('%Y-%m-%d'),
                'payee': expense.payee,
                'amount': str(expense.amount),
                'notes': expense.notes or ''
            }
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
@require_POST
def delete_expense(request, expense_id):
    """Delete expense entry via AJAX."""
    try:
        # Get the expense entry and verify ownership
        try:
            expense = Expense.objects.get(id=expense_id, user=request.user)
        except Expense.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Expense entry not found or access denied'})
        
        # Store details for success message before deletion
        payee = expense.payee
        amount = expense.amount
        
        # Delete the expense entry
        expense.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Expense entry deleted successfully: ${amount} to {payee}'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
