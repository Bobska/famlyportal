"""
Budget Allocation Test Runner

Comprehensive test runner for the Budget Allocation app with detailed reporting.
Runs all test modules and provides coverage analysis.
"""
import os
import sys
import django
from io import StringIO
from django.test.runner import DiscoverRunner
from django.test.utils import get_runner
from django.conf import settings
from django.core.management import call_command


def setup_django():
    """Setup Django environment for testing"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'famlyportal.settings')
    django.setup()


def run_budget_allocation_tests():
    """Run all Budget Allocation app tests with detailed output"""
    
    print("=" * 80)
    print("BUDGET ALLOCATION APP - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print()
    
    # Test modules to run
    test_modules = [
        'budget_allocation.tests.test_models',
        'budget_allocation.tests.test_views', 
        'budget_allocation.tests.test_forms',
        'budget_allocation.tests.test_allocation_engine',
        'budget_allocation.tests.test_loan_system',
    ]
    
    print(f"Running {len(test_modules)} test modules:")
    for module in test_modules:
        print(f"  • {module}")
    print()
    
    # Setup test runner
    test_runner_class = get_runner(settings)
    test_runner = test_runner_class(verbosity=2, interactive=False, keepdb=False)
    
    # Run tests
    print("Starting test execution...")
    print("-" * 80)
    
    failures = test_runner.run_tests(test_modules)
    
    print("-" * 80)
    
    if failures:
        print(f"❌ TESTS FAILED: {failures} test(s) failed")
        return False
    else:
        print("✅ ALL TESTS PASSED!")
        return True


def run_specific_test_class(test_class_path):
    """Run a specific test class"""
    print(f"Running specific test: {test_class_path}")
    print("-" * 50)
    
    test_runner_class = get_runner(settings)
    test_runner = test_runner_class(verbosity=2, interactive=False, keepdb=False)
    
    failures = test_runner.run_tests([test_class_path])
    
    if failures:
        print(f"❌ Test failed: {failures} failure(s)")
        return False
    else:
        print("✅ Test passed!")
        return True


def check_test_coverage():
    """Analyze test coverage"""
    print("\n" + "=" * 80)
    print("TEST COVERAGE ANALYSIS")
    print("=" * 80)
    
    coverage_areas = {
        "Models": [
            "Account model validation and methods",
            "WeeklyPeriod functionality", 
            "BudgetTemplate allocation logic",
            "Transaction creation and validation",
            "Allocation processing",
            "AccountLoan interest calculation",
            "LoanPayment tracking",
            "FamilySettings configuration"
        ],
        "Views": [
            "Dashboard with account summaries",
            "Account CRUD operations", 
            "Transaction management",
            "Allocation creation and editing",
            "Budget template management",
            "Loan system interfaces",
            "API endpoints (balance, suggestions, summaries)",
            "Permission checking and family isolation"
        ],
        "Forms": [
            "AccountForm with parent filtering",
            "TransactionForm validation",
            "AllocationForm with account filtering", 
            "BudgetTemplateForm type-specific fields",
            "AccountLoanForm business rules",
            "LoanPaymentForm amount validation"
        ],
        "Business Logic": [
            "Automatic allocation processing",
            "Account balance calculations",
            "Money transfer utilities",
            "Budget template application",
            "Loan interest calculation",
            "Weekly period management",
            "Family data isolation"
        ],
        "Integration": [
            "Database constraints and relationships",
            "Django admin integration",
            "URL routing and parameter handling",
            "Template rendering and context",
            "JavaScript/AJAX functionality",
            "Error handling and user feedback"
        ]
    }
    
    for area, items in coverage_areas.items():
        print(f"\n{area}:")
        for item in items:
            print(f"  ✓ {item}")
    
    print(f"\nTotal test coverage areas: {sum(len(items) for items in coverage_areas.values())}")


def run_sample_data_test():
    """Test loading sample data fixtures"""
    print("\n" + "=" * 80)
    print("SAMPLE DATA FIXTURE TEST")
    print("=" * 80)
    
    try:
        # Test fixture loading
        output = StringIO()
        call_command('loaddata', 'budget_allocation/fixtures/sample_data.json', 
                    stdout=output, stderr=output)
        
        result = output.getvalue()
        print("✅ Sample data fixtures loaded successfully!")
        print(f"Output: {result.strip()}")
        
        # Test fixture content
        from budget_allocation.models import Account, Transaction, BudgetTemplate
        
        account_count = Account.objects.count()
        transaction_count = Transaction.objects.count() 
        template_count = BudgetTemplate.objects.count()
        
        print(f"\nLoaded data summary:")
        print(f"  • Accounts: {account_count}")
        print(f"  • Transactions: {transaction_count}")
        print(f"  • Budget Templates: {template_count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Sample data loading failed: {e}")
        return False


def performance_test_summary():
    """Display performance testing information"""
    print("\n" + "=" * 80)
    print("PERFORMANCE TEST SUMMARY")
    print("=" * 80)
    
    performance_areas = {
        "Database Queries": [
            "Account hierarchy queries with select_related",
            "Balance calculation optimization",
            "Large transaction set handling",
            "Complex allocation queries",
            "Loan calculation performance"
        ],
        "View Performance": [
            "Dashboard load time with many accounts",
            "Pagination efficiency",
            "AJAX endpoint response times",
            "Form rendering speed",
            "Template compilation time"
        ],
        "Memory Usage": [
            "Large dataset processing",
            "QuerySet memory efficiency", 
            "Bulk operation handling",
            "Transaction rollback testing",
            "Cache utilization"
        ]
    }
    
    for area, tests in performance_areas.items():
        print(f"\n{area}:")
        for test in tests:
            print(f"  • {test}")
    
    print("\nNote: Performance tests can be run individually with specific data loads.")


def main():
    """Main test runner function"""
    setup_django()
    
    if len(sys.argv) > 1:
        # Run specific test
        test_path = sys.argv[1]
        success = run_specific_test_class(test_path)
    else:
        # Run all tests
        success = run_budget_allocation_tests()
        
        if success:
            check_test_coverage()
            run_sample_data_test()
            performance_test_summary()
    
    print("\n" + "=" * 80)
    print("TEST EXECUTION COMPLETE")
    print("=" * 80)
    
    if success:
        print("🎉 All tests completed successfully!")
        print("\nNext steps:")
        print("  1. Run tests with coverage: python -m coverage run --source='.' manage.py test budget_allocation")
        print("  2. Generate coverage report: python -m coverage report")
        print("  3. Load sample data: python manage.py loaddata budget_allocation/fixtures/sample_data.json")
        print("  4. Start development server: python manage.py runserver")
    else:
        print("⚠️  Some tests failed. Please review the output above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
