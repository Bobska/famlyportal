# FamlyPortal Architecture Document

## System Overview
FamlyPortal is a Django-based family management platform designed for multi-tenant, family-scoped data management with role-based access control and future mobile app integration.

## Architecture Principles

### 1. Multi-Tenant Family Architecture
- **Family Isolation:** Complete data separation between families
- **Shared Infrastructure:** Single application instance serves multiple families
- **Scalable Design:** Architecture supports growth from single families to enterprise use

### 2. Security-First Design
- **Role-Based Access Control (RBAC):** Admin, Parent, Child, Other roles
- **Granular Permissions:** App-level access control per family member
- **Data Isolation:** No cross-family data leakage possible
- **Secure by Default:** Child accounts have minimal permissions initially

### 3. Modular App Structure
- **Loosely Coupled:** Each app can function independently
- **Integration Ready:** Apps can share data through well-defined interfaces
- **Extensible:** New apps can be added without affecting existing functionality

## Technology Stack

### Backend
- **Framework:** Django (latest stable)
- **Database:** PostgreSQL (production) / SQLite (development)
- **Language:** Python 3.9+
- **ORM:** Django ORM with custom managers and querysets

### Frontend
- **Templates:** Django Templates with Bootstrap 5
- **Styling:** Clean, minimal CSS with single accent color
- **JavaScript:** Vanilla JS for interactions (minimal)
- **Responsive:** Mobile-friendly but desktop-first design

### Development Tools
- **IDE:** VS Code with Copilot Pro+
- **Version Control:** Git with conventional commit messages
- **Package Management:** pip with requirements.txt
- **Task Automation:** Makefile for common operations

### Future Technology
- **Mobile:** React Native / Flutter (TBD)
- **API:** Django REST Framework
- **Deployment:** Docker containers, cloud hosting
- **Caching:** Redis for session and data caching

## Data Architecture

### Core Models Hierarchy
```
User (Django Auth)
├── FamilyMember ←→ Family
│   ├── AppPermission (per app access control)
│   └── Role (admin/parent/child/other)
└── UserScopedModels (personal data)

Family
├── FamilyScopedModels (shared family data)
└── FamilyMembers (family composition)
```

### Database Design Patterns

#### Family-Scoped Data
```python
class FamilyScopedModel(BaseModel):
    family = models.ForeignKey('accounts.Family', on_delete=models.CASCADE)
    # All family-shared data inherits from this
```

#### User-Scoped Data
```python
class UserScopedModel(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Personal user data inherits from this
```

#### Permission Model
```python
class AppPermission(models.Model):
    family_member = models.ForeignKey(FamilyMember)
    app_name = models.CharField(choices=APP_CHOICES)
    has_access = models.BooleanField(default=False)
```

### Data Relationships

#### Family Structure
- **One-to-Many:** Family → FamilyMembers
- **Many-to-Many:** Users ↔ Families (through FamilyMember)
- **Hierarchical:** Admin → Parent → Child permissions

#### App Integrations
- **AutoCraftCV → Employment History:** Job data for CV generation
- **Subscription Tracker → Household Budget:** Recurring costs in budget planning
- **Subscription Tracker → Upcoming Payments:** Automatic renewal reminders
- **Budget → All Financial Apps:** Aggregated financial data
- **Payments → Credit Cards:** Payment method linking
- **Timesheet → Employment:** Current job time tracking

## Application Architecture

### Apps Structure
```
famlyportal/
├── accounts/          # Authentication & family management
├── core/             # Shared utilities and base models
├── timesheet/        # Time tracking
├── daycare_invoices/ # Daycare billing management
├── employment_history/ # Career tracking
├── upcoming_payments/ # Payment scheduling
├── credit_cards/     # Credit card management
├── household_budget/ # Budget management
├── autocraftcv/      # CV/Cover letter generation
└── static/           # Static files (CSS, JS, images)
```

### Security Architecture

#### Authentication Flow
1. User logs in (Django auth)
2. System identifies family membership(s)
3. App permissions validated per request
4. Data filtered by family scope

#### Permission Layers
```
Request → Authentication → Family Membership → App Permission → Data Access
```

