from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Family
from budget_allocation.models import Account
from budget_allocation.utils import ensure_default_accounts_exist

class Command(BaseCommand):
    help = 'Setup budget allocation for existing families and handle data migration'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--family-id',
            type=int,
            help='Setup for specific family ID only',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force setup even if accounts already exist',
        )
        parser.add_argument(
            '--migrate-data',
            action='store_true',
            help='Migrate existing household_budget data',
        )
    
    def handle(self, *args, **options):
        """Handle the setup process"""
        
        self.stdout.write(
            self.style.SUCCESS("🏦 Starting Budget Allocation Setup...")
        )
        
        if options['family_id']:
            families = Family.objects.filter(id=options['family_id'])
            if not families.exists():
                self.stdout.write(
                    self.style.ERROR(f"Family with ID {options['family_id']} not found")
                )
                return
        else:
            families = Family.objects.all()
        
        self.stdout.write(f"Found {families.count()} families to process")
        
        success_count = 0
        error_count = 0
        
        for family in families:
            try:
                with transaction.atomic():
                    self.setup_family(family, options)
                    success_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"✓ Setup complete for {family.name}")
                    )
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Error setting up {family.name}: {str(e)}")
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Setup complete: {success_count} families successful, {error_count} errors"
            )
        )
    
    def setup_family(self, family, options):
        """Setup budget allocation for a single family"""
        
        # Check if accounts already exist
        existing_accounts = Account.objects.filter(family=family)
        if existing_accounts.exists() and not options['force']:
            self.stdout.write(
                self.style.WARNING(f"  Accounts already exist for {family.name}, skipping...")
            )
            return
        
        if options['force'] and existing_accounts.exists():
            self.stdout.write(
                self.style.WARNING(f"  Force mode: Proceeding despite existing accounts for {family.name}")
            )
        
        # Ensure default accounts exist
        income_account, expense_account = ensure_default_accounts_exist(family)
        
        self.stdout.write(f"  📊 Created default accounts for {family.name}")
        self.stdout.write(f"    Income: {income_account.name}")
        self.stdout.write(f"    Expenses: {expense_account.name}")
        
        # Migrate data from household_budget if requested
        if options['migrate_data']:
            self.migrate_household_budget_data(family, income_account, expense_account)
    
    def migrate_household_budget_data(self, family, income_account, expense_account):
        """Migrate data from household_budget app"""
        
        try:
            # Import household_budget models
            from household_budget.models import BudgetCategory, Transaction
            
            self.stdout.write(f"  🔄 Migrating household_budget data for {family.name}...")
            
            # Get expense categories from household_budget
            categories = BudgetCategory.objects.filter(family=family)
            
            if not categories.exists():
                self.stdout.write(f"    No categories found in household_budget for {family.name}")
                return
            
            migration_count = 0
            
            for category in categories:
                # Determine parent account based on category type
                if category.category_type == 'expense':
                    parent_account = expense_account
                elif category.category_type == 'income':
                    parent_account = income_account
                else:
                    self.stdout.write(
                        self.style.WARNING(f"    Unknown category type: {category.category_type}, skipping {category.name}")
                    )
                    continue
                
                # Create corresponding account in budget_allocation
                account, created = Account.objects.get_or_create(
                    family=family,
                    name=category.name,
                    parent=parent_account,
                    defaults={
                        'description': category.description or f'Migrated from {category.name}',
                        'account_type': category.category_type,
                        'is_active': category.is_active,
                        'color': self._get_category_color(category.category_type, migration_count),
                    }
                )
                
                if created:
                    migration_count += 1
                    self.stdout.write(f"    ✓ Migrated category: {category.name}")
                else:
                    self.stdout.write(f"    - Already exists: {category.name}")
            
            self.stdout.write(f"  📈 Migrated {migration_count} new categories from household_budget")
            
            # Migrate transactions if they exist
            self._migrate_transactions(family, categories)
            
        except ImportError:
            self.stdout.write(
                self.style.WARNING("  household_budget app not found, skipping data migration")
            )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"  Data migration failed: {str(e)}")
            )
    
    def _migrate_transactions(self, family, categories):
        """Migrate transaction data"""
        
        try:
            from household_budget.models import Transaction
            
            transactions = Transaction.objects.filter(family=family)
            if transactions.exists():
                self.stdout.write(f"    💰 Found {transactions.count()} transactions (not migrated in this version)")
                self.stdout.write(f"    Note: Transaction migration requires budget_allocation transaction model")
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f"    Transaction migration check failed: {str(e)}")
            )
    
    def _get_category_color(self, category_type, index):
        """Get a color for migrated categories"""
        
        if category_type == 'expense':
            colors = ['#dc3545', '#fd7e14', '#ffc107', '#e83e8c', '#6f42c1', '#495057']
        else:  # income
            colors = ['#28a745', '#20c997', '#17a2b8', '#007bff', '#6610f2', '#6c757d']
        
        return colors[index % len(colors)]
