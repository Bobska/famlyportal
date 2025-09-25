// Budget Basic App JavaScript

// Global variable to track current filter state (resets on page reload)
let currentFilterType = 'all';
let currentTransactionSearch = '';

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
    
    // Initialize add expense form
    handleAddExpenseForm();
    
    // Initialize edit expense form
    handleEditExpenseForm();
    
    // Initialize delete expense functionality
    handleDeleteExpenseForm();
    
    // Initialize amount formatting
    initializeAmountFormatting();
    
    // Initialize active row functionality
    initializeActiveRows();
    
    // Initialize payee functionality
    initializePayeeFunctionality();
    
    // Initialize panel resizer functionality
    initializePanelResizer();
    
    // Initialize transaction selection system
    initializeTransactionSelection();
    
    // Initialize panel visibility mode
    setPanelVisibilityMode(PANEL_CONFIG.emptyPanelMode);
    
    // Initialize action button states (hidden by default)
    hideActionButtons();
    
    // Initialize filter with default state (only on pages with transactions)
    setTimeout(() => {
        const transactionContainer = document.querySelector('.transaction-cards-container') || document.querySelector('.payee-list-panel');
        if (transactionContainer) {
            filterTransactions('all'); // Set default filter to 'all' and highlight it
        }
    }, 100); // Small delay to ensure DOM is fully rendered
    
    // Note: Transaction card interactions now handled by week_navigation.js
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
                // Load payees first, then populate form
                loadPayeesForModal('editIncomePayeeSelect').then(() => {
                    // Populate form with existing data
                    document.getElementById('editIncomeId').value = data.income.id;
                    document.getElementById('editIncomeDate').value = data.income.date;
                    document.getElementById('editIncomeAmount').value = addCommasToNumber(data.income.amount);
                    document.getElementById('editIncomeNotes').value = data.income.notes;
                    
                    // Handle payee selection - only use dropdown since there's no text input
                    const editIncomeSelect = document.getElementById('editIncomePayeeSelect');
                    if (editIncomeSelect) {
                        // Check if payee exists in dropdown options
                        const payeeExists = Array.from(editIncomeSelect.options).some(option => option.value === data.income.payee);
                        
                        if (payeeExists) {
                            // Payee exists in dropdown - select it
                            editIncomeSelect.value = data.income.payee;
                        } else {
                            // Payee doesn't exist - clear selection
                            editIncomeSelect.value = '';
                            console.warn('Payee not found in dropdown:', data.income.payee);
                        }
                    }
                    
                    // Show modal
                    const modal = new bootstrap.Modal(document.getElementById('editIncomeModal'));
                    modal.show();
                });
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
    
    // Reset form fields
    const incomeForm = document.getElementById('addIncomeForm');
    incomeForm.reset();
    
    // Reset payee field states
    const incomeSelect = document.getElementById('incomePayeeSelect');
    const incomeInput = document.getElementById('incomePayee');
    if (incomeSelect) incomeSelect.value = '';
    if (incomeInput) {
        incomeInput.value = '';
        incomeInput.removeAttribute('readonly');
        incomeInput.classList.remove('bg-light');
    }
    
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
        const payee_choice = formData.get('payee_choice');
        const amount = formData.get('amount');
        
        if (!date || !payee_choice || !amount) {
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
                
                // Navigate to the week containing the new transaction and highlight it
                navigateToTransactionWeek(data.date, data.income_id, 'income');
                
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
        const payee_choice = formData.get('payee_choice');
        const amount = formData.get('amount');
        
        if (!date || !payee_choice || !amount) {
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
                
                // Navigate to transaction week with highlighting
                navigateToTransactionWeek(data.date, data.income_id, 'income');
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
                
                // Reload current week data instead of full page reload
                const currentOffset = window.currentWeekOffset || 0;
                if (typeof loadWeekData === 'function') {
                    loadWeekData(currentOffset);
                } else {
                    window.location.reload();
                }
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

// ===== EXPENSE FUNCTIONS =====

/**
 * Show add expense modal
 */
function showAddExpenseModal() {
    const modal = new bootstrap.Modal(document.getElementById('addExpenseModal'));
    
    // Reset form fields
    const expenseForm = document.getElementById('addExpenseForm');
    expenseForm.reset();
    
    // Reset payee field states
    const expenseSelect = document.getElementById('expensePayeeSelect');
    const expenseInput = document.getElementById('expensePayee');
    if (expenseSelect) expenseSelect.value = '';
    if (expenseInput) {
        expenseInput.value = '';
        expenseInput.removeAttribute('readonly');
        expenseInput.classList.remove('bg-light');
    }
    
    // Set today's date as default
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('expenseDate').value = today;
    
    modal.show();
}

/**
 * Show edit expense modal with data
 */
function showEditExpenseModal(expenseId) {
    // Fetch expense data
    fetch(`/budget-basic/expense/${expenseId}/get/`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Load payees first, then populate form
                loadPayeesForModal('editExpensePayeeSelect').then(() => {
                    // Populate form with existing data
                    document.getElementById('editExpenseId').value = data.expense.id;
                    document.getElementById('editExpenseDate').value = data.expense.date;
                    document.getElementById('editExpenseAmount').value = addCommasToNumber(data.expense.amount);
                    document.getElementById('editExpenseNotes').value = data.expense.notes;
                    
                    // Handle payee selection - only use dropdown since there's no text input
                    const editExpenseSelect = document.getElementById('editExpensePayeeSelect');
                    if (editExpenseSelect) {
                        // Check if payee exists in dropdown options
                        const payeeExists = Array.from(editExpenseSelect.options).some(option => option.value === data.expense.payee);
                        
                        if (payeeExists) {
                            // Payee exists in dropdown - select it
                            editExpenseSelect.value = data.expense.payee;
                        } else {
                            // Payee doesn't exist - clear selection
                            editExpenseSelect.value = '';
                            console.warn('Payee not found in dropdown:', data.expense.payee);
                        }
                    }
                    
                    // Show modal
                    const modal = new bootstrap.Modal(document.getElementById('editExpenseModal'));
                    modal.show();
                });
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while loading the expense data. Please try again.');
        });
}

/**
 * Show delete expense confirmation modal
 */
function showDeleteExpenseModal(expenseId, payee, amount) {
    // Set the expense details in the modal
    document.getElementById('deleteExpenseId').value = expenseId;
    document.getElementById('deleteExpenseDetails').innerHTML = `
        <strong>Payee:</strong> ${payee}<br>
        <strong>Amount:</strong> $${amount}
    `;
    
    // Show the modal
    const modal = new bootstrap.Modal(document.getElementById('deleteExpenseModal'));
    modal.show();
}

/**
 * Handle add expense form submission
 */
function handleAddExpenseForm() {
    const form = document.getElementById('addExpenseForm');
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
        const payee_choice = formData.get('payee_choice');
        const amount = formData.get('amount');
        
        if (!date || !payee_choice || !amount) {
            alert('Please fill in all required fields (Date, Payee, Amount)');
            return;
        }
        
        // Disable submit button to prevent double submission
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Saving...';
        
        // Send data to server
        fetch('/budget-basic/expense/add/', {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close add modal first
                const addModal = bootstrap.Modal.getInstance(document.getElementById('addExpenseModal'));
                addModal.hide();
                
                // Clear form
                form.reset();
                
                // Navigate to the week containing the new transaction and highlight it
                navigateToTransactionWeek(data.date, data.expense_id, 'expense');
            } else {
                // Show error message via alert
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while adding the expense. Please try again.');
        })
        .finally(() => {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    });
}

/**
 * Handle edit expense form submission
 */
function handleEditExpenseForm() {
    const form = document.getElementById('editExpenseForm');
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
        const payee_choice = formData.get('payee_choice');
        const amount = formData.get('amount');
        
        if (!date || !payee_choice || !amount) {
            alert('Please fill in all required fields (Date, Payee, Amount)');
            return;
        }
        
        // Get expense ID
        const expenseId = document.getElementById('editExpenseId').value;
        
        // Disable submit button to prevent double submission
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Updating...';
        
        // Send data to server
        fetch(`/budget-basic/expense/${expenseId}/edit/`, {
            method: 'POST',
            body: formData,
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close edit modal first
                const editModal = bootstrap.Modal.getInstance(document.getElementById('editExpenseModal'));
                editModal.hide();
                
                // Navigate to transaction week with highlighting
                navigateToTransactionWeek(data.date, data.expense_id, 'expense');
            } else {
                // Show error message via alert
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while updating the expense. Please try again.');
        })
        .finally(() => {
            // Re-enable submit button
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        });
    });
}

