from django.contrib import admin
from .models import Project, TimeEntry


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ['name', 'family', 'created_by', 'hourly_rate', 'is_active', 'created_at']
    list_filter = ['is_active', 'family', 'created_at']
    search_fields = ['name', 'description']
    date_hierarchy = 'created_at'
    ordering = ['family', '-created_at', 'name']
    raw_id_fields = ['family']


@admin.register(TimeEntry)
class TimeEntryAdmin(admin.ModelAdmin):
    list_display = ['user', 'project', 'date', 'start_time', 'end_time', 'break_duration', 'total_hours', 'earnings']
    list_filter = ['project__family', 'project', 'date']
    search_fields = ['user__username', 'project__name', 'description']
    date_hierarchy = 'date'
    ordering = ['-date', '-start_time']
    raw_id_fields = ['user', 'project']
    
    def get_readonly_fields(self, request, obj=None):
        # Make calculated fields readonly
        return ['total_hours', 'earnings'] + list(self.readonly_fields or [])
