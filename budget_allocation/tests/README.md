# Budget Allocation App - Testing Documentation

## Overview

The Budget Allocation app includes a comprehensive testing suite with over 3,000 lines of test code covering all major functionality areas. This document provides guidance on running tests, understanding test coverage, and working with sample data.

## Test Structure

### Test Modules

| Module | Purpose | Lines | Coverage |
|--------|---------|-------|----------|
| `test_models.py` | Model logic, relationships, validation | 1,000+ | Account hierarchy, calculations, constraints |
| `test_views.py` | View functionality, permissions, HTTP responses | 700+ | CRUD operations, API endpoints, security |
| `test_forms.py` | Form validation, widgets, data processing | 800+ | All forms with family filtering and validation |
| `test_allocation_engine.py` | Auto-allocation logic, utility functions | 530+ | Budget processing, money transfers |
| `test_loan_system.py` | Loan management, interest calculation | 800+ | Loan creation, payments, validation |

**Total: 3,800+ lines of comprehensive test coverage**

### Test Categories

#### 1. Model Tests (`test_models.py`)
- **Account Model**: Hierarchy validation, balance calculations, type constraints
- **WeeklyPeriod**: Date management, current week detection, family isolation
- **Transaction**: Amount validation, type checking, account relationships
- **BudgetTemplate**: Allocation type logic, priority handling, template processing
- **Allocation**: Transfer validation, processing status, amount calculations
- **Family Isolation**: Ensuring data separation between families

#### 2. View Tests (`test_views.py`)
- **Dashboard**: Account summaries, balance display, navigation
- **CRUD Operations**: Create, read, update, delete for all entities
- **API Endpoints**: JSON responses, real-time balance updates
- **Permissions**: Family membership checking, role-based access
- **Pagination**: Large dataset handling, page navigation
- **Error Handling**: Invalid data, missing resources, permission denied

#### 3. Form Tests (`test_forms.py`)
- **AccountForm**: Parent account filtering, validation rules
- **TransactionForm**: Amount validation, account selection
- **AllocationForm**: Account filtering, transfer validation
- **BudgetTemplateForm**: Type-specific field handling, priority validation
- **LoanForms**: Business rule enforcement, amount constraints
- **Widget Testing**: Form rendering, field attributes

#### 4. Allocation Engine Tests (`test_allocation_engine.py`)
- **Template Processing**: Automatic allocation based on templates
- **Utility Functions**: Money transfers, balance calculations
- **Constraint Handling**: Insufficient funds, allocation limits
- **Weekly Processing**: Automated allocation runs
- **Error Conditions**: Invalid transfers, missing accounts

#### 5. Loan System Tests (`test_loan_system.py`)
- **Loan Creation**: Validation, interest rate handling
- **Payment Processing**: Amount validation, balance updates
- **Interest Calculation**: Weekly compounding, precision handling
- **Business Logic**: Loan limits, repayment constraints
- **Integration**: Transaction system integration

## Running Tests

### All Tests
```bash
# Run complete test suite
python budget_allocation/tests/run_tests.py

# Django standard test runner
python manage.py test budget_allocation

# With verbose output
python manage.py test budget_allocation --verbosity=2
```

### Specific Test Modules
```bash
# Model tests only
python manage.py test budget_allocation.tests.test_models

# View tests only  
python manage.py test budget_allocation.tests.test_views

# Form tests only
python manage.py test budget_allocation.tests.test_forms

# Allocation engine tests
python manage.py test budget_allocation.tests.test_allocation_engine

# Loan system tests
python manage.py test budget_allocation.tests.test_loan_system
```

### Specific Test Classes
```bash
# Account model tests
python manage.py test budget_allocation.tests.test_models.AccountModelTests

# Dashboard view tests
python manage.py test budget_allocation.tests.test_views.DashboardViewTests

# Budget template form tests
python manage.py test budget_allocation.tests.test_forms.BudgetTemplateFormTests
```

### With Coverage Analysis
```bash
# Install coverage
pip install coverage

# Run tests with coverage
python -m coverage run --source='.' manage.py test budget_allocation

# Generate coverage report
python -m coverage report

# Generate HTML coverage report
python -m coverage html
```

## Sample Data

### Sample Data Generator

The `sample_data_generator.py` script creates comprehensive sample data for development and testing:

```bash
# Generate sample data fixture
python budget_allocation/fixtures/sample_data_generator.py
```

### Sample Data Contents

**Family Structure:**
- Johnson Family with 2 users (John & Sarah)
- Admin and Parent roles
- Family settings with 2% default interest rate

**Account Hierarchy:**
- 20 accounts in hierarchical structure
- Income accounts (salaries, side projects)
- Essential expenses (housing, groceries, transportation)
- Savings categories (emergency, retirement, house fund)
- Lifestyle spending (dining, vacation, hobbies)
- Debt payment accounts

**Financial Data:**
- 7 weekly periods (4 historical + current + 2 future)
- 44 realistic transactions across 5 weeks
- Income patterns: bi-weekly salary + weekly teaching
- Regular expense patterns following budget templates
- 35 automatic allocations based on templates

