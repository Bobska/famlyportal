// Week Navigation and Transaction Selection JavaScript

// Configuration
let weekDataUrl = '/budget-basic/get-week-data/'; // Default URL, can be overridden

// Week navigation functionality
let currentWeekOffset = 0; // Will be set from template

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
    
    // Make AJAX request to get week data
    fetch(`${weekDataUrl}?week_offset=${offset}`)
        .then(response => {
            console.log('Response status:', response.status);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Week data received:', data);
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
                balanceElement.textContent = `${balanceValue >= 0 ? '+' : ''}$${Math.abs(balanceValue).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',')}`;
                balanceElement.className = `weekly-stat-value`; // Remove color classes, use grayscale styling
                
                // Update transactions
                console.log('Updating transactions:', data.income_entries.length + data.expense_entries.length + ' total');
                updateTransactionsList(data.income_entries, data.expense_entries);
                
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
                weekLabel.textContent = 'Error';
            }
        })
        .catch(error => {
            console.error('Error loading week data:', error);
            weekLabel.textContent = 'Error';
        });
}

function updateTransactionsList(incomeEntries, expenseEntries) {
    console.log('Updating transactions container with:', incomeEntries.length, 'income,', expenseEntries.length, 'expense entries');
    
    const cardBody = document.querySelector('#transactions-card .card-body');
    if (!cardBody) {
        console.error('Transaction card body not found');
        return;
    }
    
    // Check if we have any transactions
    if (incomeEntries.length === 0 && expenseEntries.length === 0) {
        // Replace the entire card body with empty state
        cardBody.innerHTML = `
            <div class="text-center py-5 text-muted">
                <div class="mb-3">
                    <i class="bi bi-receipt" style="font-size: 3rem;"></i>
                </div>
                <p class="mb-0">No transactions for this week</p>
                <small>Add your first income or expense using the buttons above</small>
            </div>
        `;
        return;
    }
    
    // We have transactions, ensure we have the proper container structure
    let container = cardBody.querySelector('.transaction-cards-container');
    if (!container) {
        // Create the container structure
        cardBody.innerHTML = `
            <div class="transaction-cards-container">
            </div>
        `;
        container = cardBody.querySelector('.transaction-cards-container');
    }
    
    // Clear existing content
    container.innerHTML = '';
    
    // Combine and sort all transactions by date (newest first)
    const allTransactions = [
        ...incomeEntries.map(income => ({...income, type: 'income'})),
        ...expenseEntries.map(expense => ({...expense, type: 'expense'}))
    ].sort((a, b) => new Date(b.date) - new Date(a.date));
    
    console.log('Sorted transactions:', allTransactions);
    
    // Add all transactions
    allTransactions.forEach(transaction => {
        const editFunction = transaction.type === 'income' ? 'showEditIncomeModal' : 'showEditExpenseModal';
        const deleteFunction = transaction.type === 'income' ? 'showDeleteIncomeModal' : 'showDeleteExpenseModal';
        
        const html = `
            <div class="transaction-card transaction-card-data" data-transaction-id="${transaction.id}">
                <div class="transaction-col transaction-date">${transaction.date}</div>
                <div class="transaction-col transaction-payee">${transaction.payee}</div>
                <div class="transaction-col transaction-amount">${transaction.amount_display}</div>
                <div class="transaction-col transaction-actions">
                    <div class="btn-group btn-group-sm" role="group">
                        <button type="button" class="btn btn-outline-secondary btn-icon" onclick="${editFunction}(${transaction.id})" title="Edit Transaction">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button type="button" class="btn btn-outline-secondary btn-icon" onclick="${deleteFunction}(${transaction.id}, '${transaction.payee.replace(/'/g, "\\'")}', '${transaction.amount_display}')" title="Delete Transaction">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', html);
    });
    
    console.log('Transaction list updated successfully');
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
    
    // Show the panel
    detailsPanel.style.display = 'block';
}

// Function to hide transaction details
function hideTransactionDetails() {
    console.log('Hiding transaction details panel');
    const detailsPanel = document.getElementById('transaction-details-panel');
    if (detailsPanel) {
        detailsPanel.style.display = 'none';
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

function initializeTransactionSelection() {
    console.log('Initializing transaction selection');
    
    const transactionsCard = document.getElementById('transactions-card');
    if (!transactionsCard) {
        console.error('Transactions card not found!');
        return;
    }
    
    // Remove existing event listener if it exists
    if (transactionClickHandler) {
        transactionsCard.removeEventListener('click', transactionClickHandler);
        console.log('Removed previous event listener');
    }
    
    // Check if we have any transaction cards
    const transactionCards = transactionsCard.querySelectorAll('.transaction-card-data');
    console.log('Found', transactionCards.length, 'transaction cards for selection');
    
    // Create new click handler
    transactionClickHandler = function(e) {
        console.log('Click detected in transactions card', e.target);
        
        // If clicking on buttons, don't handle selection
        if (e.target.closest('.btn') || e.target.closest('.btn-group')) {
            console.log('Click on button, ignoring');
            return;
        }
        
        // If clicking on a transaction card
        const clickedCard = e.target.closest('.transaction-card-data');
        if (clickedCard) {
            console.log('Click on transaction card', clickedCard.dataset.transactionId);
            
            // Toggle selection: if already active, deselect it; otherwise select it
            const isCurrentlyActive = clickedCard.classList.contains('active');
            console.log('Card currently active:', isCurrentlyActive);
            
            // First, clear all selections
            const activeCards = document.querySelectorAll('.transaction-card-data.active');
            activeCards.forEach(card => card.classList.remove('active'));
            
            // If it wasn't active, make it active; if it was active, leave it deselected
            if (!isCurrentlyActive) {
                clickedCard.classList.add('active');
                showTransactionDetails(clickedCard);
                console.log('Transaction selected');
            } else {
                hideTransactionDetails();
                console.log('Transaction deselected');
            }
        } else {
            // Clicking elsewhere in the transaction card area (but not on a transaction) - clear selection
            console.log('Click on empty area, clearing selection');
            const activeCards = document.querySelectorAll('.transaction-card-data.active');
            activeCards.forEach(card => card.classList.remove('active'));
            hideTransactionDetails();
        }
    };
    
    // Add the new event listener
    transactionsCard.addEventListener('click', transactionClickHandler);
    console.log('Added new transaction click event listener');
}

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