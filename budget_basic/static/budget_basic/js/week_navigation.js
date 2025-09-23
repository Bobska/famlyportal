// Week Navigation and Transaction Selection JavaScript

// Configuration
let weekDataUrl = '/budget-basic/get-week-data/'; // Default URL, can be overridden

// Week navigation functionality
let currentWeekOffset = 0; // Will be set from template

// Date formatting function
function formatTransactionDate(dateString) {
    const date = new Date(dateString + 'T00:00:00'); // Add time to avoid timezone issues
    const options = { 
        weekday: 'short', 
        day: 'numeric', 
        month: 'short'
        // Removed year since we know what year we're in
    };
    return date.toLocaleDateString('en-US', options);
}

// Set the week data URL (called from template)
function setWeekDataUrl(url) {
    weekDataUrl = url;
    console.log('Week data URL set to:', weekDataUrl);
}

// Set the current week offset (called from template with server value)
function setCurrentWeekOffset(offset) {
    currentWeekOffset = offset;
    window.currentWeekOffset = offset; // Make it globally accessible
    console.log('Week offset set to:', currentWeekOffset);
}

function previousWeek() {
    currentWeekOffset--;
    loadWeekData(currentWeekOffset);
}

function nextWeek() {
    currentWeekOffset++;
    loadWeekData(currentWeekOffset);
}

