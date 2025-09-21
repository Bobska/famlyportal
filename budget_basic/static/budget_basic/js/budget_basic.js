// Budget Basic App JavaScript

document.addEventListener('DOMContentLoaded', function() {
    console.log('Budget Basic App Initialized');
    
    // Initialize mobile sidebar
    initializeMobileSidebar();
    
    // Initialize tooltips if Bootstrap tooltips are needed
    initializeTooltips();
    
    // Initialize add income form
    handleAddIncomeForm();
    
    // Initialize edit income form
    handleEditIncomeForm();
    
    // Initialize delete income functionality
    handleDeleteIncomeForm();
    
    // Initialize amount formatting
    initializeAmountFormatting();
    
    // Initialize active row functionality
    initializeActiveRows();
    
    // Initialize transaction card interactions
    initializeTransactionCards();
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
 * Show edit income modal with data
 */
function showEditIncomeModal(incomeId) {
    // Fetch income data
    fetch(`/budget-basic/income/${incomeId}/get/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Populate form with existing data
                document.getElementById('editIncomeId').value = data.income.id;
                document.getElementById('editIncomeDate').value = data.income.date;
                document.getElementById('editIncomePayee').value = data.income.payee;
                document.getElementById('editIncomeAmount').value = addCommasToNumber(data.income.amount);
                document.getElementById('editIncomeNotes').value = data.income.notes;
                
                // Show modal
                const modal = new bootstrap.Modal(document.getElementById('editIncomeModal'));
                modal.show();
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while loading the income data. Please try again.');
        });
}

/**
 * Show delete income confirmation modal
 */
function showDeleteIncomeModal(incomeId, payee, amount) {
    // Set the income details in the modal
    document.getElementById('deleteIncomeId').value = incomeId;
    document.getElementById('deleteIncomeDetails').innerHTML = `
        <strong>Payee:</strong> ${payee}<br>
        <strong>Amount:</strong> $${amount}
    `;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('deleteIncomeModal'));
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
        
        // Remove commas from amount before validation and submission
        const amountInput = form.querySelector('[name="amount"]');
        const cleanAmount = removeCommasFromAmount(amountInput.value);
        formData.set('amount', cleanAmount);
        
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
 * Handle edit income form submission
 */
function handleEditIncomeForm() {
    const form = document.getElementById('editIncomeForm');
    if (!form) return;
    
    form.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Get form data
        const formData = new FormData(form);
        const incomeId = formData.get('income_id');
        
        // Remove commas from amount before validation and submission
        const amountInput = form.querySelector('[name="amount"]');
        const cleanAmount = removeCommasFromAmount(amountInput.value);
        formData.set('amount', cleanAmount);
        
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
        submitBtn.textContent = 'Updating...';
        
        // Send data to server
        fetch(`/budget-basic/income/${incomeId}/edit/`, {
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
                const editIncomeModal = bootstrap.Modal.getInstance(document.getElementById('editIncomeModal'));
                editIncomeModal.hide();
                
                // Show success modal after edit modal is closed
                setTimeout(() => {
                    showSuccessModal(data.message);
                    
                    // Reload the page to show the updated income entry
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
            alert('An error occurred while updating the income entry. Please try again.');
        })
        .finally(() => {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    });
}

/**
 * Handle delete income confirmation
 */
function handleDeleteIncomeForm() {
    const confirmBtn = document.getElementById('confirmDeleteBtn');
    if (!confirmBtn) return;
    
    confirmBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        const incomeId = document.getElementById('deleteIncomeId').value;
        if (!incomeId) {
            alert('No income entry selected for deletion');
            return;
        }
        
        // Disable button to prevent double clicks
        const originalText = confirmBtn.textContent;
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Deleting...';
        
        // Send delete request to server
        fetch(`/budget-basic/income/${incomeId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close delete modal first
                const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteIncomeModal'));
                deleteModal.hide();
                
                // Show success modal after delete modal is closed
                setTimeout(() => {
                    showSuccessModal(data.message);
                    
                    // Reload the page to show the updated list
                    setTimeout(() => {
                        window.location.reload();
                    }, 1500);
                }, 300);
                
            } else {
                // Show error message via alert
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the income entry. Please try again.');
        })
        .finally(() => {
            // Re-enable button
            confirmBtn.disabled = false;
            confirmBtn.textContent = originalText;
        });
    });
}

/**
 * Initialize amount field formatting
 */
function initializeAmountFormatting() {
    // Add formatting to amount inputs
    const amountInputs = document.querySelectorAll('#incomeAmount, #editIncomeAmount');
    
    amountInputs.forEach(input => {
        // Format on input (as user types)
        input.addEventListener('input', function(e) {
            formatAmountInput(e.target);
        });
        
        // Format on blur (when user leaves the field)
        input.addEventListener('blur', function(e) {
            formatAmountInput(e.target);
        });
        
        // Handle paste events
        input.addEventListener('paste', function(e) {
            setTimeout(() => formatAmountInput(e.target), 10);
        });
    });
}

