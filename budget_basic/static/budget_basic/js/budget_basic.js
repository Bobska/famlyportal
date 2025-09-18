// Budget Basic App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Budget Basic App Initialized');
    
    // Initialize mobile sidebar
    initializeMobileSidebar();
    
    // Initialize tooltips if Bootstrap tooltips are needed
    initializeTooltips();
    
    // Add fade-in animation to cards
    animateCards();
});

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
 * Add fade-in animation to cards
 */
function animateCards() {
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        setTimeout(() => {
            card.classList.add('fade-in');
        }, index * 100);
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
    const incomeElement = document.querySelector('.budget-summary .text-success');
    const expensesElement = document.querySelector('.budget-summary .text-danger');
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
        balanceElement.className = `budget-value ${balance >= 0 ? 'text-success' : 'text-danger'}`;
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
        alert.className = `alert alert-${type} alert-dismissible fade show`;
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