from django.contrib import admin
from .models import BudgetCategory, Budget, BudgetItem, Transaction, SavingsGoal


@admin.register(BudgetCategory)
class BudgetCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'family', 'is_essential', 'is_active', 'sort_order']
    list_filter = ['category_type', 'is_essential', 'is_active', 'family']
    search_fields = ['name', 'description']
    ordering = ['family', 'category_type', 'sort_order', 'name']
    raw_id_fields = ['family', 'parent_category']


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ['name', 'family', 'start_date', 'end_date', 'is_active']
    list_filter = ['is_active', 'family', 'start_date']
    search_fields = ['name', 'description']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    raw_id_fields = ['family']


@admin.register(BudgetItem)
class BudgetItemAdmin(admin.ModelAdmin):
    list_display = ['budget', 'category', 'budgeted_amount', 'actual_amount']
    list_filter = ['budget__family', 'category__category_type', 'category__is_essential']
    search_fields = ['budget__name', 'category__name']
    ordering = ['budget', 'category__category_type', 'category__sort_order']
    raw_id_fields = ['budget', 'category']
    
    def get_readonly_fields(self, request, obj=None):
        # Make actual_amount readonly since it's auto-calculated
        return ['actual_amount'] + list(self.readonly_fields or [])


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_date', 'description', 'amount', 'category', 'transaction_type', 'family', 'is_reconciled']
    list_filter = ['transaction_type', 'is_reconciled', 'family', 'category__category_type']
    search_fields = ['description', 'payee', 'reference_number']
    date_hierarchy = 'transaction_date'
    ordering = ['-transaction_date']
    raw_id_fields = ['family', 'category']


@admin.register(SavingsGoal)
class SavingsGoalAdmin(admin.ModelAdmin):
    list_display = ['name', 'family', 'target_amount', 'current_amount', 'target_date', 'priority', 'is_active']
    list_filter = ['is_active', 'family', 'priority', 'target_date']
    search_fields = ['name', 'description']
    ordering = ['family', 'priority', 'target_date']
    raw_id_fields = ['family']
