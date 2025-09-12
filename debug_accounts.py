#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
django.setup()

from budget_allocation.models import Account
from accounts.models import Family
from budget_allocation.utilities import get_account_tree

def debug_accounts():
    family = Family.objects.first()
    if not family:
        print("No family found")
        return
    
    print(f"Family: {family.name}")
    print("=" * 50)
    
    # Show all accounts
    accounts = Account.objects.filter(family=family).order_by('account_type', 'name')
    print(f"Total accounts: {accounts.count()}")
    print("\nAll accounts:")
    for acc in accounts:
        parent_name = acc.parent.name if acc.parent else "None"
        print(f"  {acc.id}: {acc.name} (type: {acc.account_type}, parent: {parent_name})")
    
    # Show tree structure
    print("\nTree structure:")
    tree = get_account_tree(family)
    
    def print_tree(node_list, indent=0):
        for node in node_list:
            account = node['account']
            level = node['level']
            children = node['children']
            
            prefix = "  " * indent
            print(f"{prefix}- {account.name} (type: {account.account_type}, level: {level})")
            
            if children:
                print_tree(children, indent + 1)
    
    print_tree(tree)

if __name__ == "__main__":
    debug_accounts()