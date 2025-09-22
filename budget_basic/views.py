from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib import messages
from decimal import Decimal, InvalidOperation
from datetime import datetime, date, timedelta
from django.db.models import Sum, Max
from .models import Income, Expense, Payee


def get_cumulative_balance_up_to_week(user, target_week_offset):
    """Calculate cumulative balance from the beginning of time up to (and including) the target week."""
    # Calculate the end date of the target week
    today = date.today()
    days_since_monday = (today.weekday()) % 7
    current_monday = today - timedelta(days=days_since_monday)
    
    # Calculate target week end date (Sunday)
    target_monday = current_monday + timedelta(weeks=target_week_offset)
    target_sunday = target_monday + timedelta(days=6)
    
    # Get all income and expenses up to and including the target week
    total_income = Income.objects.filter(
        user=user,
        date__lte=target_sunday
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    total_expenses = Expense.objects.filter(
        user=user,
        date__lte=target_sunday
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    return total_income - total_expenses


def get_week_balance_only(user, week_offset):
    """Calculate balance for a specific week only (not cumulative)."""
    # Calculate week start and end dates (Monday to Sunday)
    today = date.today()
    days_since_monday = (today.weekday()) % 7
    current_monday = today - timedelta(days=days_since_monday)
    
    # Calculate target week based on offset
    target_monday = current_monday + timedelta(weeks=week_offset)
    target_sunday = target_monday + timedelta(days=6)
    
    # Get income and expense totals for the specific week
    weekly_income = Income.objects.filter(
        user=user,
        date__gte=target_monday,
        date__lte=target_sunday
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    weekly_expenses = Expense.objects.filter(
        user=user,
        date__gte=target_monday,
        date__lte=target_sunday
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    return weekly_income - weekly_expenses


def get_auto_date_for_week(user, week_offset, transaction_type=None):
    """Get the most recent transaction date in the specified week for the given type, or Monday if no transactions."""
    # Calculate week start and end dates (Monday to Sunday)
    today = date.today()
    days_since_monday = (today.weekday()) % 7
    current_monday = today - timedelta(days=days_since_monday)
    
    # Calculate target week based on offset
    target_monday = current_monday + timedelta(weeks=week_offset)
    target_sunday = target_monday + timedelta(days=6)
    
    most_recent_date = None
    
    if transaction_type == 'income':
        # Get most recent income date only
        most_recent_date = Income.objects.filter(
            user=user,
            date__gte=target_monday,
            date__lte=target_sunday
        ).aggregate(max_date=Max('date'))['max_date']
    elif transaction_type == 'expense':
        # Get most recent expense date only
        most_recent_date = Expense.objects.filter(
            user=user,
            date__gte=target_monday,
            date__lte=target_sunday
        ).aggregate(max_date=Max('date'))['max_date']
    else:
        # Legacy behavior: get most recent from both types (for backward compatibility)
        income_max_date = Income.objects.filter(
            user=user,
            date__gte=target_monday,
            date__lte=target_sunday
        ).aggregate(max_date=Max('date'))['max_date']
        
        expense_max_date = Expense.objects.filter(
            user=user,
            date__gte=target_monday,
            date__lte=target_sunday
        ).aggregate(max_date=Max('date'))['max_date']
        
        # Get the most recent date between income and expense
        if income_max_date and expense_max_date:
            most_recent_date = max(income_max_date, expense_max_date)
        elif income_max_date:
            most_recent_date = income_max_date
        elif expense_max_date:
            most_recent_date = expense_max_date
    
    # Return most recent date if found, otherwise Monday of the week
    return most_recent_date if most_recent_date else target_monday


def get_or_create_payee(user, payee_name):
    """Get or create a payee for the given user."""
    if not payee_name or not payee_name.strip():
        return None
    
    payee_name = payee_name.strip()
    payee, created = Payee.objects.get_or_create(
        user=user,
        name=payee_name
    )
    return payee


@login_required
def dashboard(request):
    """Budget Basic main dashboard view."""
    
    # Calculate total income and expenses for balance
    total_income = Income.objects.filter(user=request.user).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    total_expenses = Expense.objects.filter(user=request.user).aggregate(
        total=Sum('amount')
    )['total'] or Decimal('0.00')
    
    current_balance = total_income - total_expenses
    
    context = {
        'page_title': 'Budget Basic',
        'app_name': 'budget_basic',
        'current_balance': current_balance,
    }
    return render(request, 'budget_basic/dashboard.html', context)


@login_required
def main(request):
    """Budget Basic main transactions view."""
    # Get week offset from request (default to 0 for current week)
    week_offset = int(request.GET.get('week_offset', 0))
    
    # Calculate week start and end dates (Monday to Sunday)
    today = date.today()
    # Get Monday of current week
    days_since_monday = (today.weekday()) % 7
    current_monday = today - timedelta(days=days_since_monday)
    
    # Calculate target week based on offset
    target_monday = current_monday + timedelta(weeks=week_offset)
    target_sunday = target_monday + timedelta(days=6)
    
    # Get income and expense entries for the target week
    income_entries = Income.objects.filter(
        user=request.user,
        date__gte=target_monday,
        date__lte=target_sunday
    ).order_by('-date', '-created_at')
    
    expense_entries = Expense.objects.filter(
        user=request.user,
        date__gte=target_monday,
        date__lte=target_sunday
    ).order_by('-date', '-created_at')
    
    # Calculate weekly totals
    weekly_income = income_entries.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    weekly_expenses = expense_entries.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    weekly_balance = weekly_income - weekly_expenses
    
    # Get current month and year for monthly totals (for sidebar)
    current_month = date.today().month
    current_year = date.today().year
    
    # Calculate monthly totals for sidebar
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
        'weekly_income': weekly_income,
        'weekly_expenses': weekly_expenses,
        'weekly_balance': weekly_balance,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_balance,
        'week_offset': week_offset,
        'target_monday': target_monday,
        'target_sunday': target_sunday,
    }
    return render(request, 'budget_basic/main.html', context)


@login_required
def get_week_data(request):
    """AJAX endpoint to get week data without page reload."""
    # Get week offset from request
    week_offset = int(request.GET.get('week_offset', 0))
    
    # Calculate week start and end dates (Monday to Sunday)
    today = date.today()
    # Get Monday of current week
    days_since_monday = (today.weekday()) % 7
    current_monday = today - timedelta(days=days_since_monday)
    
    # Calculate target week based on offset
    target_monday = current_monday + timedelta(weeks=week_offset)
    target_sunday = target_monday + timedelta(days=6)
    
    # Get income and expense entries for the target week
    income_entries = Income.objects.filter(
        user=request.user,
        date__gte=target_monday,
        date__lte=target_sunday
    ).order_by('-date', '-created_at')
    
    expense_entries = Expense.objects.filter(
        user=request.user,
        date__gte=target_monday,
        date__lte=target_sunday
    ).order_by('-date', '-created_at')
    
    # Calculate weekly totals (current week only)
    weekly_income = income_entries.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    weekly_expenses = expense_entries.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    weekly_balance = weekly_income - weekly_expenses
    
    # Calculate balance carryover data
    previous_week_balance = get_cumulative_balance_up_to_week(request.user, week_offset - 1) if week_offset != 0 else Decimal('0.00')
    running_balance = get_cumulative_balance_up_to_week(request.user, week_offset)
    
    # Helper function to get relative week name
    def get_week_label(offset):
        if offset == 0:
            return 'Current Week'
        elif offset == -1:
            return 'Last Week'
        elif offset == 1:
            return 'Next Week'
        elif offset == -2:
            return '2 Weeks Ago'
        elif offset == 2:
            return 'In 2 Weeks'
        elif offset < 0:
            return f'{abs(offset)} Weeks Ago'
        else:
            return f'In {offset} Weeks'
    
    # Format transaction data
    income_data = []
    for income in income_entries:
        income_data.append({
            'id': income.pk,
            'date': income.date.strftime('%Y-%m-%d'),
            'payee': income.payee,
            'amount': float(income.amount),
            'amount_display': f"+${income.amount:,.2f}"
        })
    
    expense_data = []
    for expense in expense_entries:
        expense_data.append({
            'id': expense.pk,
            'date': expense.date.strftime('%Y-%m-%d'),
            'payee': expense.payee,
            'amount': float(expense.amount),
            'amount_display': f"-${expense.amount:,.2f}"
        })
    
    return JsonResponse({
        'success': True,
        'week_offset': week_offset,
        'week_label': get_week_label(week_offset),
        'week_start': target_monday.strftime('%d %b'),
        'week_end': target_sunday.strftime('%d %b, %Y'),
        'weekly_income': float(weekly_income),
        'weekly_expenses': float(weekly_expenses),
        'weekly_balance': float(weekly_balance),
        'previous_week_balance': float(previous_week_balance),
        'running_balance': float(running_balance),
        'income_entries': income_data,
        'expense_entries': expense_data,
    })


@login_required
@require_POST
def add_income(request):
    """Add new income entry via AJAX."""
    try:
        # Get form data
        date_str = request.POST.get('date')
        payee_choice = request.POST.get('payee_choice', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validate required fields
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date is required'})
        
        if not payee_choice:
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
        
        # Get the payee name from payee_choice (this is the payee name, not ID)
        payee_name = payee_choice
        
        # Create or get payee (this automatically creates payee if it doesn't exist)
        get_or_create_payee(request.user, payee_name)
        
        # Create income entry
        income = Income.objects.create(
            user=request.user,
            date=date,
            payee=payee_name,
            amount=amount,
            notes=notes
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Income of ${amount} from {payee_name} added successfully',
            'income_id': income.id,
            'date': date.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
        
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
        payee_choice = request.POST.get('payee_choice', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validate required fields
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date is required'})
        
        if not payee_choice:
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
        
        # Get the payee name from payee_choice (this is the payee name, not ID)
        payee_name = payee_choice
        
        # Create or get payee (this automatically creates payee if it doesn't exist)
        get_or_create_payee(request.user, payee_name)
        
        # Update income entry
        income.date = date
        income.payee = payee_name
        income.amount = amount
        income.notes = notes
        income.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Income entry updated successfully: ${amount} from {payee_name}',
            'income_id': income.id,
            'date': income.date.strftime('%Y-%m-%d')
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
        payee_choice = request.POST.get('payee_choice', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validate required fields
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date is required'})
        
        if not payee_choice:
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
        
        # Get the payee name from payee_choice (this is the payee name, not ID)
        payee_name = payee_choice
        
        # Create or get payee (this automatically creates payee if it doesn't exist)
        get_or_create_payee(request.user, payee_name)
        
        # Create expense entry
        expense = Expense.objects.create(
            user=request.user,
            date=date,
            payee=payee_name,
            amount=amount,
            notes=notes
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Expense of ${amount} to {payee_name} added successfully',
            'expense_id': expense.id,
            'date': date.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
        
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
        payee_choice = request.POST.get('payee_choice', '').strip()
        amount_str = request.POST.get('amount', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validate required fields
        if not date_str:
            return JsonResponse({'success': False, 'error': 'Date is required'})
        
        if not payee_choice:
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
        
        # Get the payee name from payee_choice (this is the payee name, not ID)
        payee_name = payee_choice
        
        # Create or get payee (this automatically creates payee if it doesn't exist)
        get_or_create_payee(request.user, payee_name)
        
        # Update expense entry
        expense.date = date
        expense.payee = payee_name
        expense.amount = amount
        expense.notes = notes
        expense.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Expense entry updated successfully: ${amount} to {payee_name}',
            'expense_id': expense.id,
            'date': expense.date.strftime('%Y-%m-%d')
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


@login_required
def get_payees(request):
    """Get list of payees for the current user."""
    try:
        payees = Payee.objects.filter(user=request.user).order_by('name')
        payee_list = [{'id': p.id, 'name': p.name} for p in payees]
        
        return JsonResponse({
            'success': True,
            'payees': payee_list
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
def get_auto_date(request):
    """Get auto-populated date for a given week offset and transaction type."""
    try:
        week_offset = int(request.GET.get('week_offset', 0))
        transaction_type = request.GET.get('type', None)  # 'income' or 'expense'
        
        auto_date = get_auto_date_for_week(request.user, week_offset, transaction_type)
        
        return JsonResponse({
            'success': True,
            'auto_date': auto_date.strftime('%Y-%m-%d')
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
@require_POST
def add_payee(request):
    """Add a new payee for the current user."""
    try:
        payee_name = request.POST.get('name', '').strip()
        
        if not payee_name:
            return JsonResponse({'success': False, 'error': 'Payee name is required'})
        
        # Check if payee already exists
        if Payee.objects.filter(user=request.user, name=payee_name).exists():
            return JsonResponse({'success': False, 'error': 'Payee already exists'})
        
        # Create new payee
        payee = Payee.objects.create(user=request.user, name=payee_name)
        
        return JsonResponse({
            'success': True,
            'payee': {'id': payee.id, 'name': payee.name},
            'message': f'Payee "{payee_name}" added successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})
