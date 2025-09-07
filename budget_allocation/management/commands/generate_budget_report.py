"""
Budget Allocation Report Generation Command

Generate comprehensive financial reports for families.

Usage:
    python manage.py generate_budget_report --family-id 1
    python manage.py generate_budget_report --all-families
    python manage.py generate_budget_report --format json --family-id 1
"""
from django.core.management.base import BaseCommand
from django.db.models import Sum, Q, Count
from decimal import Decimal
import json
from datetime import date, timedelta

from accounts.models import Family
from budget_allocation.models import (
    Account, WeeklyPeriod, Allocation, Transaction, 
    AccountLoan, LoanPayment, BudgetTemplate
)
from budget_allocation.utilities import (
    get_current_week, get_account_balance, get_available_money
)


class Command(BaseCommand):
    help = 'Generate comprehensive budget allocation reports'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--family-id',
            type=int,
            help='Generate report for specific family',
        )
        parser.add_argument(
            '--all-families',
            action='store_true',
            help='Generate reports for all families',
        )
        parser.add_argument(
            '--format',
            choices=['text', 'json'],
            default='text',
            help='Output format (text or json)',
        )
        parser.add_argument(
            '--weeks',
            type=int,
            default=4,
            help='Number of weeks to include in report (default: 4)',
        )
    
    def handle(self, *args, **options):
        self.format = options['format']
        self.weeks = options['weeks']
        
        # Get families to process
        if options['family_id']:
            families = Family.objects.filter(id=options['family_id'])
            if not families.exists():
                self.stdout.write(
                    self.style.ERROR(f'Family with ID {options["family_id"]} not found')
                )
                return
        elif options['all_families']:
            families = Family.objects.all()
        else:
            self.stdout.write(
                self.style.ERROR('Please specify --family-id or --all-families')
            )
            return
        
        if self.format == 'json':
            reports = []
            for family in families:
                reports.append(self.generate_family_report(family))
            self.stdout.write(json.dumps(reports, indent=2, default=str))
        else:
            for family in families:
                self.display_family_report(family)
    
    def generate_family_report(self, family):
        """Generate comprehensive report data for a family"""
        current_week = get_current_week(family)
        
        # Get recent weeks
        recent_weeks = WeeklyPeriod.objects.filter(
            family=family,
            start_date__lte=current_week.start_date
        ).order_by('-start_date')[:self.weeks]
        
        # Account summary
        accounts = Account.objects.filter(family=family, is_active=True)
        account_data = []
        
        for account in accounts:
            balance = get_account_balance(account, current_week)
            account_data.append({
                'name': account.name,
                'type': account.account_type,
                'balance': float(balance),
                'color': account.color,
                'parent': account.parent.name if account.parent else None
            })
        
        # Weekly data
        weekly_data = []
        for week in recent_weeks:
            week_income = Transaction.objects.filter(
                account__family=family,
                week=week,
                transaction_type='income'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            week_expenses = Transaction.objects.filter(
                account__family=family,
                week=week,
                transaction_type='expense'
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            week_allocated = Allocation.objects.filter(
                week=week
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            weekly_data.append({
                'week_start': week.start_date,
                'week_end': week.end_date,
                'income': float(week_income),
                'expenses': float(week_expenses),
                'allocated': float(week_allocated),
                'net': float(week_income - week_expenses)
            })
        
        # Loan summary
        active_loans = AccountLoan.objects.filter(
            lender_account__family=family,
            is_active=True
        )
        
        loan_data = {
            'active_count': active_loans.count(),
            'total_outstanding': float(
                active_loans.aggregate(
                    total=Sum('remaining_amount')
                )['total'] or 0
            ),
            'total_interest_charged': float(
                active_loans.aggregate(
                    total=Sum('total_interest_charged')
                )['total'] or 0
            )
        }
        
        # Budget template summary
        templates = BudgetTemplate.objects.filter(family=family, is_active=True)
        template_data = [
            {
                'account': template.account.name,
                'type': template.allocation_type,
                'amount': float(template.weekly_amount or 0),
                'percentage': float(template.percentage or 0),
                'priority': template.priority
            }
            for template in templates
        ]
        
        return {
            'family_name': family.name,
            'report_date': date.today(),
            'current_week': {
                'start': current_week.start_date,
                'end': current_week.end_date,
                'available_money': float(get_available_money(family, current_week))
            },
            'accounts': account_data,
            'weekly_history': weekly_data,
            'loans': loan_data,
            'budget_templates': template_data
        }
    
    def display_family_report(self, family):
        """Display formatted text report for a family"""
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS(f'BUDGET REPORT: {family.name}'))
        self.stdout.write('=' * 60)
        
        report_data = self.generate_family_report(family)
        current_week = report_data['current_week']
        
        # Current week summary
        self.stdout.write(f"""
CURRENT WEEK ({current_week['start']} to {current_week['end']}):
  Available Money: ${current_week['available_money']:,.2f}
""")
        
        # Account balances
        self.stdout.write('\nACCOUNT BALANCES:')
        self.stdout.write('-' * 40)
        for account in report_data['accounts']:
            parent_info = f" (under {account['parent']})" if account['parent'] else ""
            self.stdout.write(
                f"  {account['name']}{parent_info}: ${account['balance']:,.2f}"
            )
        
        # Recent weeks
        self.stdout.write(f'\nRECENT {self.weeks} WEEKS:')
        self.stdout.write('-' * 40)
        for week in report_data['weekly_history']:
            self.stdout.write(
                f"  {week['week_start']} to {week['week_end']}: "
                f"Income ${week['income']:,.2f}, "
                f"Expenses ${week['expenses']:,.2f}, "
                f"Net ${week['net']:,.2f}"
            )
        
        # Loan summary
        loans = report_data['loans']
        if loans['active_count'] > 0:
            self.stdout.write('\nACTIVE LOANS:')
            self.stdout.write('-' * 40)
            self.stdout.write(f"  Active Loans: {loans['active_count']}")
            self.stdout.write(f"  Total Outstanding: ${loans['total_outstanding']:,.2f}")
            self.stdout.write(f"  Total Interest Charged: ${loans['total_interest_charged']:,.2f}")
        
        # Budget templates
        if report_data['budget_templates']:
            self.stdout.write('\nBUDGET TEMPLATES:')
            self.stdout.write('-' * 40)
            for template in report_data['budget_templates']:
                if template['type'] == 'percentage':
                    amount_info = f"{template['percentage']}%"
                else:
                    amount_info = f"${template['amount']:,.2f}"
                self.stdout.write(
                    f"  {template['account']} ({template['type']}): {amount_info} "
                    f"(Priority {template['priority']})"
                )
        
        self.stdout.write('\n')
