from django.contrib import admin
from .models import DaycareProvider, Child, Invoice, Payment


@admin.register(DaycareProvider)
class DaycareProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'family', 'contact_person', 'email', 'is_active']
    list_filter = ['is_active', 'family']
    search_fields = ['name', 'contact_person', 'email']
    ordering = ['family', 'name']
    raw_id_fields = ['family']


@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'family', 'date_of_birth', 'provider', 'start_date', 'is_enrolled']
    list_filter = ['is_enrolled', 'family', 'provider']
    search_fields = ['first_name', 'last_name', 'family__name']
    date_hierarchy = 'start_date'
    ordering = ['family', 'last_name', 'first_name']
    raw_id_fields = ['family', 'provider']
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Name'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ['invoice_number', 'provider', 'child', 'family', 'invoice_date', 'due_date', 'amount', 'status']
    list_filter = ['status', 'family', 'provider', 'services_start_date']
    search_fields = ['invoice_number', 'child__first_name', 'child__last_name', 'provider__name']
    date_hierarchy = 'invoice_date'
    ordering = ['-invoice_date']
    raw_id_fields = ['family', 'provider', 'child']


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['invoice', 'payment_date', 'amount', 'method', 'reference_number']
    list_filter = ['method', 'payment_date']
    search_fields = ['invoice__invoice_number', 'reference_number']
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']
    raw_id_fields = ['invoice']
