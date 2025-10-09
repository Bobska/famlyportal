from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Max, Sum, Q
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Category, Expense, Income, Payee


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
    category_id: int | None = None
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
    
    # Handle category selection (optional)
    category_id = None
    category_choice = (data.get('category_choice') or '').strip()
    if category_choice:
        try:
            category_id = int(category_choice)
        except (ValueError, TypeError):
            # Invalid category ID, ignore rather than error
            category_id = None
    
    return TransactionPayload(date=parsed_date, payee_name=payee_name, amount=amount, category_id=category_id, notes=notes)


def persist_transaction(model, user, payload: TransactionPayload, *, instance=None):
    """Create or update a transaction record and ensure the payee exists."""
    get_or_create_payee(user, payload.payee_name)

    record = instance or model(user=user)
    record.date = payload.date
    record.payee = payload.payee_name
    record.amount = payload.amount
    record.notes = payload.notes
    
    # Handle category assignment
    if payload.category_id:
        try:
            category = Category.objects.get(id=payload.category_id, user=user)
            record.category = category
        except Category.DoesNotExist:
            # Invalid category ID or category doesn't belong to user, ignore
            record.category = None
    else:
        record.category = None
    
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

    # Get recent transactions (last 10 of each type)
    recent_income = Income.objects.filter(user=request.user).order_by('-date', '-id')[:10]
    recent_expenses = Expense.objects.filter(user=request.user).order_by('-date', '-id')[:10]
    
    # Combine and sort by date
    recent_transactions = []
    for income in recent_income:
        recent_transactions.append({'type': 'income', 'entry': income})
    for expense in recent_expenses:
        recent_transactions.append({'type': 'expense', 'entry': expense})
    
    # Sort by date descending
    recent_transactions.sort(key=lambda x: (x['entry'].date, x['entry'].id), reverse=True)
    
    # Count active payees, categories, and transactions
    from .models import Payee, Category
    from django.db.models import Count, Sum, F, Q
    
    payee_count = Payee.objects.filter(user=request.user).count()
    category_count = Category.objects.filter(user=request.user).count()
    transaction_count = recent_income.count() + recent_expenses.count()
    
    # Top payees by transaction count (based on payee CharField in Income/Expense)
    # Get all income transactions grouped by payee
    income_payees = (
        Income.objects.filter(user=request.user)
        .values('payee')
        .annotate(count=Count('id'))
    )
    
    # Get all expense transactions grouped by payee
    expense_payees = (
        Expense.objects.filter(user=request.user)
        .values('payee')
        .annotate(count=Count('id'))
    )
    
    # Combine and aggregate
    payee_totals = {}
    for item in income_payees:
        payee_totals[item['payee']] = payee_totals.get(item['payee'], 0) + item['count']
    for item in expense_payees:
        payee_totals[item['payee']] = payee_totals.get(item['payee'], 0) + item['count']
    
    # Sort and get top 3
    top_payees = sorted(payee_totals.items(), key=lambda x: x[1], reverse=True)[:3]
    top_payees = [{'name': name, 'total_count': count} for name, count in top_payees]
    
    # Top categories by transaction count
    top_categories = (
        Category.objects.filter(user=request.user)
        .annotate(transaction_count=Count('expense_entries'))
        .filter(transaction_count__gt=0)
        .order_by('-transaction_count')[:3]
    )
    
    # Monthly metrics
    from django.utils import timezone
    today = timezone.localdate()
    monthly_income = amount_sum(
        Income.objects.filter(user=request.user, date__year=today.year, date__month=today.month)
    )
    monthly_expenses = amount_sum(
        Expense.objects.filter(user=request.user, date__year=today.year, date__month=today.month)
    )
    monthly_balance = monthly_income - monthly_expenses
    
    # Transaction velocity (transactions per week average)
    total_transactions = Income.objects.filter(user=request.user).count() + Expense.objects.filter(user=request.user).count()
    
    # Get date range
    first_income = Income.objects.filter(user=request.user).order_by('date').first()
    first_expense = Expense.objects.filter(user=request.user).order_by('date').first()
    
    weeks_active = 1
    if first_income or first_expense:
        earliest_date = None
        if first_income and first_expense:
            earliest_date = min(first_income.date, first_expense.date)
        elif first_income:
            earliest_date = first_income.date
        else:
            earliest_date = first_expense.date
        
        days_active = (today - earliest_date).days
        weeks_active = max(1, days_active // 7)
    
    avg_transactions_per_week = total_transactions / weeks_active if weeks_active > 0 else 0

    context = {
        'page_title': 'Budget Basic',
        'app_name': 'budget_basic',
        'current_balance': current_balance,
        'recent_transactions': recent_transactions[:10],  # Limit to 10 most recent
        'payee_count': payee_count,
        'category_count': category_count,
        'transaction_count': transaction_count,
        'top_payees': top_payees,
        'top_categories': top_categories,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_balance,
        'avg_transactions_per_week': avg_transactions_per_week,
        **build_sidebar_summary_context(request),
    }
    return render(request, 'bank/dashboard.html', context)


@login_required
def shell(request):
    """
    Render the unified navigation shell that loads content via AJAX.
    This provides seamless navigation between all bank views without page reloads.
    """
    return render(request, 'bank/shell.html', {})


@login_required
def accounts(request):
    """
    Render the bank-style accounts page showing multiple account types,
    transaction history, and transfer capabilities.
    """
    from django.db.models import Count, Sum
    from django.utils import timezone
    
    # Get all user transactions
    all_income = Income.objects.filter(user=request.user)
    all_expenses = Expense.objects.filter(user=request.user)
    
    # Calculate total balances
    total_income = amount_sum(all_income)
    total_expenses = amount_sum(all_expenses)
    overall_balance = total_income - total_expenses
    
    # Simulate different account types by categorizing transactions
    # Checking Account: Primary account for expenses and income
    checking_income = all_income.filter(payee__icontains='salary').aggregate(total=Sum('amount'))['total'] or ZERO_DECIMAL
    checking_balance = overall_balance * Decimal('0.6')  # 60% in checking
    
    # Savings Account: Long-term savings
    savings_balance = overall_balance * Decimal('0.35')  # 35% in savings
    
    # Investment Account: Investment holdings
    investment_balance = overall_balance * Decimal('0.05')  # 5% in investments
    
    # Recent transactions (last 15 combined)
    recent_income = all_income.order_by('-date', '-id')[:15]
    recent_expenses = all_expenses.order_by('-date', '-id')[:15]
    
    # Combine and sort by date
    all_transactions = []
    for income in recent_income:
        all_transactions.append({
            'type': 'income',
            'entry': income,
            'date': income.date,
            'payee': income.payee,
            'amount': income.amount,
            'category': None,
        })
    for expense in recent_expenses:
        all_transactions.append({
            'type': 'expense',
            'entry': expense,
            'date': expense.date,
            'payee': expense.payee,
            'amount': expense.amount,
            'category': expense.category,
        })
    
    # Sort by date descending
    all_transactions.sort(key=lambda x: (x['date'], x['entry'].id), reverse=True)
    all_transactions = all_transactions[:15]  # Keep top 15
    
    # Calculate monthly metrics
    today = timezone.localdate()
    monthly_income = amount_sum(
        Income.objects.filter(user=request.user, date__year=today.year, date__month=today.month)
    )
    monthly_expenses = amount_sum(
        Expense.objects.filter(user=request.user, date__year=today.year, date__month=today.month)
    )
    monthly_net = monthly_income - monthly_expenses
    
    # Transaction counts by type
    income_count = all_income.count()
    expense_count = all_expenses.count()
    total_transactions = income_count + expense_count
    
    # Account activity summary
    today_transactions = Income.objects.filter(user=request.user, date=today).count() + \
                         Expense.objects.filter(user=request.user, date=today).count()
    
    # Spending by category (top 5)
    top_spending_categories = (
        Category.objects.filter(user=request.user)
        .annotate(total_spent=Sum('expense_entries__amount'))
        .filter(total_spent__gt=0)
        .order_by('-total_spent')[:5]
    )
    
    context = {
        'page_title': 'Accounts Overview',
        'overall_balance': overall_balance,
        'checking_balance': checking_balance,
        'savings_balance': savings_balance,
        'investment_balance': investment_balance,
        'recent_transactions': all_transactions,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_net': monthly_net,
        'income_count': income_count,
        'expense_count': expense_count,
        'total_transactions': total_transactions,
        'today_transactions': today_transactions,
        'top_spending_categories': top_spending_categories,
    }
    
    return render(request, 'bank/accounts.html', context)


def build_weekly_context(request):
    """Return the base context payload for weekly transaction views."""
    week_offset = int(request.GET.get('week_offset', 0))
    week_window = resolve_week_window(week_offset)

    income_entries = weekly_transactions(Income, request.user, week_window)
    expense_entries = weekly_transactions(Expense, request.user, week_window)

    weekly_income = amount_sum(income_entries)
    weekly_expenses = amount_sum(expense_entries)
    weekly_balance = weekly_income - weekly_expenses
    running_balance = get_cumulative_balance_up_to_week(request.user, week_offset)

    today = timezone.localdate()
    monthly_income = amount_sum(
        Income.objects.filter(user=request.user, date__year=today.year, date__month=today.month)
    )
    monthly_expenses = amount_sum(
        Expense.objects.filter(user=request.user, date__year=today.year, date__month=today.month)
    )
    monthly_balance = monthly_income - monthly_expenses

    return {
        'income_entries': income_entries,
        'expense_entries': expense_entries,
        'weekly_income': weekly_income,
        'weekly_expenses': weekly_expenses,
        'weekly_balance': weekly_balance,
    'running_balance': running_balance,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_balance,
        'sidebar_week_start': week_window.start,
        'sidebar_week_end': week_window.end,
        'sidebar_week_label': describe_week_offset(week_offset),
        'week_offset': week_offset,
        'target_monday': week_window.start,
        'target_sunday': week_window.end,
    }


def build_sidebar_summary_context(request, *, week_offset: int | None = None) -> dict[str, object]:
    """Return weekly summary metrics for sidebar widgets."""
    resolved_offset = week_offset if week_offset is not None else int(request.GET.get('week_offset', 0))
    week_window = resolve_week_window(resolved_offset)

    weekly_income = amount_sum(
        Income.objects.filter(
            user=request.user,
            date__gte=week_window.start,
            date__lte=week_window.end,
        )
    )
    weekly_expenses = amount_sum(
        Expense.objects.filter(
            user=request.user,
            date__gte=week_window.start,
            date__lte=week_window.end,
        )
    )
    weekly_balance = weekly_income - weekly_expenses

    return {
        'weekly_income': weekly_income,
        'weekly_expenses': weekly_expenses,
        'weekly_balance': weekly_balance,
        'sidebar_week_start': week_window.start,
        'sidebar_week_end': week_window.end,
        'sidebar_week_label': describe_week_offset(resolved_offset),
    }


def build_all_transactions_context(request):
    """Return the base context payload for the full transactions view."""
    income_entries = Income.objects.filter(user=request.user).order_by('-date', '-id')
    expense_entries = Expense.objects.filter(user=request.user).order_by('-date', '-id')

    total_income = amount_sum(income_entries)
    total_expenses = amount_sum(expense_entries)
    net_balance = total_income - total_expenses

    return {
        'income_entries': income_entries,
        'expense_entries': expense_entries,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
    }

@login_required
def weekly(request):
    """Weekly transactions overview."""
    context = {
        'page_title': 'Weekly',
        'app_name': 'budget_basic',
        **build_weekly_context(request),
    }
    return render(request, 'bank/weekly.html', context)


@login_required
def weekly_expanse(request):
    """Weekly transactions overview with Expanse theme."""
    weekly_context = build_weekly_context(request)
    
    # Calculate totals for summary panels
    total_income = weekly_context.get('weekly_income', 0)
    total_expenses = weekly_context.get('weekly_expenses', 0)
    net_balance = total_income - total_expenses
    
    context = {
        'page_title': 'Weekly Operations',
        'app_name': 'bank',
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        **weekly_context,
    }
    return render(request, 'bank/weekly_expanse.html', context)


@login_required
def transactions(request):
    """All transactions view without weekly navigation."""
    context = {
        'page_title': 'Transactions',
        'app_name': 'budget_basic',
        **build_all_transactions_context(request),
        **build_sidebar_summary_context(request),
    }
    return render(request, 'bank/transactions.html', context)


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
    """Get list of payees for the current user, optionally filtered by category."""
    try:
        category_id = request.GET.get('category_id', None)
        
        payees = Payee.objects.filter(user=request.user).prefetch_related('categories')
        
        # Filter by category if provided
        if category_id:
            try:
                category_id = int(category_id)
                payees = payees.filter(categories__id=category_id)
            except (ValueError, TypeError):
                # Invalid category ID, return all payees
                pass
        
        payees = payees.order_by('name').distinct()
        payee_list = [
            {
                'id': p.id, 
                'name': p.name,
                'transaction_type': p.transaction_type,
                'categories': [{'id': cat.id, 'name': cat.name} for cat in p.categories.all()]
            } 
            for p in payees
        ]
        
        return JsonResponse({
            'success': True,
            'payees': payee_list,
            'filtered_by_category': bool(category_id)
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
def get_categories(request):
    """Get list of categories for the current user, optionally filtered by transaction type."""
    try:
        transaction_type = request.GET.get('type', None)  # 'income', 'expense', or None for all
        
        categories = Category.objects.filter(user=request.user)
        
        # Filter by transaction type if specified
        if transaction_type in ['income', 'expense']:
            categories = categories.filter(
                Q(category_type=transaction_type) | Q(category_type='both')
            )
        
        categories = categories.order_by('name')
        category_list = [
            {
                'id': c.id, 
                'name': c.name,
                'category_type': c.category_type,
                'type_display': c.get_type_display_short()
            } 
            for c in categories
        ]
        
        return JsonResponse({
            'success': True,
            'categories': category_list
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
    """Add a new payee for the current user with optional category assignment."""
    try:
        payee_name = request.POST.get('name', '').strip()
        transaction_type = request.POST.get('transaction_type', 'expense')
        category_ids = request.POST.getlist('categories')  # Get list of category IDs
        
        if not payee_name:
            return JsonResponse({'success': False, 'error': 'Payee name is required'})
        
        # Check if payee already exists
        if Payee.objects.filter(user=request.user, name=payee_name).exists():
            return JsonResponse({'success': False, 'error': 'Payee already exists'})
        
        # Create new payee
        payee = Payee.objects.create(
            user=request.user, 
            name=payee_name,
            transaction_type=transaction_type
        )
        
        # Assign categories if provided
        if category_ids:
            # Filter to only valid categories owned by the user
            valid_categories = Category.objects.filter(
                user=request.user, 
                id__in=category_ids
            )
            payee.categories.set(valid_categories)
        
        return JsonResponse({
            'success': True,
            'payee': {
                'id': payee.id, 
                'name': payee.name,
                'transaction_type': payee.transaction_type,
                'categories': [{'id': cat.id, 'name': cat.name} for cat in payee.categories.all()]
            },
            'message': f'Payee "{payee_name}" added successfully'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


@login_required
def link_categories_to_payee(request):
    """Link multiple categories to an existing payee."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        payee_id = request.POST.get('payee_id')
        category_ids = request.POST.getlist('category_ids')
        
        if not payee_id:
            return JsonResponse({'success': False, 'error': 'Payee ID is required'})
        
        if not category_ids:
            return JsonResponse({'success': False, 'error': 'At least one category must be selected'})
        
        # Get the payee (ensure it belongs to current user)
        try:
            payee = Payee.objects.get(id=payee_id, user=request.user)
        except Payee.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Payee not found'})
        
        # Get valid categories (ensure they belong to current user)
        valid_categories = Category.objects.filter(
            user=request.user,
            id__in=category_ids
        )
        
        if not valid_categories.exists():
            return JsonResponse({'success': False, 'error': 'No valid categories selected'})
        
        # Link the categories to the payee
        payee.categories.set(valid_categories)
        
        # Return updated category list
        categories_data = [
            {'id': cat.id, 'name': cat.name} 
            for cat in payee.categories.all()
        ]
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully linked {len(categories_data)} category(ies) to {payee.name}',
            'categories': categories_data
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Server error: {str(e)}'})


# ==============================================================================
# PAYEE MANAGEMENT VIEWS
# ==============================================================================

@login_required
def payee_list(request):
    """Display list of all payees for the current user."""
    category_filter = request.GET.get('category_filter', 'all')
    
    payees = Payee.objects.filter(user=request.user).prefetch_related('categories')
    
    # Apply category filtering
    if category_filter == 'none':
        # Filter payees with no categories
        payees = payees.filter(categories__isnull=True)
    elif category_filter != 'all' and category_filter.isdigit():
        # Filter payees by specific category
        payees = payees.filter(categories__id=int(category_filter))
    
    payees = payees.order_by('name').distinct()
    categories = Category.objects.filter(user=request.user).order_by('name')
    
    context = {
        'page_title': 'Manage Payees',
        'payees': payees,
        'categories': categories,
        'current_category_filter': category_filter,
        **build_sidebar_summary_context(request),
    }
    return render(request, 'bank/payees.html', context)


@login_required
@require_POST
def payee_create(request):
    """Create a new payee via AJAX."""
    try:
        payee_name = request.POST.get('name', '').strip()
        category_ids = request.POST.getlist('categories')  # Get list of category IDs
        
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
        
        # Add categories if provided
        if category_ids:
            # Validate that all category IDs belong to the current user
            valid_categories = Category.objects.filter(user=request.user, id__in=category_ids)
            payee.categories.set(valid_categories)
        
        return JsonResponse({
            'success': True,
            'payee': {
                'id': payee.id,
                'name': payee.name,
                'categories_display': payee.get_categories_display(),
                'categories': [{'id': cat.id, 'name': cat.name} for cat in payee.categories.all()],
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
        transaction_type = request.POST.get('transaction_type', 'expense')
        category_ids = request.POST.getlist('categories')  # Get list of category IDs
        
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
        payee.transaction_type = transaction_type
        payee.save()
        
        # Update categories
        if category_ids:
            # Validate that all category IDs belong to the current user
            valid_categories = Category.objects.filter(user=request.user, id__in=category_ids)
            payee.categories.set(valid_categories)
        else:
            # Clear all categories if none provided
            payee.categories.clear()
        
        return JsonResponse({
            'success': True,
            'payee': {
                'id': payee.id,
                'name': payee.name,
                'transaction_type': payee.transaction_type,
                'categories_display': payee.get_categories_display(),
                'categories': [{'id': cat.id, 'name': cat.name} for cat in payee.categories.all()],
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
    ).prefetch_related('categories').order_by('name')[:10]
    
    payee_list = [
        {
            'id': payee.id,
            'name': payee.name,
            'categories_display': payee.get_categories_display(),
            'categories': [{'id': cat.id, 'name': cat.name} for cat in payee.categories.all()]
        }
        for payee in payees
    ]
    
    return JsonResponse({'payees': payee_list})


@login_required
def payee_filter(request):
    """Filter payees by category for the payees management page."""
    try:
        category_filter = request.GET.get('category_filter', 'all')
        search_query = request.GET.get('search', '').strip()
        
        payees = Payee.objects.filter(user=request.user).prefetch_related('categories')
        
        # Apply search filter if provided
        if search_query:
            payees = payees.filter(name__icontains=search_query)
        
        # Apply category filtering
        if category_filter == 'none':
            payees = payees.filter(categories__isnull=True)
        elif category_filter != 'all' and category_filter.isdigit():
            payees = payees.filter(categories__id=int(category_filter))
        
        payees = payees.order_by('name').distinct()
        
        # Serialize payees data for the frontend
        payees_data = []
        for payee in payees:
            category_names = [cat.name for cat in payee.categories.all()]
            category_ids = [cat.id for cat in payee.categories.all()]
            
            payees_data.append({
                'id': payee.id,
                'name': payee.name,
                'categories_display': payee.get_categories_display(),
                'category_names': category_names,
                'category_ids': category_ids,
                'created_at': payee.created_at.strftime('%Y-%m-%d'),
                'updated_at': payee.updated_at.strftime('%Y-%m-%d %H:%M')
            })
        
        return JsonResponse({
            'success': True,
            'payees': payees_data,
            'count': len(payees_data),
            'filter': category_filter
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        })


# ==============================
# CATEGORY MANAGEMENT VIEWS
# ==============================

@login_required
def category_list(request):
    """Display all categories for the current user with statistics."""
    categories = Category.objects.filter(user=request.user).prefetch_related('payees')
    context = {
        'categories': categories,
        **build_sidebar_summary_context(request),
    }
    return render(request, 'bank/categories.html', context)


@login_required  
@require_POST
def category_create(request):
    """Create a new category via AJAX."""
    try:
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        
        if not name:
            return JsonResponse({
                'success': False, 
                'error': 'Category name is required.'
            })
        
        # Check for duplicate category names (case-insensitive)
        if Category.objects.filter(user=request.user, name__iexact=name).exists():
            return JsonResponse({
                'success': False,
                'error': f'Category "{name}" already exists.'
            })
        
        # Create new category
        category = Category.objects.create(
            user=request.user,
            name=name,
            description=description or None
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Category "{name}" created successfully!',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description or '',
                'payees_count': category.get_payees_count(),
                'payees_display': category.get_payees_display(),
                'created_at': category.created_at.isoformat(),
                'updated_at': category.updated_at.isoformat()
            }
        })
        
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': f'Validation error: {e.message}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False, 
            'error': f'Error creating category: {str(e)}'
        })


@login_required
@require_POST  
def category_update(request, category_id):
    """Update an existing category via AJAX."""
    try:
        category = Category.objects.get(id=category_id, user=request.user)
        
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()
        category_type = request.POST.get('category_type', 'expense').strip()
        
        if not name:
            return JsonResponse({
                'success': False,
                'error': 'Category name is required.'
            })
        
        # Validate category_type
        if category_type not in ['income', 'expense', 'both']:
            category_type = 'expense'
        
        # Check for duplicate names (excluding current category)
        if Category.objects.filter(
            user=request.user, 
            name__iexact=name
        ).exclude(id=category_id).exists():
            return JsonResponse({
                'success': False,
                'error': f'Category "{name}" already exists.'
            })
        
        # Update category
        category.name = name
        category.description = description or None
        category.category_type = category_type
        category.save()
        
        return JsonResponse({
            'success': True,
            'message': f'Category "{name}" updated successfully!',
            'category': {
                'id': category.id,
                'name': category.name,
                'description': category.description or '',
                'category_type': category.get_category_type_display(),
                'payees_count': category.get_payees_count(),
                'payees_display': category.get_payees_display(),
                'created_at': category.created_at.isoformat(),
                'updated_at': category.updated_at.isoformat()
            }
        })
        
    except Category.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Category not found.'
        })
    except ValidationError as e:
        return JsonResponse({
            'success': False,
            'error': f'Validation error: {e.message}'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error updating category: {str(e)}'
        })


@login_required
@require_POST
def category_delete(request, category_id):
    """Delete a category via AJAX with transaction usage checking."""
    try:
        category = Category.objects.get(id=category_id, user=request.user)
        
        # TODO: Check if category is being used in any transactions
        # For now, we'll allow deletion but this should be implemented
        # when categories are linked to transactions
        
        category_name = category.name
        category.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Category "{category_name}" deleted successfully!'
        })
        
    except Category.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Category not found.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error deleting category: {str(e)}'
        })


@login_required
def category_search(request):
    """Search categories for typeahead/autocomplete functionality."""
    query = request.GET.get('q', '').strip()
    
    if not query:
        return JsonResponse({'categories': []})
    
    categories = Category.objects.filter(
        user=request.user,
        name__icontains=query
    ).order_by('name')[:10]
    
    category_list = [
        {
            'id': category.id,
            'name': category.name,
            'description': category.description or ''
        }
        for category in categories
    ]
    
    return JsonResponse({'categories': category_list})


@login_required
def category_payees(request, category_id):
    """Get payees linked to a specific category."""
    try:
        category = Category.objects.get(id=category_id, user=request.user)
        
        # Get all payees linked to this category
        payees = category.payees.all().prefetch_related('categories').order_by('name')
        
        payee_list = [
            {
                'id': payee.id,
                'name': payee.name,
                'categories_display': payee.get_categories_display(),
                'category_ids': [cat.id for cat in payee.categories.all()],
                'created_at': payee.created_at.isoformat(),
                'updated_at': payee.updated_at.isoformat(),
            }
            for payee in payees
        ]
        
        return JsonResponse({
            'success': True,
            'category': {
                'id': category.id,
                'name': category.name,
            },
            'payees': payee_list,
            'count': len(payee_list)
        })
        
    except Category.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Category not found or access denied.'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error fetching payees: {str(e)}'
        })


# ============================================================================
# AJAX Content Loading Endpoints for Navigation Shell
# ============================================================================

@login_required
def ajax_dashboard_content(request):
    """Return dashboard content as HTML for AJAX loading in navigation shell."""
    from django.template.loader import render_to_string
    
    # Get dashboard context (reuse existing dashboard logic)
    context = dashboard(request).context_data if hasattr(dashboard(request), 'context_data') else {}
    
    # Rebuild context since dashboard() returns HttpResponse, not context
    total_income = amount_sum(Income.objects.filter(user=request.user))
    total_expenses = amount_sum(Expense.objects.filter(user=request.user))
    current_balance = total_income - total_expenses
    
    recent_income = Income.objects.filter(user=request.user).order_by('-date', '-id')[:10]
    recent_expenses = Expense.objects.filter(user=request.user).order_by('-date', '-id')[:10]
    
    recent_transactions = []
    for income in recent_income:
        recent_transactions.append({'type': 'income', 'entry': income})
    for expense in recent_expenses:
        recent_transactions.append({'type': 'expense', 'entry': expense})
    
    recent_transactions.sort(key=lambda x: (x['entry'].date, x['entry'].id), reverse=True)
    
    from django.db.models import Count, Sum
    payee_count = Payee.objects.filter(user=request.user).count()
    category_count = Category.objects.filter(user=request.user).count()
    
    income_payees = Income.objects.filter(user=request.user).values('payee').annotate(count=Count('id'))
    expense_payees = Expense.objects.filter(user=request.user).values('payee').annotate(count=Count('id'))
    
    payee_totals = {}
    for item in income_payees:
        payee_totals[item['payee']] = payee_totals.get(item['payee'], 0) + item['count']
    for item in expense_payees:
        payee_totals[item['payee']] = payee_totals.get(item['payee'], 0) + item['count']
    
    top_payees = sorted(payee_totals.items(), key=lambda x: x[1], reverse=True)[:3]
    top_payees = [{'name': name, 'total_count': count} for name, count in top_payees]
    
    top_categories = (
        Category.objects.filter(user=request.user)
        .annotate(transaction_count=Count('expense_entries'))
        .filter(transaction_count__gt=0)
        .order_by('-transaction_count')[:3]
    )
    
    from django.utils import timezone
    today = timezone.localdate()
    monthly_income = amount_sum(Income.objects.filter(user=request.user, date__year=today.year, date__month=today.month))
    monthly_expenses = amount_sum(Expense.objects.filter(user=request.user, date__year=today.year, date__month=today.month))
    monthly_balance = monthly_income - monthly_expenses
    
    total_transactions = Income.objects.filter(user=request.user).count() + Expense.objects.filter(user=request.user).count()
    first_income = Income.objects.filter(user=request.user).order_by('date').first()
    first_expense = Expense.objects.filter(user=request.user).order_by('date').first()
    
    weeks_active = 1
    if first_income or first_expense:
        earliest_date = None
        if first_income and first_expense:
            earliest_date = min(first_income.date, first_expense.date)
        elif first_income:
            earliest_date = first_income.date
        else:
            earliest_date = first_expense.date
        days_active = (today - earliest_date).days
        weeks_active = max(1, days_active // 7)
    
    avg_transactions_per_week = total_transactions / weeks_active if weeks_active > 0 else 0
    
    sidebar_context = build_sidebar_summary_context(request)
    
    context = {
        'current_balance': current_balance,
        'recent_transactions': recent_transactions[:10],
        'payee_count': payee_count,
        'category_count': category_count,
        'transaction_count': len(recent_transactions[:10]),
        'top_payees': top_payees,
        'top_categories': top_categories,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_balance': monthly_balance,
        'avg_transactions_per_week': avg_transactions_per_week,
        **sidebar_context,
    }
    
    html = render_to_string('bank/partials/dashboard_content.html', context, request=request)
    
    return JsonResponse({
        'status': 'success',
        'html': html,
        'view': 'dashboard'
    })


@login_required
def ajax_accounts_content(request):
    """Return accounts content as HTML for AJAX loading in navigation shell."""
    from django.template.loader import render_to_string
    from django.db.models import Sum
    from django.utils import timezone
    
    # Get all user transactions
    all_income = Income.objects.filter(user=request.user)
    all_expenses = Expense.objects.filter(user=request.user)
    
    # Calculate total balances
    total_income = amount_sum(all_income)
    total_expenses = amount_sum(all_expenses)
    overall_balance = total_income - total_expenses
    
    # Simulate account balances
    checking_balance = overall_balance * Decimal('0.6')
    savings_balance = overall_balance * Decimal('0.35')
    investment_balance = overall_balance * Decimal('0.05')
    
    # Recent transactions (last 15 combined)
    recent_income = all_income.order_by('-date', '-id')[:15]
    recent_expenses = all_expenses.order_by('-date', '-id')[:15]
    
    all_transactions = []
    for income in recent_income:
        all_transactions.append({
            'type': 'income',
            'entry': income,
            'date': income.date,
            'payee': income.payee,
            'amount': income.amount,
            'category': None,
        })
    for expense in recent_expenses:
        all_transactions.append({
            'type': 'expense',
            'entry': expense,
            'date': expense.date,
            'payee': expense.payee,
            'amount': expense.amount,
            'category': expense.category,
        })
    
    all_transactions.sort(key=lambda x: (x['date'], x['entry'].id), reverse=True)
    all_transactions = all_transactions[:15]
    
    # Monthly metrics
    today = timezone.localdate()
    monthly_income = amount_sum(Income.objects.filter(user=request.user, date__year=today.year, date__month=today.month))
    monthly_expenses = amount_sum(Expense.objects.filter(user=request.user, date__year=today.year, date__month=today.month))
    monthly_net = monthly_income - monthly_expenses
    
    # Transaction counts
    income_count = all_income.count()
    expense_count = all_expenses.count()
    total_transactions = income_count + expense_count
    today_transactions = Income.objects.filter(user=request.user, date=today).count() + \
                         Expense.objects.filter(user=request.user, date=today).count()
    
    # Top spending categories
    top_spending_categories = (
        Category.objects.filter(user=request.user)
        .annotate(total_spent=Sum('expense_entries__amount'))
        .filter(total_spent__gt=0)
        .order_by('-total_spent')[:5]
    )
    
    context = {
        'overall_balance': overall_balance,
        'checking_balance': checking_balance,
        'savings_balance': savings_balance,
        'investment_balance': investment_balance,
        'recent_transactions': all_transactions,
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_net': monthly_net,
        'income_count': income_count,
        'expense_count': expense_count,
        'total_transactions': total_transactions,
        'today_transactions': today_transactions,
        'top_spending_categories': top_spending_categories,
    }
    
    html = render_to_string('bank/partials/accounts_content.html', context, request=request)
    
    return JsonResponse({
        'status': 'success',
        'html': html,
        'view': 'accounts'
    })


@login_required
def ajax_weekly_content(request):
    """Return weekly view content for AJAX loading."""
    # Build the weekly context with all necessary data
    weekly_context = build_weekly_context(request)
    
    # Calculate totals for summary panels
    total_income = weekly_context.get('weekly_income', 0)
    total_expenses = weekly_context.get('weekly_expenses', 0)
    net_balance = total_income - total_expenses
    weekly_net = weekly_context.get('weekly_balance', 0)
    current_date = timezone.now()
    
    context = {
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_balance': net_balance,
        'weekly_net': weekly_net,
        'current_date': current_date,
        **weekly_context,
    }
    
    # Render the partial template
    html = render_to_string('bank/partials/weekly_content.html', context, request=request)
    
    return JsonResponse({
        'status': 'success',
        'html': html,
        'view': 'weekly',
        'week_offset': weekly_context.get('week_offset', 0)
    })


@login_required
def ajax_transactions_content(request):
    """Return transactions view content for AJAX loading (placeholder)."""
    return JsonResponse({
        'status': 'error',
        'error': 'Transactions AJAX view not yet implemented',
        'html': '<div class="shell-error-panel"><h2>VIEW NOT READY</h2><p>Transactions view conversion in progress</p></div>'
    })


@login_required
def ajax_payees_content(request):
    """Return payees view content for AJAX loading (placeholder)."""
    return JsonResponse({
        'status': 'error',
        'error': 'Payees AJAX view not yet implemented',
        'html': '<div class="shell-error-panel"><h2>VIEW NOT READY</h2><p>Payees view conversion in progress</p></div>'
    })


@login_required
def ajax_categories_content(request):
    """Return categories view content for AJAX loading (placeholder)."""
    return JsonResponse({
        'status': 'error',
        'error': 'Categories AJAX view not yet implemented',
        'html': '<div class="shell-error-panel"><h2>VIEW NOT READY</h2><p>Categories view conversion in progress</p></div>'
    })

