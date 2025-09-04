from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.utils import timezone
from django.db.models import Q, Sum, Count, Avg, F
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from decimal import Decimal
import json
import csv
import calendar
from datetime import datetime, timedelta

# Import decorators and mixins (will create these if they don't exist)
try:
    from core.decorators import family_required, app_permission_required
    from core.mixins import FamilyScopedMixin
except ImportError:
    # Create placeholder decorators if not available
    def family_required(view_func):
        """Placeholder decorator - ensure user has family"""
        def wrapper(request, *args, **kwargs):
            if not hasattr(request.user, 'familymember_set') or not request.user.familymember_set.exists():
                messages.error(request, 'You must be part of a family to access this feature.')
                return redirect('accounts:join_family')
            return view_func(request, *args, **kwargs)
        return wrapper
    
    def app_permission_required(app_name):
        """Placeholder decorator - check app permissions"""
        def decorator(view_func):
            def wrapper(request, *args, **kwargs):
                # For now, just check if user is authenticated
                if not request.user.is_authenticated:
                    return redirect('accounts:login')
                return view_func(request, *args, **kwargs)
            return wrapper
        return decorator
    
    class FamilyScopedMixin:
        """Placeholder mixin for family scoping"""
        def get_family(self):
            """Get the user's family"""
            return None  # Simplified for now
        
        def get_queryset(self):
            """Filter queryset by family"""
            return super().get_queryset() if hasattr(super(), 'get_queryset') else None

from .models import (
    BudgetCategory, Budget, BudgetItem, Transaction, SavingsGoal
)
from .forms import (
    BudgetCategoryForm, BudgetForm, BudgetItemForm, TransactionForm,
    QuickTransactionForm, SavingsGoalForm, BudgetFilterForm, ContributionForm
)


