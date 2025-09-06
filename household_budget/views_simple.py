from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.utils.decorators import method_decorator
from django.db.models import Sum
from datetime import date
from decimal import Decimal

from .models import Category, Transaction


# Dashboard View
@login_required
def dashboard(request):
    """Budget app dashboard"""
    # For now, simple dashboard without family filtering
    context = {
        'monthly_income': Decimal('0.00'),
        'monthly_expenses': Decimal('0.00'),
        'monthly_net': Decimal('0.00'),
        'recent_transactions': Transaction.objects.all()[:10],
    }
    return render(request, 'household_budget/dashboard.html', context)


# Transaction Views
@method_decorator(login_required, name='dispatch')
class TransactionListView(ListView):
    model = Transaction
    template_name = 'household_budget/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 25


@method_decorator(login_required, name='dispatch')
class TransactionCreateView(CreateView):
    model = Transaction
    template_name = 'household_budget/transaction_form.html'
    fields = ['merchant_payee', 'date', 'amount', 'transaction_type', 'category', 'notes']
    success_url = reverse_lazy('household_budget:transaction_list')


@method_decorator(login_required, name='dispatch')
class TransactionUpdateView(UpdateView):
    model = Transaction
    template_name = 'household_budget/transaction_form.html'
    fields = ['merchant_payee', 'date', 'amount', 'transaction_type', 'category', 'notes']
    success_url = reverse_lazy('household_budget:transaction_list')


@method_decorator(login_required, name='dispatch')
class TransactionDeleteView(DeleteView):
    model = Transaction
    template_name = 'household_budget/transaction_confirm_delete.html'
    success_url = reverse_lazy('household_budget:transaction_list')


# Category Views
@login_required
def category_tree(request):
    """Category management with tree view"""
    root_categories = Category.objects.filter(parent__isnull=True, is_active=True)
    context = {'root_categories': root_categories}
    return render(request, 'household_budget/category_tree.html', context)


# Reports View
@login_required
def reports(request):
    """Budget reports and summaries"""
    context = {
        'income_total': Decimal('0.00'),
        'expense_total': Decimal('0.00'),
        'net_total': Decimal('0.00'),
    }
    return render(request, 'household_budget/reports.html', context)