**Budget Templates:**
- 7 budget templates covering all allocation types
- Fixed amounts for essential expenses
- Percentage-based savings (10% emergency, 15% retirement)
- Range-based flexible spending
- Priority-based allocation ordering

**Loan Examples:**
- Inter-account loans with interest
- Payment history tracking
- Active and completed loan examples

### Loading Sample Data

```bash
# Load sample data into database
python manage.py loaddata budget_allocation/fixtures/sample_data.json

# Verify data loading
python manage.py shell
>>> from budget_allocation.models import Account, Transaction
>>> print(f"Accounts: {Account.objects.count()}")
>>> print(f"Transactions: {Transaction.objects.count()}")
```

## Test Development Guidelines

### Writing New Tests

1. **Follow Naming Conventions:**
   ```python
   class NewFeatureModelTests(TestCase):
       def test_specific_functionality(self):
           """Test description"""
   ```

2. **Use Base Test Classes:**
   ```python
   class MyTestCase(BudgetAllocationTestCase):
       """Inherits family setup and common utilities"""
   ```

3. **Test Family Isolation:**
   ```python
   def test_family_data_isolation(self):
       # Create second family
       other_family = Family.objects.create(name='Other Family')
       # Verify no cross-family data access
   ```

4. **Test Error Conditions:**
   ```python
   def test_invalid_input_handling(self):
       with self.assertRaises(ValidationError):
           # Test invalid data
   ```

### Test Data Best Practices

1. **Use Realistic Data:**
   ```python
   # Good: Realistic account names and amounts
   account = Account.objects.create(
       name="Emergency Fund",
       account_type="spending"
   )
   
   # Avoid: Generic test data
   account = Account.objects.create(
       name="Test Account 1",
       account_type="spending"
   )
   ```

2. **Test Edge Cases:**
   ```python
   # Test boundary conditions
   def test_zero_amount_transaction(self):
   def test_maximum_amount_handling(self):
   def test_negative_balance_scenarios(self):
   ```

3. **Verify Relationships:**
   ```python
   def test_cascade_deletion(self):
       # Test that related objects are properly handled
   ```

## Performance Testing

### Database Query Optimization

Tests include verification of:
- `select_related()` usage for foreign keys
- `prefetch_related()` for reverse relationships
- Efficient pagination queries
- Bulk operations for large datasets

### Memory Usage Testing

```python
def test_large_dataset_handling(self):
    """Test memory efficiency with large datasets"""
    # Create large number of transactions
    # Verify memory usage stays reasonable
```

### Response Time Testing

```python
def test_dashboard_load_time(self):
    """Test dashboard performance with many accounts"""
    # Measure response time
    # Verify under acceptable threshold
```

## Continuous Integration

### Test Automation

The test suite is designed for CI/CD integration:

```yaml
# Example GitHub Actions workflow
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python manage.py test budget_allocation
```

### Quality Gates

Tests enforce:
- ✅ 100% test pass rate required
- ✅ No database constraint violations
- ✅ Proper error handling for all edge cases
- ✅ Family data isolation maintained
- ✅ Performance benchmarks met

## Troubleshooting

### Common Test Issues

1. **Family Isolation Failures:**
   ```python
   # Ensure proper family setup in setUp()
   def setUp(self):
       self.family = Family.objects.create(name='Test Family')
       # Set up family member relationship
   ```

2. **Database State Issues:**
   ```bash
   # Reset test database
   python manage.py flush --settings=famlyportal.test_settings
   ```

3. **Migration Issues:**
   ```bash
   # Ensure migrations are applied
   python manage.py migrate --settings=famlyportal.test_settings
   ```

### Debug Mode Testing

```python
# Enable debug output in tests
import logging
logging.basicConfig(level=logging.DEBUG)

# Use Django's override_settings for test-specific configuration
from django.test import override_settings

@override_settings(DEBUG=True)
def test_with_debug(self):
    # Test with debug information
```

## Test Maintenance

### Regular Maintenance Tasks

1. **Update Tests for New Features:**
   - Add tests for new models, views, forms
   - Update sample data for new scenarios
   - Extend coverage for edge cases

2. **Performance Regression Testing:**
   - Monitor test execution time
   - Profile database queries
   - Update performance benchmarks

3. **Dependency Updates:**
   - Test compatibility with Django updates
   - Verify third-party library compatibility
   - Update test dependencies

### Test Coverage Goals

- **Models:** 100% line coverage, all validation paths
- **Views:** 95%+ coverage, all HTTP methods and error conditions
- **Forms:** 100% validation coverage, all field types
- **Utilities:** 100% function coverage, all code paths
- **Integration:** All user workflows, error scenarios

## Next Steps

After running tests successfully:

1. **Development:** Use sample data for feature development
2. **Deployment:** Run full test suite before releases
3. **Monitoring:** Set up test alerts for CI/CD
4. **Documentation:** Keep test documentation updated

The comprehensive test suite ensures the Budget Allocation app maintains high quality and reliability across all functionality areas.
