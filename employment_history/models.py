from django.db import models
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from core.models import BaseModel, UserScopedModel

User = get_user_model()


class CompanyManager(models.Manager):
    """Custom manager for Company model"""
    
    def by_industry(self, industry):
        """Return companies by industry"""
        return self.filter(industry__icontains=industry)


class Company(BaseModel):
    """Company model for employment history"""
    name = models.CharField(
        max_length=200,
        unique=True,
        help_text="Company name"
    )
    industry = models.CharField(
        max_length=100,
        blank=True,
        help_text="Industry sector"
    )
    location = models.CharField(
        max_length=200,
        blank=True,
        help_text="Company location (city, state/country)"
    )
    website = models.URLField(
        blank=True,
        help_text="Company website URL"
    )
    description = models.TextField(
        blank=True,
        help_text="Company description"
    )
    size = models.CharField(
        max_length=50,
        blank=True,
        help_text="Company size (e.g., 1-10, 11-50, etc.)"
    )
    
    objects = CompanyManager()
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
    
    def __str__(self):
        return self.name


class PositionManager(models.Manager):
    """Custom manager for Position model"""
    
    def current(self):
        """Return current positions"""
        return self.filter(is_current=True)
    
    def for_user(self, user):
        """Return positions for a specific user"""
        return self.filter(user=user)
    
    def by_date_range(self, start_date, end_date):
        """Return positions within date range"""
        return self.filter(
            start_date__lte=end_date
        ).filter(
            models.Q(end_date__gte=start_date) | models.Q(end_date__isnull=True)
        )


class Position(UserScopedModel):
    """Employment position model"""
    company = models.ForeignKey(
        Company,
        on_delete=models.CASCADE,
        help_text="Company where position was held"
    )
    title = models.CharField(
        max_length=200,
        help_text="Job title"
    )
    start_date = models.DateField(
        help_text="Start date of employment"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date of employment (leave blank if current)"
    )
    description = models.TextField(
        blank=True,
        help_text="Job description and responsibilities"
    )
    salary_range = models.CharField(
        max_length=100,
        blank=True,
        help_text="Salary range (e.g., $50,000 - $60,000)"
    )
    is_current = models.BooleanField(
        default=False,
        help_text="Whether this is a current position"
    )
    employment_type = models.CharField(
        max_length=50,
        choices=[
            ('full_time', 'Full-time'),
            ('part_time', 'Part-time'),
            ('contract', 'Contract'),
            ('freelance', 'Freelance'),
            ('internship', 'Internship'),
            ('temporary', 'Temporary'),
        ],
        default='full_time',
        help_text="Type of employment"
    )
    achievements = models.TextField(
        blank=True,
        help_text="Key achievements and accomplishments"
    )
    reason_for_leaving = models.TextField(
        blank=True,
        help_text="Reason for leaving (if applicable)"
    )
    supervisor_name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Name of supervisor/manager"
    )
    supervisor_contact = models.CharField(
        max_length=200,
        blank=True,
        help_text="Supervisor contact information"
    )
    
    objects = PositionManager()
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Position'
        verbose_name_plural = 'Positions'
    
    def __str__(self):
        return f"{self.title} at {self.company.name}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.start_date > timezone.now().date():
            raise ValidationError("Start date cannot be in the future.")
        
        if self.end_date:
            if self.end_date < self.start_date:
                raise ValidationError("End date cannot be before start date.")
            
            if self.end_date > timezone.now().date():
                raise ValidationError("End date cannot be in the future.")
            
            if self.is_current:
                raise ValidationError("Current positions should not have an end date.")
        
        # Check for overlapping current positions
        if self.is_current:
            current_positions = Position.objects.filter(
                user=self.user,
                is_current=True
            )
            if self.pk:
                current_positions = current_positions.exclude(pk=self.pk)
            
            if current_positions.exists():
                raise ValidationError(
                    "You can only have one current position. "
                    "Please end other current positions first."
                )
    
    @property
    def duration_months(self):
        """Calculate duration in months"""
        end = self.end_date or timezone.now().date()
        months = (end.year - self.start_date.year) * 12
        months += end.month - self.start_date.month
        return max(1, months)  # At least 1 month
    
    @property
    def duration_display(self):
        """Get human-readable duration"""
        months = self.duration_months
        years = months // 12
        remaining_months = months % 12
        
        if years > 0:
            if remaining_months > 0:
                return f"{years} year{'s' if years > 1 else ''}, {remaining_months} month{'s' if remaining_months > 1 else ''}"
            else:
                return f"{years} year{'s' if years > 1 else ''}"
        else:
            return f"{months} month{'s' if months > 1 else ''}"
    
    def save(self, *args, **kwargs):
        """Override save to handle current position logic"""
        if self.is_current:
            self.end_date = None
        super().save(*args, **kwargs)


