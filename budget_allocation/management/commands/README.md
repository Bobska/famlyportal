# Budget Allocation Management Commands

This document explains the Django management commands available for budget allocation setup and data migration.

## Commands Overview

### 1. setup_budget_allocation
Sets up budget allocation for existing families and handles data migration.

### 2. migrate_household_budget  
Migrates data from household_budget app to budget_allocation.

### 3. budget_account_utils
Utility commands for account management, validation, and maintenance.

## Command Usage

### Setup Budget Allocation

```bash
# Setup budget allocation for all families
python manage.py setup_budget_allocation

# Setup for specific family
python manage.py setup_budget_allocation --family-id 1

# Setup with data migration from household_budget
python manage.py setup_budget_allocation --migrate-data

# Force setup even if accounts already exist
python manage.py setup_budget_allocation --force

# Combine options
python manage.py setup_budget_allocation --family-id 1 --force --migrate-data
```

**Features:**
- ✅ Creates default Income and Expenses accounts for families
- ✅ Handles existing account detection
- ✅ Migrates categories from household_budget app (if available)
- ✅ Transaction-safe operations
- ✅ Detailed logging and error reporting

### Migrate Household Budget Data

```bash
# Dry run to see what would be migrated
python manage.py migrate_household_budget --dry-run

# Migrate specific family with verbose output
python manage.py migrate_household_budget --family-id 1 --verbose

# Migrate all families
python manage.py migrate_household_budget
```

**Features:**
- ✅ Safe dry-run mode for testing
- ✅ Migrates categories to accounts with proper hierarchy
- ✅ Preserves category descriptions and active status
- ✅ Assigns appropriate colors to migrated accounts
- ✅ Shows transaction and budget counts (migration coming soon)

### Account Management Utilities

```bash
# List all accounts
python manage.py budget_account_utils list

# List accounts in tree format
python manage.py budget_account_utils list --show-tree

# List accounts for specific family
python manage.py budget_account_utils list --family-id 1 --show-tree

# Validate account data integrity
python manage.py budget_account_utils validate

# Validate and fix issues
python manage.py budget_account_utils validate --fix

# Clean up orphaned accounts (dry run)
python manage.py budget_account_utils clean --dry-run

# Clean up accounts for specific family
python manage.py budget_account_utils clean --family-id 1

# Reset all accounts for a family (DESTRUCTIVE)
python manage.py budget_account_utils reset --family-id 1 --confirm
```

**Features:**
- ✅ Tree-view display of account hierarchies
- ✅ Data integrity validation
- ✅ Automatic issue detection and fixing
- ✅ Safe cleanup of orphaned data
- ✅ Account reset functionality with confirmation
- ✅ Circular reference detection

## Validation Checks

The `validate` action checks for:

1. **Orphaned Accounts** - Accounts without families
2. **Invalid Root Accounts** - Root accounts that shouldn't have parents
3. **Missing Default Accounts** - Families without Income/Expenses accounts
4. **Circular References** - Parent-child relationship loops
5. **Type Mismatches** - Child accounts with different types than parents

## Migration Features

### From household_budget App

When migrating from household_budget, the command:

1. **Maps Categories to Accounts**
   - Income categories → Child accounts under Income
   - Expense categories → Child accounts under Expenses
   - Preserves descriptions and active status

2. **Assigns Colors**
   - Expense accounts: Red spectrum colors
   - Income accounts: Green spectrum colors
   - Rotates through color palette for variety

3. **Shows Migration Preview**
   - Dry-run mode shows what would be migrated
   - Verbose mode provides detailed information
   - Transaction and budget counts (not migrated yet)

## Error Handling

All commands include:
- ✅ Transaction safety (atomic operations)
- ✅ Graceful error handling
- ✅ Detailed error messages
- ✅ Rollback on failures
- ✅ Progress reporting

## Examples

### Initial Setup for New Family

```bash
# Create accounts for family ID 1
python manage.py setup_budget_allocation --family-id 1
```

### Data Migration Workflow

```bash
# 1. Check what would be migrated
python manage.py migrate_household_budget --dry-run --verbose

# 2. Validate current state
python manage.py budget_account_utils validate

# 3. Fix any issues
python manage.py budget_account_utils validate --fix

# 4. Perform migration
python manage.py migrate_household_budget

# 5. Verify results
python manage.py budget_account_utils list --show-tree
```

### Maintenance and Cleanup

```bash
# Regular validation
python manage.py budget_account_utils validate --fix

# Check for cleanup needs
python manage.py budget_account_utils clean --dry-run

# Clean up if needed
python manage.py budget_account_utils clean
```

### Emergency Reset

```bash
# Reset accounts for family (DESTRUCTIVE - use with caution)
python manage.py budget_account_utils reset --family-id 1 --confirm
```

## Output Examples

### Tree View Output
```
🏠 Green Family (5 accounts)
  📊 Income (income)
    └── Salary
    └── Freelance Work
  📊 Expenses (expense)
    └── Housing
        └── Rent
        └── Utilities
    └── Food
```

### Validation Output
```
🔍 Validating Account Data Integrity

🏠 Validating Green Family
  ❌ 2 root accounts with parents
    ✓ Fixed root account parents
  ✅ Green Family is valid
```

### Migration Preview
```
🔄 Starting Household Budget Migration...
🧪 DRY RUN MODE - No changes will be made

📊 Processing Green Family...
  Found 5 categories, 120 transactions, 12 budgets
  🔍 Migration preview for Green Family:
    💰 Income categories (2):
      - Salary: Monthly salary income
      - Freelance: Freelance project income
    💸 Expense categories (3):
      - Housing: Rent and utilities
      - Food: Groceries and dining
      - Transportation: Car and public transport
```

## Implementation Notes

- **Thread Safety**: All operations use Django transactions
- **Performance**: Efficient queries with proper indexing
- **Logging**: Comprehensive logging for debugging
- **Error Recovery**: Graceful handling of edge cases
- **Extensibility**: Easy to add new validation rules
- **Compatibility**: Works with existing Django admin and models