function loadWeekData(offset) {
    // Show loading state
    const weekLabel = document.querySelector('.week-label-large');
    const weekDate = document.querySelector('.week-date-large');
    weekLabel.textContent = 'Loading...';
    
    console.log(`Loading week data for offset: ${offset}`);
    console.log('Week data URL:', weekDataUrl);
    
    // Make AJAX request to get week data
    fetch(`${weekDataUrl}?week_offset=${offset}`)
        .then(response => {
            console.log('Response status:', response.status);
            console.log('Response headers:', response.headers);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Week data received:', data);
            console.log('Data success flag:', data.success);
            console.log('Week label from data:', data.week_label);
            if (data.success) {
                // Clear any existing transaction selection and details panel when changing weeks
                hideTransactionDetails();
                
                // Clear any active state on week nav buttons when changing weeks
                clearWeekNavSelection();

                // Update week display
                weekLabel.textContent = data.week_label;
                weekDate.textContent = `${data.week_start} - ${data.week_end}`;
                
                // Update weekly totals
                document.getElementById('weekly-income').textContent = `+$${data.weekly_income.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
                document.getElementById('weekly-expenses').textContent = `-$${data.weekly_expenses.toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
                
                const balanceElement = document.getElementById('weekly-balance');
                const balanceValue = data.weekly_balance;
                balanceElement.textContent = `${balanceValue >= 0 ? '+' : '-'}$${Math.abs(balanceValue).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
                balanceElement.className = `weekly-stat-value`; // Remove color classes, use grayscale styling
                
                // Update running balance display
                const runningBalanceElement = document.getElementById('running-balance');
                const runningBalanceValue = data.running_balance;
                runningBalanceElement.textContent = `${runningBalanceValue >= 0 ? '+' : '-'}$${Math.abs(runningBalanceValue).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
                runningBalanceElement.className = runningBalanceValue >= 0 ? 'text-success' : 'text-danger';
                
                // Update transactions
                console.log('Updating transactions:', data.income_entries.length + data.expense_entries.length + ' total');
                updateTransactionsList(data.income_entries, data.expense_entries);
                
                // Retain current filter selection when week changes
                if (window.filterTransactions && window.currentFilterType) {
                    console.log('Retaining filter:', window.currentFilterType);
                    window.filterTransactions(window.currentFilterType);
                } else if (window.filterTransactions) {
                    window.filterTransactions('all');
                }
                
                // Re-initialize transaction card event listeners after updating
                initializeTransactionSelection();
                
                // Check if we need to highlight a specific transaction
                if (window.BudgetBasic && window.BudgetBasic.checkForTransactionHighlight) {
                    window.BudgetBasic.checkForTransactionHighlight();
                }
                
                currentWeekOffset = data.week_offset;
                window.currentWeekOffset = data.week_offset; // Keep global reference updated
            } else {
                console.error('Failed to load week data:', data);
                console.error('Response structure:', JSON.stringify(data, null, 2));
                weekLabel.textContent = 'Error Loading Week';
            }
        })
        .catch(error => {
            console.error('Error loading week data:', error);
            console.error('Error details:', error.message);
            weekLabel.textContent = 'Network Error';
        });
}

function updateTransactionsList(incomeEntries, expenseEntries) {
    console.log('Updating transactions container with:', incomeEntries.length, 'income,', expenseEntries.length, 'expense entries');
    
    // Look for the new panel structure first
    let container = document.querySelector('.transactions-with-panel .transaction-cards-container');
    const transactionsCard = document.querySelector('#transactions-card');
    
    if (!transactionsCard) {
        console.error('Transactions card not found');
        return;
    }
    
    // Check if we have any transactions
    if (incomeEntries.length === 0 && expenseEntries.length === 0) {
        // Replace with empty state, add card-body wrapper for proper styling
        transactionsCard.innerHTML = `
            <div class="card-body">
                <div class="text-center py-5 text-muted">
                    <div class="mb-3">
                        <i class="bi bi-receipt" style="font-size: 3rem;"></i>
                    </div>
                    <p class="mb-0">No transactions for this week</p>
                    <small>Add your first income or expense using the buttons above</small>
                </div>
            </div>
        `;
        return;
    }
    
    // We have transactions, ensure we have the proper panel structure
    if (!container) {
        // Create the panel structure
        transactionsCard.innerHTML = `
            <div class="transactions-with-panel">
                <!-- Left Side: Transaction Cards Container -->
                <div class="transaction-cards-container" id="transaction-list">
                    <!-- Left Panel Header -->
                    <div class="panel-header">
                        <div class="panel-title">Transactions</div>
                    </div>
                    
                    <!-- Transaction List Content -->
                    <div class="transaction-list-content">
                    </div>
                </div>
                
                <!-- Right Side: Details Panel -->
                <div class="transaction-details-panel" id="transaction-details-panel">
                    <div class="panel-header">
                        <h6 class="mb-0">Transaction Details</h6>
                        <button type="button" class="btn btn-sm btn-outline-secondary" onclick="clearTransactionSelection()">
                            <i class="bi bi-x"></i>
                        </button>
                    </div>
                    <div class="panel-content">
                        <div class="detail-section">
                            <div class="detail-row">
                                <span class="detail-label">Date:</span>
                                <span class="detail-value" id="detail-date">Panel is working!</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Payee/Merchant:</span>
                                <span class="detail-value" id="detail-payee">Testing mode - week changed</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Amount:</span>
                                <span class="detail-value" id="detail-amount">$0.00</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Type:</span>
                                <span class="detail-value" id="detail-type">Test</span>
                            </div>
                            <div class="detail-row">
                                <span class="detail-label">Notes:</span>
                                <span class="detail-value" id="detail-notes">Week navigation successful!</span>
                            </div>
                        </div>
                        <div class="panel-actions">
                            <button type="button" class="btn btn-sm btn-outline-primary" id="edit-transaction-btn" onclick="editSelectedTransaction()">
                                <i class="bi bi-pencil me-1"></i>Edit
                            </button>
                            <button type="button" class="btn btn-sm btn-outline-danger" id="delete-transaction-btn" onclick="deleteSelectedTransaction()">
                                <i class="bi bi-trash me-1"></i>Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `;
        container = document.querySelector('.transactions-with-panel .transaction-cards-container .transaction-list-content');
    } else {
        // If container exists, find the transaction-list-content div
        container = container.querySelector('.transaction-list-content') || container;
    }
    
    // Clear existing content
    container.innerHTML = '';
    
    // Add income transactions
    incomeEntries.forEach(income => {
        const transactionHtml = `
            <div class="transaction-card transaction-card-data" 
                 data-transaction-id="${income.id}" 
                 data-transaction-type="income"
                 data-transaction-date="${income.date}"
                 data-transaction-payee="${income.payee.replace(/"/g, '&quot;')}"
                 data-transaction-amount="${income.amount}"
                 data-transaction-notes="${(income.notes || '').replace(/"/g, '&quot;')}"
                 onclick="selectTransaction(this)">
                <div class="transaction-col transaction-date">${formatTransactionDate(income.date)}</div>
                <div class="transaction-col transaction-payee">${income.payee}</div>
                <div class="transaction-col transaction-amount">+$${parseFloat(income.amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</div>
                <div class="transaction-col transaction-actions">
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-secondary btn-icon" onclick="event.stopPropagation(); showEditIncomeModal(${income.id})" title="Edit Transaction">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="btn btn-outline-secondary btn-icon" onclick="event.stopPropagation(); showDeleteIncomeModal(${income.id}, '${income.payee.replace(/'/g, "\\'")}', '${parseFloat(income.amount).toFixed(2)}')" title="Delete Transaction">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', transactionHtml);
    });
    
    // Add expense transactions
    expenseEntries.forEach(expense => {
        const transactionHtml = `
            <div class="transaction-card transaction-card-data" 
                 data-transaction-id="${expense.id}" 
                 data-transaction-type="expense"
                 data-transaction-date="${expense.date}"
                 data-transaction-payee="${expense.payee.replace(/"/g, '&quot;')}"
                 data-transaction-amount="${expense.amount}"
                 data-transaction-notes="${(expense.notes || '').replace(/"/g, '&quot;')}"
                 onclick="selectTransaction(this)">
                <div class="transaction-col transaction-date">${formatTransactionDate(expense.date)}</div>
                <div class="transaction-col transaction-payee">${expense.payee}</div>
                <div class="transaction-col transaction-amount">-$${parseFloat(expense.amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</div>
                <div class="transaction-col transaction-actions">
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-secondary btn-icon" onclick="event.stopPropagation(); showEditExpenseModal(${expense.id})" title="Edit Transaction">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="btn btn-outline-secondary btn-icon" onclick="event.stopPropagation(); showDeleteExpenseModal(${expense.id}, '${expense.payee.replace(/'/g, "\\'")}', '${parseFloat(expense.amount).toFixed(2)}')" title="Delete Transaction">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', transactionHtml);
    });
    
    console.log('Transactions list updated successfully');
}