/**
 * Format amount input with commas
 */
function formatAmountInput(input) {
    let value = input.value;
    
    // Remove all non-numeric characters except decimal point and commas
    value = value.replace(/[^\d.,]/g, '');
    
    // Remove existing commas before processing
    value = value.replace(/,/g, '');
    
    // Ensure only one decimal point
    const parts = value.split('.');
    if (parts.length > 2) {
        value = parts[0] + '.' + parts.slice(1).join('');
    }
    
    // Limit to 2 decimal places
    if (parts[1] && parts[1].length > 2) {
        value = parts[0] + '.' + parts[1].substring(0, 2);
    }
    
    // Add commas to the integer part
    if (value.includes('.')) {
        const [integerPart, decimalPart] = value.split('.');
        const formattedInteger = addCommasToNumber(integerPart);
        input.value = formattedInteger + '.' + decimalPart;
    } else {
        input.value = addCommasToNumber(value);
    }
}

/**
 * Add commas to a number string
 */
function addCommasToNumber(numberStr) {
    if (!numberStr) return '';
    return numberStr.replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Remove commas from amount for form submission
 */
function removeCommasFromAmount(amountStr) {
    return amountStr.replace(/,/g, '');
}

/**
 * Initialize active row functionality
 */
function initializeActiveRows() {
    // Add click event listeners to all table rows
    const tableRows = document.querySelectorAll('.table tbody tr');
    
    tableRows.forEach(row => {
        // Make rows clickable (add pointer cursor)
        row.style.cursor = 'pointer';
        
        // Add click event listener
        row.addEventListener('click', function(e) {
            // Don't activate row if clicking on action buttons
            if (e.target.closest('.btn') || e.target.closest('.btn-group')) {
                return;
            }
            
            // Remove active class from all rows
            tableRows.forEach(r => r.classList.remove('table-row-active'));
            
            // Add active class to clicked row
            this.classList.add('table-row-active');
            
            // Optional: Store the active row ID for later use
            const rowData = getRowData(this);
            if (rowData) {
                // You can use this data for other functionality
                console.log('Active row selected:', rowData);
            }
        });
        
        // Add double-click to edit functionality
        row.addEventListener('dblclick', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.btn') || e.target.closest('.btn-group')) {
                return;
            }
            
            // Get the income ID and trigger edit modal
            const editBtn = this.querySelector('[onclick*="showEditIncomeModal"]');
            if (editBtn) {
                const onclickAttr = editBtn.getAttribute('onclick');
                const incomeId = onclickAttr.match(/\d+/)?.[0];
                if (incomeId) {
                    showEditIncomeModal(parseInt(incomeId));
                }
            }
        });
    });
}

/**
 * Get data from a table row
 */
function getRowData(row) {
    const cells = row.querySelectorAll('td');
    if (cells.length >= 3) {
        return {
            date: cells[0].textContent.trim(),
            payee: cells[1].textContent.trim(),
            amount: cells[2].textContent.trim(),
            row: row
        };
    }
    return null;
}

/**
 * Clear active row selection
 */
function clearActiveRows() {
    const activeRows = document.querySelectorAll('.table-row-active');
    activeRows.forEach(row => row.classList.remove('table-row-active'));
}

/**
 * Initialize transaction card interactions
 */
function initializeTransactionCards() {
    // Add click event listeners to all transaction cards
    const transactionCards = document.querySelectorAll('.transaction-card-data');
    
    transactionCards.forEach(card => {
        // Add click event listener
        card.addEventListener('click', function(e) {
            // Don't activate card if clicking on action buttons
            if (e.target.closest('.btn') || e.target.closest('.btn-group')) {
                return;
            }
            
            // Remove active class from all cards
            transactionCards.forEach(c => c.classList.remove('active'));
            
            // Add active class to clicked card
            this.classList.add('active');
            
            // Optional: Store the active card ID for later use
            const cardData = getCardData(this);
            if (cardData) {
                console.log('Active card selected:', cardData);
            }
        });
        
        // Add double-click to edit functionality
        card.addEventListener('dblclick', function(e) {
            // Don't trigger if clicking on action buttons
            if (e.target.closest('.btn') || e.target.closest('.btn-group')) {
                return;
            }
            
            // Get the income ID and trigger edit modal
            const transactionId = this.dataset.transactionId;
            if (transactionId) {
                showEditIncomeModal(parseInt(transactionId));
            }
        });
    });
}

/**
 * Get data from a transaction card
 */
function getCardData(card) {
    const cols = card.querySelectorAll('.transaction-col');
    if (cols.length >= 3) {
        return {
            transactionId: card.dataset.transactionId,
            date: cols[0].textContent.trim(),
            payee: cols[1].textContent.trim(),
            amount: cols[2].textContent.trim(),
            card: card
        };
    }
    return null;
}

/**
 * Clear active card selection
 */
function clearActiveCards() {
    const activeCards = document.querySelectorAll('.transaction-card-data.active');
    activeCards.forEach(card => card.classList.remove('active'));
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