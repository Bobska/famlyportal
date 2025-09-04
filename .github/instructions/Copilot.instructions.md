---
applyTo: '**'
---
# FamlyPortal Copilot Development Instructions

## Project Overview
- **Project Name:** FamlyPortal (famlyportal.com)
- **Technology:** Django web application with future mobile expansion
- **Purpose:** Family/household management platform with multiple integrated apps
- **Architecture:** Multi-tenant family-based system with role-based permissions

## Core Principles

### 1. Family-Centric Architecture
- All data is scoped to families (except user authentication)
- Users belong to families through `FamilyMember` model
- Family admins control member permissions and app access
- Complete data isolation between families

### 2. Role-Based Security
- **Admin:** Full access to all family data and member management
- **Parent:** Access to all apps except admin functions
- **Child:** Limited access (timesheet, employment_history, autocraftcv by default)
- **Other:** Basic access (timesheet only by default)
- Granular app-level permissions controlled by admins

### 3. Clean, Simple UI/UX
- Minimal, functional Bootstrap 5 styling
- Clear navigation and workflows
- Single accent color scheme (whites, grays, one accent)
- Functionality over visual complexity
- Mobile-responsive but desktop-first

## Django Apps Structure

### Core Apps
- **accounts:** User authentication, family management, permissions
- **core:** Shared utilities, base models, common functions

### Feature Apps
- **timesheet:** Time tracking and project management
- **daycare_invoices:** Daycare billing and payment tracking
- **employment_history:** Career tracking and skill management
- **upcoming_payments:** Payment scheduling and reminders
- **credit_cards:** Credit card management and tracking
- **household_budget:** Family budget and expense tracking
- **autocraftcv:** AI-powered CV/cover letter generation

## Database Design Standards

### Model Conventions
```python
# All models should include:
class BaseModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True

# Family-scoped models:
class FamilyScopedModel(BaseModel):
    family = models.ForeignKey('accounts.Family', on_delete=models.CASCADE)
    
    class Meta:
        abstract = True

# User-scoped models:
class UserScopedModel(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    
    class Meta:
        abstract = True
```

### Required Model Features
- Proper `__str__` methods for admin readability
- Meta class with appropriate ordering
- Foreign key relationships with proper on_delete behavior
- Validation methods where needed
- Manager classes for common queries

## Development Standards

### Code Quality
- Follow PEP 8 naming conventions
- Use type hints where beneficial
- Write docstrings for complex functions
- Keep functions focused and single-purpose
- Use Django's built-in features over custom solutions

### Security Requirements
- All views must check family membership
- Sensitive apps (credit_cards, household_budget, etc.) require explicit permission
- No direct model access - always filter by family/user
- Validate user permissions before any data operation

### URL and View Patterns
```python
# URL structure: /<app>/<action>/<id>/
urlpatterns = [
    path('timesheet/', views.dashboard, name='timesheet_dashboard'),
    path('timesheet/entry/new/', views.create_entry, name='timesheet_create_entry'),
    path('timesheet/entry/<int:pk>/edit/', views.edit_entry, name='timesheet_edit_entry'),
]

# View decorators for security
@login_required
@family_required
@app_permission_required('timesheet')
def dashboard(request):
    # Implementation
```

### Template Structure
- Extend from `base.html`
- Use template blocks: `title`, `content`, `extra_css`, `extra_js`
- Include breadcrumbs for navigation
- Use Django's built-in form rendering with Bootstrap classes
- Keep templates clean and minimal

### Form Handling
- Use Django ModelForms where possible
- Include proper validation and error handling
- Add family/user filtering in form `__init__` methods
- Use crispy forms for consistent styling

## Testing Standards
- Write tests for all models, views, and forms
- Test permission systems thoroughly
- Use Django's TestCase with proper setUp methods
- Test family data isolation
- Include edge cases and error conditions

## Integration Points

### App Interactions
- **AutoCraftCV ↔ Employment History:** Use job/skill data for CV generation
- **Upcoming Payments ↔ Credit Cards:** Link payment reminders to cards
- **Subscription Tracker ↔ Household Budget:** Recurring subscription costs in budget
- **Subscription Tracker ↔ Upcoming Payments:** Automatic payment reminders for renewals
- **Household Budget ↔ All Financial Apps:** Financial data aggregation
- **Timesheet ↔ Employment History:** Track work time for current positions

### External Services (Future)
- Email notifications for reminders
- AI services for AutoCraftCV
- Payment gateway integrations
- Mobile app API endpoints

## Development Workflow

### When Creating New Features
1. Design models with proper relationships
2. Create migrations and test them
3. Build admin interface for data management
4. Implement views with proper security
5. Create clean, functional templates
6. Add comprehensive tests
7. Update documentation

### Permission Checking Pattern
```python
def get_family_queryset(request, model_class):
    """Get queryset filtered by user's family"""
    family_member = request.user.familymember_set.first()
    if not family_member:
        return model_class.objects.none()
    return model_class.objects.filter(family=family_member.family)
```

## Performance Considerations
- Use `select_related` and `prefetch_related` for efficiency
- Index commonly queried fields
- Paginate large datasets
- Cache expensive operations
- Optimize database queries

## Common Patterns to Follow

### Model Relationships
- User ← FamilyMember → Family (many-to-many through table)
- Family → FamilyScopedModel (one-to-many)
- User → UserScopedModel (one-to-many)
- FamilyMember → AppPermission (one-to-many)

### Error Handling
- Use Django's messaging framework for user feedback
- Return appropriate HTTP status codes
- Log errors for debugging
- Provide helpful error messages

### API Future-Readiness
- Design views to easily add JSON responses
- Keep business logic in models/services
- Use consistent response patterns
- Plan for mobile app endpoints

Remember: Always prioritize security, family data isolation, and user experience simplicity. When in doubt, choose the more secure and user-friendly option.