class SkillManager(models.Manager):
    """Custom manager for Skill model"""
    
    def by_category(self, category):
        """Return skills by category"""
        return self.filter(category__icontains=category)


class Skill(BaseModel):
    """Skill model for tracking professional skills"""
    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Skill name"
    )
    category = models.CharField(
        max_length=100,
        help_text="Skill category (e.g., Programming, Design, Management)"
    )
    description = models.TextField(
        blank=True,
        help_text="Skill description"
    )
    
    objects = SkillManager()
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = 'Skill'
        verbose_name_plural = 'Skills'
    
    def __str__(self):
        return f"{self.name} ({self.category})"


class PositionSkillManager(models.Manager):
    """Custom manager for PositionSkill model"""
    
    def for_position(self, position):
        """Return skills for a specific position"""
        return self.filter(position=position)
    
    def for_user(self, user):
        """Return all skills for a user across positions"""
        return self.filter(position__user=user)


class PositionSkill(BaseModel):
    """Many-to-many relationship between Position and Skill with proficiency"""
    
    PROFICIENCY_CHOICES = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]
    
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        help_text="Position where skill was used"
    )
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        help_text="Skill used in this position"
    )
    proficiency_level = models.CharField(
        max_length=20,
        choices=PROFICIENCY_CHOICES,
        default='intermediate',
        help_text="Proficiency level for this skill"
    )
    years_experience = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Years of experience with this skill"
    )
    notes = models.TextField(
        blank=True,
        help_text="Additional notes about skill usage"
    )
    
    objects = PositionSkillManager()
    
    class Meta:
        unique_together = ['position', 'skill']
        ordering = ['skill__category', 'skill__name']
        verbose_name = 'Position Skill'
        verbose_name_plural = 'Position Skills'
    
    def __str__(self):
        return f"{self.skill.name} - {dict(self.PROFICIENCY_CHOICES)[self.proficiency_level]}"


class Education(UserScopedModel):
    """Education model for tracking educational background"""
    institution = models.CharField(
        max_length=200,
        help_text="Educational institution name"
    )
    degree = models.CharField(
        max_length=100,
        help_text="Degree or certification obtained"
    )
    field_of_study = models.CharField(
        max_length=100,
        blank=True,
        help_text="Field of study or major"
    )
    start_date = models.DateField(
        help_text="Start date of education"
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date (leave blank if ongoing)"
    )
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="GPA (if applicable)"
    )
    description = models.TextField(
        blank=True,
        help_text="Additional details about education"
    )
    is_current = models.BooleanField(
        default=False,
        help_text="Whether currently pursuing this education"
    )
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = 'Education'
        verbose_name_plural = 'Education'
    
    def __str__(self):
        return f"{self.degree} from {self.institution}"
    
    def clean(self):
        """Custom validation"""
        super().clean()
        
        if self.end_date and self.end_date < self.start_date:
            raise ValidationError("End date cannot be before start date.")
        
        if self.gpa is not None and (self.gpa < 0 or self.gpa > 4.0):
            raise ValidationError("GPA must be between 0.0 and 4.0.")