// Function to show transaction details
function showTransactionDetails(transactionCard) {
    const detailsPanel = document.getElementById('transaction-details-panel');
    const transactionId = transactionCard.dataset.transactionId;
    
    // Extract data from the transaction card
    const date = transactionCard.querySelector('.transaction-col.transaction-date').textContent;
    const payee = transactionCard.querySelector('.transaction-col.transaction-payee').textContent;
    const amount = transactionCard.querySelector('.transaction-col.transaction-amount').textContent;
    const type = amount.startsWith('+') ? 'Income' : 'Expense';
    
    // Update the details panel
    document.getElementById('detail-date').textContent = date;
    document.getElementById('detail-payee').textContent = payee;
    document.getElementById('detail-amount').textContent = amount;
    document.getElementById('detail-type').textContent = type;
    
    // Show the panel - use flex instead of block to maintain layout
    detailsPanel.style.display = 'flex';
}

// Function to hide transaction details
function hideTransactionDetails() {
    console.log('Hiding transaction details panel (DISABLED FOR TESTING)');
    const detailsPanel = document.getElementById('transaction-details-panel');
    if (detailsPanel) {
        // TESTING: Don't hide the panel, just clear the data
        // detailsPanel.style.display = 'none';
        console.log('Panel hiding disabled for testing');
        
        // Reset panel content to test values
        document.getElementById('detail-date').textContent = 'Panel is working!';
        document.getElementById('detail-payee').textContent = 'Testing mode - week changed';
        document.getElementById('detail-amount').textContent = '$0.00';
        document.getElementById('detail-type').textContent = 'Test';
        document.getElementById('detail-notes').textContent = 'Week navigation successful!';
    }
    
    // Clear all selections
    const activeCards = document.querySelectorAll('.transaction-card-data.active');
    if (activeCards.length > 0) {
        console.log('Clearing', activeCards.length, 'active transaction selections');
        activeCards.forEach(card => card.classList.remove('active'));
    }
}

// Initialize transaction selection functionality
let transactionClickHandler; // Store the click handler so we can remove it

// Note: initializeTransactionSelection is now handled entirely by budget_basic.js
// This was causing a conflict where this stub function was overriding the real implementation

// Function to get relative week name (used for dynamic updates if needed)
function getRelativeWeekName(offset) {
    switch(offset) {
        case -2: return '2 Weeks Ago';
        case -1: return 'Last Week';
        case 0: return 'Current Week';
        case 1: return 'Next Week';
        case 2: return 'In 2 Weeks';
        default: 
            if (offset < -2) return `${Math.abs(offset)} Weeks Ago`;
            if (offset > 2) return `In ${offset} Weeks`;
            return 'Unknown Week';
    }
}

// Main initialization function
function initializeWeekNavigation() {
    console.log('Initializing week navigation');
    
    // Clear any active state on prev/next buttons on init
    clearWeekNavSelection();

    // Initialize tooltips for week navigation
    const weekNavButtons = document.querySelectorAll('.btn-week-nav[data-bs-toggle="tooltip"]');
    weekNavButtons.forEach(function(element) {
        new bootstrap.Tooltip(element);
    });
    
    // Initialize transaction selection
    initializeTransactionSelection();
}

// Auto-initialize when DOM is ready (fallback)
document.addEventListener('DOMContentLoaded', function() {
    console.log('Week navigation JavaScript loaded');
    // Don't auto-initialize here, let the template call initializeWeekNavigation()
});

// Utility: clear active/selected state from previous/next week buttons
function clearWeekNavSelection() {
    try {
        const activeButtons = document.querySelectorAll('.btn-week-nav');
        if (activeButtons.length > 0) {
            activeButtons.forEach(btn => {
                btn.classList.remove('active');
                // Remove ARIA pressed state if present
                if (btn.hasAttribute('aria-pressed')) {
                    btn.setAttribute('aria-pressed', 'false');
                }
                // If the button has focus, blur it so it doesn't look active
                try {
                    if (document.activeElement === btn) btn.blur();
                } catch (err) {
                    // ignore
                }
            });
            console.log('Cleared active state and aria-pressed from', activeButtons.length, 'week nav buttons');
        }
    } catch (err) {
        console.warn('Failed to clear week nav selection:', err);
    }
}