from django.contrib import admin
from core.admin import FamilyScopedModelAdmin
from .models import (
    Account, AccountHistory, WeeklyPeriod, BudgetTemplate,
    Allocation, Transaction, AccountLoan, LoanPayment, FamilySettings
)


@admin.register(Account)
class AccountAdmin(FamilyScopedModelAdmin):
    """Admin for Account model"""
    list_display = ['name', 'account_type', 'parent', 'is_active', 'sort_order']
    list_filter = ['account_type', 'is_active']
    search_fields = ['name', 'description']
    ordering = ['sort_order', 'name']


@admin.register(AccountHistory)
class AccountHistoryAdmin(FamilyScopedModelAdmin):
    """Admin for AccountHistory model"""
    list_display = ['account', 'action', 'timestamp']
    list_filter = ['action', 'timestamp']
    readonly_fields = ['timestamp']


@admin.register(WeeklyPeriod)
class WeeklyPeriodAdmin(FamilyScopedModelAdmin):
    """Admin for WeeklyPeriod model"""
    list_display = ['start_date', 'end_date', 'is_active', 'is_allocated', 'allocation_locked']
    list_filter = ['is_active', 'is_allocated', 'allocation_locked']
    ordering = ['-start_date']


@admin.register(BudgetTemplate)
class BudgetTemplateAdmin(FamilyScopedModelAdmin):
    """Admin for BudgetTemplate model"""
    list_display = ['account', 'allocation_type', 'priority', 'is_essential', 'is_active']
    list_filter = ['allocation_type', 'priority', 'is_essential', 'is_active']
    ordering = ['priority', 'account__name']


@admin.register(Allocation)
class AllocationAdmin(FamilyScopedModelAdmin):
    """Admin for Allocation model"""
    list_display = ['week', 'from_account', 'to_account', 'amount']
    list_filter = ['week']
    ordering = ['-week__start_date']


@admin.register(Transaction)
class TransactionAdmin(FamilyScopedModelAdmin):
    """Admin for Transaction model"""
    list_display = ['transaction_date', 'account', 'description', 'amount', 'transaction_type', 'is_reconciled']
    list_filter = ['transaction_type', 'is_reconciled', 'transaction_date']
    search_fields = ['description', 'payee']
    ordering = ['-transaction_date']


@admin.register(AccountLoan)
class AccountLoanAdmin(FamilyScopedModelAdmin):
    """Admin for AccountLoan model"""
    list_display = ['lender_account', 'borrower_account', 'remaining_amount', 'weekly_interest_rate', 'is_active']
    list_filter = ['is_active', 'loan_date']
    ordering = ['-loan_date']


@admin.register(LoanPayment)
class LoanPaymentAdmin(FamilyScopedModelAdmin):
    """Admin for LoanPayment model"""
    list_display = ['loan', 'amount', 'payment_date']
    list_filter = ['payment_date']
    ordering = ['-payment_date']


@admin.register(FamilySettings)
class FamilySettingsAdmin(FamilyScopedModelAdmin):
    """Admin for FamilySettings model"""
    list_display = ['family', 'week_start_day', 'auto_allocate_enabled', 'auto_repay_enabled']
    list_filter = ['week_start_day', 'auto_allocate_enabled', 'auto_repay_enabled']
