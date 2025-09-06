from django.contrib import admin
from .models import Category, Transaction


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'family', 'icon', 'color', 'is_active', 'sort_order']
    list_filter = ['is_active', 'family', 'parent']
    search_fields = ['name']
    ordering = ['family', 'sort_order', 'name']
    raw_id_fields = ['family', 'parent']
    list_editable = ['sort_order', 'is_active']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('family', 'parent')


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['merchant_payee', 'amount', 'transaction_type', 'category', 'date', 'family']
    list_filter = ['transaction_type', 'family', 'category', 'date']
    search_fields = ['merchant_payee', 'notes']
    date_hierarchy = 'date'
    ordering = ['-date', '-created_at']
    raw_id_fields = ['family', 'category']
    list_per_page = 50
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('family', 'category')
