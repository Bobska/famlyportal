from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Max, Sum
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Expense, Income, Payee


ZERO_DECIMAL = Decimal("0.00")


@dataclass(frozen=True)
class WeekWindow:
    """Represent a Monday-through-Sunday window relative to the current date."""

    start: date
    end: date

    @property
    def iso_bounds(self) -> tuple[str, str]:
        """Return the ISO formatted start and end dates."""
        return self.start.isoformat(), self.end.isoformat()


def resolve_week_window(week_offset: int, reference: date | None = None) -> WeekWindow:
    """Return the week window for the requested offset from the reference date."""
    anchor = reference or timezone.localdate()
    current_monday = anchor - timedelta(days=anchor.weekday())
    start = current_monday + timedelta(weeks=week_offset)
    return WeekWindow(start=start, end=start + timedelta(days=6))


def amount_sum(queryset) -> Decimal:
    """Aggregate a queryset's amount total, defaulting to zero when empty."""
    return queryset.aggregate(total=Sum('amount'))['total'] or ZERO_DECIMAL


def weekly_transactions(model, user, window: WeekWindow):
    """Return transactions for a user constrained to the supplied week window."""
    return (
        model.objects.filter(
            user=user,
            date__gte=window.start,
            date__lte=window.end,
        )
        .order_by('-date', '-created_at')
    )


def cumulative_total(model, user, *, end_date: date) -> Decimal:
    """Return the cumulative total up to and including end_date for the model."""
    return amount_sum(model.objects.filter(user=user, date__lte=end_date))


def format_transaction_entry(entry, *, is_income: bool) -> dict[str, object]:
    """Serialize a transaction for JSON responses."""
    sign = '+' if is_income else '-'
    return {
        'id': entry.pk,
        'date': entry.date.strftime('%Y-%m-%d'),
        'payee': entry.payee,
        'amount': float(entry.amount),
        'amount_display': f"{sign}${entry.amount:,.2f}",
    }


def describe_week_offset(offset: int) -> str:
    """Return a human readable label for a relative week offset."""
    labels = {
        -2: '2 Weeks Ago',
        -1: 'Last Week',
        0: 'Current Week',
        1: 'Next Week',
        2: 'In 2 Weeks',
    }
    if offset in labels:
        return labels[offset]
    if offset < 0:
        return f"{abs(offset)} Weeks Ago"
    return f"In {offset} Weeks"

def format_currency(amount: Decimal) -> str:
    """Return a currency formatted string for Decimal values."""
    return f"{amount:,.2f}"

@dataclass
class TransactionPayload:
    """Validated transaction data extracted from incoming POST requests."""

    date: date
    payee_name: str
    amount: Decimal
    notes: str = ''

def build_transaction_payload(data) -> TransactionPayload:
    """Validate and normalise POSTed transaction data."""
    date_raw = (data.get('date') or '').strip()
    if not date_raw:
        raise ValidationError('Date is required')
    try:
        parsed_date = datetime.strptime(date_raw, '%Y-%m-%d').date()
    except ValueError as exc:
        raise ValidationError('Invalid date format') from exc

    payee_name = (data.get('payee_choice') or '').strip()
    if not payee_name:
        raise ValidationError('Payee is required')

    amount_raw = (data.get('amount') or '').replace(',', '').strip()
    if not amount_raw:
        raise ValidationError('Amount is required')
    try:
        amount = Decimal(amount_raw)
    except (InvalidOperation, ValueError) as exc:
        raise ValidationError('Invalid amount format') from exc
    if amount <= ZERO_DECIMAL:
        raise ValidationError('Amount must be positive.')

    notes = (data.get('notes') or '').strip()
    return TransactionPayload(date=parsed_date, payee_name=payee_name, amount=amount, notes=notes)


def persist_transaction(model, user, payload: TransactionPayload, *, instance=None):
    """Create or update a transaction record and ensure the payee exists."""
    get_or_create_payee(user, payload.payee_name)

    record = instance or model(user=user)
    record.date = payload.date
    record.payee = payload.payee_name
    record.amount = payload.amount
    record.notes = payload.notes
    record.save()
    return record

