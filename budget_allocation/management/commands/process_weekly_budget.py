"""
Budget Allocation Weekly Processing Command

This command should be run weekly (typically at the start of each week) to:
1. Create new weekly periods
2. Apply budget templates automatically
3. Process interest on loans
4. Execute auto-repayments
5. Generate weekly reports

Usage:
    python manage.py process_weekly_budget

Schedule this command to run automatically via cron job or task scheduler.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from decimal import Decimal
from datetime import date, timedelta

from accounts.models import Family
from budget_allocation.models import (
    WeeklyPeriod, AccountLoan, LoanPayment, FamilySettings,
    Account, Allocation, Transaction
)
from budget_allocation.utilities import (
    get_current_week, apply_budget_templates, get_account_balance
)


class Command(BaseCommand):
    help = 'Process weekly budget operations for all families'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--family-id',
            type=int,
            help='Process only specific family (optional)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force processing even if already processed this week',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.force = options['force']
        
        if self.dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Get families to process
        if options['family_id']:
            families = Family.objects.filter(id=options['family_id'])
            if not families.exists():
                self.stdout.write(
                    self.style.ERROR(f'Family with ID {options["family_id"]} not found')
                )
                return
        else:
            families = Family.objects.all()
        
        self.stdout.write(f'Processing {families.count()} families...')
        
        for family in families:
            self.process_family(family)
        
        self.stdout.write(
            self.style.SUCCESS('Weekly processing completed successfully!')
        )
    
    def process_family(self, family):
        """Process weekly operations for a single family"""
        self.stdout.write(f'Processing family: {family.name}')
        
        try:
            with transaction.atomic():
                # Get current week
                current_week = get_current_week(family)
                
                # Check if already processed this week
                if current_week.is_allocated and not self.force:
                    self.stdout.write(
                        self.style.WARNING(
                            f'  Family {family.name} already processed this week'
                        )
                    )
                    return
                
                # Step 1: Apply budget templates
                self.apply_budget_templates(family, current_week)
                
                # Step 2: Process loan interest
                self.process_loan_interest(family, current_week)
                
                # Step 3: Execute auto-repayments
                self.execute_auto_repayments(family, current_week)
                
                # Step 4: Mark week as processed
                if not self.dry_run:
                    current_week.is_allocated = True
                    current_week.save()
                
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Family {family.name} processed successfully')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'  ✗ Error processing family {family.name}: {str(e)}')
            )
    
    def apply_budget_templates(self, family, week):
        """Apply budget templates for automatic allocation"""
        self.stdout.write('    Applying budget templates...')
        
        if self.dry_run:
            self.stdout.write('      [DRY RUN] Would apply budget templates')
            return
        
        apply_budget_templates(family, week)
        self.stdout.write('      ✓ Budget templates applied')
    
    def process_loan_interest(self, family, week):
        """Apply interest to active loans"""
        self.stdout.write('    Processing loan interest...')
        
        # Get family settings
        settings = FamilySettings.objects.filter(family=family).first()
        if not settings:
            self.stdout.write('      No family settings found, skipping interest')
            return
        
        active_loans = AccountLoan.objects.filter(
            lender_account__family=family,
            is_active=True
        )
        
        interest_applied = 0
        
        for loan in active_loans:
            if self.dry_run:
                interest_rate = loan.weekly_interest_rate
                interest_amount = loan.remaining_amount * interest_rate
                self.stdout.write(
                    f'      [DRY RUN] Would apply ${interest_amount:.2f} interest to loan {loan.pk}'
                )
                interest_applied += 1
            else:
                # Apply interest by increasing the loan balance
                interest_rate = loan.weekly_interest_rate
                interest_amount = loan.remaining_amount * interest_rate
                
                if interest_amount > 0:
                    loan.remaining_amount += interest_amount
                    loan.total_interest_charged += interest_amount
                    loan.save()
                    
                    # Create transaction record for interest
                    Transaction.objects.create(
                        account=loan.borrower_account,
                        week=week,
                        amount=interest_amount,
                        transaction_type='expense',
                        description=f'Interest charge on loan from {loan.lender_account.name}'
                    )
                    
                    interest_applied += 1
        
        if interest_applied > 0:
            self.stdout.write(f'      ✓ Interest applied to {interest_applied} loans')
        else:
            self.stdout.write('      No active loans requiring interest')
    
    def execute_auto_repayments(self, family, week):
        """Execute automatic loan repayments"""
        self.stdout.write('    Processing auto-repayments...')
        
        # Get family settings
        settings = FamilySettings.objects.filter(family=family).first()
        if not settings or not settings.auto_repay_enabled:
            self.stdout.write('      Auto-repay disabled, skipping')
            return
        
        active_loans = AccountLoan.objects.filter(
            lender_account__family=family,
            is_active=True
        )
        
        repayments_made = 0
        
        for loan in active_loans:
            available_balance = get_account_balance(loan.borrower_account, week)
            
            # Calculate auto-repayment amount (25% of available balance or full loan)
            max_payment = min(
                available_balance * Decimal('0.25'),
                loan.remaining_amount
            )
            
            # Only auto-repay if amount is above threshold
            if max_payment >= settings.notification_threshold:
                if self.dry_run:
                    self.stdout.write(
                        f'      [DRY RUN] Would auto-repay ${max_payment:.2f} on loan {loan.pk}'
                    )
                    repayments_made += 1
                else:
                    # Create payment record
                    payment = LoanPayment.objects.create(
                        loan=loan,
                        amount=max_payment,
                        week=week,
                        payment_date=week.start_date,
                        notes='Automatic loan payment'
                    )
                    
                    # Create transfer transactions
                    Transaction.objects.create(
                        account=loan.borrower_account,
                        week=week,
                        amount=max_payment,
                        transaction_type='expense',
                        description=f'Auto loan payment to {loan.lender_account.name}'
                    )
                    
                    Transaction.objects.create(
                        account=loan.lender_account,
                        week=week,
                        amount=max_payment,
                        transaction_type='income',
                        description=f'Auto loan payment from {loan.borrower_account.name}'
                    )
                    
                    # Update loan balance
                    loan.remaining_amount -= max_payment
                    if loan.remaining_amount <= 0:
                        loan.is_active = False
                    loan.save()
                    
                    repayments_made += 1
        
        if repayments_made > 0:
            self.stdout.write(f'      ✓ {repayments_made} auto-repayments processed')
        else:
            self.stdout.write('      No auto-repayments needed')
