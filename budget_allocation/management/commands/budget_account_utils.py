from django.core.management.base import BaseCommand
from django.db import transaction
from accounts.models import Family
from budget_allocation.models import Account

class Command(BaseCommand):
    help = 'Utility commands for budget allocation account management'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='action', help='Available actions')
        
        # List accounts
        list_parser = subparsers.add_parser('list', help='List all accounts')
        list_parser.add_argument('--family-id', type=int, help='Filter by family ID')
        list_parser.add_argument('--show-tree', action='store_true', help='Show account hierarchy')
        
        # Clean accounts
        clean_parser = subparsers.add_parser('clean', help='Clean up orphaned or invalid accounts')
        clean_parser.add_argument('--dry-run', action='store_true', help='Show what would be cleaned')
        clean_parser.add_argument('--family-id', type=int, help='Clean specific family only')
        
        # Reset accounts
        reset_parser = subparsers.add_parser('reset', help='Reset accounts for a family')
        reset_parser.add_argument('--family-id', type=int, required=True, help='Family ID to reset')
        reset_parser.add_argument('--confirm', action='store_true', help='Confirm the reset action')
        
        # Validate accounts
        validate_parser = subparsers.add_parser('validate', help='Validate account data integrity')
        validate_parser.add_argument('--family-id', type=int, help='Validate specific family only')
        validate_parser.add_argument('--fix', action='store_true', help='Attempt to fix issues')
    
    def handle(self, *args, **options):
        """Handle the management action"""
        
        action = options.get('action')
        
        if action == 'list':
            self.list_accounts(options)
        elif action == 'clean':
            self.clean_accounts(options)
        elif action == 'reset':
            self.reset_accounts(options)
        elif action == 'validate':
            self.validate_accounts(options)
        else:
            self.print_help('manage.py', 'budget_account_utils')
    
    def list_accounts(self, options):
        """List accounts with optional filtering"""
        
        self.stdout.write(self.style.SUCCESS("📊 Budget Allocation Accounts"))
        
        if options['family_id']:
            families = Family.objects.filter(id=options['family_id'])
        else:
            families = Family.objects.all()
        
        for family in families:
            accounts = Account.objects.filter(family=family)
            
            if not accounts.exists():
                self.stdout.write(f"\n{family.name}: No accounts")
                continue
            
            self.stdout.write(f"\n🏠 {family.name} ({accounts.count()} accounts)")
            
            if options['show_tree']:
                self._show_account_tree(family)
            else:
                for account in accounts.order_by('parent__name', 'name'):
                    parent_name = account.parent.name if account.parent else "Root"
                    self.stdout.write(f"  - {account.name} (Parent: {parent_name}, Type: {account.account_type})")
    
    def clean_accounts(self, options):
        """Clean up orphaned or invalid accounts"""
        
        self.stdout.write(self.style.WARNING("🧹 Cleaning Budget Allocation Accounts"))
        
        if options['dry_run']:
            self.stdout.write(self.style.WARNING("🧪 DRY RUN MODE - No changes will be made"))
        
        if options['family_id']:
            families = Family.objects.filter(id=options['family_id'])
        else:
            families = Family.objects.all()
        
        issues_found = 0
        
        for family in families:
            accounts = Account.objects.filter(family=family)
            
            # Check for circular references
            for account in accounts:
                if self._has_circular_reference(account):
                    issues_found += 1
                    self.stdout.write(
                        self.style.ERROR(f"❌ Circular reference detected: {account.name} in {family.name}")
                    )
                    if not options['dry_run']:
                        account.parent = None
                        account.save()
                        self.stdout.write(f"  ✓ Fixed: Reset parent for {account.name}")
            
            # Check for invalid account types
            for account in accounts:
                if account.parent and account.account_type != account.parent.account_type:
                    issues_found += 1
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ Type mismatch: {account.name} ({account.account_type}) under {account.parent.name} ({account.parent.account_type})")
                    )
                    if not options['dry_run']:
                        account.account_type = account.parent.account_type
                        account.save()
                        self.stdout.write(f"  ✓ Fixed: Updated type for {account.name}")
        
        if issues_found == 0:
            self.stdout.write(self.style.SUCCESS("✅ No issues found"))
        else:
            self.stdout.write(f"Found {issues_found} issues")
    
    def reset_accounts(self, options):
        """Reset accounts for a family"""
        
        family_id = options['family_id']
        family = Family.objects.get(id=family_id)
        
        accounts = Account.objects.filter(family=family)
        
        self.stdout.write(f"⚠️ This will delete ALL {accounts.count()} accounts for {family.name}")
        
        if not options['confirm']:
            self.stdout.write(self.style.ERROR("❌ Add --confirm to proceed with reset"))
            return
        
        with transaction.atomic():
            deleted_count = accounts.count()
            accounts.delete()
            
            # Recreate default accounts
            from budget_allocation.utils import ensure_default_accounts_exist
            income_account, expense_account = ensure_default_accounts_exist(family)
            
            self.stdout.write(
                self.style.SUCCESS(f"✅ Reset complete: Deleted {deleted_count} accounts, created 2 default accounts")
            )
    
    def validate_accounts(self, options):
        """Validate account data integrity"""
        
        self.stdout.write(self.style.SUCCESS("🔍 Validating Account Data Integrity"))
        
        if options['family_id']:
            families = Family.objects.filter(id=options['family_id'])
        else:
            families = Family.objects.all()
        
        total_issues = 0
        
        for family in families:
            self.stdout.write(f"\n🏠 Validating {family.name}")
            family_issues = 0
            
            accounts = Account.objects.filter(family=family)
            
            # 1. Check for accounts without families
            orphaned = accounts.filter(family__isnull=True)
            if orphaned.exists():
                family_issues += orphaned.count()
                self.stdout.write(self.style.ERROR(f"  ❌ {orphaned.count()} orphaned accounts (no family)"))
                if options['fix']:
                    orphaned.delete()
                    self.stdout.write("    ✓ Deleted orphaned accounts")
            
            # 2. Check for root accounts with parents
            invalid_roots = accounts.filter(parent__isnull=False, account_type__in=['income', 'expense'])
            if invalid_roots.exists():
                family_issues += invalid_roots.count()
                self.stdout.write(self.style.ERROR(f"  ❌ {invalid_roots.count()} root accounts with parents"))
                if options['fix']:
                    for account in invalid_roots:
                        if account.name in ['Income', 'Expenses']:
                            account.parent = None
                            account.save()
                    self.stdout.write("    ✓ Fixed root account parents")
            
            # 3. Check for missing default accounts
            has_income = accounts.filter(parent__isnull=True, account_type='income').exists()
            has_expense = accounts.filter(parent__isnull=True, account_type='expense').exists()
            
            if not has_income or not has_expense:
                family_issues += 1
                self.stdout.write(self.style.ERROR(f"  ❌ Missing default accounts (Income: {has_income}, Expenses: {has_expense})"))
                if options['fix']:
                    from budget_allocation.utils import ensure_default_accounts_exist
                    ensure_default_accounts_exist(family)
                    self.stdout.write("    ✓ Created missing default accounts")
            
            # 4. Check for circular references
            for account in accounts:
                if self._has_circular_reference(account):
                    family_issues += 1
                    self.stdout.write(self.style.ERROR(f"  ❌ Circular reference: {account.name}"))
                    if options['fix']:
                        account.parent = None
                        account.save()
                        self.stdout.write(f"    ✓ Fixed: Reset parent for {account.name}")
            
            if family_issues == 0:
                self.stdout.write(self.style.SUCCESS(f"  ✅ {family.name} is valid"))
            else:
                total_issues += family_issues
                self.stdout.write(self.style.WARNING(f"  ⚠️ {family_issues} issues found"))
        
        if total_issues == 0:
            self.stdout.write(self.style.SUCCESS("\n🎉 All families validated successfully"))
        else:
            self.stdout.write(f"\n⚠️ Total issues found: {total_issues}")
    
    def _show_account_tree(self, family):
        """Show accounts in tree format"""
        
        root_accounts = Account.objects.filter(family=family, parent=None)
        
        for root in root_accounts:
            self.stdout.write(f"  📊 {root.name} ({root.account_type})")
            self._show_children(root, indent="    ")
    
    def _show_children(self, account, indent=""):
        """Recursively show child accounts"""
        
        children = Account.objects.filter(parent=account)
        for child in children:
            self.stdout.write(f"{indent}└── {child.name}")
            self._show_children(child, indent + "    ")
    
    def _has_circular_reference(self, account, visited=None):
        """Check for circular references in account hierarchy"""
        
        if visited is None:
            visited = set()
        
        if account.id in visited:
            return True
        
        if not account.parent:
            return False
        
        visited.add(account.id)
        return self._has_circular_reference(account.parent, visited)