def get_user_transaction(model, user, pk):
    """Return a transaction belonging to the user or None when missing."""
    return model.objects.filter(id=pk, user=user).first()

def get_cumulative_balance_up_to_week(user, target_week_offset):
    """Return the running balance up to and including the target week."""
    window = resolve_week_window(target_week_offset)
    total_income = cumulative_total(Income, user, end_date=window.end)
    total_expenses = cumulative_total(Expense, user, end_date=window.end)
    return total_income - total_expenses



def get_week_balance_only(user, week_offset):
    """Return the net balance for a single week window."""
    window = resolve_week_window(week_offset)
    weekly_income = amount_sum(weekly_transactions(Income, user, window))
    weekly_expenses = amount_sum(weekly_transactions(Expense, user, window))
    return weekly_income - weekly_expenses



def get_auto_date_for_week(user, week_offset, transaction_type=None):
    """Return the latest transaction date for the resolved week and type."""
    window = resolve_week_window(week_offset)
    model_map = {
        'income': Income,
        'expense': Expense,
    }

    def latest_for_model(model):
        return model.objects.filter(
            user=user,
            date__gte=window.start,
            date__lte=window.end,
        ).aggregate(max_date=Max('date'))['max_date']

    if transaction_type in model_map:
        return latest_for_model(model_map[transaction_type]) or window.start

    latest_candidates = [d for d in (latest_for_model(Income), latest_for_model(Expense)) if d]
    return max(latest_candidates) if latest_candidates else window.start



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
    """Render the high-level balance summary for Budget Basic."""

    # Compute the aggregate balance once to avoid double iteration in templates.
    total_income = amount_sum(Income.objects.filter(user=request.user))
    total_expenses = amount_sum(Expense.objects.filter(user=request.user))
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

    week_offset = int(request.GET.get('week_offset', 0))
    week_window = resolve_week_window(week_offset)

    income_entries = weekly_transactions(Income, request.user, week_window)
    expense_entries = weekly_transactions(Expense, request.user, week_window)

    weekly_income = amount_sum(income_entries)
    weekly_expenses = amount_sum(expense_entries)
    weekly_balance = weekly_income - weekly_expenses

    today = timezone.localdate()
    monthly_income = amount_sum(
        Income.objects.filter(user=request.user, date__year=today.year, date__month=today.month)
    )
    monthly_expenses = amount_sum(
        Expense.objects.filter(user=request.user, date__year=today.year, date__month=today.month)
    )
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
        'target_monday': week_window.start,
        'target_sunday': week_window.end,
    }
    return render(request, 'budget_basic/main.html', context)


@login_required
def get_week_data(request):
    """Return week-specific transaction data for async updates."""

    week_offset = int(request.GET.get('week_offset', 0))
    week_window = resolve_week_window(week_offset)

    income_entries = weekly_transactions(Income, request.user, week_window)
    expense_entries = weekly_transactions(Expense, request.user, week_window)

    weekly_income = amount_sum(income_entries)
    weekly_expenses = amount_sum(expense_entries)
    weekly_balance = weekly_income - weekly_expenses

    previous_week_balance = (
        get_cumulative_balance_up_to_week(request.user, week_offset - 1)
        if week_offset != 0
        else ZERO_DECIMAL
    )
    running_balance = get_cumulative_balance_up_to_week(request.user, week_offset)

    response = {
        'success': True,
        'week_offset': week_offset,
        'week_label': describe_week_offset(week_offset),
        'week_start': week_window.start.strftime('%d %b'),
        'week_end': week_window.end.strftime('%d %b, %Y'),
        'weekly_income': float(weekly_income),
        'weekly_expenses': float(weekly_expenses),
        'weekly_balance': float(weekly_balance),
        'previous_week_balance': float(previous_week_balance),
        'running_balance': float(running_balance),
        'income_entries': [
            format_transaction_entry(entry, is_income=True) for entry in income_entries
        ],
        'expense_entries': [
            format_transaction_entry(entry, is_income=False) for entry in expense_entries
        ],
    }
    return JsonResponse(response)



