from django.contrib import admin
from .models import Income, Expense, Payee


@admin.register(Payee)
class PayeeAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)
    readonly_fields = ('created_at', 'updated_at')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set user for new objects
            obj.user = request.user
        super().save_model(request, obj, form, change)


@admin.register(Income)
class IncomeAdmin(admin.ModelAdmin):
    list_display = ('date', 'payee', 'amount', 'user', 'created_at')
    list_filter = ('date', 'user', 'created_at')
    search_fields = ('payee', 'notes')
    ordering = ('-date', '-created_at')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Transaction Details', {
            'fields': ('user', 'date', 'payee', 'amount')
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
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(user=request.user)


    @admin.register(Expense)
    class ExpenseAdmin(admin.ModelAdmin):
        list_display = ('date', 'payee', 'amount', 'user', 'created_at')
        list_filter = ('date', 'user', 'created_at')
        search_fields = ('payee', 'notes')
        ordering = ('-date', '-created_at')
        readonly_fields = ('created_at', 'updated_at')
    
        fieldsets = (
            ('Transaction Details', {
                'fields': ('user', 'date', 'payee', 'amount')
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
            qs = super().get_queryset(request)
            if request.user.is_superuser:
                return qs
            return qs.filter(user=request.user)
