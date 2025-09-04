---
applyTo: '**'
---
# FamlyPortal Django Project: VS Code Copilot Instructions

## Critical Development Workflow

### MANDATORY Testing & Commit Process
**⚠️ NEVER commit untested code! Always follow this exact sequence:**

1. **Check Current Branch & Test First**
   ```bash
   # 1. VERIFY you're on the correct feature branch
   git branch --show-current
   # Should show: feature/timesheet-app/[your-feature] or feature/[app-name]/[your-feature]
   
   # 2. ALWAYS test your changes first
   python manage.py check
   python manage.py makemigrations
   python manage.py migrate
   python manage.py runserver
   # -> Open browser and test functionality thoroughly
   
   # 3. ONLY commit after successful testing
   git add .
   git commit -m "feat(timesheet): add entry validation logic"
   
   # 4. Push to feature branch (NOT main!)
   git push origin feature/timesheet-app/validation-logic
   ```

2. **Test Verification Requirements**
   - Verify Django server starts without errors
   - Test all new forms and validation in browser
   - Check database migrations apply correctly
   - Confirm no broken existing functionality

## Project Context & Architecture

### Project Overview
- **Name**: FamlyPortal - Integrated family management platform
- **Tech Stack**: Django 5.2.5, Python 3.10+, SQLite (dev), Bootstrap 5
- **Architecture**: Standalone Django apps → unified integration
- **Development Phase**: Multi-app development and integration planning

### Current Applications Status
1. **Timesheet App**: ✅ Feature branch active: `feature/timesheet-app`
2. **Daycare Invoice Tracker**: ✅ Production-ready, needs integration
3. **Employment History**: 📋 Planning phase
4. **Upcoming Payments**: 📋 Planning phase
5. **Credit Card Management**: 📋 Planning phase
6. **Household Budget**: 📋 Planning phase

### Git Branching Strategy (CRITICAL)
**⚠️ ALWAYS work on feature branches - NEVER commit directly to main!**

Current Active Branches:
- `main` - Production-ready code only
- `feature/timesheet-app` - Timesheet integration branch
- `feature/timesheet-app/*` - Specific timesheet features

Branch Creation Rules:
```bash
# For new timesheet features:
git checkout feature/timesheet-app
git checkout -b feature/timesheet-app/your-feature-name

# For new apps (future):
git checkout main
git checkout -b feature/new-app-name

# For app-specific features:
git checkout feature/app-name
git checkout -b feature/app-name/specific-feature
```

## Git Commit Message Standards (2025 Best Practices)

### Conventional Commits Format
```
<type>(optional scope): <description>

[optional body]

[optional footer]
```

### Commit Types
- **feat**: New features or functionality
- **fix**: Bug fixes and corrections  
- **docs**: Documentation changes
- **style**: Code formatting (no logic changes)
- **refactor**: Code refactoring without changing functionality
- **test**: Adding or updating tests
- **chore**: Maintenance tasks, dependencies, build processes

### The Seven Golden Rules
1. **Limit subject to 50 characters** - Forces concise thinking
2. **Capitalize first letter only** - Standard convention
3. **No period at end** - Saves space and follows convention
4. **Use imperative mood** - "Add feature" not "Added feature"
5. **Blank line before body** - Improves readability
6. **Wrap body at 72 characters** - Git log compatibility
7. **Explain WHAT and WHY, not HOW** - Code shows how

### Imperative Mood Test
Complete this sentence: "If applied, this commit will ___"
- ✅ "If applied, this commit will **add user authentication system**"
- ❌ "If applied, this commit will **added user authentication system**"

### Examples of Excellent Commits
```bash
# Feature additions
git commit -m "feat: add time entry overlap validation"
git commit -m "feat(timesheet): implement job management CRUD operations"

# Bug fixes  
git commit -m "fix: resolve timezone issue in time calculations"
git commit -m "fix(forms): correct validation error display"

# Documentation
git commit -m "docs: update installation instructions for Django 5.2"

# Refactoring
git commit -m "refactor: simplify time calculation logic in models"

# Testing
git commit -m "test: add unit tests for timesheet validation"
```

## Django Development Standards

### Model Best Practices
```python
# Always include proper model methods
class TimeEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    job = models.ForeignKey('Job', on_delete=models.CASCADE)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    break_duration = models.IntegerField(choices=BREAK_CHOICES, default=0)
    
    class Meta:
        verbose_name_plural = "time entries"
        ordering = ['-date', '-start_time']
    
    def __str__(self):
        return f"{self.user.username} - {self.job.name} - {self.date}"
    
    def total_hours(self):
        """Calculate total work hours excluding breaks."""
        # Implementation logic here
        return total_decimal_hours
    
    def clean(self):
        """Custom validation for model."""
        # Implement overlap validation
        pass
```

### View Patterns
```python
# Use class-based views for CRUD operations
class TimeEntryCreateView(LoginRequiredMixin, CreateView):
    model = TimeEntry
    form_class = TimeEntryForm
    template_name = 'timesheet/entry_form.html'
    success_url = reverse_lazy('timesheet:dashboard')
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
```