@login_required
@require_POST
def add_income(request):
    """Add new income entry via AJAX."""

    try:
        payload = build_transaction_payload(request.POST)
    except ValidationError as exc:
        return JsonResponse({'success': False, 'error': str(exc)})

    try:
        income = persist_transaction(Income, request.user, payload)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return JsonResponse({'success': False, 'error': f'Server error: {exc}'})

    return JsonResponse({
        'success': True,
        'message': (
            f"Income of ${format_currency(payload.amount)} from {payload.payee_name} added successfully"
        ),
        'income_id': income.id,
        'date': income.date.isoformat(),
    })



@login_required
@require_POST
def edit_income(request, income_id):
    """Edit existing income entry via AJAX."""

    income = get_user_transaction(Income, request.user, income_id)
    if not income:
        return JsonResponse({'success': False, 'error': 'Income entry not found or access denied'})

    try:
        payload = build_transaction_payload(request.POST)
    except ValidationError as exc:
        return JsonResponse({'success': False, 'error': str(exc)})

    try:
        income = persist_transaction(Income, request.user, payload, instance=income)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return JsonResponse({'success': False, 'error': f'Server error: {exc}'})

    return JsonResponse({
        'success': True,
        'message': (
            f"Income entry updated successfully: ${format_currency(payload.amount)} from {payload.payee_name}"
        ),
        'income_id': income.id,
        'date': income.date.strftime('%Y-%m-%d'),
    })



@login_required
def get_income(request, income_id):
    """Get income entry data for editing via AJAX."""

    income = get_user_transaction(Income, request.user, income_id)
    if not income:
        return JsonResponse({'success': False, 'error': 'Income entry not found or access denied'})

    return JsonResponse({
        'success': True,
        'income': {
            'id': income.id,
            'date': income.date.strftime('%Y-%m-%d'),
            'payee': income.payee,
            'amount': str(income.amount),
            'notes': income.notes or '',
        },
    })



@login_required
@require_POST
def delete_income(request, income_id):
    """Delete income entry via AJAX."""

    income = get_user_transaction(Income, request.user, income_id)
    if not income:
        return JsonResponse({'success': False, 'error': 'Income entry not found or access denied'})

    payee = income.payee
    amount_display = format_currency(income.amount)
    income.delete()

    return JsonResponse({
        'success': True,
        'message': f'Income entry deleted successfully: ${amount_display} from {payee}',
    })



# ===== EXPENSE VIEWS =====

@login_required
@require_POST
def add_expense(request):
    """Add new expense entry via AJAX."""

    try:
        payload = build_transaction_payload(request.POST)
    except ValidationError as exc:
        return JsonResponse({'success': False, 'error': str(exc)})

    try:
        expense = persist_transaction(Expense, request.user, payload)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return JsonResponse({'success': False, 'error': f'Server error: {exc}'})

    return JsonResponse({
        'success': True,
        'message': (
            f"Expense of ${format_currency(payload.amount)} to {payload.payee_name} added successfully"
        ),
        'expense_id': expense.id,
        'date': expense.date.isoformat(),
    })



@login_required
@require_POST
def edit_expense(request, expense_id):
    """Edit existing expense entry via AJAX."""

    expense = get_user_transaction(Expense, request.user, expense_id)
    if not expense:
        return JsonResponse({'success': False, 'error': 'Expense entry not found or access denied'})

    try:
        payload = build_transaction_payload(request.POST)
    except ValidationError as exc:
        return JsonResponse({'success': False, 'error': str(exc)})

    try:
        expense = persist_transaction(Expense, request.user, payload, instance=expense)
    except Exception as exc:  # pragma: no cover - defensive fallback
        return JsonResponse({'success': False, 'error': f'Server error: {exc}'})

    return JsonResponse({
        'success': True,
        'message': (
            f"Expense entry updated successfully: ${format_currency(payload.amount)} to {payload.payee_name}"
        ),
        'expense_id': expense.id,
        'date': expense.date.strftime('%Y-%m-%d'),
    })



@login_required
def get_expense(request, expense_id):
    """Get expense entry data for editing via AJAX."""

    expense = get_user_transaction(Expense, request.user, expense_id)
    if not expense:
        return JsonResponse({'success': False, 'error': 'Expense entry not found or access denied'})

    return JsonResponse({
        'success': True,
        'expense': {
            'id': expense.id,
            'date': expense.date.strftime('%Y-%m-%d'),
            'payee': expense.payee,
            'amount': str(expense.amount),
            'notes': expense.notes or '',
        },
    })