/**
 * Handle delete expense confirmation
 */
function handleDeleteExpenseForm() {
    const confirmBtn = document.getElementById('confirmDeleteExpenseBtn');
    if (!confirmBtn) return;
    
    confirmBtn.addEventListener('click', function(e) {
        e.preventDefault();
        
        const expenseId = document.getElementById('deleteExpenseId').value;
        if (!expenseId) {
            alert('No expense entry selected for deletion');
            return;
        }
        
        // Disable button to prevent double clicks
        const originalText = confirmBtn.textContent;
        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Deleting...';
        
        // Send delete request to server
        fetch(`/budget-basic/expense/${expenseId}/delete/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken()
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Close delete modal first
                const deleteModal = bootstrap.Modal.getInstance(document.getElementById('deleteExpenseModal'));
                deleteModal.hide();
                
                // Reload current week data instead of full page reload
                const currentOffset = window.currentWeekOffset || 0;
                if (typeof loadWeekData === 'function') {
                    loadWeekData(currentOffset);
                } else {
                    window.location.reload();
                }
            } else {
                // Show error message via alert
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while deleting the expense entry. Please try again.');
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
        const amountInputs = document.querySelectorAll('#incomeAmount, #editIncomeAmount, #expenseAmount, #editExpenseAmount');
    
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

function formatSignedCurrency(amount) {
    const numeric = Number(amount) || 0;
    const formatted = formatCurrency(numeric);
    if (numeric > 0) {
        return `+${formatted}`;
    }
    return formatted;
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

/**
 * Payee Management Functions
 */
let payeeCache = [];
let currentBaseModal = null; // Track which modal opened the payee modal

// Load payees from server
async function loadPayees() {
    try {
        const response = await fetch('/budget-basic/payees/');
        const data = await response.json();
        
        if (data.success) {
            payeeCache = data.payees;
            updatePayeeSelects();
        }
    } catch (error) {
        console.error('Error loading payees:', error);
    }
}

// Load payees for a specific modal
async function loadPayeesForModal(selectId) {
    try {
        const response = await fetch('/budget-basic/payees/');
        const data = await response.json();
        
        if (data.success) {
            payeeCache = data.payees;
            updatePayeeSelectById(selectId);
        }
    } catch (error) {
        console.error('Error loading payees for modal:', error);
    }
}

// Update a specific payee select element by ID
function updatePayeeSelectById(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    // Clear existing options (except first one)
    while (select.children.length > 1) {
        select.removeChild(select.lastChild);
    }
    
    // Add payee options
    payeeCache.forEach(payee => {
        const option = document.createElement('option');
        option.value = payee.name;
        option.textContent = payee.name;
        select.appendChild(option);
    });
}

// Update all payee select elements
function updatePayeeSelects() {
    const incomeSelect = document.getElementById('incomePayeeSelect');
    const expenseSelect = document.getElementById('expensePayeeSelect');
    const editIncomeSelect = document.getElementById('editIncomePayeeSelect');
    const editExpenseSelect = document.getElementById('editExpensePayeeSelect');
    
    [incomeSelect, expenseSelect, editIncomeSelect, editExpenseSelect].forEach(select => {
        if (!select) return;
        
        // Clear existing options (except first one)
        while (select.children.length > 1) {
            select.removeChild(select.lastChild);
        }
        
        // Add payee options
        payeeCache.forEach(payee => {
            const option = document.createElement('option');
            option.value = payee.name;
            option.textContent = payee.name;
            select.appendChild(option);
        });
    });
}

// Handle payee selection change
function handlePayeeSelection(selectElement, inputElement) {
    selectElement.addEventListener('change', function() {
        if (this.value) {
            inputElement.value = this.value;
            inputElement.setAttribute('readonly', true);
            inputElement.classList.add('bg-light');
        } else {
            inputElement.value = '';
            inputElement.removeAttribute('readonly');
            inputElement.classList.remove('bg-light');
        }
    });
}

// Handle manual payee input
function handlePayeeInput(inputElement, selectElement) {
    inputElement.addEventListener('input', function() {
        if (this.value && selectElement.value) {
            // Clear selection if user types manually
            selectElement.value = '';
            this.removeAttribute('readonly');
            this.classList.remove('bg-light');
        }
    });
}

// Add new payee
async function addNewPayee(payeeName) {
    try {
        const formData = new FormData();
        formData.append('name', payeeName);
        formData.append('csrfmiddlewaretoken', document.querySelector('[name=csrfmiddlewaretoken]').value);
        
        const response = await fetch('/budget-basic/payee/add/', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Add to cache and update selects
            payeeCache.push(data.payee);
            payeeCache.sort((a, b) => a.name.localeCompare(b.name));
            updatePayeeSelects();
            return true;
        } else {
            showErrorMessage(data.error || 'Failed to add payee');
            return false;
        }
    } catch (error) {
        console.error('Error adding payee:', error);
        showErrorMessage('Error adding payee');
        return false;
    }
}

// Auto-date functionality
async function getAutoDate(weekOffset = 0, transactionType = null) {
    try {
        let url = `/budget-basic/auto-date/?week_offset=${weekOffset}`;
        if (transactionType) {
            url += `&type=${transactionType}`;
        }
        
        const response = await fetch(url);
        const data = await response.json();
        
        if (data.success) {
            return data.auto_date;
        }
    } catch (error) {
        console.error('Error getting auto date:', error);
    }
    return null;
}

// Set auto date for form
async function setAutoDate(dateInputId) {
    const dateInput = document.getElementById(dateInputId);
    if (!dateInput) return;
    
    // Determine transaction type based on input ID
    let transactionType = null;
    if (dateInputId.toLowerCase().includes('income')) {
        transactionType = 'income';
    } else if (dateInputId.toLowerCase().includes('expense')) {
        transactionType = 'expense';
    }
    
    // Get current week offset from the global variable
    const weekOffset = typeof currentWeekOffset !== 'undefined' ? currentWeekOffset : 0;
    const autoDate = await getAutoDate(weekOffset, transactionType);
    
    if (autoDate) {
        dateInput.value = autoDate;
    }
}

// Initialize payee and auto-date functionality
function initializePayeeFunctionality() {
    // Load payees on page load
    loadPayees();
    
    // Set up payee selection for income modal
    const incomeSelect = document.getElementById('incomePayeeSelect');
    const incomeInput = document.getElementById('incomePayee');
    const addPayeeIncomeBtn = document.getElementById('addPayeeIncomeBtn');
    const addNewPayeeIncomeBtn = document.getElementById('addNewPayeeIncomeBtn');
    const autoDateIncomeBtn = document.getElementById('autoDateIncome');
    
    if (incomeSelect && incomeInput) {
        handlePayeeSelection(incomeSelect, incomeInput);
        handlePayeeInput(incomeInput, incomeSelect);
    }
    
    if (addPayeeIncomeBtn && incomeInput) {
        addPayeeIncomeBtn.addEventListener('click', async function() {
            const payeeName = incomeInput.value.trim();
            if (payeeName) {
                const success = await addNewPayee(payeeName);
                if (success) {
                    // Select the newly added payee
                    incomeSelect.value = payeeName;
                    incomeInput.value = payeeName;
                    incomeInput.setAttribute('readonly', true);
                    incomeInput.classList.add('bg-light');
                }
            }
        });
    }
    
    if (addNewPayeeIncomeBtn) {
        addNewPayeeIncomeBtn.addEventListener('click', function() {
            showAddPayeeModal('income');
        });
    }
    
    if (autoDateIncomeBtn) {
        autoDateIncomeBtn.addEventListener('click', function() {
            setAutoDate('incomeDate');
        });
    }
    
    // Set up payee selection for expense modal
    const expenseSelect = document.getElementById('expensePayeeSelect');
    const expenseInput = document.getElementById('expensePayee');
    const addPayeeExpenseBtn = document.getElementById('addPayeeExpenseBtn');
    const addNewPayeeExpenseBtn = document.getElementById('addNewPayeeExpenseBtn');
    const autoDateExpenseBtn = document.getElementById('autoDateExpense');
    
    if (expenseSelect && expenseInput) {
        handlePayeeSelection(expenseSelect, expenseInput);
        handlePayeeInput(expenseInput, expenseSelect);
    }
    
    if (addPayeeExpenseBtn && expenseInput) {
        addPayeeExpenseBtn.addEventListener('click', async function() {
            const payeeName = expenseInput.value.trim();
            if (payeeName) {
                const success = await addNewPayee(payeeName);
                if (success) {
                    // Select the newly added payee
                    expenseSelect.value = payeeName;
                    expenseInput.value = payeeName;
                    expenseInput.setAttribute('readonly', true);
                    expenseInput.classList.add('bg-light');
                }
            }
        });
    }
    
    if (addNewPayeeExpenseBtn) {
        addNewPayeeExpenseBtn.addEventListener('click', function() {
            showAddPayeeModal('expense');
        });
    }
    
    if (autoDateExpenseBtn) {
        autoDateExpenseBtn.addEventListener('click', function() {
            setAutoDate('expenseDate');
        });
    }
    
    // Set up payee selection for edit income modal
    const editIncomeSelect = document.getElementById('editIncomePayeeSelect');
    const addPayeeEditIncomeBtn = document.getElementById('addPayeeEditIncomeBtn');
    const addNewPayeeEditIncomeBtn = document.getElementById('addNewPayeeEditIncomeBtn');
    
    // Note: Edit modals only have dropdown selects, no text inputs
    
    if (addPayeeEditIncomeBtn) {
        addPayeeEditIncomeBtn.addEventListener('click', async function() {
            console.warn('Add payee from edit modal not implemented - use dropdown or add new payee modal');
        });
    }
    
    if (addNewPayeeEditIncomeBtn) {
        addNewPayeeEditIncomeBtn.addEventListener('click', function() {
            showAddPayeeModal('edit-income');
        });
    }
    
    // Set up payee selection for edit expense modal
    const editExpenseSelect = document.getElementById('editExpensePayeeSelect');
    const addPayeeEditExpenseBtn = document.getElementById('addPayeeEditExpenseBtn');
    const addNewPayeeEditExpenseBtn = document.getElementById('addNewPayeeEditExpenseBtn');
    
    // Note: Edit modals only have dropdown selects, no text inputs
    
    if (addPayeeEditExpenseBtn) {
        addPayeeEditExpenseBtn.addEventListener('click', async function() {
            console.warn('Add payee from edit modal not implemented - use dropdown or add new payee modal');
        });
    }
    
    if (addNewPayeeEditExpenseBtn) {
        addNewPayeeEditExpenseBtn.addEventListener('click', function() {
            showAddPayeeModal('edit-expense');
        });
    }
    
    // Set up the Add Payee modal form submission
    const addPayeeForm = document.getElementById('addPayeeForm');
    if (addPayeeForm) {
        addPayeeForm.addEventListener('submit', handleAddPayeeModalForm);
    }
    
    // Auto-populate date when modals are opened
    const addIncomeModal = document.getElementById('addIncomeModal');
    const addExpenseModal = document.getElementById('addExpenseModal');
    
    if (addIncomeModal) {
        addIncomeModal.addEventListener('shown.bs.modal', function() {
            setAutoDate('incomeDate');
        });
    }
    
    if (addExpenseModal) {
        addExpenseModal.addEventListener('shown.bs.modal', function() {
            setAutoDate('expenseDate');
        });
    }
}

/**
 * Calculate week offset from a given date relative to current week
 */
function calculateWeekOffset(transactionDate) {
    const today = new Date();
    const daysSinceMonday = (today.getDay() + 6) % 7; // Convert Sunday=0 to Monday=0 format
    const currentMonday = new Date(today);
    currentMonday.setDate(today.getDate() - daysSinceMonday);
    currentMonday.setHours(0, 0, 0, 0);
    
    const txDate = new Date(transactionDate);
    const txDaysSinceMonday = (txDate.getDay() + 6) % 7;
    const txMonday = new Date(txDate);
    txMonday.setDate(txDate.getDate() - txDaysSinceMonday);
    txMonday.setHours(0, 0, 0, 0);
    
    const diffTime = txMonday.getTime() - currentMonday.getTime();
    const diffWeeks = Math.round(diffTime / (7 * 24 * 60 * 60 * 1000));
    
    return diffWeeks;
}

/**
 * Navigate to the week containing the given date and highlight the transaction
 */
function navigateToTransactionWeek(transactionDate, transactionId, transactionType) {
    console.log('Navigating to week for transaction:', transactionDate, transactionId, transactionType);
    
    const weekOffset = calculateWeekOffset(transactionDate);
    console.log('Calculated week offset:', weekOffset);
    
    // Get current week offset from window or assume 0
    const currentOffset = window.currentWeekOffset || 0;
    console.log('Current week offset:', currentOffset);
    
    // Check if we need to navigate to a different week
    if (weekOffset !== currentOffset) {
        // Store transaction info for highlighting after week loads
        window.highlightTransactionAfterLoad = {
            id: transactionId,
            type: transactionType
        };
        
        // Navigate to the correct week (this will trigger loadWeekData)
        if (typeof loadWeekData === 'function') {
            loadWeekData(weekOffset);
        } else {
            console.error('loadWeekData function not available');
        }
    } else {
        // We're already on the correct week, but need to reload data to show new transaction
        window.highlightTransactionAfterLoad = {
            id: transactionId,
            type: transactionType
        };
        
        // Reload current week data to include the new transaction
        if (typeof loadWeekData === 'function') {
            loadWeekData(currentOffset);
        } else {
            console.error('loadWeekData function not available');
        }
    }
}

/**
 * Highlight a specific transaction with visual feedback
 */
function highlightTransaction(transactionId, transactionType) {
    console.log('Highlighting transaction:', transactionId, transactionType);
    
    // Wait a bit for DOM to be ready if we just loaded a new week
    setTimeout(() => {
        const transactionCard = document.querySelector(`.transaction-card[data-transaction-id="${transactionId}"]`);
        if (transactionCard) {
            // Add highlight class
            transactionCard.classList.add('transaction-highlight');
            
            // Scroll to the transaction
            transactionCard.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'center' 
            });
            
            // Remove highlight after 3 seconds
            setTimeout(() => {
                transactionCard.classList.remove('transaction-highlight');
            }, 3000);
        } else {
            console.warn('Transaction card not found for ID:', transactionId);
        }
    }, 100);
}

/**
 * Check if we need to highlight a transaction after week load
 * This should be called after week data is loaded
 */
function checkForTransactionHighlight() {
    if (window.highlightTransactionAfterLoad) {
        const { id, type } = window.highlightTransactionAfterLoad;
        highlightTransaction(id, type);
        window.highlightTransactionAfterLoad = null; // Clear the flag
    }
}

/**
 * Stacked Modal Management Functions
 */

/**
 * Show the Add Payee modal on top of the current modal
 */
function showAddPayeeModal(modalType) {
    console.log('Opening Add Payee modal for:', modalType);
    
    // Store which modal opened this payee modal
    currentBaseModal = modalType;
    
    // Find the currently open modal and add fade effect
    const openModals = document.querySelectorAll('.modal.show');
    openModals.forEach(modal => {
        modal.classList.add('modal-faded');
    });
    
    // Clear the add payee form and alert container
    const form = document.getElementById('addPayeeForm');
    if (form) form.reset();
    
    const alertContainer = document.getElementById('addPayeeAlertContainer');
    if (alertContainer) {
        alertContainer.innerHTML = '';
    }
    
    // Show the add payee modal with stacked styling
    const addPayeeModal = document.getElementById('addPayeeModal');
    if (addPayeeModal) {
        addPayeeModal.classList.add('modal-stacked');
        const modal = new bootstrap.Modal(addPayeeModal, {
            backdrop: 'static', // Prevent closing by clicking backdrop
            keyboard: true
        });
        modal.show();
        
        // Focus on the name input when modal is shown
        addPayeeModal.addEventListener('shown.bs.modal', function() {
            const nameInput = document.getElementById('newPayeeName');
            if (nameInput) nameInput.focus();
        }, { once: true });
        
        // Handle modal close to remove stacked styling and fade effect
        addPayeeModal.addEventListener('hidden.bs.modal', function() {
            addPayeeModal.classList.remove('modal-stacked');
            
            // Remove fade effect from base modals
            const openModals = document.querySelectorAll('.modal.show');
            openModals.forEach(modal => {
                modal.classList.remove('modal-faded');
            });
            
            currentBaseModal = null;
        }, { once: true });
    }
}

/**
 * Show message in payee modal alert container
 */
function showPayeeModalMessage(message, type = 'danger') {
    const alertContainer = document.getElementById('addPayeeAlertContainer');
    if (!alertContainer) return;
    
    // Clear existing alerts
    alertContainer.innerHTML = '';
    
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible mb-3`;
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    alertContainer.appendChild(alert);
    
    // Auto-dismiss after 5 seconds for success messages
    if (type === 'success') {
        setTimeout(() => {
            if (alert && alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
}

/**
 * Handle Add Payee modal form submission
 */
async function handleAddPayeeModalForm(e) {
    e.preventDefault();
    
    const form = e.target;
    const formData = new FormData(form);
    const payeeName = formData.get('name').trim();
    
    // Clear any existing alerts
    const alertContainer = document.getElementById('addPayeeAlertContainer');
    if (alertContainer) {
        alertContainer.innerHTML = '';
    }
    
    if (!payeeName) {
        showPayeeModalMessage('Please enter a payee name');
        return;
    }
    
    try {
        // Show loading state
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.textContent = 'Adding...';
        
        const response = await fetch('/budget-basic/payee/add/', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Add to cache and update selects
            payeeCache.push(data.payee);
            payeeCache.sort((a, b) => a.name.localeCompare(b.name));
            updatePayeeSelects();
            
            // Select the newly added payee in the appropriate modal
            selectNewlyAddedPayee(data.payee.name);
            
            // Close the add payee modal
            const addPayeeModal = bootstrap.Modal.getInstance(document.getElementById('addPayeeModal'));
            if (addPayeeModal) {
                addPayeeModal.hide();
            }
            
            showSuccessMessage(`Payee "${data.payee.name}" added successfully`);
        } else {
            showPayeeModalMessage(data.error || 'Failed to add payee');
        }
    } catch (error) {
        console.error('Error adding payee:', error);
        showPayeeModalMessage('Error adding payee');
    } finally {
        // Reset button state
        const submitBtn = form.querySelector('button[type="submit"]');
        submitBtn.disabled = false;
        submitBtn.textContent = 'Add Payee';
    }
}

/**
 * Select the newly added payee in the appropriate modal
 */
function selectNewlyAddedPayee(payeeName) {
    let selectElement;
    
    switch (currentBaseModal) {
        case 'income':
            selectElement = document.getElementById('incomePayeeSelect');
            break;
        case 'expense':
            selectElement = document.getElementById('expensePayeeSelect');
            break;
        case 'edit-income':
            selectElement = document.getElementById('editIncomePayeeSelect');
            break;
        case 'edit-expense':
            selectElement = document.getElementById('editExpensePayeeSelect');
            break;
    }
    
    if (selectElement) {
        // Select the new payee in the dropdown by name
        selectElement.value = payeeName;
        
        // Trigger change event to update any dependent elements
        selectElement.dispatchEvent(new Event('change'));
    }
}

/**
 * Filter transactions by type (income, expense, or all)
 */
function filterTransactions(filterType) {
    currentFilterType = filterType;
    window.currentFilterType = filterType;

    const filterLabel = document.getElementById('filterLabel');
    if (filterLabel) {
        switch (filterType) {
            case 'income':
                filterLabel.textContent = 'Income';
                break;
            case 'expense':
                filterLabel.textContent = 'Expenses';
                break;
            default:
                filterLabel.textContent = 'All';
        }
    }

    updateDropdownActiveState(filterType);
    applyTransactionFilters();
}

/**
 * Update dropdown active state highlighting
 */
function applyTransactionFilters() {
    const cards = document.querySelectorAll('.transaction-card');
    const normalizedSearch = currentTransactionSearch.trim().toLowerCase();
    let visibleIncome = 0;
    let visibleExpense = 0;
    let incomeTotal = 0;
    let expenseTotal = 0;

    cards.forEach(card => {
        const { transactionType = '', transactionPayee = '', transactionNotes = '', transactionAmount = '' } = card.dataset || {};
        const type = transactionType;
        const payee = transactionPayee.toLowerCase();
        const notes = transactionNotes.toLowerCase();
        const amount = transactionAmount.toString().toLowerCase();
        const numericAmount = Number.parseFloat(transactionAmount || '0');

        const matchesType = currentFilterType === 'all' || currentFilterType === type;
        const matchesSearch = !normalizedSearch || payee.includes(normalizedSearch) || notes.includes(normalizedSearch) || amount.includes(normalizedSearch);

        const shouldShow = matchesType && matchesSearch;
        card.style.display = shouldShow ? 'flex' : 'none';

        if (shouldShow) {
            if (type === 'income') {
                visibleIncome += 1;
                if (Number.isFinite(numericAmount)) {
                    incomeTotal += numericAmount;
                }
            } else if (type === 'expense') {
                visibleExpense += 1;
                if (Number.isFinite(numericAmount)) {
                    expenseTotal += numericAmount;
                }
            }
        }
    });

    updateTransactionTotalsDisplay(currentFilterType, {
        incomeTotal,
        expenseTotal,
        visibleCount: visibleIncome + visibleExpense
    });

    updateEmptyStateMessage(currentFilterType, visibleIncome, visibleExpense);
}

function updateTransactionTotalsDisplay(filterType, totals = {}) {
    const bar = document.getElementById('transaction-total-bar');
    if (!bar) {
        return;
    }

    const { incomeTotal = 0, expenseTotal = 0, visibleCount = 0 } = totals;
    const labelElement = document.getElementById('transaction-total-label');
    const valueElement = document.getElementById('transaction-total-value');
    const subtextElement = document.getElementById('transaction-total-subtext');

    let label = 'Net Balance';
    let numericValue = incomeTotal - expenseTotal;

    if (filterType === 'income') {
        label = 'Total Income';
        numericValue = incomeTotal;
    } else if (filterType === 'expense') {
        label = 'Total Expenses';
        numericValue = -expenseTotal;
    }

    if (labelElement) {
        labelElement.textContent = label;
    }

    if (valueElement) {
        valueElement.textContent = formatSignedCurrency(numericValue);
        valueElement.classList.remove('is-positive', 'is-negative', 'is-neutral');
        if (numericValue > 0) {
            valueElement.classList.add('is-positive');
        } else if (numericValue < 0) {
            valueElement.classList.add('is-negative');
        } else {
            valueElement.classList.add('is-neutral');
        }
    }

    bar.dataset.income = incomeTotal.toFixed(2);
    bar.dataset.expense = expenseTotal.toFixed(2);
    bar.dataset.net = (incomeTotal - expenseTotal).toFixed(2);
    bar.dataset.currentFilter = filterType;

    if (subtextElement) {
        const runningValue = Number.parseFloat(bar.dataset.running || '0');
        if (Number.isFinite(runningValue)) {
            subtextElement.textContent = `Running balance: ${formatSignedCurrency(runningValue)}`;
        } else {
            subtextElement.textContent = '';
        }
    }
}

function handleTransactionSearch(query) {
    currentTransactionSearch = (query || '').toString();
    window.currentTransactionSearch = currentTransactionSearch;
    applyTransactionFilters();
}

function updateDropdownActiveState(activeFilter) {
    const dropdownItems = document.querySelectorAll('#transactionFilterDropdown + .dropdown-menu .dropdown-item');
    
    dropdownItems.forEach(item => {
        item.classList.remove('active');
        
        // Check which filter this item represents
        const onclick = item.getAttribute('onclick');
        if (onclick) {
            if (onclick.includes("'all')") && activeFilter === 'all') {
                item.classList.add('active');
            } else if (onclick.includes("'income')") && activeFilter === 'income') {
                item.classList.add('active');
            } else if (onclick.includes("'expense')") && activeFilter === 'expense') {
                item.classList.add('active');
            }
        }
    });
}

/**
 * Update empty state message based on filter
 */
function updateEmptyStateMessage(filterType, incomeCount, expenseCount) {
    const container = document.querySelector('.transaction-cards-container') || document.querySelector('.payee-list-panel');

    if (!container) {
        return;
    }

    if (document.body.classList.contains('payees-page')) {
        const existingMessage = container.querySelector('.no-transactions-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        return;
    }

    const listHost = container.querySelector('.transaction-list-content') || container;
    let emptyMessage = listHost.querySelector('.no-transactions-message');

    const hasSearch = typeof currentTransactionSearch === 'string' && currentTransactionSearch.trim() !== '';

    let showEmpty = false;
    let message = '';

    switch (filterType) {
        case 'income':
            showEmpty = incomeCount === 0;
            message = hasSearch ? 'No income transactions match your search.' : 'No income transactions for this week.';
            break;
        case 'expense':
            showEmpty = expenseCount === 0;
            message = hasSearch ? 'No expense transactions match your search.' : 'No expense transactions for this week.';
            break;
        default:
            showEmpty = (incomeCount + expenseCount) === 0;
            message = hasSearch ? 'No transactions match your search.' : 'No transactions for this week.';
            break;
    }

    if (showEmpty) {
        if (!emptyMessage) {
            emptyMessage = document.createElement('div');
            emptyMessage.className = 'no-transactions-message text-center text-muted py-4';
            emptyMessage.innerHTML = `<i class="bi bi-inbox-fill fs-1 mb-3 d-block"></i><p class="mb-0">${message}</p>`;
            listHost.appendChild(emptyMessage);
        } else {
            const paragraph = emptyMessage.querySelector('p');
            if (paragraph) {
                paragraph.textContent = message;
            } else {
                emptyMessage.innerHTML = `<i class="bi bi-inbox-fill fs-1 mb-3 d-block"></i><p class="mb-0">${message}</p>`;
            }
            emptyMessage.style.display = 'block';
        }
    } else if (emptyMessage) {
        emptyMessage.style.display = 'none';
    }
}

// =========================
// TRANSACTION SIDE PANEL
// =========================

// Transaction panel visibility configuration
const PANEL_CONFIG = {
    // Set to 'fade' for faded panel when empty, 'hide' to completely hide panel
    emptyPanelMode: 'fade' // Options: 'fade' or 'hide'
};

let selectedTransactionElement = null;

/**
 * Show and enable the edit/delete action buttons
 */
function showActionButtons() {
    const editBtn = document.getElementById('edit-transaction-btn');
    const deleteBtn = document.getElementById('delete-transaction-btn');
    
    if (editBtn) {
        editBtn.disabled = false;
    }
    
    if (deleteBtn) {
        deleteBtn.disabled = false;
    }
}

/**
 * Disable the edit/delete action buttons
 */
function hideActionButtons() {
    const editBtn = document.getElementById('edit-transaction-btn');
    const deleteBtn = document.getElementById('delete-transaction-btn');
    
    if (editBtn) {
        editBtn.disabled = true;
    }
    
    if (deleteBtn) {
        deleteBtn.disabled = true;
    }
}

/**
 * Select a transaction and show details in side panel
 */
function selectTransaction(element, event) {
    // Prevent event bubbling to avoid triggering background click handlers
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    
    // Check if this element is already selected (toggle behavior)
    if (selectedTransactionElement === element) {
        // Same element clicked - deselect it
        clearTransactionSelection();
        return;
    }
    
    // Clear previous selection
    if (selectedTransactionElement) {
        selectedTransactionElement.classList.remove('selected');
    }
    
    // Mark new selection
    selectedTransactionElement = element;
    element.classList.add('selected');
    
    // Get transaction data from data attributes
    const transactionData = {
        id: element.getAttribute('data-transaction-id'),
        type: element.getAttribute('data-transaction-type'),
        date: element.getAttribute('data-transaction-date'),
        payee: element.getAttribute('data-transaction-payee'),
        amount: element.getAttribute('data-transaction-amount'),
        notes: element.getAttribute('data-transaction-notes') || 'No notes'
    };
    
    // Show the side panel
    showTransactionPanel(transactionData);
}

/**
 * Clear transaction selection and hide panel
 */
function clearTransactionSelection() {
    // Remove selection styling from previous selection
    if (selectedTransactionElement) {
        selectedTransactionElement.classList.remove('selected');
        selectedTransactionElement = null;
    }
    
    // Hide the panel
    hideTransactionPanel();
}

/**
 * Show the transaction details panel
 */
function showTransactionPanel(data) {
    const container = document.querySelector('.transactions-with-panel') || document.querySelector('.payees-panel');
    const panel = document.getElementById('transaction-details-panel');
    
    if (!container || !panel) {
        return;
    }
    
    // Activate panel layout
    panel.classList.add('has-content');
    
    // Populate panel data
    const detailContent = document.getElementById('transaction-detail-content');

    const payeeName = (data.payee || 'Transaction').trim() || 'Transaction';
    const notes = (data.notes || '').trim();
    const numericAmount = Number(data.amount || 0);
    const formattedAmount = formatCurrency(Math.abs(numericAmount));
    let amountDisplay = formattedAmount;
    if (data.type === 'expense' && numericAmount >= 0) {
        amountDisplay = '-' + formattedAmount;
    } else if (data.type === 'income' && numericAmount >= 0) {
        amountDisplay = '+' + formattedAmount;
    }

    document.getElementById('detail-payee').textContent = payeeName;
    let displayDate = '-';
    if (data.date) {
        const dateCandidate = new Date(`${data.date}T00:00:00`);
        if (!Number.isNaN(dateCandidate.getTime())) {
            displayDate = dateCandidate.toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' });
        } else {
            displayDate = data.date;
        }
    }
    document.getElementById('detail-date').textContent = displayDate;
    document.getElementById('detail-type').textContent = (data.type || '-').charAt(0).toUpperCase() + (data.type || '-').slice(1);
    document.getElementById('detail-amount').textContent = amountDisplay;
    document.getElementById('detail-notes').textContent = notes || 'No notes';

    panel.setAttribute('data-selected-id', data.id);
    panel.setAttribute('data-selected-type', data.type);

    showActionButtons();
}

/**
 * Hide the transaction details panel
 */
function hideTransactionPanel() {
    const container = document.querySelector('.transactions-with-panel') || document.querySelector('.payees-panel');
    const panel = document.getElementById('transaction-details-panel');
    
    if (!container || !panel) return;
    
    // Deactivate panel layout
    panel.classList.remove('has-content');
    
    // Clear the panel content to show it's empty
    clearPanelContent();
    
    // Clear stored data
    panel.removeAttribute('data-selected-id');
    panel.removeAttribute('data-selected-type');
    
    // Hide and disable action buttons
    hideActionButtons();
}

/**
 * Clear panel content to show empty state
 */
function clearPanelContent() {
    // Reset panel content to empty/placeholder state
    // Note: Not using hidden attribute to prevent layout reflow
    document.getElementById('detail-payee').textContent = 'Select a transaction';
    document.getElementById('detail-date').textContent = '-';
    document.getElementById('detail-amount').textContent = '$0.00';
    document.getElementById('detail-type').textContent = '-';
    document.getElementById('detail-notes').textContent = '-';
}

/**
 * Set panel visibility mode
 * @param {string} mode - 'fade' or 'hide'
 */
function setPanelVisibilityMode(mode) {
    const panel = document.getElementById('transaction-details-panel');
    if (!panel) return;
    
    // Remove existing mode classes
    panel.classList.remove('panel-mode-fade', 'panel-mode-hide');
    
    // Add new mode class
    if (mode === 'hide') {
        panel.classList.add('panel-mode-hide');
        PANEL_CONFIG.emptyPanelMode = 'hide';
    } else {
        panel.classList.add('panel-mode-fade');
        PANEL_CONFIG.emptyPanelMode = 'fade';
    }
}

/**
 * Edit the currently selected transaction
 */
function editSelectedTransaction() {
    const panel = document.getElementById('transaction-details-panel');
    if (!panel) return;
    
    const id = panel.getAttribute('data-selected-id');
    const type = panel.getAttribute('data-selected-type');
    
    if (!id || !type) {
        console.warn('No transaction selected for editing');
        return;
    }
    
    // Additional safety check - ensure buttons are enabled
    const editBtn = document.getElementById('edit-transaction-btn');
    if (editBtn && editBtn.disabled) {
        console.warn('Edit button is disabled - no valid selection');
        return;
    }
    
    if (type === 'income') {
        showEditIncomeModal(parseInt(id));
    } else if (type === 'expense') {
        showEditExpenseModal(parseInt(id));
    }
}

/**
 * Delete the currently selected transaction
 */
function deleteSelectedTransaction() {
    const panel = document.getElementById('transaction-details-panel');
    if (!panel) return;
    
    const id = panel.getAttribute('data-selected-id');
    const type = panel.getAttribute('data-selected-type');
    
    if (!id || !type) {
        console.warn('No transaction selected for deletion');
        return;
    }
    
    // Additional safety check - ensure buttons are enabled
    const deleteBtn = document.getElementById('delete-transaction-btn');
    if (deleteBtn && deleteBtn.disabled) {
        console.warn('Delete button is disabled - no valid selection');
        return;
    }
    
    // Get transaction data for confirmation
    const payee = document.getElementById('detail-payee').textContent;
    const amount = document.getElementById('detail-amount').textContent.replace(/[+\-$]/g, '');
    
    if (type === 'income') {
        showDeleteIncomeModal(parseInt(id), payee, amount);
    } else if (type === 'expense') {
        showDeleteExpenseModal(parseInt(id), payee, amount);
    }
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
    closeSidebar,
    loadPayees,
    initializePayeeFunctionality,
    navigateToTransactionWeek,
    highlightTransaction,
    checkForTransactionHighlight,
    showAddPayeeModal,
    selectNewlyAddedPayee,
    filterTransactions,
    selectTransaction,
    clearTransactionSelection,
    editSelectedTransaction,
    deleteSelectedTransaction,
    showActionButtons,
    hideActionButtons
};

// ===== PANEL RESIZER FUNCTIONALITY =====

let isResizing = false;
let startX = 0;
let startLeftWidth = 0;

/**
 * Initialize panel resizer functionality
 */
function initializePanelResizer() {
    const resizer = document.getElementById('panel-resizer');
    
    if (!resizer) {
        console.warn('Panel resizer element not found');
        return;
    }
    
    resizer.addEventListener('mousedown', startResize);
    document.addEventListener('mousemove', doResize);
    document.addEventListener('mouseup', stopResize);
    
    // Add additional safety handlers to ensure cleanup
    document.addEventListener('mouseleave', stopResize);
    window.addEventListener('blur', stopResize);
    
    // Prevent text selection during resize
    resizer.addEventListener('selectstart', (e) => e.preventDefault());
}

/**
 * Initialize transaction selection system with proper event handling
 */
function initializeTransactionSelection() {
    try {
        const transactionCardsContainer = document.querySelector('.transaction-cards-container') || document.querySelector('.payee-list-panel');
        
        if (!transactionCardsContainer) {
            console.warn('Transaction cards container not found - selection system not initialized');
            return;
        }
        
        // Add event listener for background clicks to clear selection
        transactionCardsContainer.addEventListener('click', function(e) {
            // Check if click is on a transaction card
            const transactionCard = e.target.closest('.transaction-card-data');
            
            if (!transactionCard) {
                // Background click detected - clear selection
                clearTransactionSelection();
            }
        }, true); // Use capture phase
        
    } catch (error) {
        console.error('Error initializing transaction selection:', error);
    }
}


function getResizablePanels() {
    const container = document.querySelector('.transactions-with-panel') || document.querySelector('.payees-panel');
    const leftPanel = document.querySelector('.transaction-cards-container') || document.querySelector('.payee-list-panel');
    const rightPanel = document.querySelector('.transaction-details-panel') || document.querySelector('.payee-detail-panel');

    return { container, leftPanel, rightPanel };
}

/**
 * Start panel resize operation
 */
function startResize(e) {
    isResizing = true;
    startX = e.clientX;

    const { leftPanel, rightPanel } = getResizablePanels();

    if (leftPanel) {
        startLeftWidth = leftPanel.offsetWidth;
        leftPanel.classList.add('resizing');
    }

    if (rightPanel) {
        rightPanel.classList.add('resizing');
    }
    
    // Add dragging state
    const resizer = document.getElementById('panel-resizer');
    if (resizer) {
        resizer.classList.add('dragging');
    }
    
    // Prevent text selection during drag
    document.body.style.userSelect = 'none';
    
    e.preventDefault();
}

/**
 * Perform panel resize
 */
function doResize(e) {
    if (!isResizing) return;

    const { container, leftPanel, rightPanel } = getResizablePanels();

    if (!container || !leftPanel || !rightPanel) return;
    
    const deltaX = e.clientX - startX;
    const desiredLeftWidth = startLeftWidth + deltaX;

    const containerStyles = getComputedStyle(container);
    const paddingLeft = parseFloat(containerStyles.paddingLeft) || 0;
    const paddingRight = parseFloat(containerStyles.paddingRight) || 0;
    const containerWidth = container.clientWidth;
    const availableWidth = containerWidth - paddingLeft - paddingRight;

    const resizer = document.getElementById('panel-resizer');
    const resizerWidth = resizer ? resizer.offsetWidth : 6;

    const isPayeesPage = document.body.classList.contains('payees-page');
    const minLeftWidth = isPayeesPage ? 200 : 300; // ensure list stays readable
    const minRightWidth = isPayeesPage ? 200 : 250; // keep detail panel legible
    const maxLeftWidth = availableWidth - minRightWidth - resizerWidth;

    const targetLeft = Math.max(minLeftWidth, Math.min(desiredLeftWidth, maxLeftWidth));
    const targetRight = availableWidth - targetLeft - resizerWidth;

    if (leftPanel) {
        leftPanel.style.width = `${targetLeft}px`;
        leftPanel.style.flex = `0 0 ${targetLeft}px`;
    }

    if (rightPanel) {
        const appliedRightWidth = Math.max(minRightWidth, targetRight);
        rightPanel.style.width = `${appliedRightWidth}px`;
        rightPanel.style.flex = `0 0 ${appliedRightWidth}px`;
    }

    e.preventDefault();
}

/**
 * Stop panel resize operation
 */
function stopResize() {
    if (!isResizing) return;

    isResizing = false;

    // Remove dragging and resizing states
    const resizer = document.getElementById('panel-resizer');
    const { leftPanel, rightPanel } = getResizablePanels();
    
    if (resizer) {
        resizer.classList.remove('dragging');
    }
    
    if (leftPanel) {
        leftPanel.classList.remove('resizing');
    }
    
    if (rightPanel) {
        rightPanel.classList.remove('resizing');
    }
    
    // Restore text selection - use both methods for maximum compatibility
    document.body.style.removeProperty('user-select');
    document.body.style.userSelect = '';
}

// Make functions available globally for onclick handlers
window.filterTransactions = filterTransactions;
window.currentFilterType = currentFilterType;
window.currentTransactionSearch = currentTransactionSearch;
window.handleTransactionSearch = handleTransactionSearch;
window.selectTransaction = selectTransaction;
window.clearTransactionSelection = clearTransactionSelection;
window.setPanelVisibilityMode = setPanelVisibilityMode;
window.editSelectedTransaction = editSelectedTransaction;
window.deleteSelectedTransaction = deleteSelectedTransaction;
window.initializePanelResizer = initializePanelResizer;
window.showActionButtons = showActionButtons;
window.hideActionButtons = hideActionButtons;
window.updateTransactionTotalsDisplay = updateTransactionTotalsDisplay;
window.formatSignedCurrency = formatSignedCurrency;

