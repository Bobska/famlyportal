from django.contrib import admin
from django.utils.html import format_html
from django.db.models import Count
from django.urls import reverse
from core.admin import FamilyScopedModelAdmin
from .models import Company, Position, Skill, PositionSkill, Education


@admin.register(Company)
class CompanyAdmin(FamilyScopedModelAdmin):
    """Enhanced Company Admin"""
    
    list_display = [
        'name',
        'industry',
        'location',
        'size_display',
        'website_link',
        'position_count_display'
    ]
    list_filter = ['industry', 'size', 'created_at']
    search_fields = ['name', 'industry', 'location', 'website']
    ordering = ['name']
    
    fieldsets = (
        ('Company Information', {
            'fields': ('name', 'industry', 'location', 'size')
        }),
        ('Contact Details', {
            'fields': ('website', 'description'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with position counts"""
        qs = super().get_queryset(request)
        return qs.annotate(
            position_count_annotated=Count('position')
        )
    
    def size_display(self, obj):
        """Display company size with formatting"""
        size_colors = {
            'startup': 'purple',
            'small': 'blue', 
            'medium': 'green',
            'large': 'orange',
            'enterprise': 'red'
        }
        color = size_colors.get(obj.size, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_size_display()
        )
    size_display.short_description = 'Size'
    size_display.admin_order_field = 'size'
    
    def website_link(self, obj):
        """Display website as clickable link"""
        if obj.website:
            return format_html(
                '<a href="{}" target="_blank" title="Visit website">🔗</a>',
                obj.website
            )
        return '-'
    website_link.short_description = 'Website'
    
    def position_count_display(self, obj):
        """Display position count with link"""
        count = getattr(obj, 'position_count_annotated', obj.position_set.count())
        if count > 0:
            return format_html(
                '<a href="{}?company__id__exact={}">{} positions</a>',
                reverse('admin:employment_history_position_changelist'),
                obj.id,
                count
            )
        return '0 positions'
    position_count_display.short_description = 'Positions'
    position_count_display.admin_order_field = 'position_count_annotated'


@admin.register(Position)
class PositionAdmin(FamilyScopedModelAdmin):
    """Enhanced Position Admin"""
    
    list_display = [
        'title',
        'company',
        'user_display',
        'employment_period_display',
        'employment_type',
        'current_position_display',
        'skills_count_display'
    ]
    list_filter = ['employment_type', 'is_current', 'company', 'start_date']
    search_fields = ['title', 'company__name', 'user__username', 'responsibilities']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    raw_id_fields = ['user', 'company']
    
    fieldsets = (
        ('Position Details', {
            'fields': ('title', 'company', 'user')
        }),
        ('Employment Period', {
            'fields': ('start_date', 'end_date', 'is_current', 'employment_type')
        }),
        ('Compensation', {
            'fields': ('salary', 'hourly_rate'),
            'description': 'Enter either salary (annual) or hourly rate',
            'classes': ('collapse',)
        }),
        ('Job Details', {
            'fields': ('responsibilities', 'achievements'),
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
        return qs.select_related('user', 'company').annotate(
            skills_count_annotated=Count('positionskill')
        )
    
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
    user_display.short_description = 'Employee'
    user_display.admin_order_field = 'user__username'
    
    def employment_period_display(self, obj):
        """Display employment period"""
        start = obj.start_date.strftime('%m/%Y')
        if obj.is_current:
            return format_html(
                '<span style="font-family: monospace; color: green;">{} - Present</span>',
                start
            )
        elif obj.end_date:
            return format_html(
                '<span style="font-family: monospace;">{} - {}</span>',
                start,
                obj.end_date.strftime('%m/%Y')
            )
        return start
    employment_period_display.short_description = 'Period'
    employment_period_display.admin_order_field = 'start_date'
    
    def current_position_display(self, obj):
        """Display current position status"""
        if obj.is_current:
            return format_html('<span style="color: green;">●</span> Current')
        return format_html('<span style="color: gray;">●</span> Past')
    current_position_display.short_description = 'Status'
    current_position_display.admin_order_field = 'is_current'
    
    def skills_count_display(self, obj):
        """Display skills count"""
        count = getattr(obj, 'skills_count_annotated', obj.positionskill_set.count())
        if count > 0:
            return format_html(
                '<span style="color: blue;">{} skills</span>',
                count
            )
        return '0 skills'
    skills_count_display.short_description = 'Skills'
    skills_count_display.admin_order_field = 'skills_count_annotated'


@admin.register(Skill)
class SkillAdmin(FamilyScopedModelAdmin):
    """Enhanced Skill Admin"""
    
    list_display = [
        'name',
        'category',
        'position_count_display'
    ]
    list_filter = ['category', 'created_at']
    search_fields = ['name', 'category', 'description']
    ordering = ['category', 'name']
    
    fieldsets = (
        ('Skill Information', {
            'fields': ('name', 'category')
        }),
        ('Details', {
            'fields': ('description',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with position counts"""
        qs = super().get_queryset(request)
        return qs.annotate(
            position_count_annotated=Count('positionskill')
        )
    
    def position_count_display(self, obj):
        """Display how many positions use this skill"""
        count = getattr(obj, 'position_count_annotated', obj.positionskill_set.count())
        if count > 0:
            return format_html(
                '<span style="color: blue;">{} positions</span>',
                count
            )
        return '0 positions'
    position_count_display.short_description = 'Used In'
    position_count_display.admin_order_field = 'position_count_annotated'


@admin.register(PositionSkill)
class PositionSkillAdmin(FamilyScopedModelAdmin):
    """Enhanced Position-Skill relationship admin"""
    
    list_display = [
        'position_display',
        'skill',
        'proficiency_level_display',
        'years_experience'
    ]
    list_filter = ['proficiency_level', 'skill__category']
    search_fields = ['position__title', 'skill__name']
    raw_id_fields = ['position', 'skill']
    
    def get_queryset(self, request):
        """Optimize queryset"""
        qs = super().get_queryset(request)
        return qs.select_related('position__company', 'skill')
    
    def position_display(self, obj):
        """Display position with company"""
        return format_html(
            '<a href="{}" title="Company: {}">{}</a>',
            reverse('admin:employment_history_position_change', args=[obj.position.id]),
            obj.position.company.name,
            obj.position.title
        )
    position_display.short_description = 'Position'
    position_display.admin_order_field = 'position__title'
    
    def proficiency_level_display(self, obj):
        """Display proficiency level with color"""
        level_colors = {
            'beginner': 'orange',
            'intermediate': 'blue',
            'advanced': 'green',
            'expert': 'purple'
        }
        color = level_colors.get(obj.proficiency_level, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_proficiency_level_display()
        )
    proficiency_level_display.short_description = 'Proficiency'
    proficiency_level_display.admin_order_field = 'proficiency_level'


@admin.register(Education)
class EducationAdmin(FamilyScopedModelAdmin):
    """Enhanced Education Admin"""
    
    list_display = [
        'degree_display',
        'institution',
        'user_display',
        'field_of_study',
        'education_period_display',
        'current_status_display'
    ]
    list_filter = ['is_current', 'degree', 'start_date']
    search_fields = ['degree', 'institution', 'field_of_study', 'user__username']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    raw_id_fields = ['user']
    
    fieldsets = (
        ('Education Details', {
            'fields': ('user', 'degree', 'institution', 'field_of_study')
        }),
        ('Period', {
            'fields': ('start_date', 'end_date', 'is_current')
        }),
        ('Additional Information', {
            'fields': ('gpa', 'description'),
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
        return qs.select_related('user')
    
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
    user_display.short_description = 'Student'
    user_display.admin_order_field = 'user__username'
    
    def degree_display(self, obj):
        """Display degree with formatting"""
        degree_colors = {
            'high_school': 'blue',
            'associate': 'green',
            'bachelor': 'orange',
            'master': 'purple',
            'phd': 'red',
            'certificate': 'gray'
        }
        color = degree_colors.get(obj.degree, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_degree_display()
        )
    degree_display.short_description = 'Degree'
    degree_display.admin_order_field = 'degree'
    
    def education_period_display(self, obj):
        """Display education period"""
        start = obj.start_date.strftime('%m/%Y')
        if obj.is_current:
            return format_html(
                '<span style="font-family: monospace; color: green;">{} - Present</span>',
                start
            )
        elif obj.end_date:
            return format_html(
                '<span style="font-family: monospace;">{} - {}</span>',
                start,
                obj.end_date.strftime('%m/%Y')
            )
        return start
    education_period_display.short_description = 'Period'
    education_period_display.admin_order_field = 'start_date'
    
    def current_status_display(self, obj):
        """Display current education status"""
        if obj.is_current:
            return format_html('<span style="color: green;">●</span> In Progress')
        return format_html('<span style="color: blue;">●</span> Completed')
    current_status_display.short_description = 'Status'
    current_status_display.admin_order_field = 'is_current'