@login_required
@require_POST
def delete_expense(request, expense_id):
    """Delete expense entry via AJAX."""

    expense = get_user_transaction(Expense, request.user, expense_id)
    if not expense:
        return JsonResponse({'success': False, 'error': 'Expense entry not found or access denied'})

    payee = expense.payee
    amount_display = format_currency(expense.amount)
    expense.delete()

    return JsonResponse({
        'success': True,
        'message': f'Expense entry deleted successfully: ${amount_display} to {payee}',
    })



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


# ==============================================================================
# PAYEE MANAGEMENT VIEWS
# ==============================================================================

@login_required
def payee_list(request):
    """Display list of all payees for the current user."""
    payees = Payee.objects.filter(user=request.user).order_by('name')
    
    context = {
        'page_title': 'Manage Payees',
        'payees': payees,
    }
    return render(request, 'budget_basic/payees.html', context)


@login_required
@require_POST
def payee_create(request):
    """Create a new payee via AJAX."""
    try:
        payee_name = request.POST.get('name', '').strip()
        
        if not payee_name:
            return JsonResponse({
                'success': False,
                'error': 'Payee name is required'
            })
        
        # Check if payee already exists
        if Payee.objects.filter(user=request.user, name=payee_name).exists():
            return JsonResponse({
                'success': False,
                'error': f'Payee "{payee_name}" already exists'
            })
        
        # Create new payee
        payee = Payee.objects.create(
            user=request.user,
            name=payee_name
        )
        
        return JsonResponse({
            'success': True,
            'payee': {
                'id': payee.id,
                'name': payee.name,
                'created_at': payee.created_at.strftime('%Y-%m-%d %H:%M')
            },
            'message': f'Payee "{payee_name}" created successfully'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })


@login_required
@require_POST
def payee_update(request, payee_id):
    """Update an existing payee via AJAX."""
    try:
        payee = Payee.objects.get(id=payee_id, user=request.user)
        new_name = request.POST.get('name', '').strip()
        
        if not new_name:
            return JsonResponse({
                'success': False,
                'error': 'Payee name is required'
            })
        
        # Check if another payee with this name already exists
        if Payee.objects.filter(user=request.user, name=new_name).exclude(id=payee_id).exists():
            return JsonResponse({
                'success': False,
                'error': f'Payee "{new_name}" already exists'
            })
        
        old_name = payee.name
        payee.name = new_name
        payee.save()
        
        return JsonResponse({
            'success': True,
            'payee': {
                'id': payee.id,
                'name': payee.name,
                'updated_at': payee.updated_at.strftime('%Y-%m-%d %H:%M')
            },
            'message': f'Payee updated from "{old_name}" to "{new_name}"'
        })
        
    except Payee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Payee not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })


@login_required
@require_POST
def payee_delete(request, payee_id):
    """Delete a payee via AJAX."""
    try:
        payee = Payee.objects.get(id=payee_id, user=request.user)
        
        # Check if payee is being used in transactions
        income_count = Income.objects.filter(user=request.user, payee=payee.name).count()
        expense_count = Expense.objects.filter(user=request.user, payee=payee.name).count()
        total_transactions = income_count + expense_count
        
        if total_transactions > 0:
            return JsonResponse({
                'success': False,
                'error': f'Cannot delete "{payee.name}" - it is used in {total_transactions} transaction(s). Delete those transactions first.'
            })
        
        payee_name = payee.name
        payee.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Payee "{payee_name}" deleted successfully'
        })
        
    except Payee.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Payee not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })


@login_required
def payee_search(request):
    """Search payees for autocomplete functionality."""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'payees': []})
    
    payees = Payee.objects.filter(
        user=request.user,
        name__icontains=query
    ).order_by('name')[:10]
    
    payee_list = [
        {
            'id': payee.id,
            'name': payee.name
        }
        for payee in payees
    ]
    
    return JsonResponse({'payees': payee_list})