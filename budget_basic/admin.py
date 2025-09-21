from django.contrib import admin
from .models import Income, Expense


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
