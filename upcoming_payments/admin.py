from django.contrib import admin
from .models import PaymentCategory, RecurringPayment, PaymentInstance, PaymentReminder


@admin.register(PaymentCategory)
class PaymentCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'family', 'is_active']
    list_filter = ['is_active', 'family']
    search_fields = ['name', 'description']
    ordering = ['family', 'name']
    raw_id_fields = ['family']


@admin.register(RecurringPayment)
class RecurringPaymentAdmin(admin.ModelAdmin):
    list_display = ['payee', 'amount', 'frequency', 'next_due_date', 'family', 'is_active']
    list_filter = ['frequency', 'is_active', 'auto_pay', 'family']
    search_fields = ['payee', 'description']
    date_hierarchy = 'next_due_date'
    ordering = ['next_due_date', 'payee']
    raw_id_fields = ['family', 'category']


@admin.register(PaymentInstance)
class PaymentInstanceAdmin(admin.ModelAdmin):
    list_display = ['recurring_payment', 'due_date', 'amount', 'status', 'paid_date']
    list_filter = ['status', 'due_date', 'family']
    search_fields = ['recurring_payment__payee', 'confirmation_number']
    date_hierarchy = 'due_date'
    ordering = ['due_date']
    raw_id_fields = ['family', 'recurring_payment']


@admin.register(PaymentReminder)
class PaymentReminderAdmin(admin.ModelAdmin):
    list_display = ['payment_instance', 'reminder_date', 'sent_date', 'email_sent', 'push_sent']
    list_filter = ['email_sent', 'push_sent', 'reminder_date']
    search_fields = ['payment_instance__recurring_payment__payee']
    date_hierarchy = 'reminder_date'
    ordering = ['reminder_date']
    raw_id_fields = ['family', 'payment_instance']
