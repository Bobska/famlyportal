// Budget Basic App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Budget Basic App Initialized');
    
    // Initialize mobile sidebar
    initializeMobileSidebar();
    
    // Initialize tooltips if Bootstrap tooltips are needed
    initializeTooltips();
    
    // Initialize add income form
    handleAddIncomeForm();
});

/**
 * Show coming soon modal
 */
function showComingSoonModal() {
    const modal = new bootstrap.Modal(document.getElementById('comingSoonModal'));
    modal.show();
}

/**
 * Show add income modal
 */
function showAddIncomeModal() {
    const modal = new bootstrap.Modal(document.getElementById('addIncomeModal'));
    
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('incomeDate').value = today;
    
    modal.show();
}

/**
 * Handle add income form submission
 */
function handleAddIncomeForm() {
    const form = document.getElementById('addIncomeForm');
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(form);
        const incomeData = {
            date: formData.get('date'),
            payee: formData.get('payee'),
            amount: formData.get('amount'),
            notes: formData.get('notes')
        };
        
        console.log('Income data:', incomeData);
        
        // For now, just show a success message and close modal
        alert('Income added successfully!\n\nDate: ' + incomeData.date + '\nPayee: ' + incomeData.payee + '\nAmount: $' + incomeData.amount);
        
        // Reset form and close modal
        form.reset();
        const modal = bootstrap.Modal.getInstance(document.getElementById('addIncomeModal'));
        modal.hide();
        
        // TODO: Send data to server when backend is implemented
    });
}

/**
 * Initialize mobile sidebar functionality
 */
function initializeMobileSidebar() {
    // Create mobile sidebar toggle button if it doesn't exist
    const navbar = document.querySelector('.budget-basic-nav .navbar-nav');
    if (navbar && window.innerWidth <= 768) {
        const toggleButton = document.createElement('li');
        toggleButton.className = 'nav-item d-lg-none';
        toggleButton.innerHTML = `
            <a class="nav-link" href="#" id="sidebarToggle">
                <i class="fas fa-bars me-1"></i>Menu
            </a>
        `;
        navbar.insertBefore(toggleButton, navbar.firstChild);
        
        // Add event listener for sidebar toggle
        document.getElementById('sidebarToggle').addEventListener('click', function(e) {
            e.preventDefault();
            toggleSidebar();
        });
    }
    
    // Close sidebar when clicking outside on mobile
    document.addEventListener('click', function(e) {
        if (window.innerWidth <= 768) {
            const sidebar = document.querySelector('.budget-basic-sidebar');
            const sidebarToggle = document.getElementById('sidebarToggle');
            
            if (sidebar && !sidebar.contains(e.target) && 
                sidebarToggle && !sidebarToggle.contains(e.target)) {
                closeSidebar();
            }
        }
    });
}

/**
 * Toggle sidebar visibility on mobile
 */
function toggleSidebar() {
    document.body.classList.toggle('sidebar-open');
}

/**
 * Close sidebar on mobile
 */
function closeSidebar() {
    document.body.classList.remove('sidebar-open');
}

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Format currency for display
 */
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

/**
 * Update budget summary in sidebar
 */
function updateBudgetSummary(income, expenses) {
    const incomeElement = document.querySelector('.budget-summary .budget-value');
    const expensesElement = document.querySelector('.budget-summary .budget-value:nth-child(2n)');
    const balanceElement = document.querySelector('.budget-summary .budget-value:last-child');
    
    if (incomeElement) {
        incomeElement.textContent = formatCurrency(income);
    }
    
    if (expensesElement) {
        expensesElement.textContent = formatCurrency(expenses);
    }
    
    if (balanceElement) {
        const balance = income - expenses;
        balanceElement.textContent = formatCurrency(balance);
        balanceElement.className = 'budget-value';
    }
}

/**
 * Show loading state for buttons
 */
function showButtonLoading(button) {
    const originalText = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin me-1"></i>Loading...';
    
    // Return function to restore button
    return function() {
        button.disabled = false;
        button.innerHTML = originalText;
    };
}

/**
 * Show success message
 */
function showSuccessMessage(message) {
    showMessage(message, 'success');
}

/**
 * Show error message
 */
function showErrorMessage(message) {
    showMessage(message, 'danger');
}

/**
 * Show message with Bootstrap alert
 */
function showMessage(message, type = 'info') {
    const alertContainer = document.querySelector('#main-content');
    if (alertContainer) {
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        alertContainer.insertBefore(alert, alertContainer.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

/**
 * Validate form inputs
 */
function validateForm(form) {
    let isValid = true;
    const requiredFields = form.querySelectorAll('[required]');
    
    requiredFields.forEach(field => {
        if (!field.value.trim()) {
            field.classList.add('is-invalid');
            isValid = false;
        } else {
            field.classList.remove('is-invalid');
        }
    });
    
    return isValid;
}

// Export functions for use in other scripts
window.BudgetBasic = {
    formatCurrency,
    updateBudgetSummary,
    showButtonLoading,
    showSuccessMessage,
    showErrorMessage,
    validateForm,
    toggleSidebar,
    closeSidebar
};