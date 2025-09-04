from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Sum, Count, Q
from django.urls import reverse
from datetime import datetime, timedelta
from core.admin import FamilyScopedModelAdmin
from .models import Project, TimeEntry


@admin.register(Project)
class ProjectAdmin(FamilyScopedModelAdmin):
    """Enhanced Project Admin with family scoping"""
    
    list_display = [
        'name', 
        'created_by_display',
        'hourly_rate_display', 
        'entry_count_display',
        'total_hours_display',
        'status_display', 
        'created_display'
    ]
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['-created_at']
    raw_id_fields = ['family', 'created_by']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Project Details', {
            'fields': ('name', 'description', 'family', 'created_by')
        }),
        ('Payment Information', {
            'fields': ('hourly_rate',),
            'description': 'Hourly rate for this project'
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
        """Optimize queryset with entry counts and hours"""
        qs = super().get_queryset(request)
        return qs.annotate(
            entry_count_annotated=Count('timeentry'),
            total_hours_annotated=Sum('timeentry__total_hours'),
            total_earnings_annotated=Sum('timeentry__earnings')
        ).select_related('created_by', 'family')
    
    def created_by_display(self, obj):
        """Display creator with link"""
        if obj.created_by:
            user = obj.created_by
            name = f"{user.first_name} {user.last_name}".strip() or user.username
            return format_html(
                '<a href="{}" title="{}">{}</a>',
                reverse('admin:accounts_user_change', args=[user.id]),
                user.email,
                name
            )
        return '-'
    created_by_display.short_description = 'Created By'
    created_by_display.admin_order_field = 'created_by__username'
    
    def hourly_rate_display(self, obj):
        """Display formatted hourly rate"""
        return format_html(
            '<span style="font-weight: bold; color: green;">${}/hr</span>',
            obj.hourly_rate
        )
    hourly_rate_display.short_description = 'Hourly Rate'
    hourly_rate_display.admin_order_field = 'hourly_rate'
    
    def entry_count_display(self, obj):
        """Display time entry count with link"""
        count = getattr(obj, 'entry_count_annotated', obj.timeentry_set.count())
        if count > 0:
            return format_html(
                '<a href="{}?project__id__exact={}">{} entries</a>',
                reverse('admin:timesheet_timeentry_changelist'),
                obj.id,
                count
            )
        return '0 entries'
    entry_count_display.short_description = 'Time Entries'
    entry_count_display.admin_order_field = 'entry_count_annotated'
    
    def total_hours_display(self, obj):
        """Display total hours worked"""
        total = getattr(obj, 'total_hours_annotated', 0) or 0
        if total > 0:
            return format_html(
                '<span style="color: blue; font-weight: bold;">{:.1f} hrs</span>',
                total
            )
        return '0 hrs'
    total_hours_display.short_description = 'Total Hours'
    total_hours_display.admin_order_field = 'total_hours_annotated'
    
    def status_display(self, obj):
        """Display project status"""
        if obj.is_active:
            return format_html('<span style="color: green;">●</span> Active')
        return format_html('<span style="color: red;">●</span> Inactive')
    status_display.short_description = 'Status'
    status_display.admin_order_field = 'is_active'
    
    def deactivate_projects(self, request, queryset):
        """Bulk action to deactivate projects"""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {updated} projects.')
    deactivate_projects.short_description = "Deactivate selected projects"
    
    def activate_projects(self, request, queryset):
        """Bulk action to activate projects"""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'Activated {updated} projects.')
    activate_projects.short_description = "Activate selected projects"


@admin.register(TimeEntry)
class TimeEntryAdmin(FamilyScopedModelAdmin):
    """Enhanced Time Entry Admin with family scoping"""
    
    list_display = [
        'user_display',
        'project',
        'date', 
        'time_range_display',
        'break_duration_display', 
        'total_hours_display',
        'earnings_display',
        'created_display'
    ]
    list_filter = ['date', 'project', 'break_duration', 'created_at']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'project__name', 'description']
    ordering = ['-date', '-start_time']
    date_hierarchy = 'date'
    raw_id_fields = ['user', 'project']
    
    fieldsets = (
        ('Entry Details', {
            'fields': ('user', 'project', 'date')
        }),
        ('Time Information', {
            'fields': ('start_time', 'end_time', 'break_duration'),
            'description': 'Break duration is in minutes'
        }),
        ('Additional Details', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Calculated Fields', {
            'fields': ('total_hours', 'earnings'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_readonly_fields(self, request, obj=None):
        """Make calculated fields readonly"""
        return ['total_hours', 'earnings', 'created_at', 'updated_at']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('user', 'project')
    
    def user_display(self, obj):
        """Display user with link"""
        user = obj.user
        name = f"{user.first_name} {user.last_name}".strip() or user.username
        return format_html(
            '<a href="{}" title="{}">{}</a>',
            reverse('admin:accounts_user_change', args=[user.id]),
            user.email,
            name
        )
    user_display.short_description = 'User'
    user_display.admin_order_field = 'user__username'
    
    def time_range_display(self, obj):
        """Display time range"""
        return format_html(
            '<span style="font-family: monospace;">{} - {}</span>',
            obj.start_time.strftime('%H:%M'),
            obj.end_time.strftime('%H:%M')
        )
    time_range_display.short_description = 'Time Range'
    time_range_display.admin_order_field = 'start_time'
    
    def break_duration_display(self, obj):
        """Display break duration"""
        if obj.break_duration > 0:
            return format_html(
                '<span style="color: orange;">{} min</span>',
                obj.break_duration
            )
        return '-'
    break_duration_display.short_description = 'Break'
    break_duration_display.admin_order_field = 'break_duration'
    
    def total_hours_display(self, obj):
        """Display total hours worked"""
        total = obj.total_hours
        color = 'green' if total >= 8 else 'blue'
        return format_html(
            '<strong style="color: {};">{:.2f} hrs</strong>',
            color,
            total
        )
    total_hours_display.short_description = 'Total Hours'
    total_hours_display.admin_order_field = 'total_hours'
    
    def earnings_display(self, obj):
        """Display earnings"""
        return format_html(
            '<strong style="color: green;">${:.2f}</strong>',
            obj.earnings
        )
    earnings_display.short_description = 'Earnings'
    earnings_display.admin_order_field = 'earnings'
    
    def duplicate_entries(self, request, queryset):
        """Bulk action to duplicate time entries for next day"""
        count = 0
        for entry in queryset:
            next_day = entry.date + timedelta(days=1)
            TimeEntry.objects.create(
                user=entry.user,
                project=entry.project,
                date=next_day,
                start_time=entry.start_time,
                end_time=entry.end_time,
                break_duration=entry.break_duration,
                description=entry.description
            )
            count += 1
        self.message_user(request, f'Duplicated {count} entries for next day.')
    duplicate_entries.short_description = "Duplicate for next day"
    
    def mark_as_overtime(self, request, queryset):
        """Mark entries as overtime (8+ hours)"""
        overtime_count = 0
        for entry in queryset:
            if entry.total_hours >= 8:
                entry.description = (entry.description or '') + ' [OVERTIME]'
                entry.save()
                overtime_count += 1
        self.message_user(request, f'Marked {overtime_count} entries as overtime.')
    mark_as_overtime.short_description = "Mark as overtime"
