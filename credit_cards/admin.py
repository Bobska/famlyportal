from django.contrib import admin
from .models import CreditCard, Transaction, Payment


@admin.register(CreditCard)
class CreditCardAdmin(admin.ModelAdmin):
    list_display = ['nickname', 'card_type', 'last_four_digits', 'issuer', 'family', 'current_balance', 'credit_limit', 'is_active']
    list_filter = ['card_type', 'is_active', 'family', 'issuer']
    search_fields = ['nickname', 'last_four_digits', 'issuer', 'account_holder']
    ordering = ['family', 'nickname']
    raw_id_fields = ['family']
    
    def get_readonly_fields(self, request, obj=None):
        # Make available_credit readonly since it's auto-calculated
        return ['available_credit'] + list(self.readonly_fields or [])


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['transaction_date', 'description', 'merchant', 'amount', 'credit_card', 'transaction_type', 'is_pending']
    list_filter = ['transaction_type', 'is_pending', 'transaction_date', 'credit_card__family']
    search_fields = ['description', 'merchant', 'reference_number']
    date_hierarchy = 'transaction_date'
    ordering = ['-transaction_date']
    raw_id_fields = ['credit_card']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['payment_date', 'credit_card', 'amount', 'payment_method', 'is_scheduled', 'confirmation_number']
    list_filter = ['payment_method', 'is_scheduled', 'payment_date']
    search_fields = ['confirmation_number', 'credit_card__nickname']
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']
    raw_id_fields = ['credit_card']
