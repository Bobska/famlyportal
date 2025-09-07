from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from core.admin import FamilyScopedModelAdmin
from .models import (
    Account, AccountHistory, WeeklyPeriod, BudgetTemplate,
    Allocation, Transaction, AccountLoan, LoanPayment, FamilySettings
)


@admin.register(Account)
class AccountAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for Account model"""
    
    list_display = [
        'name', 
        'account_type', 
        'parent_display', 
        'family_display', 
        'is_active_display', 
        'sort_order',
        'children_count'
    ]
    list_filter = ['account_type', 'is_active', 'family']
    search_fields = ['name', 'description']
    ordering = ['family', 'account_type', 'sort_order', 'name']
    raw_id_fields = ['family', 'parent']
    readonly_fields = ['date_activated', 'date_deactivated', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Account Details', {
            'fields': ('name', 'account_type', 'parent', 'family', 'description', 'color')
        }),
        ('Status', {
            'fields': ('is_active', 'sort_order')
        }),
        ('Dates', {
            'fields': ('date_activated', 'date_deactivated'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_accounts', 'deactivate_accounts']
    
    def parent_display(self, obj):
        """Display parent account with link"""
        if obj.parent:
            return format_html(
                '<a href="{}" title="{}">{}</a>',
                reverse('admin:budget_allocation_account_change', args=[obj.parent.id]),
                obj.parent.full_path,
                obj.parent.name
            )
        return '-'
    parent_display.short_description = 'Parent'
    parent_display.admin_order_field = 'parent__name'
    
    def family_display(self, obj):
        """Display family with link"""
        return format_html(
            '<a href="{}" title="View family">{}</a>',
            reverse('admin:accounts_family_change', args=[obj.family.id]),
            obj.family.name
        )
    family_display.short_description = 'Family'
    family_display.admin_order_field = 'family__name'
    
    def is_active_display(self, obj):
        """Display active status with color"""
        if obj.is_active:
            return format_html('<span style="color: green;">✓ Active</span>')
        return format_html('<span style="color: red;">✗ Inactive</span>')
    is_active_display.short_description = 'Status'
    is_active_display.admin_order_field = 'is_active'
    
    def children_count(self, obj):
        """Display number of child accounts"""
        count = obj.children.count()
        if count > 0:
            return format_html(
                '<a href="{}?parent__id__exact={}" title="View child accounts">{} children</a>',
                reverse('admin:budget_allocation_account_changelist'),
                obj.id,
                count
            )
        return '0 children'
    children_count.short_description = 'Children'
    
    def activate_accounts(self, request, queryset):
        """Activate selected accounts"""
        count = 0
        for account in queryset:
            account.activate()
            count += 1
        self.message_user(request, f'Activated {count} accounts.')
    activate_accounts.short_description = "Activate selected accounts"
    
    def deactivate_accounts(self, request, queryset):
        """Deactivate selected accounts"""
        count = 0
        for account in queryset:
            account.deactivate()
            count += 1
        self.message_user(request, f'Deactivated {count} accounts.')
    deactivate_accounts.short_description = "Deactivate selected accounts"


@admin.register(AccountHistory)
class AccountHistoryAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for AccountHistory model"""
    
    list_display = [
        'account_display', 
        'action_display', 
        'timestamp_display', 
        'old_value_short', 
        'new_value_short'
    ]
    list_filter = ['action', 'timestamp']
    search_fields = ['account__name', 'notes']
    readonly_fields = ['timestamp', 'created_at', 'updated_at']
    ordering = ['-timestamp']
    raw_id_fields = ['family', 'account']
    
    fieldsets = (
        ('History Details', {
            'fields': ('account', 'action', 'timestamp')
        }),
        ('Changes', {
            'fields': ('old_value', 'new_value', 'notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def account_display(self, obj):
        """Display account with link"""
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            reverse('admin:budget_allocation_account_change', args=[obj.account.id]),
            obj.account.full_path,
            obj.account.name
        )
    account_display.short_description = 'Account'
    account_display.admin_order_field = 'account__name'
    
    def action_display(self, obj):
        """Display action with color coding"""
        colors = {
            'created': 'blue',
            'activated': 'green',
            'deactivated': 'red',
            'renamed': 'orange',
            'moved': 'purple'
        }
        color = colors.get(obj.action, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_action_display()
        )
    action_display.short_description = 'Action'
    action_display.admin_order_field = 'action'
    
    def timestamp_display(self, obj):
        """Display formatted timestamp"""
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S')
    timestamp_display.short_description = 'When'
    timestamp_display.admin_order_field = 'timestamp'
    
    def old_value_short(self, obj):
        """Display truncated old value"""
        if obj.old_value:
            return obj.old_value[:50] + '...' if len(obj.old_value) > 50 else obj.old_value
        return '-'
    old_value_short.short_description = 'Old Value'
    
    def new_value_short(self, obj):
        """Display truncated new value"""
        if obj.new_value:
            return obj.new_value[:50] + '...' if len(obj.new_value) > 50 else obj.new_value
        return '-'
    new_value_short.short_description = 'New Value'


@admin.register(WeeklyPeriod)
class WeeklyPeriodAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for WeeklyPeriod model"""
    
    list_display = [
        'period_display', 
        'family_display', 
        'is_active_display', 
        'is_allocated_display', 
        'allocation_locked_display',
        'transactions_count',
        'allocations_count'
    ]
    list_filter = ['is_active', 'is_allocated', 'allocation_locked', 'family']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    raw_id_fields = ['family']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Period Details', {
            'fields': ('start_date', 'end_date', 'family')
        }),
        ('Status', {
            'fields': ('is_active', 'is_allocated', 'allocation_locked')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def period_display(self, obj):
        """Display period range"""
        return f"{obj.start_date} to {obj.end_date}"
    period_display.short_description = 'Period'
    period_display.admin_order_field = 'start_date'
    
    def family_display(self, obj):
        """Display family with link"""
        return format_html(
            '<a href="{}" title="View family">{}</a>',
            reverse('admin:accounts_family_change', args=[obj.family.id]),
            obj.family.name
        )
    family_display.short_description = 'Family'
    family_display.admin_order_field = 'family__name'
    
    def is_active_display(self, obj):
        """Display active status"""
        return '✓' if obj.is_active else '✗'
    is_active_display.short_description = 'Active'
    is_active_display.admin_order_field = 'is_active'
    
    def is_allocated_display(self, obj):
        """Display allocated status"""
        return '✓' if obj.is_allocated else '✗'
    is_allocated_display.short_description = 'Allocated'
    is_allocated_display.admin_order_field = 'is_allocated'
    
    def allocation_locked_display(self, obj):
        """Display locked status"""
        return '🔒' if obj.allocation_locked else '🔓'
    allocation_locked_display.short_description = 'Locked'
    allocation_locked_display.admin_order_field = 'allocation_locked'
    
    def transactions_count(self, obj):
        """Display transaction count with link"""
        count = obj.allocation_transactions.count()
        if count > 0:
            return format_html(
                '<a href="{}?week__id__exact={}" title="View transactions">{} transactions</a>',
                reverse('admin:budget_allocation_transaction_changelist'),
                obj.id,
                count
            )
        return '0 transactions'
    transactions_count.short_description = 'Transactions'
    
    def allocations_count(self, obj):
        """Display allocation count with link"""
        count = obj.allocations.count()
        if count > 0:
            return format_html(
                '<a href="{}?week__id__exact={}" title="View allocations">{} allocations</a>',
                reverse('admin:budget_allocation_allocation_changelist'),
                obj.id,
                count
            )
        return '0 allocations'
    allocations_count.short_description = 'Allocations'


@admin.register(BudgetTemplate)
class BudgetTemplateAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for BudgetTemplate model"""
    
    list_display = [
        'account_display', 
        'allocation_type_display', 
        'weekly_amount_display', 
        'percentage_display', 
        'priority_display', 
        'is_essential_display', 
        'never_miss_display',
        'is_active_display'
    ]
    list_filter = ['allocation_type', 'priority', 'is_essential', 'never_miss', 'is_active']
    search_fields = ['account__name']
    ordering = ['priority', 'account__name']
    raw_id_fields = ['family', 'account']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Template Details', {
            'fields': ('account', 'allocation_type', 'family')
        }),
        ('Allocation Settings', {
            'fields': ('weekly_amount', 'percentage', 'min_amount', 'max_amount')
        }),
        ('Priority & Behavior', {
            'fields': ('priority', 'is_essential', 'never_miss', 'auto_allocate', 'is_active')
        }),
        ('Bill Planning', {
            'fields': ('annual_amount', 'due_date', 'current_saved'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def account_display(self, obj):
        """Display account with link"""
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            reverse('admin:budget_allocation_account_change', args=[obj.account.id]),
            obj.account.full_path,
            obj.account.name
        )
    account_display.short_description = 'Account'
    account_display.admin_order_field = 'account__name'
    
    def allocation_type_display(self, obj):
        """Display allocation type with color"""
        colors = {
            'fixed': 'blue',
            'percentage': 'green',
            'range': 'orange',
            'calculated': 'purple'
        }
        color = colors.get(obj.allocation_type, 'black')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_allocation_type_display()
        )
    allocation_type_display.short_description = 'Type'
    allocation_type_display.admin_order_field = 'allocation_type'
    
    def weekly_amount_display(self, obj):
        """Display weekly amount"""
        if obj.weekly_amount:
            return f"${obj.weekly_amount:,.2f}"
        return '-'
    weekly_amount_display.short_description = 'Weekly Amount'
    weekly_amount_display.admin_order_field = 'weekly_amount'
    
    def percentage_display(self, obj):
        """Display percentage"""
        if obj.percentage:
            return f"{obj.percentage}%"
        return '-'
    percentage_display.short_description = 'Percentage'
    percentage_display.admin_order_field = 'percentage'
    
    def priority_display(self, obj):
        """Display priority with visual indicator"""
        stars = '★' * obj.priority
        return format_html('<span title="Priority {}">{}</span>', obj.priority, stars)
    priority_display.short_description = 'Priority'
    priority_display.admin_order_field = 'priority'
    
    def is_essential_display(self, obj):
        """Display essential status"""
        return '⚠️' if obj.is_essential else ''
    is_essential_display.short_description = 'Essential'
    is_essential_display.admin_order_field = 'is_essential'
    
    def never_miss_display(self, obj):
        """Display never miss status"""
        return '🔥' if obj.never_miss else ''
    never_miss_display.short_description = 'Never Miss'
    never_miss_display.admin_order_field = 'never_miss'
    
    def is_active_display(self, obj):
        """Display active status"""
        return '✓' if obj.is_active else '✗'
    is_active_display.short_description = 'Active'
    is_active_display.admin_order_field = 'is_active'


@admin.register(Allocation)
class AllocationAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for Allocation model"""
    
    list_display = [
        'week_display', 
        'from_account_display', 
        'to_account_display', 
        'amount_display', 
        'created_at_display'
    ]
    list_filter = ['week__start_date', 'from_account__account_type', 'to_account__account_type']
    search_fields = ['from_account__name', 'to_account__name', 'notes']
    date_hierarchy = 'week__start_date'
    ordering = ['-week__start_date', '-created_at']
    raw_id_fields = ['family', 'week', 'from_account', 'to_account']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Allocation Details', {
            'fields': ('week', 'from_account', 'to_account', 'amount', 'family')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def week_display(self, obj):
        """Display week with link"""
        return format_html(
            '<a href="{}" title="View week">{}</a>',
            reverse('admin:budget_allocation_weeklyperiod_change', args=[obj.week.id]),
            f"{obj.week.start_date} to {obj.week.end_date}"
        )
    week_display.short_description = 'Week'
    week_display.admin_order_field = 'week__start_date'
    
    def from_account_display(self, obj):
        """Display from account with link"""
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            reverse('admin:budget_allocation_account_change', args=[obj.from_account.id]),
            obj.from_account.full_path,
            obj.from_account.name
        )
    from_account_display.short_description = 'From Account'
    from_account_display.admin_order_field = 'from_account__name'
    
    def to_account_display(self, obj):
        """Display to account with link"""
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            reverse('admin:budget_allocation_account_change', args=[obj.to_account.id]),
            obj.to_account.full_path,
            obj.to_account.name
        )
    to_account_display.short_description = 'To Account'
    to_account_display.admin_order_field = 'to_account__name'
    
    def amount_display(self, obj):
        """Display amount with formatting"""
        return format_html(
            '<strong style="color: green;">${:,.2f}</strong>',
            obj.amount
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def created_at_display(self, obj):
        """Display formatted creation date"""
        return obj.created_at.strftime('%Y-%m-%d %H:%M')
    created_at_display.short_description = 'Created'
    created_at_display.admin_order_field = 'created_at'


@admin.register(Transaction)
class TransactionAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for Transaction model"""
    
    list_display = [
        'transaction_date', 
        'account_display', 
        'description_short', 
        'amount_display', 
        'transaction_type_display', 
        'is_reconciled_display',
        'week_display'
    ]
    list_filter = ['transaction_type', 'is_reconciled', 'week__start_date', 'account__account_type']
    search_fields = ['description', 'payee', 'reference', 'account__name']
    date_hierarchy = 'transaction_date'
    ordering = ['-transaction_date', '-created_at']
    raw_id_fields = ['family', 'week', 'account']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('transaction_date', 'account', 'week', 'family')
        }),
        ('Transaction Info', {
            'fields': ('description', 'amount', 'transaction_type', 'payee', 'reference')
        }),
        ('Status', {
            'fields': ('is_reconciled',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def account_display(self, obj):
        """Display account with link"""
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            reverse('admin:budget_allocation_account_change', args=[obj.account.id]),
            obj.account.full_path,
            obj.account.name
        )
    account_display.short_description = 'Account'
    account_display.admin_order_field = 'account__name'
    
    def description_short(self, obj):
        """Display truncated description"""
        return obj.description[:50] + '...' if len(obj.description) > 50 else obj.description
    description_short.short_description = 'Description'
    description_short.admin_order_field = 'description'
    
    def amount_display(self, obj):
        """Display amount with color coding"""
        color = 'green' if obj.transaction_type == 'income' else 'red'
        sign = '+' if obj.transaction_type == 'income' else '-'
        return format_html(
            '<strong style="color: {};">{} ${:,.2f}</strong>',
            color,
            sign,
            obj.amount
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def transaction_type_display(self, obj):
        """Display transaction type with color"""
        color = 'green' if obj.transaction_type == 'income' else 'red'
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_transaction_type_display()
        )
    transaction_type_display.short_description = 'Type'
    transaction_type_display.admin_order_field = 'transaction_type'
    
    def is_reconciled_display(self, obj):
        """Display reconciled status"""
        return '✓' if obj.is_reconciled else '✗'
    is_reconciled_display.short_description = 'Reconciled'
    is_reconciled_display.admin_order_field = 'is_reconciled'
    
    def week_display(self, obj):
        """Display week with link"""
        return format_html(
            '<a href="{}" title="View week">{}</a>',
            reverse('admin:budget_allocation_weeklyperiod_change', args=[obj.week.id]),
            f"{obj.week.start_date}"
        )
    week_display.short_description = 'Week'
    week_display.admin_order_field = 'week__start_date'


@admin.register(AccountLoan)
class AccountLoanAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for AccountLoan model"""
    
    list_display = [
        'lender_account_display', 
        'borrower_account_display', 
        'original_amount_display', 
        'remaining_amount_display', 
        'weekly_interest_rate_display', 
        'is_active_display',
        'payments_count'
    ]
    list_filter = ['is_active', 'loan_date', 'weekly_interest_rate']
    search_fields = ['lender_account__name', 'borrower_account__name']
    ordering = ['-loan_date']
    raw_id_fields = ['family', 'lender_account', 'borrower_account']
    readonly_fields = ['total_interest_charged', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Loan Details', {
            'fields': ('lender_account', 'borrower_account', 'family', 'loan_date')
        }),
        ('Amounts', {
            'fields': ('original_amount', 'remaining_amount', 'weekly_interest_rate')
        }),
        ('Status', {
            'fields': ('is_active', 'total_interest_charged')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def lender_account_display(self, obj):
        """Display lender account with link"""
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            reverse('admin:budget_allocation_account_change', args=[obj.lender_account.id]),
            obj.lender_account.full_path,
            obj.lender_account.name
        )
    lender_account_display.short_description = 'Lender'
    lender_account_display.admin_order_field = 'lender_account__name'
    
    def borrower_account_display(self, obj):
        """Display borrower account with link"""
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            reverse('admin:budget_allocation_account_change', args=[obj.borrower_account.id]),
            obj.borrower_account.full_path,
            obj.borrower_account.name
        )
    borrower_account_display.short_description = 'Borrower'
    borrower_account_display.admin_order_field = 'borrower_account__name'
    
    def original_amount_display(self, obj):
        """Display original amount"""
        return f"${obj.original_amount:,.2f}"
    original_amount_display.short_description = 'Original'
    original_amount_display.admin_order_field = 'original_amount'
    
    def remaining_amount_display(self, obj):
        """Display remaining amount with color"""
        color = 'red' if obj.remaining_amount > 0 else 'green'
        return format_html(
            '<strong style="color: {};">${:,.2f}</strong>',
            color,
            obj.remaining_amount
        )
    remaining_amount_display.short_description = 'Remaining'
    remaining_amount_display.admin_order_field = 'remaining_amount'
    
    def weekly_interest_rate_display(self, obj):
        """Display interest rate as percentage"""
        return f"{obj.weekly_interest_rate * 100:.2f}%"
    weekly_interest_rate_display.short_description = 'Weekly Rate'
    weekly_interest_rate_display.admin_order_field = 'weekly_interest_rate'
    
    def is_active_display(self, obj):
        """Display active status"""
        return '✓' if obj.is_active else '✗'
    is_active_display.short_description = 'Active'
    is_active_display.admin_order_field = 'is_active'
    
    def payments_count(self, obj):
        """Display payment count with link"""
        count = obj.payments.count()
        if count > 0:
            return format_html(
                '<a href="{}?loan__id__exact={}" title="View payments">{} payments</a>',
                reverse('admin:budget_allocation_loanpayment_changelist'),
                obj.id,
                count
            )
        return '0 payments'
    payments_count.short_description = 'Payments'


@admin.register(LoanPayment)
class LoanPaymentAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for LoanPayment model"""
    
    list_display = [
        'loan_display', 
        'amount_display', 
        'payment_date', 
        'week_display'
    ]
    list_filter = ['payment_date', 'week__start_date']
    search_fields = ['loan__lender_account__name', 'loan__borrower_account__name', 'notes']
    ordering = ['-payment_date']
    raw_id_fields = ['family', 'loan', 'week']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Payment Details', {
            'fields': ('loan', 'amount', 'payment_date', 'week', 'family')
        }),
        ('Notes', {
            'fields': ('notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def loan_display(self, obj):
        """Display loan with link"""
        return format_html(
            '<a href="{}" title="View loan">{} → {}</a>',
            reverse('admin:budget_allocation_accountloan_change', args=[obj.loan.id]),
            obj.loan.lender_account.name,
            obj.loan.borrower_account.name
        )
    loan_display.short_description = 'Loan'
    loan_display.admin_order_field = 'loan__loan_date'
    
    def amount_display(self, obj):
        """Display payment amount"""
        return format_html(
            '<strong style="color: green;">${:,.2f}</strong>',
            obj.amount
        )
    amount_display.short_description = 'Amount'
    amount_display.admin_order_field = 'amount'
    
    def week_display(self, obj):
        """Display week with link"""
        return format_html(
            '<a href="{}" title="View week">{}</a>',
            reverse('admin:budget_allocation_weeklyperiod_change', args=[obj.week.id]),
            f"{obj.week.start_date}"
        )
    week_display.short_description = 'Week'
    week_display.admin_order_field = 'week__start_date'


@admin.register(FamilySettings)
class FamilySettingsAdmin(FamilyScopedModelAdmin):
    """Enhanced admin for FamilySettings model"""
    
    list_display = [
        'family_display', 
        'week_start_day_display', 
        'default_interest_rate_display', 
        'auto_allocate_enabled_display', 
        'auto_repay_enabled_display',
        'notification_threshold_display'
    ]
    list_filter = ['week_start_day', 'auto_allocate_enabled', 'auto_repay_enabled']
    ordering = ['family__name']
    raw_id_fields = ['family']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Family Settings', {
            'fields': ('family', 'week_start_day')
        }),
        ('Defaults', {
            'fields': ('default_interest_rate', 'notification_threshold')
        }),
        ('Automation', {
            'fields': ('auto_allocate_enabled', 'auto_repay_enabled')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def family_display(self, obj):
        """Display family with link"""
        return format_html(
            '<a href="{}" title="View family">{}</a>',
            reverse('admin:accounts_family_change', args=[obj.family.id]),
            obj.family.name
        )
    family_display.short_description = 'Family'
    family_display.admin_order_field = 'family__name'
    
    def week_start_day_display(self, obj):
        """Display week start day"""
        return obj.get_week_start_day_display()
    week_start_day_display.short_description = 'Week Starts'
    week_start_day_display.admin_order_field = 'week_start_day'
    
    def default_interest_rate_display(self, obj):
        """Display interest rate as percentage"""
        return f"{obj.default_interest_rate * 100:.2f}%"
    default_interest_rate_display.short_description = 'Default Rate'
    default_interest_rate_display.admin_order_field = 'default_interest_rate'
    
    def auto_allocate_enabled_display(self, obj):
        """Display auto allocate status"""
        return '✓' if obj.auto_allocate_enabled else '✗'
    auto_allocate_enabled_display.short_description = 'Auto Allocate'
    auto_allocate_enabled_display.admin_order_field = 'auto_allocate_enabled'
    
    def auto_repay_enabled_display(self, obj):
        """Display auto repay status"""
        return '✓' if obj.auto_repay_enabled else '✗'
    auto_repay_enabled_display.short_description = 'Auto Repay'
    auto_repay_enabled_display.admin_order_field = 'auto_repay_enabled'
    
    def notification_threshold_display(self, obj):
        """Display notification threshold"""
        return f"${obj.notification_threshold:,.2f}"
    notification_threshold_display.short_description = 'Notification Threshold'
    notification_threshold_display.admin_order_field = 'notification_threshold'
