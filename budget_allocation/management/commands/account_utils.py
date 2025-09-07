"""
Account Management Utility Command

Useful utilities for managing accounts, transferring money, and performing maintenance.

Usage:
    python manage.py account_utils transfer --from-id 1 --to-id 2 --amount 100.00 --family-id 1
    python manage.py account_utils balance --account-id 1 --family-id 1
    python manage.py account_utils tree --family-id 1
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal

from accounts.models import Family
from budget_allocation.models import Account, WeeklyPeriod
from budget_allocation.utilities import (
    get_current_week, get_account_balance, transfer_money, get_account_tree
)


class Command(BaseCommand):
    help = 'Account management utilities'
    
    def add_arguments(self, parser):
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # Transfer money command
        transfer_parser = subparsers.add_parser('transfer', help='Transfer money between accounts')
        transfer_parser.add_argument('--from-id', type=int, required=True, help='Source account ID')
        transfer_parser.add_argument('--to-id', type=int, required=True, help='Destination account ID')
        transfer_parser.add_argument('--amount', type=str, required=True, help='Amount to transfer')
        transfer_parser.add_argument('--family-id', type=int, required=True, help='Family ID')
        transfer_parser.add_argument('--description', default='Manual transfer', help='Transfer description')
        
        # Check balance command
        balance_parser = subparsers.add_parser('balance', help='Check account balance')
        balance_parser.add_argument('--account-id', type=int, required=True, help='Account ID')
        balance_parser.add_argument('--family-id', type=int, required=True, help='Family ID')
        
        # Show account tree command
        tree_parser = subparsers.add_parser('tree', help='Show account tree for family')
        tree_parser.add_argument('--family-id', type=int, required=True, help='Family ID')
        
        # List accounts command
        list_parser = subparsers.add_parser('list', help='List all accounts for family')
        list_parser.add_argument('--family-id', type=int, required=True, help='Family ID')
        list_parser.add_argument('--include-balances', action='store_true', help='Include current balances')
    
    def handle(self, *args, **options):
        command = options.get('command')
        
        if not command:
            self.stdout.write(self.style.ERROR('Please specify a command: transfer, balance, tree, or list'))
            return
        
        if command == 'transfer':
            self.handle_transfer(options)
        elif command == 'balance':
            self.handle_balance(options)
        elif command == 'tree':
            self.handle_tree(options)
        elif command == 'list':
            self.handle_list(options)
        else:
            self.stdout.write(self.style.ERROR(f'Unknown command: {command}'))
    
    def handle_transfer(self, options):
        """Handle money transfer between accounts"""
        try:
            family = Family.objects.get(id=options['family_id'])
            from_account = Account.objects.get(id=options['from_id'], family=family)
            to_account = Account.objects.get(id=options['to_id'], family=family)
            amount = Decimal(options['amount'])
            description = options['description']
            
            current_week = get_current_week(family)
            
            # Check current balance
            current_balance = get_account_balance(from_account, current_week)
            
            self.stdout.write(f'Transfer Details:')
            self.stdout.write(f'  From: {from_account.name} (Current Balance: ${current_balance:,.2f})')
            self.stdout.write(f'  To: {to_account.name}')
            self.stdout.write(f'  Amount: ${amount:,.2f}')
            self.stdout.write(f'  Description: {description}')
            
            if current_balance < amount:
                self.stdout.write(
                    self.style.ERROR(
                        f'Insufficient funds! Available: ${current_balance:,.2f}, Required: ${amount:,.2f}'
                    )
                )
                return
            
            # Confirm transfer
            confirm = input('\nProceed with transfer? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Transfer cancelled.')
                return
            
            # Execute transfer
            with transaction.atomic():
                transfer_money(
                    from_account=from_account,
                    to_account=to_account,
                    amount=amount,
                    week=current_week,
                    description=description
                )
            
            self.stdout.write(self.style.SUCCESS('Transfer completed successfully!'))
            
            # Show updated balances
            new_from_balance = get_account_balance(from_account, current_week)
            new_to_balance = get_account_balance(to_account, current_week)
            
            self.stdout.write(f'Updated Balances:')
            self.stdout.write(f'  {from_account.name}: ${new_from_balance:,.2f}')
            self.stdout.write(f'  {to_account.name}: ${new_to_balance:,.2f}')
            
        except Family.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Family with ID {options["family_id"]} not found'))
        except Account.DoesNotExist:
            self.stdout.write(self.style.ERROR('One or both accounts not found'))
        except ValueError as e:
            self.stdout.write(self.style.ERROR(f'Invalid amount: {e}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Transfer failed: {e}'))
    
    def handle_balance(self, options):
        """Check account balance"""
        try:
            family = Family.objects.get(id=options['family_id'])
            account = Account.objects.get(id=options['account_id'], family=family)
            current_week = get_current_week(family)
            balance = get_account_balance(account, current_week)
            
            self.stdout.write(f'Account Balance:')
            self.stdout.write(f'  Account: {account.name}')
            self.stdout.write(f'  Type: {account.account_type}')
            self.stdout.write(f'  Current Balance: ${balance:,.2f}')
            self.stdout.write(f'  As of Week: {current_week.start_date} to {current_week.end_date}')
            
        except Family.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Family with ID {options["family_id"]} not found'))
        except Account.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Account with ID {options["account_id"]} not found'))
    
    def handle_tree(self, options):
        """Display account tree"""
        try:
            family = Family.objects.get(id=options['family_id'])
            tree = get_account_tree(family)
            current_week = get_current_week(family)
            
            self.stdout.write(f'Account Tree for {family.name}:')
            self.stdout.write('=' * 50)
            
            def display_tree(nodes, level=0):
                for node in nodes:
                    account = node['account']
                    balance = get_account_balance(account, current_week)
                    indent = '  ' * level
                    self.stdout.write(
                        f'{indent}├─ {account.name} ({account.account_type}) - ${balance:,.2f}'
                    )
                    if node['children']:
                        display_tree(node['children'], level + 1)
            
            display_tree(tree)
            
        except Family.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Family with ID {options["family_id"]} not found'))
    
    def handle_list(self, options):
        """List all accounts"""
        try:
            family = Family.objects.get(id=options['family_id'])
            accounts = Account.objects.filter(family=family).order_by('account_type', 'name')
            current_week = get_current_week(family) if options['include_balances'] else None
            
            self.stdout.write(f'Accounts for {family.name}:')
            self.stdout.write('=' * 60)
            
            for account in accounts:
                status = 'Active' if account.is_active else 'Inactive'
                parent_info = f' (under {account.parent.name})' if account.parent else ''
                
                if options['include_balances'] and current_week:
                    balance = get_account_balance(account, current_week)
                    balance_info = f' - Balance: ${balance:,.2f}'
                else:
                    balance_info = ''
                
                self.stdout.write(
                    f'  [{account.pk}] {account.name} ({account.account_type})'
                    f'{parent_info} - {status}{balance_info}'
                )
            
        except Family.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Family with ID {options["family_id"]} not found'))
