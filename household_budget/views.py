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
from .forms import TransactionForm, CategoryForm
from accounts.models import Family, FamilyMember
from accounts.decorators import family_required

def get_user_family(user):
    """Helper function to get user's family"""
    try:
        family_member = FamilyMember.objects.get(user=user)
        return family_member.family
    except FamilyMember.DoesNotExist:
        return None


# Dashboard View
@login_required
@family_required
def dashboard(request):
    """Budget app dashboard"""
    # For now, simple dashboard without family filtering
    context = {
        'monthly_income': Decimal('0.00'),
        'monthly_expenses': Decimal('0.00'),
        'monthly_net': Decimal('0.00'),
        'recent_transactions': Transaction.objects.all()[:10],
        'top_categories': [],
    }
    return render(request, 'household_budget/dashboard.html', context)


# Transaction Views
@method_decorator(login_required, name='dispatch')
class TransactionListView(ListView):
    model = Transaction
    template_name = 'household_budget/transaction_list.html'
    context_object_name = 'transactions'
    paginate_by = 25
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['total_income'] = Decimal('0.00')
        context['total_expenses'] = Decimal('0.00')
        context['net_total'] = Decimal('0.00')
        return context


@method_decorator([login_required, family_required], name='dispatch')
class TransactionCreateView(CreateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'household_budget/transaction_form.html'
    success_url = reverse_lazy('household_budget:transaction_list')
    
    def form_valid(self, form):
        """Set the family from the current user"""
        try:
            family_member = FamilyMember.objects.get(user=self.request.user)
            form.instance.family = family_member.family
            return super().form_valid(form)
        except FamilyMember.DoesNotExist:
            messages.error(self.request, "You must be part of a family to create transactions. Please join or create a family first.")
            return redirect('accounts:dashboard')
    
    def get_form_kwargs(self):
        """Add family to form kwargs"""
        kwargs = super().get_form_kwargs()
        family = get_user_family(self.request.user)
        kwargs['family'] = family
        return kwargs


@method_decorator([login_required, family_required], name='dispatch')
class TransactionUpdateView(UpdateView):
    model = Transaction
    form_class = TransactionForm
    template_name = 'household_budget/transaction_form.html'
    success_url = reverse_lazy('household_budget:transaction_list')
    
    def get_form_kwargs(self):
        """Add family to form kwargs"""
        kwargs = super().get_form_kwargs()
        family = get_user_family(self.request.user)
        kwargs['family'] = family
        return kwargs


@method_decorator([login_required, family_required], name='dispatch')
class TransactionDeleteView(DeleteView):
    model = Transaction
    template_name = 'household_budget/transaction_confirm_delete.html'
    success_url = reverse_lazy('household_budget:transaction_list')


# Category Views
@login_required 
@family_required
def category_tree(request):
    """Category tree management view"""
    categories = Category.objects.filter(parent__isnull=True)
    
    context = {
        'categories': categories,
        'category_stats': [],
    }
    return render(request, 'household_budget/category_tree.html', context)


@method_decorator([login_required, family_required], name='dispatch')
class CategoryCreateView(CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'household_budget/category_form.html'
    success_url = reverse_lazy('household_budget:category_tree')
    
    def form_valid(self, form):
        """Set the family from the current user"""
        try:
            family_member = FamilyMember.objects.get(user=self.request.user)
            form.instance.family = family_member.family
            return super().form_valid(form)
        except FamilyMember.DoesNotExist:
            messages.error(self.request, "You must be part of a family to create categories. Please join or create a family first.")
            return redirect('accounts:dashboard')
    
    def get_form_kwargs(self):
        """Add family to form kwargs"""
        kwargs = super().get_form_kwargs()
        family = get_user_family(self.request.user)
        kwargs['family'] = family
        return kwargs


# Reports View
@login_required
@family_required
def reports(request):
    """Budget reports view"""
    context = {
        'monthly_data': [],
        'category_breakdown': [],
    }
    return render(request, 'household_budget/reports.html', context)
