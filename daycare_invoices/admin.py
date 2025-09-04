from django.contrib import admin
from .models import DaycareProvider, Child, Invoice, Payment


@admin.register(DaycareProvider)
class DaycareProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'family', 'contact_person', 'phone', 'email', 'is_active']
    list_filter = ['is_active', 'family']
    search_fields = ['name', 'contact_person', 'phone', 'email']
    ordering = ['family', 'name']
    raw_id_fields = ['family']


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ['name', 'family', 'date_of_birth', 'daycare_provider', 'enrollment_date', 'is_enrolled']
    list_filter = ['is_enrolled', 'family', 'daycare_provider']
    search_fields = ['name', 'family__name']
    date_hierarchy = 'enrollment_date'
    ordering = ['family', 'name']
    raw_id_fields = ['family', 'daycare_provider']


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'daycare_provider', 'child', 'family', 'invoice_date', 'due_date', 'total_amount', 'status']
    list_filter = ['status', 'family', 'daycare_provider', 'service_period_start']
    search_fields = ['invoice_number', 'child__name', 'daycare_provider__name']
    date_hierarchy = 'invoice_date'
    ordering = ['-invoice_date']
    raw_id_fields = ['family', 'daycare_provider', 'child']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'payment_date', 'amount', 'payment_method', 'status', 'confirmation_number']
    list_filter = ['status', 'payment_method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'confirmation_number']
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']
    raw_id_fields = ['invoice']