@login_required
@family_required
@app_permission_required('household_budget')
def dashboard(request):
    """Main budget dashboard with overview and quick actions"""
    family_member = request.user.familymember_set.first()
    family = family_member.family
    
    # Get current budget
    current_budget = Budget.objects.filter(family=family, is_active=True).first()
    
    # Calculate current month totals
    today = timezone.now().date()
    month_start = today.replace(day=1)
    next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
    
    # Get current month transactions
    month_transactions = Transaction.objects.filter(
        family=family,
        transaction_date__gte=month_start,
        transaction_date__lt=next_month
    )
    
    # Calculate monthly totals
    month_income = month_transactions.filter(
        transaction_type='income'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    month_expenses = month_transactions.filter(
        transaction_type='expense'
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    month_net = month_income - month_expenses
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(
        family=family
    ).select_related('category').order_by('-transaction_date', '-created_at')[:10]
    
    # Get active savings goals
    savings_goals = SavingsGoal.objects.filter(
        family=family,
        is_active=True
    ).order_by('priority')[:5]
    
    # Calculate budget progress if current budget exists
    budget_progress = {}
    budget_alerts = []
    
    if current_budget:
        budget_items = BudgetItem.objects.filter(
            budget=current_budget
        ).select_related('category')
        
        for item in budget_items:
            # Calculate actual amount for this month
            actual = month_transactions.filter(
                category=item.category
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            # Update the budget item's actual amount
            item.actual_amount = actual
            item.save()
            
            # Calculate progress percentage
            if item.budgeted_amount > 0:
                progress_pct = (actual / item.budgeted_amount * 100)
                budget_progress[str(item.category.pk)] = {
                    'category': item.category,
                    'budgeted': item.budgeted_amount,
                    'actual': actual,
                    'progress': min(progress_pct, 100),
                    'over_budget': actual > item.budgeted_amount,
                    'variance': item.variance,
                }
                
                # Add alerts for over-budget categories
                if item.category.category_type == 'expense' and actual > item.budgeted_amount:
                    budget_alerts.append({
                        'type': 'danger',
                        'message': f"{item.category.name} is over budget by ${actual - item.budgeted_amount:.2f}"
                    })
                elif item.category.category_type == 'expense' and progress_pct > 90:
                    budget_alerts.append({
                        'type': 'warning',
                        'message': f"{item.category.name} is at {progress_pct:.1f}% of budget"
                    })
    
    # Handle quick transaction form
    if request.method == 'POST':
        quick_form = QuickTransactionForm(request.POST, family=family)
        if quick_form.is_valid():
            transaction = quick_form.save()
            messages.success(request, f'Transaction "{transaction.description}" added successfully!')
            return redirect('household_budget:dashboard')
    else:
        quick_form = QuickTransactionForm(family=family)
    
    # Get spending by category for chart
    category_spending = month_transactions.filter(
        transaction_type='expense'
    ).values(
        'category__name',
        'category__color'
    ).annotate(
        total=Sum('amount')
    ).order_by('-total')[:10]
    
    context = {
        'current_budget': current_budget,
        'month_income': month_income,
        'month_expenses': month_expenses,
        'month_net': month_net,
        'recent_transactions': recent_transactions,
        'savings_goals': savings_goals,
        'budget_progress': budget_progress,
        'budget_alerts': budget_alerts,
        'quick_form': quick_form,
        'category_spending': category_spending,
        'current_month': today.strftime('%B %Y'),
    }
    
    return render(request, 'household_budget/dashboard.html', context)


@login_required
@family_required
@app_permission_required('household_budget')
def budget_overview(request):
    """Detailed budget breakdown and analysis"""
    family_member = request.user.familymember_set.first()
    family = family_member.family
    
    # Get current budget
    current_budget = Budget.objects.filter(family=family, is_active=True).first()
    
    if not current_budget:
        messages.warning(request, 'No active budget found. Please create a budget first.')
        return redirect('household_budget:budget_create')
    
    # Get budget items
    budget_items = BudgetItem.objects.filter(
        budget=current_budget
    ).select_related('category').order_by('category__category_type', 'category__name')
    
    # Separate income and expense items
    income_items = budget_items.filter(category__category_type='income')
    expense_items = budget_items.filter(category__category_type='expense')
    
    # Calculate totals
    total_income_budgeted = income_items.aggregate(total=Sum('budgeted_amount'))['total'] or Decimal('0.00')
    total_income_actual = income_items.aggregate(total=Sum('actual_amount'))['total'] or Decimal('0.00')
    total_expenses_budgeted = expense_items.aggregate(total=Sum('budgeted_amount'))['total'] or Decimal('0.00')
    total_expenses_actual = expense_items.aggregate(total=Sum('actual_amount'))['total'] or Decimal('0.00')
    
    # Calculate variances
    income_variance = total_income_actual - total_income_budgeted
    expense_variance = total_expenses_budgeted - total_expenses_actual  # Positive is good (under budget)
    net_budgeted = total_income_budgeted - total_expenses_budgeted
    net_actual = total_income_actual - total_expenses_actual
    net_variance = net_actual - net_budgeted
    
    context = {
        'current_budget': current_budget,
        'income_items': income_items,
        'expense_items': expense_items,
        'total_income_budgeted': total_income_budgeted,
        'total_income_actual': total_income_actual,
        'total_expenses_budgeted': total_expenses_budgeted,
        'total_expenses_actual': total_expenses_actual,
        'income_variance': income_variance,
        'expense_variance': expense_variance,
        'net_budgeted': net_budgeted,
        'net_actual': net_actual,
        'net_variance': net_variance,
    }
    
    return render(request, 'household_budget/budget_overview.html', context)


@login_required
@family_required
@app_permission_required('household_budget')
def transaction_list(request):
    """Paginated transaction list with filtering"""
    family_member = request.user.familymember_set.first()
    family = family_member.family
    
    # Get all transactions for family
    transactions = Transaction.objects.filter(
        family=family
    ).select_related('category')
    
    # Initialize filter form
    filter_form = BudgetFilterForm(request.GET, family=family)
    
    # Apply filters
    if filter_form.is_valid():
        data = filter_form.cleaned_data
        
        if data['start_date']:
            transactions = transactions.filter(transaction_date__gte=data['start_date'])
        if data['end_date']:
            transactions = transactions.filter(transaction_date__lte=data['end_date'])
        if data['category']:
            transactions = transactions.filter(category=data['category'])
        if data['transaction_type']:
            transactions = transactions.filter(transaction_type=data['transaction_type'])
        if data['min_amount']:
            transactions = transactions.filter(amount__gte=data['min_amount'])
        if data['max_amount']:
            transactions = transactions.filter(amount__lte=data['max_amount'])
        if data['search']:
            search_q = Q(description__icontains=data['search']) | \
                      Q(payee__icontains=data['search']) | \
                      Q(notes__icontains=data['search'])
            transactions = transactions.filter(search_q)
        if data['is_reconciled']:
            is_reconciled = data['is_reconciled'] == 'true'
            transactions = transactions.filter(is_reconciled=is_reconciled)
        
        # Apply sorting
        if data['sort']:
            transactions = transactions.order_by(data['sort'])
        else:
            transactions = transactions.order_by('-transaction_date', '-created_at')
    else:
        transactions = transactions.order_by('-transaction_date', '-created_at')
    
    # Handle CSV export
    if request.GET.get('export') == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="transactions.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['Date', 'Description', 'Amount', 'Type', 'Category', 'Payee', 'Account', 'Reconciled', 'Notes'])
        
        for transaction in transactions:
            writer.writerow([
                transaction.transaction_date,
                transaction.description,
                transaction.amount,
                transaction.transaction_type,
                transaction.category.name if transaction.category else '',
                transaction.payee,
                transaction.account,
                'Yes' if transaction.is_reconciled else 'No',
                transaction.notes,
            ])
        
        return response
    
    # Pagination
    paginator = Paginator(transactions, 25)  # 25 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Calculate totals for current filter
    total_income = transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    total_expenses = transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    net_total = total_income - total_expenses
    
    context = {
        'page_obj': page_obj,
        'filter_form': filter_form,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_total': net_total,
        'total_count': transactions.count(),
    }
    
    return render(request, 'household_budget/transaction_list.html', context)


@login_required
@family_required
@app_permission_required('household_budget')
def category_management(request):
    """Manage budget categories"""
    family_member = request.user.familymember_set.first()
    family = family_member.family
    
    # Get categories by type
    income_categories = BudgetCategory.objects.filter(
        family=family,
        category_type='income'
    ).order_by('sort_order', 'name')
    
    expense_categories = BudgetCategory.objects.filter(
        family=family,
        category_type='expense'
    ).order_by('sort_order', 'name')
    
    context = {
        'income_categories': income_categories,
        'expense_categories': expense_categories,
    }
    
    return render(request, 'household_budget/category_management.html', context)


@login_required
@family_required
@app_permission_required('household_budget')
def savings_goals(request):
    """List and manage savings goals"""
    family_member = request.user.familymember_set.first()
    family = family_member.family
    
    # Get savings goals
    active_goals = SavingsGoal.objects.filter(
        family=family,
        is_active=True
    ).order_by('priority')
    
    achieved_goals = SavingsGoal.objects.filter(
        family=family
    ).filter(
        current_amount__gte=F('target_amount')
    ).order_by('-updated_at')[:5]
    
    # Handle contribution form submission
    if request.method == 'POST' and 'goal_id' in request.POST:
        goal_id = request.POST.get('goal_id')
        goal = get_object_or_404(SavingsGoal, id=goal_id, family=family)
        
        contribution_form = ContributionForm(request.POST)
        if contribution_form.is_valid():
            amount = contribution_form.cleaned_data['amount']
            description = contribution_form.cleaned_data.get('description', '')
            
            try:
                goal.add_contribution(amount, description)
                messages.success(request, f'Contribution of ${amount} added to {goal.name}!')
                return redirect('household_budget:savings_goals')
            except Exception as e:
                messages.error(request, f'Error adding contribution: {str(e)}')
    
    context = {
        'active_goals': active_goals,
        'achieved_goals': achieved_goals,
        'contribution_form': ContributionForm(),
    }
    
    return render(request, 'household_budget/savings_goals.html', context)


@login_required
@family_required
@app_permission_required('household_budget')
def reports(request):
    """Financial reports and analytics"""
    family_member = request.user.familymember_set.first()
    family = family_member.family
    
    # Get date range (default to current year)
    year = int(request.GET.get('year', timezone.now().year))
    month = request.GET.get('month')
    
    # Build date filters
    if month:
        month = int(month)
        start_date = datetime(year, month, 1).date()
        if month == 12:
            end_date = datetime(year + 1, 1, 1).date()
        else:
            end_date = datetime(year, month + 1, 1).date()
        period_name = f"{calendar.month_name[month]} {year}"
    else:
        start_date = datetime(year, 1, 1).date()
        end_date = datetime(year + 1, 1, 1).date()
        period_name = str(year)
    
    # Get transactions for period
    transactions = Transaction.objects.filter(
        family=family,
        transaction_date__gte=start_date,
        transaction_date__lt=end_date
    )
    
    # Calculate totals
    total_income = transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    total_expenses = transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    net_total = total_income - total_expenses
    
    # Spending by category
    category_breakdown = transactions.filter(
        transaction_type='expense'
    ).values(
        'category__name',
        'category__color',
        'category__is_essential'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Income by category
    income_breakdown = transactions.filter(
        transaction_type='income'
    ).values(
        'category__name',
        'category__color'
    ).annotate(
        total=Sum('amount'),
        count=Count('id')
    ).order_by('-total')
    
    # Monthly trends (if viewing full year)
    monthly_trends = []
    if not month:
        for m in range(1, 13):
            month_start = datetime(year, m, 1).date()
            if m == 12:
                month_end = datetime(year + 1, 1, 1).date()
            else:
                month_end = datetime(year, m + 1, 1).date()
            
            month_transactions = transactions.filter(
                transaction_date__gte=month_start,
                transaction_date__lt=month_end
            )
            
            month_income = month_transactions.filter(
                transaction_type='income'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            month_expenses = month_transactions.filter(
                transaction_type='expense'
            ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
            
            monthly_trends.append({
                'month': calendar.month_name[m],
                'income': month_income,
                'expenses': month_expenses,
                'net': month_income - month_expenses,
            })
    
    # Calculate essential vs non-essential spending
    essential_spending = transactions.filter(
        transaction_type='expense',
        category__is_essential=True
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    non_essential_spending = transactions.filter(
        transaction_type='expense',
        category__is_essential=False
    ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    
    context = {
        'year': year,
        'month': month,
        'period_name': period_name,
        'total_income': total_income,
        'total_expenses': total_expenses,
        'net_total': net_total,
        'category_breakdown': category_breakdown,
        'income_breakdown': income_breakdown,
        'monthly_trends': monthly_trends,
        'essential_spending': essential_spending,
        'non_essential_spending': non_essential_spending,
        'years': range(2020, timezone.now().year + 2),
        'months': [(i, calendar.month_name[i]) for i in range(1, 13)],
    }
    
    return render(request, 'household_budget/reports.html', context)


# AJAX Views

@login_required
@family_required
@app_permission_required('household_budget')
def quick_transaction(request):
    """AJAX endpoint for quick transaction entry"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})
    
    family_member = request.user.familymember_set.first()
    family = family_member.family
    
    form = QuickTransactionForm(request.POST, family=family)
    if form.is_valid():
        transaction = form.save()
        return JsonResponse({
            'success': True,
            'transaction': {
                'id': transaction.id,
                'description': transaction.description,
                'amount': str(transaction.amount),
                'category': transaction.category.name if transaction.category else '',
                'type': transaction.get_transaction_type_display(),
                'date': transaction.transaction_date.strftime('%Y-%m-%d'),
            }
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        })


@login_required
@family_required
@app_permission_required('household_budget')
def budget_chart_data(request):
    """JSON data for budget charts"""
    family_member = request.user.familymember_set.first()
    family = family_member.family
    
    chart_type = request.GET.get('type', 'spending')
    
    # Get current month data
    today = timezone.now().date()
    month_start = today.replace(day=1)
    next_month = month_start.replace(month=month_start.month + 1) if month_start.month < 12 else month_start.replace(year=month_start.year + 1, month=1)
    
    transactions = Transaction.objects.filter(
        family=family,
        transaction_date__gte=month_start,
        transaction_date__lt=next_month
    )
    
    if chart_type == 'spending':
        # Spending by category
        data = transactions.filter(
            transaction_type='expense'
        ).values(
            'category__name',
            'category__color'
        ).annotate(
            total=Sum('amount')
        ).order_by('-total')[:10]
        
        chart_data = {
            'labels': [item['category__name'] or 'Uncategorized' for item in data],
            'datasets': [{
                'data': [float(item['total']) for item in data],
                'backgroundColor': [item['category__color'] or '#6c757d' for item in data],
            }]
        }
        
    elif chart_type == 'budget_vs_actual':
        # Budget vs actual comparison
        current_budget = Budget.objects.filter(family=family, is_active=True).first()
        if current_budget:
            budget_items = BudgetItem.objects.filter(
                budget=current_budget,
                category__category_type='expense'
            ).select_related('category')
            
            labels = []
            budgeted = []
            actual = []
            colors = []
            
            for item in budget_items:
                actual_amount = transactions.filter(
                    category=item.category
                ).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
                
                labels.append(item.category.name)
                budgeted.append(float(item.budgeted_amount))
                actual.append(float(actual_amount))
                colors.append(item.category.color)
            
            chart_data = {
                'labels': labels,
                'datasets': [
                    {
                        'label': 'Budgeted',
                        'data': budgeted,
                        'backgroundColor': 'rgba(54, 162, 235, 0.8)',
                    },
                    {
                        'label': 'Actual',
                        'data': actual,
                        'backgroundColor': 'rgba(255, 99, 132, 0.8)',
                    }
                ]
            }
        else:
            chart_data = {'labels': [], 'datasets': []}
    
    else:
        chart_data = {'labels': [], 'datasets': []}
    
    return JsonResponse(chart_data)


# Class-Based Views (Simplified)

class BudgetCreateView(LoginRequiredMixin, CreateView):
    """Create new budget"""
    model = Budget
    form_class = BudgetForm
    template_name = 'household_budget/budget_form.html'
    success_url = reverse_lazy('household_budget:budget_overview')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get family from user
        family_member = self.request.user.familymember_set.first()
        kwargs['family'] = family_member.family if family_member else None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Budget created successfully!')
        return super().form_valid(form)


class BudgetUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing budget"""
    model = Budget
    form_class = BudgetForm
    template_name = 'household_budget/budget_form.html'
    success_url = reverse_lazy('household_budget:budget_overview')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get family from user
        family_member = self.request.user.familymember_set.first()
        kwargs['family'] = family_member.family if family_member else None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Budget updated successfully!')
        return super().form_valid(form)


class TransactionCreateView(LoginRequiredMixin, CreateView):
    """Create new transaction"""
    model = Transaction
    form_class = TransactionForm
    template_name = 'household_budget/transaction_form.html'
    success_url = reverse_lazy('household_budget:transaction_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get family from user
        family_member = self.request.user.familymember_set.first()
        kwargs['family'] = family_member.family if family_member else None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Transaction added successfully!')
        return super().form_valid(form)


class TransactionUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing transaction"""
    model = Transaction
    form_class = TransactionForm
    template_name = 'household_budget/transaction_form.html'
    success_url = reverse_lazy('household_budget:transaction_list')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get family from user
        family_member = self.request.user.familymember_set.first()
        kwargs['family'] = family_member.family if family_member else None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Transaction updated successfully!')
        return super().form_valid(form)


class TransactionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete transaction"""
    model = Transaction
    template_name = 'household_budget/transaction_confirm_delete.html'
    success_url = reverse_lazy('household_budget:transaction_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Transaction deleted successfully!')
        return super().delete(request, *args, **kwargs)


class CategoryCreateView(LoginRequiredMixin, CreateView):
    """Create new budget category"""
    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = 'household_budget/category_form.html'
    success_url = reverse_lazy('household_budget:category_management')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get family from user
        family_member = self.request.user.familymember_set.first()
        kwargs['family'] = family_member.family if family_member else None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Category created successfully!')
        return super().form_valid(form)


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing budget category"""
    model = BudgetCategory
    form_class = BudgetCategoryForm
    template_name = 'household_budget/category_form.html'
    success_url = reverse_lazy('household_budget:category_management')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get family from user
        family_member = self.request.user.familymember_set.first()
        kwargs['family'] = family_member.family if family_member else None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Category updated successfully!')
        return super().form_valid(form)


class SavingsGoalCreateView(LoginRequiredMixin, CreateView):
    """Create new savings goal"""
    model = SavingsGoal
    form_class = SavingsGoalForm
    template_name = 'household_budget/savings_goal_form.html'
    success_url = reverse_lazy('household_budget:savings_goals')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get family from user
        family_member = self.request.user.familymember_set.first()
        kwargs['family'] = family_member.family if family_member else None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Savings goal created successfully!')
        return super().form_valid(form)


class SavingsGoalUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing savings goal"""
    model = SavingsGoal
    form_class = SavingsGoalForm
    template_name = 'household_budget/savings_goal_form.html'
    success_url = reverse_lazy('household_budget:savings_goals')
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        # Get family from user
        family_member = self.request.user.familymember_set.first()
        kwargs['family'] = family_member.family if family_member else None
        return kwargs
    
    def form_valid(self, form):
        messages.success(self.request, 'Savings goal updated successfully!')
        return super().form_valid(form)