#### Default Permissions Matrix
| Role  | Timesheet | Daycare | Employment | Payments | Credit | Budget | AutoCV |
|-------|-----------|---------|------------|----------|---------|---------|--------|
| Admin | ✓         | ✓       | ✓          | ✓        | ✓       | ✓       | ✓      |
| Parent| ✓         | ✓       | ✓          | ✓        | ✓       | ✓       | ✓      |
| Child | ✓         | ✗       | ✓          | ✗        | ✗       | ✗       | ✓      |
| Other | ✓         | ✗       | ✗          | ✗        | ✗       | ✗       | ✗      |

### API Architecture (Future)

#### RESTful Endpoints
```
/api/v1/
├── auth/              # Authentication endpoints
├── families/          # Family management
├── timesheet/         # Time tracking API
├── employment/        # Employment history API
├── budget/           # Budget management API
└── autocraftcv/      # CV generation API
```

#### Mobile App Integration
- **Authentication:** Token-based auth with family context
- **Data Sync:** RESTful APIs with family-scoped data
- **Offline Support:** Local storage with sync capabilities
- **Push Notifications:** Payment reminders, family updates

## Security Considerations

### Data Protection
- **Encryption:** Sensitive data encrypted at rest
- **HTTPS:** All communications encrypted in transit
- **Input Validation:** All user inputs validated and sanitized
- **SQL Injection Prevention:** ORM-based queries only

### Access Control
- **Family Isolation:** Queries always filtered by family
- **Permission Checking:** Every view validates app access
- **Session Security:** Secure session configuration
- **CSRF Protection:** Django CSRF middleware enabled

### Privacy
- **Data Minimization:** Only collect necessary data
- **User Control:** Users can delete their own data
- **Family Privacy:** No cross-family data sharing
- **Audit Logging:** Track sensitive data access

## Performance Architecture

### Database Optimization
- **Indexing:** Strategic indexes on frequently queried fields
- **Query Optimization:** Use select_related/prefetch_related
- **Connection Pooling:** PostgreSQL connection management
- **Migration Strategy:** Zero-downtime migration approach

### Caching Strategy
- **Template Caching:** Cache rendered templates
- **Query Caching:** Cache expensive database queries
- **Static Files:** CDN for static assets
- **Session Caching:** Redis for session storage

### Scalability
- **Horizontal Scaling:** Stateless application design
- **Database Scaling:** Read replicas for query optimization
- **Load Balancing:** Multiple application instances
- **Microservices Ready:** Apps can be extracted to services

## Integration Patterns

### Inter-App Communication
```python
# Service layer for cross-app data access
class EmploymentService:
    @staticmethod
    def get_user_skills(user):
        # Returns skills for AutoCraftCV
        
    @staticmethod
    def get_current_position(user):
        # Returns current job for Timesheet
```

### External Integrations (Future)
- **Email Services:** SendGrid/AWS SES for notifications
- **AI Services:** OpenAI/Claude API for AutoCraftCV
- **Payment Gateways:** Stripe for subscription billing
- **Cloud Storage:** AWS S3 for file uploads

## Deployment Architecture

### Development Environment
```
Local Development:
├── SQLite Database
├── Django Development Server
├── Static Files Served by Django
└── Environment Variables in .env
```

### Production Environment (Future)
```
Production Stack:
├── PostgreSQL Database (RDS/managed)
├── Django Application (Docker containers)
├── Nginx (Static files + Reverse proxy)
├── Redis (Caching + Sessions)
└── Cloud Hosting (AWS/DigitalOcean)
```

## Testing Architecture

### Test Layers
- **Unit Tests:** Model and utility function tests
- **Integration Tests:** App interaction testing
- **Security Tests:** Permission and data isolation tests
- **UI Tests:** Template and form testing
- **API Tests:** Future API endpoint testing

### Test Data Management
- **Fixtures:** Base test data for all apps
- **Factories:** Dynamic test data generation
- **Family Isolation Testing:** Ensure no cross-family data leaks
- **Permission Testing:** Validate role-based access

## Monitoring & Maintenance

### Application Monitoring
- **Error Tracking:** Django logging and error collection
- **Performance Monitoring:** Database query analysis
- **Security Monitoring:** Failed login attempts, suspicious activity
- **Usage Analytics:** Family and app usage patterns

### Maintenance Procedures
- **Database Migrations:** Automated with rollback capability
- **Backup Strategy:** Regular database and media backups
- **Update Process:** Staged deployment with testing
- **Security Updates:** Regular dependency updates

This architecture supports the current family management needs while providing a foundation for future mobile apps, API integrations, and potential enterprise features.