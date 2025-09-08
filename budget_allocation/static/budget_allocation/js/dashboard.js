/**
 * Budget Allocation Dashboard JavaScript
 * Enhanced functionality for account tree, modals, and interactive components
 */

// Global state
let accountData = {};
let currentWeek = {};

// Initialize dashboard when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeAccountTree();
    initializeModals();
    initializeQuickActions();
    setupEventListeners();
    loadAccountData();
});

/**
 * Account Tree Management
 */
function initializeAccountTree() {
    // Initialize account tree toggle functionality
    const toggleButtons = document.querySelectorAll('.toggle-account');
    
    toggleButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const accountId = this.dataset.accountId;
            toggleAccountChildren(accountId);
        });
    });
}

function toggleAccountChildren(accountId) {
    const childrenContainer = document.getElementById(`children-${accountId}`);
    const toggleButton = document.querySelector(`[data-account-id="${accountId}"]`);
    const icon = toggleButton.querySelector('i');
    
    if (childrenContainer) {
        if (childrenContainer.style.display === 'none') {
            childrenContainer.style.display = 'block';
            icon.classList.remove('fa-chevron-right');
            icon.classList.add('fa-chevron-down');
            toggleButton.classList.remove('collapsed');
        } else {
            childrenContainer.style.display = 'none';
            icon.classList.remove('fa-chevron-down');
            icon.classList.add('fa-chevron-right');
            toggleButton.classList.add('collapsed');
        }
    }
}

function expandAllAccounts() {
    const childrenContainers = document.querySelectorAll('.child-accounts');
    const toggleButtons = document.querySelectorAll('.toggle-account');
    
    childrenContainers.forEach(container => {
        container.style.display = 'block';
    });
    
    toggleButtons.forEach(button => {
        const icon = button.querySelector('i');
        icon.classList.remove('fa-chevron-right');
        icon.classList.add('fa-chevron-down');
        button.classList.remove('collapsed');
    });
}

function collapseAllAccounts() {
    const childrenContainers = document.querySelectorAll('.child-accounts');
    const toggleButtons = document.querySelectorAll('.toggle-account');
    
    childrenContainers.forEach(container => {
        container.style.display = 'none';
    });
    
    toggleButtons.forEach(button => {
        const icon = button.querySelector('i');
        icon.classList.remove('fa-chevron-down');
        icon.classList.add('fa-chevron-right');
        button.classList.add('collapsed');
    });
}

/**
 * Modal Management
 */
function initializeModals() {
    // Initialize Bootstrap modals
    const modalElements = document.querySelectorAll('.modal');
    modalElements.forEach(modalEl => {
        new bootstrap.Modal(modalEl);
    });
    
    // Setup modal form submissions
    setupModalForms();
}

function setupModalForms() {
    // Record Income Modal
    const incomeForm = document.getElementById('recordIncomeForm');
    if (incomeForm) {
        incomeForm.addEventListener('submit', handleIncomeSubmission);
    }
    
    // Record Expense Modal
    const expenseForm = document.getElementById('recordExpenseForm');
    if (expenseForm) {
        expenseForm.addEventListener('submit', handleExpenseSubmission);
    }
    
    // Allocate Money Modal
    const allocateForm = document.getElementById('allocateMoneyForm');
    if (allocateForm) {
        allocateForm.addEventListener('submit', handleAllocationSubmission);
    }
}

async function handleIncomeSubmission(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const submitBtn = this.querySelector('button[type="submit"]');
    
    try {
        setLoadingState(submitBtn, true);
        
        const response = await fetch('/budget_allocation/transactions/create/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (response.ok) {
            const result = await response.json();
            showNotification('Income recorded successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('recordIncomeModal')).hide();
            this.reset();
            await refreshDashboardData();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Error recording income', 'error');
        }
    } catch (error) {
        showNotification('Network error occurred', 'error');
    } finally {
        setLoadingState(submitBtn, false);
    }
}

async function handleExpenseSubmission(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const submitBtn = this.querySelector('button[type="submit"]');
    
    try {
        setLoadingState(submitBtn, true);
        
        const response = await fetch('/budget_allocation/transactions/create/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (response.ok) {
            showNotification('Expense recorded successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('recordExpenseModal')).hide();
            this.reset();
            await refreshDashboardData();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Error recording expense', 'error');
        }
    } catch (error) {
        showNotification('Network error occurred', 'error');
    } finally {
        setLoadingState(submitBtn, false);
    }
}

async function handleAllocationSubmission(e) {
    e.preventDefault();
    const formData = new FormData(this);
    const submitBtn = this.querySelector('button[type="submit"]');
    
    try {
        setLoadingState(submitBtn, true);
        
        const response = await fetch('/budget_allocation/allocations/create/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (response.ok) {
            showNotification('Money allocated successfully!', 'success');
            bootstrap.Modal.getInstance(document.getElementById('allocateMoneyModal')).hide();
            this.reset();
            await refreshDashboardData();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Error allocating money', 'error');
        }
    } catch (error) {
        showNotification('Network error occurred', 'error');
    } finally {
        setLoadingState(submitBtn, false);
    }
}

/**
 * Quick Actions
 */
function initializeQuickActions() {
    // Setup quick action buttons
    const quickActionBtns = document.querySelectorAll('.quick-action-btn');
    quickActionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.dataset.action;
            handleQuickAction(action);
        });
    });
}

