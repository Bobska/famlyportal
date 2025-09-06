from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.db.models import Sum, Q
from django.http import JsonResponse
from datetime import datetime, date
from decimal import Decimal

from accounts.decorators import family_required, app_permission_required
from .models import Category, Transaction


# Dashboard View
@login_required
@family_required
@app_permission_required('household_budget')
def dashboard(request):
    """Budget app dashboard"""
    family = request.user.primary_family
    
    # Get current month transactions summary
    current_month = date.today().replace(day=1)
    current_year = current_month.year
    current_month_num = current_month.month
    
    monthly_transactions = Transaction.objects.filter(
        family=family,
        date__year=current_year,
        date__month=current_month_num
    )
    
    # Calculate monthly totals
    monthly_income = monthly_transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    monthly_expenses = monthly_transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(family=family)[:10]
    
    # Get top categories
    top_categories = Category.objects.filter(
        family=family,
        transaction__transaction_type='expense',
        transaction__date__year=current_year,
        transaction__date__month=current_month_num
    ).annotate(
        total_spent=Sum('transaction__amount')
    ).order_by('-total_spent')[:5]
    
    context = {
        'monthly_income': monthly_income,
        'monthly_expenses': monthly_expenses,
        'monthly_net': monthly_income - monthly_expenses,
        'recent_transactions': recent_transactions,
        'top_categories': top_categories,
        'current_month': current_month,
    }
    
    return render(request, 'household_budget/dashboard.html', context)


# Transaction Views
@method_decorator([login_required, family_required, app_permission_required('household_budget')], name='dispatch')
class TransactionListView(ListView):
    model = Transaction
    template_name = 'household_budget/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 25
    
    def get_queryset(self):
        queryset = Transaction.objects.filter(family=self.request.user.primary_family)
        
        # Filter by transaction type
        transaction_type = self.request.GET.get('type')
        if transaction_type and transaction_type in ['income', 'expense', 'transfer']:
            queryset = queryset.filter(transaction_type=transaction_type)
        
        # Filter by category
        category_id = self.request.GET.get('category')
        if category_id:
            try:
                category = Category.objects.get(id=category_id, family=self.request.user.primary_family)
                queryset = queryset.filter(category=category)
            except Category.DoesNotExist:
                pass
        
        # Filter by date range
        date_from = self.request.GET.get('date_from')
        date_to = self.request.GET.get('date_to')
        if date_from:
            queryset = queryset.filter(date__gte=date_from)
        if date_to:
            queryset = queryset.filter(date__lte=date_to)
        
        return queryset.order_by('-date', '-created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            family=self.request.user.primary_family,
            is_active=True
        ).order_by('name')
        return context


@method_decorator([login_required, family_required, app_permission_required('household_budget')], name='dispatch')
class TransactionCreateView(CreateView):
    model = Transaction
    template_name = 'household_budget/transaction_form.html'
    fields = ['merchant_payee', 'date', 'amount', 'transaction_type', 'category', 'notes']
    success_url = reverse_lazy('household_budget:transaction_list')
    
    def form_valid(self, form):
        form.instance.family = self.request.user.primary_family
        messages.success(self.request, 'Transaction added successfully!')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter categories by family
        form.fields['category'].queryset = Category.objects.filter(
            family=self.request.user.primary_family,
            is_active=True
        ).order_by('name')
        # Set default date to today
        form.fields['date'].initial = date.today()
        return form


@method_decorator([login_required, family_required, app_permission_required('household_budget')], name='dispatch')
class TransactionUpdateView(UpdateView):
    model = Transaction
    template_name = 'household_budget/transaction_form.html'
    fields = ['merchant_payee', 'date', 'amount', 'transaction_type', 'category', 'notes']
    success_url = reverse_lazy('household_budget:transaction_list')
    
    def get_queryset(self):
        return Transaction.objects.filter(family=self.request.user.primary_family)
    
    def form_valid(self, form):
        messages.success(self.request, 'Transaction updated successfully!')
        return super().form_valid(form)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Filter categories by family
        form.fields['category'].queryset = Category.objects.filter(
            family=self.request.user.primary_family,
            is_active=True
        ).order_by('name')
        return form


@method_decorator([login_required, family_required, app_permission_required('household_budget')], name='dispatch')
class TransactionDeleteView(DeleteView):
    model = Transaction
    template_name = 'household_budget/transaction_confirm_delete.html'
    success_url = reverse_lazy('household_budget:transaction_list')
    
    def get_queryset(self):
        return Transaction.objects.filter(family=self.request.user.primary_family)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Transaction deleted successfully!')
        return super().delete(request, *args, **kwargs)


# Category Views
@login_required
@family_required
@app_permission_required('household_budget')
def category_tree(request):
    """Category management with tree view"""
    family = request.user.primary_family
    
    # Get root categories (no parent)
    root_categories = Category.objects.filter(
        family=family,
        parent__isnull=True,
        is_active=True
    ).order_by('sort_order', 'name')
    
    context = {
        'root_categories': root_categories,
    }
    
    return render(request, 'household_budget/category_tree.html', context)


# Reports View
@login_required
@family_required
@app_permission_required('household_budget')
def reports(request):
    """Budget reports and summaries"""
    family = request.user.primary_family
    
    # Get date range from request or default to current month
    today = date.today()
    start_date = request.GET.get('start_date', today.replace(day=1))
    end_date = request.GET.get('end_date', today)
    
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    
    # Get transactions for the period
    transactions = Transaction.objects.filter(
        family=family,
        date__range=[start_date, end_date]
    )
    
    # Calculate totals
    income_total = transactions.filter(transaction_type='income').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    expense_total = transactions.filter(transaction_type='expense').aggregate(
        total=Sum('amount'))['total'] or Decimal('0.00')
    
    # Category breakdown
    category_breakdown = Category.objects.filter(
        family=family,
        transaction__in=transactions,
        transaction__transaction_type='expense'
    ).annotate(
        total_spent=Sum('transaction__amount')
    ).order_by('-total_spent')[:10]
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'income_total': income_total,
        'expense_total': expense_total,
        'net_total': income_total - expense_total,
        'category_breakdown': category_breakdown,
        'transactions': transactions[:20],  # Recent transactions
    }
    
    return render(request, 'household_budget/reports.html', context)
