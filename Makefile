# FamlyPortal Development Shortcuts
# Usage: make <command>

.PHONY: help setup install migrate run test clean reset dev prod check lint format

# Default target
help:
	@echo "FamlyPortal Development Commands:"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  setup     - Complete project setup (install + migrate + superuser)"
	@echo "  install   - Install dependencies"
	@echo "  migrate   - Run database migrations"
	@echo "  reset     - Reset database (WARNING: Deletes all data)"
	@echo ""
	@echo "Development:"
	@echo "  dev       - Start development server with auto-reload"
	@echo "  run       - Start development server"
	@echo "  test      - Run all tests"
	@echo "  check     - Run Django system checks"
	@echo ""
	@echo "Code Quality:"
	@echo "  lint      - Run code linting"
	@echo "  format    - Auto-format code"
	@echo "  clean     - Clean up cache files"
	@echo ""
	@echo "Production:"
	@echo "  prod      - Start production server"
	@echo "  collect   - Collect static files"

# One-command setup for new development environment
setup: install migrate superuser
	@echo "✅ FamlyPortal setup complete!"
	@echo "Run 'make dev' to start development server"

# Install all dependencies
install:
	@echo "📦 Installing dependencies..."
	pip install -r requirements.txt

# Database operations
migrate:
	@echo "🗄️  Running migrations..."
	python manage.py makemigrations
	python manage.py migrate

# Create superuser interactively
superuser:
	@echo "👤 Creating superuser..."
	python manage.py createsuperuser

# Reset database (dangerous!)
reset:
	@echo "⚠️  WARNING: This will delete all data!"
	@read -p "Are you sure? (y/N): " confirm && [ "$$confirm" = "y" ] || exit 1
	rm -f db.sqlite3
	find . -path "*/migrations/*.py" -not -name "__init__.py" -delete
	find . -path "*/migrations/*.pyc" -delete
	$(MAKE) migrate
	@echo "🗄️  Database reset complete"

# Development server
dev:
	@echo "🚀 Starting development server with auto-reload..."
	python manage.py runserver 8000

run:
	@echo "🚀 Starting development server..."
	python manage.py runserver

# Testing
test:
	@echo "🧪 Running tests..."
	python manage.py test

# Django system checks
check:
	@echo "🔍 Running Django system checks..."
	python manage.py check

# Code quality
lint:
	@echo "🔍 Running code linting..."
	flake8 .
	pylint **/*.py

format:
	@echo "✨ Formatting code..."
	black .
	isort .

# Cleanup
clean:
	@echo "🧹 Cleaning up cache files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +

# Production
collect:
	@echo "📦 Collecting static files..."
	python manage.py collectstatic --noinput

prod: collect
	@echo "🌟 Starting production server..."
	gunicorn famlyportal.wsgi:application --bind 0.0.0.0:8000

# Development workflow shortcuts
quick: migrate dev

# Full refresh (careful!)
refresh: clean reset setup

# Show current environment info
info:
	@echo "FamlyPortal Environment Info:"
	@echo "Python: $(shell python --version)"
	@echo "Django: $(shell python -c 'import django; print(django.get_version())')"
	@echo "Database: PostgreSQL (check .env file)"
	@echo "Apps: accounts, timesheet, daycare_invoices, employment_history, upcoming_payments, credit_cards, household_budget, autocraftcv, subscription_tracker, core"