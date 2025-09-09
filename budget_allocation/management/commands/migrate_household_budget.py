from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Family

class Command(BaseCommand):
    help = 'Migrate household_budget data to budget_allocation'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )
        parser.add_argument(
            '--family-id',
            type=int,
            help='Migrate specific family only',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed migration information',
        )
    
    def handle(self, *args, **options):
        """Handle the migration process"""
        
        self.stdout.write(
            self.style.SUCCESS("🔄 Starting Household Budget Migration...")
        )
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("🧪 DRY RUN MODE - No changes will be made"))
        
        # Get families to migrate
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
                self.migrate_family_data(family, options)
                success_count += 1
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f"✗ Migration failed for {family.name}: {str(e)}")
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🎉 Migration complete: {success_count} families successful, {error_count} errors"
            )
        )
    
    def migrate_family_data(self, family, options):
        """Migrate data for a single family"""
        
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        try:
            from household_budget.models import BudgetCategory, Transaction, Budget
            from budget_allocation.models import Account, WeeklyPeriod
            from budget_allocation.utils import ensure_default_accounts_exist
            
            self.stdout.write(f"\n📊 Processing {family.name}...")
            
            # Get household_budget data
            categories = BudgetCategory.objects.filter(family=family)
            transactions = Transaction.objects.filter(family=family)
            budgets = Budget.objects.filter(family=family) if hasattr(Budget, 'family') else Budget.objects.none()
            
            self.stdout.write(f"  Found {categories.count()} categories, {transactions.count()} transactions, {budgets.count()} budgets")
            
            if not categories.exists() and not transactions.exists():
                self.stdout.write(f"  No data to migrate for {family.name}")
                return
            
            if dry_run:
                self._show_migration_preview(family, categories, transactions, budgets, verbose)
                return
            
            # Ensure default accounts exist
            income_account, expense_account = ensure_default_accounts_exist(family)
            
            # Migrate categories to accounts
            category_mapping = {}
            migrated_count = 0
            
            with transaction.atomic():
                for category in categories:
                    parent = expense_account if category.category_type == 'expense' else income_account
                    
                    account, created = Account.objects.get_or_create(
                        family=family,
                        name=category.name,
                        parent=parent,
                        defaults={
                            'description': category.description or f'Migrated from household_budget: {category.name}',
                            'account_type': category.category_type,
                            'is_active': category.is_active,
                            'color': self._get_category_color(category.category_type, len(category_mapping)),
                        }
                    )
                    
                    category_mapping[category.id] = account
                    
                    if created:
                        migrated_count += 1
                        if verbose:
                            self.stdout.write(f"    ✓ Created: {category.name} -> {account.name}")
                    elif verbose:
                        self.stdout.write(f"    - Exists: {category.name}")
                
                self.stdout.write(f"  📈 Migrated {migrated_count} categories to accounts")
                
                # Future: Migrate transactions and budgets
                if transactions.exists():
                    self.stdout.write(f"  💰 {transactions.count()} transactions found (migration not implemented yet)")
                
                if budgets.exists():
                    self.stdout.write(f"  📋 {budgets.count()} budgets found (migration not implemented yet)")
            
        except ImportError:
            self.stdout.write(
                self.style.ERROR("❌ household_budget app not found - cannot migrate data")
            )
            raise
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"❌ Migration failed for {family.name}: {str(e)}")
            )
            raise
    
    def _show_migration_preview(self, family, categories, transactions, budgets, verbose):
        """Show what would be migrated without making changes"""
        
        self.stdout.write(f"  🔍 Migration preview for {family.name}:")
        
        # Categories
        income_categories = categories.filter(category_type='income')
        expense_categories = categories.filter(category_type='expense')
        
        if income_categories.exists():
            self.stdout.write(f"    💰 Income categories ({income_categories.count()}):")
            if verbose:
                for cat in income_categories:
                    self.stdout.write(f"      - {cat.name}: {cat.description or 'No description'}")
        
        if expense_categories.exists():
            self.stdout.write(f"    💸 Expense categories ({expense_categories.count()}):")
            if verbose:
                for cat in expense_categories:
                    self.stdout.write(f"      - {cat.name}: {cat.description or 'No description'}")
        
        # Transactions by category
        if transactions.exists() and verbose:
            self.stdout.write(f"    💰 Transaction summary:")
            for category in categories:
                cat_transactions = transactions.filter(category=category)
                if cat_transactions.exists():
                    total = sum(t.amount for t in cat_transactions)
                    self.stdout.write(f"      - {category.name}: {cat_transactions.count()} transactions, total: ${total}")
        
        # Budgets
        if budgets.exists() and verbose:
            self.stdout.write(f"    📋 Budget summary:")
            for budget in budgets[:5]:  # Show first 5
                self.stdout.write(f"      - {budget}")
    
    def _get_category_color(self, category_type, index):
        """Get a color for migrated categories"""
        
        if category_type == 'expense':
            colors = [
                '#dc3545',  # Red
                '#fd7e14',  # Orange
                '#ffc107',  # Yellow
                '#e83e8c',  # Pink
                '#6f42c1',  # Purple
                '#495057',  # Dark gray
                '#721c24',  # Dark red
                '#8a4a0b',  # Dark orange
            ]
        else:  # income
            colors = [
                '#28a745',  # Green
                '#20c997',  # Teal
                '#17a2b8',  # Info blue
                '#007bff',  # Primary blue
                '#6610f2',  # Indigo
                '#6c757d',  # Gray
                '#155724',  # Dark green
                '#0f5132',  # Darker green
            ]
        
        return colors[index % len(colors)]
