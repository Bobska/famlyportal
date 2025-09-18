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
 * Show success modal with a message
 */
function showSuccessModal(message) {
    document.getElementById('successMessage').textContent = message;
    const modal = new bootstrap.Modal(document.getElementById('successModal'));
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
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(form);
        
        // Validate required fields
        const date = formData.get('date');
        const payee = formData.get('payee');
        const amount = formData.get('amount');
        
        if (!date || !payee || !amount) {
            alert('Please fill in all required fields (Date, Payee, Amount)');
            return;
        }
        
        // Disable submit button to prevent double submission
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';
        
        // Send data to server
        fetch('/budget-basic/income/add/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Reset form and close modal first
                form.reset();
                const addIncomeModal = bootstrap.Modal.getInstance(document.getElementById('addIncomeModal'));
                addIncomeModal.hide();
                
                // Show success modal after add modal is closed
                setTimeout(() => {
                    showSuccessModal(data.message);
                    
                    // Reload the page to show the new income entry
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                }, 300);
                
            } else {
                // Show error message via alert (keep alerts for errors)
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while saving the income entry. Please try again.');
        })
        .finally(() => {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    });
}

/**
 * Get CSRF token from the page
 */
function getCsrfToken() {
    const token = document.querySelector('[name=csrfmiddlewaretoken]');
    if (token) {
        return token.value;
    }
    
    // Fallback: get from cookies
    const cookies = document.cookie.split(';');
    for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'csrftoken') {
            return value;
        }
    }
    return '';
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