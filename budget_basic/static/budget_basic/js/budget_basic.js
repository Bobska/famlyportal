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
                    
                    // Handle payee selection - check if it exists in dropdown
                    const editIncomeSelect = document.getElementById('editIncomePayeeSelect');
                    const editIncomeInput = document.getElementById('editIncomePayee');
                    const payeeExists = Array.from(editIncomeSelect.options).some(option => option.value === data.income.payee);
                    
                    if (payeeExists) {
                        // Payee exists in dropdown - select it and make input readonly
                        editIncomeSelect.value = data.income.payee;
                        editIncomeInput.value = data.income.payee;
                        editIncomeInput.setAttribute('readonly', true);
                        editIncomeInput.classList.add('bg-light');
                    } else {
                        // Payee doesn't exist - clear dropdown and allow manual entry
                        editIncomeSelect.value = '';
                        editIncomeInput.value = data.income.payee;
                        editIncomeInput.removeAttribute('readonly');
                        editIncomeInput.classList.remove('bg-light');
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
                    
                    // Handle payee selection - check if it exists in dropdown
                    const editExpenseSelect = document.getElementById('editExpensePayeeSelect');
                    const editExpenseInput = document.getElementById('editExpensePayee');
                    const payeeExists = Array.from(editExpenseSelect.options).some(option => option.value === data.expense.payee);
                    
                    if (payeeExists) {
                        // Payee exists in dropdown - select it and make input readonly
                        editExpenseSelect.value = data.expense.payee;
                        editExpenseInput.value = data.expense.payee;
                        editExpenseInput.setAttribute('readonly', true);
                        editExpenseInput.classList.add('bg-light');
                    } else {
                        // Payee doesn't exist - clear dropdown and allow manual entry
                        editExpenseSelect.value = '';
                        editExpenseInput.value = data.expense.payee;
                        editExpenseInput.removeAttribute('readonly');
                        editExpenseInput.classList.remove('bg-light');
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
        const payee = formData.get('payee');
        const amount = formData.get('amount');
        
        if (!date || !payee || !amount) {
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
    
    if (autoDateIncomeBtn) {
        autoDateIncomeBtn.addEventListener('click', function() {
            setAutoDate('incomeDate');
        });
    }
    
    // Set up payee selection for expense modal
    const expenseSelect = document.getElementById('expensePayeeSelect');
    const expenseInput = document.getElementById('expensePayee');
    const addPayeeExpenseBtn = document.getElementById('addPayeeExpenseBtn');
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
    
    if (autoDateExpenseBtn) {
        autoDateExpenseBtn.addEventListener('click', function() {
            setAutoDate('expenseDate');
        });
    }
    
    // Set up payee selection for edit income modal
    const editIncomeSelect = document.getElementById('editIncomePayeeSelect');
    const editIncomeInput = document.getElementById('editIncomePayee');
    const addPayeeEditIncomeBtn = document.getElementById('addPayeeEditIncomeBtn');
    
    if (editIncomeSelect && editIncomeInput) {
        handlePayeeSelection(editIncomeSelect, editIncomeInput);
        handlePayeeInput(editIncomeInput, editIncomeSelect);
    }
    
    if (addPayeeEditIncomeBtn && editIncomeInput) {
        addPayeeEditIncomeBtn.addEventListener('click', async function() {
            const payeeName = editIncomeInput.value.trim();
            if (payeeName) {
                const success = await addNewPayee(payeeName);
                if (success) {
                    // Select the newly added payee
                    editIncomeSelect.value = payeeName;
                    editIncomeInput.value = payeeName;
                    editIncomeInput.setAttribute('readonly', true);
                    editIncomeInput.classList.add('bg-light');
                }
            }
        });
    }
    
    // Set up payee selection for edit expense modal
    const editExpenseSelect = document.getElementById('editExpensePayeeSelect');
    const editExpenseInput = document.getElementById('editExpensePayee');
    const addPayeeEditExpenseBtn = document.getElementById('addPayeeEditExpenseBtn');
    
    if (editExpenseSelect && editExpenseInput) {
        handlePayeeSelection(editExpenseSelect, editExpenseInput);
        handlePayeeInput(editExpenseInput, editExpenseSelect);
    }
    
    if (addPayeeEditExpenseBtn && editExpenseInput) {
        addPayeeEditExpenseBtn.addEventListener('click', async function() {
            const payeeName = editExpenseInput.value.trim();
            if (payeeName) {
                const success = await addNewPayee(payeeName);
                if (success) {
                    // Select the newly added payee
                    editExpenseSelect.value = payeeName;
                    editExpenseInput.value = payeeName;
                    editExpenseInput.setAttribute('readonly', true);
                    editExpenseInput.classList.add('bg-light');
                }
            }
        });
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
    checkForTransactionHighlight
};