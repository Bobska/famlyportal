# FamlyPortal - Family Management Platform

## Project Overview
FamlyPortal is a comprehensive family management platform built with Django. It integrates multiple applications to help families manage various aspects of their household, finances, and personal information with a focus on budget allocation and financial planning.

## Project Structure

### Django Apps
- **accounts** - User authentication and family management
- **core** - Shared utilities and base functionality  
- **budget_allocation** - ✅ **COMPLETE** - Advanced budget allocation with account hierarchies
- **timesheet** - Time tracking and project management
- **daycare_invoices** - Daycare billing and payment tracking
- **employment_history** - Career tracking and skill management
- **upcoming_payments** - Payment scheduling and reminders
- **credit_cards** - Credit card management and tracking
- **household_budget** - Family budget and expense tracking
- **autocraftcv** - AI-powered CV/cover letter generation

## Key Features

### 🏦 Budget Allocation System (Production Ready)
- **Account Hierarchies** - Parent-child account relationships with unlimited nesting
- **Visual Management** - Tree-view display with color coding and intuitive navigation
- **Child Account Creation** - Seamless form-based creation with validation
- **Account Types** - Income and Expense categories with automatic inheritance
- **Family Isolation** - Complete data separation between families
- **Management Commands** - Production-ready setup and migration tools

### 👥 Family Management
- **Multi-Family Support** - Users can belong to multiple families
- **Role-Based Permissions** - Admin, Parent, Child, Other roles with granular access
- **Invite System** - Easy family joining with secure invite codes
- **Profile Management** - Comprehensive user profiles with avatars

## Installation & Setup

### Prerequisites
- Python 3.10+
- PostgreSQL (for production)

### Development Setup

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd famlyportal
   ```

2. **Create and activate virtual environment:**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   # or
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration:**
   ```bash
   # Copy template and configure
   cp .env.template .env
   # Edit .env with your settings
   ```

5. **Database Setup:**
   ```bash
   python manage.py migrate
   python manage.py createsuperuser
   ```

6. **Budget Allocation Setup:**
   ```bash
   # Setup budget allocation for all families
   python manage.py setup_budget_allocation
   
   # Or setup for specific family
   python manage.py setup_budget_allocation --family-id 1
   ```

7. **Run Development Server:**
   ```bash
   python manage.py runserver
   ```

## Budget Allocation Management

### Setup Commands
```bash
# Setup budget allocation for all families
python manage.py setup_budget_allocation

# Setup with data migration from household_budget
python manage.py setup_budget_allocation --migrate-data

# Migrate household_budget data (dry run)
python manage.py migrate_household_budget --dry-run --verbose
```

### Account Management
```bash
# List all accounts in tree format
python manage.py budget_account_utils list --show-tree

# Validate account data integrity
python manage.py budget_account_utils validate --fix

# Clean up orphaned accounts
python manage.py budget_account_utils clean --dry-run
```

See [`budget_allocation/management/commands/README.md`](budget_allocation/management/commands/README.md) for complete documentation.

## Configuration

### Environment Variables
Create a `.env` file based on `.env.template`:

- `SECRET_KEY` - Django secret key
- `DEBUG` - Debug mode (True/False)
- `ALLOWED_HOSTS` - Comma-separated list of allowed hosts
- `DB_ENGINE` - Database engine (default: sqlite3)
- `DB_NAME` - Database name
- `DB_USER` - Database user
- `DB_PASSWORD` - Database password
- `DB_HOST` - Database host
- `DB_PORT` - Database port

### Database Configuration
- **Development:** SQLite (default)
- **Production:** PostgreSQL (recommended)

## Development Guidelines

### Project Architecture
- **Family-Centric Design** - All data scoped to families with complete isolation
- **Role-Based Security** - Granular permissions with app-level access control
- **Account Hierarchies** - Unlimited nesting with parent-child relationships
- **Clean UI/UX** - Minimal Bootstrap 5 styling with functionality focus
- **Django Best Practices** - Proper models, forms, views, and templates

### Code Standards
- Follow PEP 8 conventions and Django best practices
- Use type hints and comprehensive docstrings
- Implement proper error handling and validation
- Write tests for all functionality
- Use conventional commit messages

### Database Design
- **Family Isolation** - `family` foreign key on all user data
- **Account Hierarchies** - Self-referencing `parent` field with validation
- **User Relationships** - Many-to-many through `FamilyMember` model
- **Data Integrity** - Model validation and management command verification

## Current Status

### ✅ Completed Features
- **User Authentication & Family System** - Complete multi-family user management
- **Budget Allocation System** - Full account hierarchy management with:
  - Parent-child account relationships
  - Visual tree display and management
  - Form-based account creation with validation
  - Color-coded organization system
  - Management commands for setup and maintenance
  - Data migration tools from household_budget
  - Account validation and cleanup utilities

### 🔄 In Development
- **Timesheet Integration** - Connect with employment history
- **Payment Management** - Upcoming payments and credit card tracking  
- **Advanced Reporting** - Budget analysis and forecasting
- **Mobile Responsiveness** - Enhanced mobile experience

### 📋 Planned Features
- **AutoCraftCV Integration** - AI-powered resume generation
- **Subscription Tracking** - Recurring payment management
- **Financial Analytics** - Advanced budget insights
- **Multi-Currency Support** - International family support

## Production Deployment

### Management Commands
The system includes production-ready management commands:
- `setup_budget_allocation` - Initial family setup and data migration
- `migrate_household_budget` - Safe data migration with dry-run support
- `budget_account_utils` - Validation, cleanup, and maintenance tools

### Security Features
- Family data isolation with proper permission checking
- Role-based access control with app-level permissions
- Input validation and XSS protection
- CSRF protection on all forms
- Secure authentication and session management

## Technology Stack
- **Backend:** Django 5.2.5, Python 3.10+
- **Database:** PostgreSQL (production), SQLite (development)
- **Frontend:** Bootstrap 5, Django Templates, Crispy Forms
- **JavaScript:** Vanilla JS with modern ES6+ features
- **Styling:** Bootstrap 5 with custom SCSS enhancements
- **Security:** Django's built-in security features + custom family isolation
- **Development:** python-decouple, Django debug toolbar

## Git Workflow
- **`main`** - Production-ready code (auto-deployment ready)
- **`develop`** - Integration branch for testing
- **`staging`** - Pre-production testing environment
- **`production`** - Live production branch
- **Feature branches** - `feature/feature-name` for development
- Follow conventional commit messages with proper scoping

## API Documentation
- Budget allocation models with comprehensive validation
- Management commands with detailed help and error handling
- Family permission system with decorator-based access control
- Account hierarchy utilities with circular reference detection

---

**Last Updated:** September 10, 2025  
**Django Version:** 5.2.5  
**Python Version:** 3.10+  
**Status:** Production Ready (Budget Allocation System)