### Form Standards
```python
# Include proper validation and error handling
class TimeEntryForm(forms.ModelForm):
    class Meta:
        model = TimeEntry
        fields = ['job', 'date', 'start_time', 'end_time', 'break_duration']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
        }
    
    def clean(self):
        # Add validation logic
        return cleaned_data
```

## Code Quality Standards

### Python Style Guidelines
- Follow PEP 8 conventions strictly
- Use meaningful variable names: `time_entry` not `te`
- Include docstrings for complex functions
- Use type hints where beneficial
- Handle errors gracefully with try/except blocks

### Template Standards
```django
<!-- Use template inheritance -->
{% extends 'base.html' %}
{% load static %}

{% block title %}Timesheet Dashboard{% endblock %}

{% block content %}
<div class="container mt-4">
    <h2>Today's Time Entries</h2>
    <!-- Bootstrap 5 classes for styling -->
    <div class="row">
        <div class="col-md-8">
            <!-- Content here -->
        </div>
    </div>
</div>
{% endblock %}
```

### URL Patterns
```python
# Use descriptive URL names
urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('entry/add/', views.TimeEntryCreateView.as_view(), name='entry_create'),
    path('entry/<int:pk>/edit/', views.TimeEntryUpdateView.as_view(), name='entry_update'),
    path('jobs/', views.JobListView.as_view(), name='job_list'),
]
```

## Database & Migration Standards

### Model Field Guidelines
- Use appropriate field types (DecimalField for money, TimeField for time)
- Include helpful_text for complex fields
- Set appropriate max_length for CharField
- Use choices for predefined options
- Add db_index=True for frequently queried fields

### Migration Best Practices
```bash
# Always create migrations after model changes
python manage.py makemigrations
python manage.py migrate

# Check for migration conflicts
python manage.py showmigrations
```

## Bootstrap 5 UI Standards

### Form Styling
```html
<form method="post" class="needs-validation" novalidate>
    {% csrf_token %}
    <div class="mb-3">
        <label for="{{ form.job.id_for_label }}" class="form-label">Job</label>
        {{ form.job|add_class:"form-select" }}
        {% if form.job.errors %}
            <div class="invalid-feedback d-block">{{ form.job.errors.0 }}</div>
        {% endif %}
    </div>
    <button type="submit" class="btn btn-primary">Save Entry</button>
</form>
```

### Responsive Design
- Use Bootstrap grid system: `col-md-6`, `col-lg-4`
- Include mobile-friendly navigation
- Ensure forms work on all screen sizes
- Use Bootstrap utility classes: `mt-4`, `mb-3`, `text-center`

## Security Requirements

### Authentication & Authorization
```python
# Always use LoginRequiredMixin for protected views
class TimeEntryListView(LoginRequiredMixin, ListView):
    model = TimeEntry
    
    def get_queryset(self):
        # Filter to current user's data only
        return TimeEntry.objects.filter(user=self.request.user)
```

### Input Validation
- Use Django forms for all user input
- Implement clean() methods for custom validation
- Sanitize data before database operations
- Use CSRF protection on all forms

## Error Handling Patterns

### View Error Handling
```python
def create_time_entry(request):
    try:
        # Process logic here
        return redirect('success_url')
    except ValidationError as e:
        messages.error(request, f"Validation error: {e}")
        return render(request, 'form.html', context)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        messages.error(request, "An error occurred. Please try again.")
        return render(request, 'form.html', context)
```

## Testing Requirements

### Model Testing
```python
class TimeEntryModelTest(TestCase):
    def test_total_hours_calculation(self):
        """Test that total hours are calculated correctly."""
        # Test implementation
        
    def test_overlap_validation(self):
        """Test that overlapping entries are prevented."""
        # Test implementation
```

### View Testing
```python
class TimeEntryViewTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'pass')
        self.client.login(username='testuser', password='pass')
        
    def test_entry_creation(self):
        """Test creating new time entry."""
        # Test implementation
```

## Performance Guidelines

### Database Optimization
- Use `select_related()` for foreign key relationships
- Use `prefetch_related()` for many-to-many relationships
- Implement pagination for large datasets
- Add database indexes for frequently queried fields

### Template Optimization
- Load static files efficiently: `{% load static %}`
- Use template caching for repeated elements
- Minimize database queries in templates

## Integration Planning Notes

### App Integration Strategy
- Design models with shared User relationships
- Plan for unified navigation system
- Consider shared base templates
- Design APIs for cross-app data access

### Deployment Preparation
- Environment variables for sensitive settings
- Static file collection: `python manage.py collectstatic`
- Production database migration strategy
- Logging configuration for debugging

## Response Guidelines for Copilot

When generating code:
1. **Always include proper error handling**
2. **Use descriptive variable names that match the domain**
3. **Include helpful comments for business logic**
4. **Follow Django best practices and conventions**
5. **Consider performance implications**
6. **Include proper validation in forms and models**
7. **Use Bootstrap 5 classes for styling**
8. **Implement proper authentication and authorization**

Remember: **Test thoroughly before every commit!** The workflow is always: Code → Test → Commit → Push.

---

**Project Status**: Multi-app development phase  
**Last Updated**: August 28, 2025  
**Copilot Instructions Version**: 1.0