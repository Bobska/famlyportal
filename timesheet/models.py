from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from core.models import FamilyScopedModel, FamilyUserScopedModel, StatusChoices

User = get_user_model()


class ProjectManager(models.Manager):
    """Custom manager for Project model"""
    
    def active(self):
        """Return only active projects"""
        return self.filter(is_active=True)
    
    def for_family(self, family):
        """Return projects for a specific family"""
        return self.filter(family=family)


class Project(FamilyScopedModel):
    """Project model for timesheet tracking"""
    name = models.CharField(
        max_length=200,
        help_text="Name of the project"
    )
    description = models.TextField(
        blank=True,
        help_text="Detailed description of the project"
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_projects',
        help_text="User who created this project"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this project is currently active"
    )
    client_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Client or company name for this project"
    )
    hourly_rate = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Hourly rate for this project"
    )
    
    objects = ProjectManager()
    
    class Meta:
        ordering = ['name']
        unique_together = ['family', 'name']
        verbose_name = 'Project'
        verbose_name_plural = 'Projects'
    
    def __str__(self):
        return f"{self.name} ({self.family.name})"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        if self.hourly_rate is not None and self.hourly_rate < 0:
            raise ValidationError("Hourly rate cannot be negative.")
    
    @property
    def total_hours_logged(self):
        """Calculate total hours logged for this project"""
        return sum(entry.total_hours for entry in self.timeentry_set.all())
    
    @property
    def total_earnings(self):
        """Calculate total earnings for this project"""
        if self.hourly_rate:
            return self.total_hours_logged * self.hourly_rate
        return 0


class TimeEntryManager(models.Manager):
    """Custom manager for TimeEntry model"""
    
    def for_date_range(self, start_date, end_date):
        """Return entries within a date range"""
        return self.filter(date__range=[start_date, end_date])
    
    def for_user(self, user):
        """Return entries for a specific user"""
        return self.filter(user=user)
    
    def for_project(self, project):
        """Return entries for a specific project"""
        return self.filter(project=project)


class TimeEntry(FamilyUserScopedModel):
    """Time entry model for tracking work hours"""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        help_text="Project this time entry belongs to"
    )
    date = models.DateField(
        default=timezone.now,
        help_text="Date of the work"
    )
    start_time = models.TimeField(
        help_text="Start time of work"
    )
    end_time = models.TimeField(
        help_text="End time of work"
    )
    break_duration = models.PositiveIntegerField(
        default=0,
        help_text="Break duration in minutes"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of work performed"
    )
    is_billable = models.BooleanField(
        default=True,
        help_text="Whether this time entry is billable"
    )
    
    objects = TimeEntryManager()
    
    class Meta:
        ordering = ['-date', '-start_time']
        verbose_name = 'Time Entry'
        verbose_name_plural = 'Time Entries'
    
    def __str__(self):
        return f"{self.user.username} - {self.project.name} - {self.date}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError("End time must be after start time.")
        
        if self.date and self.date > timezone.now().date():
            raise ValidationError("Time entry date cannot be in the future.")
        
        # Check for overlapping entries
        if self.pk:
            overlapping = TimeEntry.objects.filter(
                user=self.user,
                date=self.date
            ).exclude(pk=self.pk)
        else:
            overlapping = TimeEntry.objects.filter(
                user=self.user,
                date=self.date
            )
        
        for entry in overlapping:
            if self._times_overlap(entry):
                raise ValidationError(
                    f"Time entry overlaps with existing entry: {entry}"
                )
    
    def _times_overlap(self, other_entry):
        """Check if this entry overlaps with another entry"""
        return (
            (self.start_time < other_entry.end_time and 
             self.end_time > other_entry.start_time)
        )
    
    @property
    def total_hours(self):
        """Calculate total hours worked (excluding breaks)"""
        if not (self.start_time and self.end_time):
            return 0
        
        start_datetime = datetime.combine(self.date, self.start_time)
        end_datetime = datetime.combine(self.date, self.end_time)
        
        # Handle overnight entries
        if self.end_time < self.start_time:
            end_datetime += timedelta(days=1)
        
        total_time = end_datetime - start_datetime
        total_minutes = total_time.total_seconds() / 60
        
        # Subtract break duration
        work_minutes = total_minutes - self.break_duration
        
        # Convert to hours
        return round(work_minutes / 60, 2)
    
    @property
    def earnings(self):
        """Calculate earnings for this entry"""
        if self.project.hourly_rate and self.is_billable:
            return self.total_hours * self.project.hourly_rate
        return 0
    
    def save(self, *args, **kwargs):
        """Override save to ensure family consistency"""
        if self.project_id:
            self.family = self.project.family
        super().save(*args, **kwargs)
