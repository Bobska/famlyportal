from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count, Q
from django.urls import reverse
from decimal import Decimal
from core.admin import FamilyScopedModelAdmin
from .models import DaycareProvider, Child, Invoice, Payment


@admin.register(DaycareProvider)
class DaycareProviderAdmin(FamilyScopedModelAdmin):
    """Enhanced Daycare Provider Admin with family scoping"""
    
    list_display = [
        'name', 
        'contact_person',
        'email',
        'child_count_display',
        'invoice_count_display',
        'status_display'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'contact_person', 'email', 'phone']
    ordering = ['name']
    raw_id_fields = ['family']
    
    fieldsets = (
        ('Provider Information', {
            'fields': ('name', 'family', 'contact_person', 'email', 'phone')
        }),
        ('Address', {
            'fields': ('address',),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with counts"""
        qs = super().get_queryset(request)
        return qs.annotate(
            child_count_annotated=Count('child'),
            invoice_count_annotated=Count('invoice')
        )
    
    def child_count_display(self, obj):
        """Display enrolled children count"""
        count = getattr(obj, 'child_count_annotated', obj.child_set.count())
        if count > 0:
            return format_html(
                '<a href="{}?provider__id__exact={}">{} children</a>',
                reverse('admin:daycare_invoices_child_changelist'),
                obj.id,
                count
            )
        return '0 children'
    child_count_display.short_description = 'Children'
    child_count_display.admin_order_field = 'child_count_annotated'
    
    def invoice_count_display(self, obj):
        """Display invoice count"""
        count = getattr(obj, 'invoice_count_annotated', obj.invoice_set.count())
        if count > 0:
            return format_html(
                '<a href="{}?provider__id__exact={}">{} invoices</a>',
                reverse('admin:daycare_invoices_invoice_changelist'),
                obj.id,
                count
            )
        return '0 invoices'
    invoice_count_display.short_description = 'Invoices'
    invoice_count_display.admin_order_field = 'invoice_count_annotated'
    
    def status_display(self, obj):
        """Display provider status"""
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> Active')
        return format_html('<span style="color: red;">●</span> Inactive')
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'is_active'


@admin.register(Child)
class ChildAdmin(FamilyScopedModelAdmin):
    """Enhanced Child Admin with family scoping"""
    
    list_display = [
        'full_name_display', 
        'age_display',
        'provider', 
        'enrollment_period_display',
        'status_display'
    ]
    list_filter = ['is_enrolled', 'provider', 'start_date']
    search_fields = ['first_name', 'last_name', 'provider__name']
    date_hierarchy = 'start_date'
    ordering = ['last_name', 'first_name']
    raw_id_fields = ['family', 'provider']
    
    fieldsets = (
        ('Child Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'family')
        }),
        ('Enrollment Details', {
            'fields': ('provider', 'start_date', 'end_date', 'is_enrolled')
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('provider', 'family')
    
    def full_name_display(self, obj):
        """Display full name with link"""
        return format_html(
            '<strong>{} {}</strong>',
            obj.first_name,
            obj.last_name
        )
    full_name_display.short_description = 'Name'
    full_name_display.admin_order_field = 'last_name'
    
    def age_display(self, obj):
        """Display child's age"""
        from datetime import date
        today = date.today()
        age = today.year - obj.date_of_birth.year
        if today.month < obj.date_of_birth.month or (today.month == obj.date_of_birth.month and today.day < obj.date_of_birth.day):
            age -= 1
        return f"{age} years old"
    age_display.short_description = 'Age'
    
    def enrollment_period_display(self, obj):
        """Display enrollment period"""
        if obj.end_date:
            return format_html(
                '<span style="font-family: monospace;">{} - {}</span>',
                obj.start_date.strftime('%m/%d/%Y'),
                obj.end_date.strftime('%m/%d/%Y')
            )
        return format_html(
            '<span style="font-family: monospace;">Since {}</span>',
            obj.start_date.strftime('%m/%d/%Y')
        )
    enrollment_period_display.short_description = 'Enrollment Period'
    enrollment_period_display.admin_order_field = 'start_date'
    
    def status_display(self, obj):
        """Display enrollment status"""
        if obj.is_enrolled:
            return format_html('<span style="color: green;">●</span> Enrolled')
        return format_html('<span style="color: red;">●</span> Not Enrolled')
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'is_enrolled'


@admin.register(Invoice)
class InvoiceAdmin(FamilyScopedModelAdmin):
    """Enhanced Invoice Admin with family scoping"""
    
    list_display = [
        'invoice_number',
        'provider',
        'child_display',
        'period_display',
        'amount_display',
        'due_date',
        'status_display'
    ]
    list_filter = ['status', 'provider', 'services_start_date', 'due_date']
    search_fields = ['invoice_number', 'child__first_name', 'child__last_name', 'provider__name']
    date_hierarchy = 'invoice_date'
    ordering = ['-invoice_date']
    raw_id_fields = ['family', 'provider', 'child']
    
    fieldsets = (
        ('Invoice Details', {
            'fields': ('invoice_number', 'family', 'provider', 'child')
        }),
        ('Dates & Amount', {
            'fields': ('invoice_date', 'due_date', 'services_start_date', 'services_end_date', 'amount')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('provider', 'child', 'family')
    
    def child_display(self, obj):
        """Display child name with link"""
        return format_html(
            '<a href="{}" title="Age: {}">{} {}</a>',
            reverse('admin:daycare_invoices_child_change', args=[obj.child.id]),
            obj.child.age_display() if hasattr(obj.child, 'age_display') else 'Unknown',
            obj.child.first_name,
            obj.child.last_name
        )
    child_display.short_description = 'Child'
    child_display.admin_order_field = 'child__last_name'
    
    def period_display(self, obj):
        """Display service period"""
        return format_html(
            '<span style="font-family: monospace;">{} - {}</span>',
            obj.services_start_date.strftime('%m/%d'),
            obj.services_end_date.strftime('%m/%d/%Y')
        )
    period_display.short_description = 'Service Period'
    period_display.admin_order_field = 'services_start_date'
    
    def amount_display(self, obj):
        """Display amount with formatting"""
        return format_html(
            '<strong style="color: blue;">${:,.2f}</strong>',
            obj.amount
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def status_display(self, obj):
        """Display invoice status with color"""
        status_colors = {
            'pending': 'orange',
            'paid': 'green',
            'overdue': 'red',
            'cancelled': 'gray'
        }
        color = status_colors.get(obj.status, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">●</span> {}',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'status'
    
    def mark_as_paid(self, request, queryset):
        """Bulk action to mark invoices as paid"""
        updated = queryset.update(status='paid')
        self.message_user(request, f'Marked {updated} invoices as paid.')
    mark_as_paid.short_description = "Mark as paid"


@admin.register(Payment)
class PaymentAdmin(FamilyScopedModelAdmin):
    """Enhanced Payment Admin with family scoping"""
    
    list_display = [
        'invoice_display',
        'amount_display',
        'payment_date',
        'method',
        'reference_number',
        'created_display'
    ]
    list_filter = ['method', 'payment_date', 'created_at']
    search_fields = ['invoice__invoice_number', 'reference_number']
    date_hierarchy = 'payment_date'
    ordering = ['-payment_date']
    raw_id_fields = ['invoice']
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('invoice', 'amount', 'payment_date')
        }),
        ('Payment Method', {
            'fields': ('method', 'reference_number')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('invoice__provider', 'invoice__child')
    
    def invoice_display(self, obj):
        """Display invoice with child and provider info"""
        return format_html(
            '<a href="{}" title="Child: {} {} | Provider: {}">{}</a>',
            reverse('admin:daycare_invoices_invoice_change', args=[obj.invoice.id]),
            obj.invoice.child.first_name,
            obj.invoice.child.last_name,
            obj.invoice.provider.name,
            obj.invoice.invoice_number
        )
    invoice_display.short_description = 'Invoice'
    invoice_display.admin_order_field = 'invoice__invoice_number'
    
    def amount_display(self, obj):
        """Display payment amount"""
        return format_html(
            '<strong style="color: green;">${:,.2f}</strong>',
            obj.amount
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
