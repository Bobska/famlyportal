from django.contrib import admin
from .models import Company, Position, Skill, PositionSkill, Education


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'location', 'size']
    list_filter = ['industry', 'size']
    search_fields = ['name', 'industry', 'location']
    ordering = ['name']


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'user', 'start_date', 'end_date', 'is_current', 'employment_type']
    list_filter = ['is_current', 'employment_type', 'company']
    search_fields = ['title', 'company__name', 'user__username']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    raw_id_fields = ['user', 'company']


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ['name', 'category']
    list_filter = ['category']
    search_fields = ['name', 'category']
    ordering = ['category', 'name']


@admin.register(PositionSkill)
class PositionSkillAdmin(admin.ModelAdmin):
    list_display = ['position', 'skill', 'proficiency_level', 'years_experience']
    list_filter = ['proficiency_level', 'skill__category']
    search_fields = ['position__title', 'skill__name']
    raw_id_fields = ['position', 'skill']


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ['degree', 'institution', 'user', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current', 'degree']
    search_fields = ['degree', 'institution', 'field_of_study', 'user__username']
    date_hierarchy = 'start_date'
    ordering = ['-start_date']
    raw_id_fields = ['user']