function handleQuickAction(action) {
    switch (action) {
        case 'record_income':
            showModal('recordIncomeModal');
            break;
        case 'record_expense':
            showModal('recordExpenseModal');
            break;
        case 'allocate_money':
            showModal('allocateMoneyModal');
            break;
        default:
            console.warn(`Unknown quick action: ${action}`);
    }
}

function showModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        bootstrap.Modal.getInstance(modal) || new bootstrap.Modal(modal);
        bootstrap.Modal.getInstance(modal).show();
    }
}

/**
 * Template and Loan Quick Actions
 */
async function applyTemplate(templateId) {
    const confirmMsg = 'Apply this budget template? This will create allocations based on the template.';
    if (!confirm(confirmMsg)) return;
    
    try {
        const response = await fetch(`/budget_allocation/templates/${templateId}/apply/`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (response.ok) {
            showNotification('Template applied successfully!', 'success');
            await refreshDashboardData();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Error applying template', 'error');
        }
    } catch (error) {
        showNotification('Network error occurred', 'error');
    }
}

async function quickRepayLoan(loanId) {
    const amount = prompt('Enter repayment amount:');
    if (!amount || isNaN(amount) || parseFloat(amount) <= 0) {
        showNotification('Please enter a valid amount', 'error');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('amount', amount);
        
        const response = await fetch(`/budget_allocation/loans/${loanId}/repay/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': getCsrfToken()
            }
        });
        
        if (response.ok) {
            showNotification('Loan payment recorded successfully!', 'success');
            await refreshDashboardData();
        } else {
            const error = await response.json();
            showNotification(error.message || 'Error processing payment', 'error');
        }
    } catch (error) {
        showNotification('Network error occurred', 'error');
    }
}

/**
 * Data Management
 */
async function loadAccountData() {
    try {
        const response = await fetch('/budget-allocation/api/accounts/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            accountData = await response.json();
            updateAccountBalances();
        }
    } catch (error) {
        console.error('Error loading account data:', error);
    }
}

function updateAccountBalances() {
    const balanceElements = document.querySelectorAll('.balance-amount');
    balanceElements.forEach(element => {
        const accountId = element.dataset.accountId;
        if (accountData[accountId]) {
            element.textContent = `$${accountData[accountId].balance.toFixed(2)}`;
        }
    });
}

async function refreshDashboardData() {
    try {
        // Refresh account balances
        await loadAccountData();
        
        // Optionally refresh entire dashboard content
        const response = await fetch(window.location.href, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const html = await response.text();
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            
            // Update specific sections
            updateSection('.week-summary-card', doc);
            updateSection('.account-overview-card', doc);
            updateSection('.transaction-list', doc);
        }
    } catch (error) {
        console.error('Error refreshing dashboard:', error);
    }
}

function updateSection(selector, sourceDoc) {
    const currentSection = document.querySelector(selector);
    const newSection = sourceDoc.querySelector(selector);
    
    if (currentSection && newSection) {
        currentSection.innerHTML = newSection.innerHTML;
    }
}

/**
 * Event Listeners
 */
function setupEventListeners() {
    // Real-time balance updates
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('account-link')) {
            // Add visual feedback for account clicks
            e.target.closest('.account-item').classList.add('fade-in');
        }
    });
    
    // Form validation
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!validateForm(this)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    const requiredFields = form.querySelectorAll('[required]');
    let isValid = true;
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            showFieldError(field, 'This field is required');
            isValid = false;
        } else {
            clearFieldError(field);
        }
    });
    
    return isValid;
}

function showFieldError(field, message) {
    clearFieldError(field);
    field.classList.add('is-invalid');
    
    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

function clearFieldError(field) {
    field.classList.remove('is-invalid');
    const errorDiv = field.parentNode.querySelector('.invalid-feedback');
    if (errorDiv) {
        errorDiv.remove();
    }
}

/**
 * Utility Functions
 */
function setLoadingState(element, isLoading) {
    if (isLoading) {
        element.disabled = true;
        element.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Processing...';
        element.classList.add('loading');
    } else {
        element.disabled = false;
        element.innerHTML = element.dataset.originalText || 'Submit';
        element.classList.remove('loading');
    }
}

function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show position-fixed`;
    notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
    
    notification.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    return token ? token.value : '';
}

/**
 * Animation Helpers
 */
function animateStatChange(element, newValue) {
    element.style.transform = 'scale(1.1)';
    element.style.transition = 'transform 0.2s ease';
    
    setTimeout(() => {
        element.textContent = newValue;
        element.style.transform = 'scale(1)';
    }, 100);
}

// Export functions for global access
window.BudgetAllocation = {
    expandAllAccounts,
    collapseAllAccounts,
    applyTemplate,
    quickRepayLoan,
    refreshDashboardData
};
