# FamlyPortal - Family Management Platform

## Project Overview
FamlyPortal is a comprehensive family management platform built with Django. It integrates multiple applications to help families manage various aspects of their household, finances, and personal information.

## Project Structure

### Django Apps
- **accounts** - User authentication and family management
- **core** - Shared utilities and base functionality
- **timesheet** - Time tracking and project management
- **daycare_invoices** - Daycare billing and payment tracking
- **employment_history** - Career tracking and skill management
- **upcoming_payments** - Payment scheduling and reminders
- **credit_cards** - Credit card management and tracking
- **household_budget** - Family budget and expense tracking

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

6. **Run Development Server:**
   ```bash
   python manage.py runserver
   ```

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
- Family-centric data isolation
- Role-based permissions (Admin, Parent, Child, Other)
- Clean, minimal Bootstrap 5 UI
- Django best practices

### Code Standards
- Follow PEP 8 conventions
- Use Django's built-in features
- Implement proper error handling
- Write tests for all functionality

## Current Status
✅ **Prompt 1 Complete** - Initial Django project setup
- Django project created with all required apps
- Basic URL routing structure implemented
- Environment configuration with python-decouple
- PostgreSQL adapter and common packages installed
- Static files and media files configuration
- Basic logging configuration
- Initial migrations applied
- Development server tested and working

## Next Steps
- Implement user authentication system
- Design family and permission models
- Create base templates and navigation
- Develop core functionality for each app

## Technology Stack
- **Backend:** Django 5.2.6
- **Database:** PostgreSQL (production), SQLite (development)
- **Frontend:** Bootstrap 5, Django Templates
- **Styling:** Crispy Forms with Bootstrap 5
- **Environment:** python-decouple for configuration

## Git Workflow
- `main` - Production-ready code
- `feature/initial-django-setup` - Current feature branch
- Follow conventional commit messages
- Test thoroughly before committing

---

**Last Updated:** September 4, 2025  
**Django Version:** 5.2.6  
**Python Version:** 3.10+
