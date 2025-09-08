"""
Budget Allocation Sample Data Fixtures

Creates realistic sample data for development and testing:
- Family structure with multiple users
- Hierarchical account structure (root, income, spending categories)
- Budget templates for automatic allocation
- Sample transactions and allocations
- Loan examples
- Multiple weekly periods
"""
import json
from datetime import date, timedelta
from decimal import Decimal


def create_sample_data():
    """Generate comprehensive sample data for Budget Allocation app"""
    
    # Base data structure
    data = []
    
    # 1. Family and Users
    family_data = {
        "model": "accounts.family",
        "pk": 1,
        "fields": {
            "name": "Johnson Family",
            "created_by": 1,
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    }
    data.append(family_data)
    
    # Sample users
    users = [
        {
            "model": "auth.user",
            "pk": 1,
            "fields": {
                "username": "john_johnson",
                "first_name": "John",
                "last_name": "Johnson",
                "email": "john@johnsonfamily.com",
                "is_staff": False,
                "is_superuser": False,
                "date_joined": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "auth.user",
            "pk": 2,
            "fields": {
                "username": "sarah_johnson",
                "first_name": "Sarah",
                "last_name": "Johnson",
                "email": "sarah@johnsonfamily.com",
                "is_staff": False,
                "is_superuser": False,
                "date_joined": "2024-01-01T00:00:00Z"
            }
        }
    ]
    data.extend(users)
    
    # Family members
    family_members = [
        {
            "model": "accounts.familymember",
            "pk": 1,
            "fields": {
                "user": 1,
                "family": 1,
                "role": "admin",
                "joined_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "accounts.familymember",
            "pk": 2,
            "fields": {
                "user": 2,
                "family": 1,
                "role": "parent",
                "joined_at": "2024-01-01T00:00:00Z"
            }
        }
    ]
    data.extend(family_members)
    
    # 2. Family Settings
    settings_data = {
        "model": "budget_allocation.familysettings",
        "pk": 1,
        "fields": {
            "family": 1,
            "week_start_day": 0,  # Monday
            "default_interest_rate": "0.0200",
            "auto_allocate_enabled": True,
            "auto_repay_enabled": False,
            "notification_threshold": "100.00",
            "created_at": "2024-01-01T00:00:00Z",
            "updated_at": "2024-01-01T00:00:00Z"
        }
    }
    data.append(settings_data)
    
    # 3. Account Hierarchy
    accounts = [
        # Root account
        {
            "model": "budget_allocation.account",
            "pk": 1,
            "fields": {
                "family": 1,
                "name": "Johnson Family Budget",
                "description": "Root account for all family finances",
                "account_type": "root",
                "parent": None,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        
        # Income accounts
        {
            "model": "budget_allocation.account",
            "pk": 2,
            "fields": {
                "family": 1,
                "name": "Income",
                "description": "All family income sources",
                "account_type": "income",
                "parent": 1,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 3,
            "fields": {
                "family": 1,
                "name": "John's Salary",
                "description": "Primary income from software development job",
                "account_type": "income",
                "parent": 2,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 4,
            "fields": {
                "family": 1,
                "name": "Sarah's Salary",
                "description": "Income from teaching position",
                "account_type": "income",
                "parent": 2,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 5,
            "fields": {
                "family": 1,
                "name": "Side Projects",
                "description": "Freelance and consulting income",
                "account_type": "income",
                "parent": 2,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        
        # Essential spending accounts
        {
            "model": "budget_allocation.account",
            "pk": 6,
            "fields": {
                "family": 1,
                "name": "Essential Expenses",
                "description": "Must-have expenses for daily living",
                "account_type": "spending",
                "parent": 1,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 7,
            "fields": {
                "family": 1,
                "name": "Housing",
                "description": "Rent, utilities, maintenance",
                "account_type": "spending",
                "parent": 6,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 8,
            "fields": {
                "family": 1,
                "name": "Groceries",
                "description": "Food and household supplies",
                "account_type": "spending",
                "parent": 6,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 9,
            "fields": {
                "family": 1,
                "name": "Transportation",
                "description": "Car payments, gas, public transit",
                "account_type": "spending",
                "parent": 6,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 10,
            "fields": {
                "family": 1,
                "name": "Healthcare",
                "description": "Insurance, medications, doctor visits",
                "account_type": "spending",
                "parent": 6,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        
        # Savings accounts
        {
            "model": "budget_allocation.account",
            "pk": 11,
            "fields": {
                "family": 1,
                "name": "Savings & Investments",
                "description": "Long-term savings and investment funds",
                "account_type": "spending",
                "parent": 1,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 12,
            "fields": {
                "family": 1,
                "name": "Emergency Fund",
                "description": "Emergency savings (6 months expenses)",
                "account_type": "spending",
                "parent": 11,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 13,
            "fields": {
                "family": 1,
                "name": "Retirement",
                "description": "401k and IRA contributions",
                "account_type": "spending",
                "parent": 11,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 14,
            "fields": {
                "family": 1,
                "name": "House Down Payment",
                "description": "Saving for first home purchase",
                "account_type": "spending",
                "parent": 11,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        
        # Discretionary spending
        {
            "model": "budget_allocation.account",
            "pk": 15,
            "fields": {
                "family": 1,
                "name": "Lifestyle & Entertainment",
                "description": "Non-essential but enjoyable expenses",
                "account_type": "spending",
                "parent": 1,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 16,
            "fields": {
                "family": 1,
                "name": "Dining Out",
                "description": "Restaurants and takeout",
                "account_type": "spending",
                "parent": 15,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 17,
            "fields": {
                "family": 1,
                "name": "Vacation Fund",
                "description": "Annual vacation savings",
                "account_type": "spending",
                "parent": 15,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 18,
            "fields": {
                "family": 1,
                "name": "Hobbies",
                "description": "Personal interests and hobbies",
                "account_type": "spending",
                "parent": 15,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        
        # Debt accounts
        {
            "model": "budget_allocation.account",
            "pk": 19,
            "fields": {
                "family": 1,
                "name": "Debt Payments",
                "description": "Credit cards, loans, and other debt",
                "account_type": "spending",
                "parent": 1,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.account",
            "pk": 20,
            "fields": {
                "family": 1,
                "name": "Student Loans",
                "description": "Monthly student loan payments",
                "account_type": "spending",
                "parent": 19,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    ]
    data.extend(accounts)
    
    # 4. Weekly Periods (last 4 weeks + current + next 2)
    base_date = date(2024, 8, 19)  # Monday
    weekly_periods = []
    
    for i in range(-4, 3):  # 7 weeks total
        week_start = base_date + timedelta(weeks=i)
        week_end = week_start + timedelta(days=6)
        
        weekly_periods.append({
            "model": "budget_allocation.weeklyperiod",
            "pk": i + 5,  # pk 1-7
            "fields": {
                "family": 1,
                "start_date": week_start.isoformat(),
                "end_date": week_end.isoformat(),
                "is_current": i == 0,  # Current week
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        })
    
    data.extend(weekly_periods)
    
    # 5. Budget Templates
    budget_templates = [
        # Essential fixed allocations
        {
            "model": "budget_allocation.budgettemplate",
            "pk": 1,
            "fields": {
                "family": 1,
                "account": 7,  # Housing
                "name": "Weekly Housing Allocation",
                "description": "Fixed weekly amount for rent and utilities",
                "allocation_type": "fixed",
                "weekly_amount": "500.00",
                "priority": 1,
                "is_essential": True,
                "never_miss": True,
                "auto_allocate": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.budgettemplate",
            "pk": 2,
            "fields": {
                "family": 1,
                "account": 8,  # Groceries
                "name": "Weekly Grocery Budget",
                "description": "Food and household supplies",
                "allocation_type": "fixed",
                "weekly_amount": "150.00",
                "priority": 1,
                "is_essential": True,
                "never_miss": True,
                "auto_allocate": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.budgettemplate",
            "pk": 3,
            "fields": {
                "family": 1,
                "account": 9,  # Transportation
                "name": "Transportation Costs",
                "description": "Gas, car payment, maintenance",
                "allocation_type": "fixed",
                "weekly_amount": "100.00",
                "priority": 1,
                "is_essential": True,
                "never_miss": True,
                "auto_allocate": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        
        # Percentage-based savings
        {
            "model": "budget_allocation.budgettemplate",
            "pk": 4,
            "fields": {
                "family": 1,
                "account": 12,  # Emergency Fund
                "name": "Emergency Fund Building",
                "description": "10% of income to emergency savings",
                "allocation_type": "percentage",
                "percentage": "10.00",
                "priority": 2,
                "is_essential": False,
                "never_miss": False,
                "auto_allocate": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.budgettemplate",
            "pk": 5,
            "fields": {
                "family": 1,
                "account": 13,  # Retirement
                "name": "Retirement Savings",
                "description": "15% of income for retirement",
                "allocation_type": "percentage",
                "percentage": "15.00",
                "priority": 2,
                "is_essential": False,
                "never_miss": False,
                "auto_allocate": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        
        # Range-based allocations
        {
            "model": "budget_allocation.budgettemplate",
            "pk": 6,
            "fields": {
                "family": 1,
                "account": 16,  # Dining Out
                "name": "Dining Out Budget",
                "description": "Flexible restaurant budget",
                "allocation_type": "range",
                "min_amount": "50.00",
                "max_amount": "200.00",
                "priority": 4,
                "is_essential": False,
                "never_miss": False,
                "auto_allocate": True,
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.budgettemplate",
            "pk": 7,
            "fields": {
                "family": 1,
                "account": 17,  # Vacation Fund
                "name": "Vacation Savings",
                "description": "Save for annual vacation",
                "allocation_type": "fixed",
                "weekly_amount": "75.00",
                "priority": 3,
                "is_essential": False,
                "never_miss": False,
                "auto_allocate": True,
                "is_active": True,
                "annual_amount": "4000.00",
                "current_saved": "1250.00",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    ]
    data.extend(budget_templates)
    
    # 6. Sample Transactions (last 4 weeks)
    transactions = []
    transaction_id = 1
    
    # Weekly income pattern
    for week_offset in range(-4, 1):  # Last 4 weeks + current
        week_pk = week_offset + 5
        transaction_date = base_date + timedelta(weeks=week_offset)
        
        # John's salary (bi-weekly, on even weeks)
        if week_offset % 2 == 0:
            transactions.append({
                "model": "budget_allocation.transaction",
                "pk": transaction_id,
                "fields": {
                    "account": 3,  # John's Salary
                    "week": week_pk,
                    "amount": "2400.00",
                    "transaction_type": "income",
                    "description": "Bi-weekly salary - Software Development",
                    "transaction_date": transaction_date.isoformat(),
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            })
            transaction_id += 1
        
        # Sarah's salary (weekly)
        transactions.append({
            "model": "budget_allocation.transaction",
            "pk": transaction_id,
            "fields": {
                "account": 4,  # Sarah's Salary
                "week": week_pk,
                "amount": "800.00",
                "transaction_type": "income",
                "description": "Weekly teaching salary",
                "transaction_date": transaction_date.isoformat(),
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        })
        transaction_id += 1
        
        # Occasional side project income
        if week_offset == -2:
            transactions.append({
                "model": "budget_allocation.transaction",
                "pk": transaction_id,
                "fields": {
                    "account": 5,  # Side Projects
                    "week": week_pk,
                    "amount": "500.00",
                    "transaction_type": "income",
                    "description": "Freelance web development project",
                    "transaction_date": (transaction_date + timedelta(days=2)).isoformat(),
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            })
            transaction_id += 1
        
        # Regular expenses
        expense_patterns = [
            (7, "500.00", "Weekly housing allocation"),
            (8, "150.00", "Weekly grocery shopping"),
            (9, "100.00", "Transportation costs"),
            (10, "50.00", "Healthcare expenses"),
            (16, "75.00", "Dining out"),
            (12, "200.00", "Emergency fund contribution"),
            (13, "300.00", "Retirement savings"),
        ]
        
        for account_id, amount, description in expense_patterns:
            transactions.append({
                "model": "budget_allocation.transaction",
                "pk": transaction_id,
                "fields": {
                    "account": account_id,
                    "week": week_pk,
                    "amount": f"-{amount}",
                    "transaction_type": "expense",
                    "description": description,
                    "transaction_date": (transaction_date + timedelta(days=1)).isoformat(),
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            })
            transaction_id += 1
    
    data.extend(transactions)
    
    # 7. Sample Allocations (automated from templates)
    allocations = []
    allocation_id = 1
    
    for week_offset in range(-4, 1):
        week_pk = week_offset + 5
        week_income = 800.00  # Sarah's weekly
        if week_offset % 2 == 0:
            week_income += 2400.00  # John's bi-weekly
        
        # Template-based allocations
        template_allocations = [
            (1, 7, "500.00"),    # Housing
            (2, 8, "150.00"),    # Groceries
            (3, 9, "100.00"),    # Transportation
            (4, 12, str(week_income * 0.10)),  # Emergency Fund (10%)
            (5, 13, str(week_income * 0.15)),  # Retirement (15%)
            (6, 16, "75.00"),    # Dining Out (mid-range)
            (7, 17, "75.00"),    # Vacation Fund
        ]
        
        for template_id, account_id, amount in template_allocations:
            allocations.append({
                "model": "budget_allocation.allocation",
                "pk": allocation_id,
                "fields": {
                    "week": week_pk,
                    "to_account": account_id,
                    "from_account": 2,  # Income account
                    "amount": amount,
                    "allocation_type": "automatic",
                    "description": f"Auto-allocation from budget template",
                    "template": template_id,
                    "processed": True,
                    "processed_date": (base_date + timedelta(weeks=week_offset)).isoformat(),
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z"
                }
            })
            allocation_id += 1
    
    data.extend(allocations)
    
    # 8. Sample Loans
    loans = [
        {
            "model": "budget_allocation.accountloan",
            "pk": 1,
            "fields": {
                "family": 1,
                "lender_account": 12,  # Emergency Fund
                "borrower_account": 17,  # Vacation Fund
                "original_amount": "1500.00",
                "remaining_amount": "900.00",
                "weekly_interest_rate": "0.0150",  # 1.5%
                "loan_date": (base_date - timedelta(weeks=6)).isoformat(),
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.accountloan",
            "pk": 2,
            "fields": {
                "family": 1,
                "lender_account": 13,  # Retirement
                "borrower_account": 14,  # House Down Payment
                "original_amount": "2000.00",
                "remaining_amount": "2000.00",
                "weekly_interest_rate": "0.0100",  # 1%
                "loan_date": base_date.isoformat(),
                "is_active": True,
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    ]
    data.extend(loans)
    
    # 9. Sample Loan Payments
    loan_payments = [
        {
            "model": "budget_allocation.loanpayment",
            "pk": 1,
            "fields": {
                "family": 1,
                "loan": 1,
                "week": 2,  # 3 weeks ago
                "amount": "200.00",
                "payment_date": (base_date - timedelta(weeks=3)).isoformat(),
                "notes": "Partial loan repayment",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        },
        {
            "model": "budget_allocation.loanpayment",
            "pk": 2,
            "fields": {
                "family": 1,
                "loan": 1,
                "week": 4,  # 1 week ago
                "amount": "400.00",
                "payment_date": (base_date - timedelta(weeks=1)).isoformat(),
                "notes": "Large payment toward vacation loan",
                "created_at": "2024-01-01T00:00:00Z",
                "updated_at": "2024-01-01T00:00:00Z"
            }
        }
    ]
    data.extend(loan_payments)
    
    return data


def save_fixtures():
    """Save sample data to JSON fixture file"""
    sample_data = create_sample_data()
    
    fixture_file = "budget_allocation/fixtures/sample_data.json"
    
    with open(fixture_file, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"Sample data saved to {fixture_file}")
    print(f"Total records: {len(sample_data)}")
    
    # Print summary
    model_counts = {}
    for item in sample_data:
        model = item['model']
        model_counts[model] = model_counts.get(model, 0) + 1
    
    print("\nRecord breakdown:")
    for model, count in sorted(model_counts.items()):
        print(f"  {model}: {count}")


if __name__ == "__main__":
    save_fixtures()
