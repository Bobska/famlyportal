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
    
    // Find the transaction list content container (always exists now)
    const container = document.querySelector('.transaction-list-content');
    
    if (!container) {
        console.error('Transaction list content container not found');
        return;
    }
    
    // Clear existing content
    container.innerHTML = '';
    
    // Check if we have any transactions
    if (incomeEntries.length === 0 && expenseEntries.length === 0) {
        // Show empty state within the existing panel structure
        container.innerHTML = `
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
    
    // Add income transactions
    const escapeHtml = (value) => String(value ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');

    incomeEntries.forEach(income => {
        const payeeAttr = escapeHtml(income.payee || '');
        const notesAttr = escapeHtml(income.notes || '');
        const payeeName = escapeHtml(income.payee || 'Unnamed Income');
        const noteMarkup = income.notes ? `<small class="transaction-note transaction-meta text-muted d-none d-xl-inline">${escapeHtml(income.notes)}</small>` : '';
        const amountDisplay = escapeHtml(income.amount_display || `+$${Number(income.amount || 0).toFixed(2)}`);

        const transactionHtml = `
            <div class="transaction-card transaction-card-data payee-row payee-card" 
                 data-transaction-id="${income.id}" 
                 data-transaction-type="income"
                 data-transaction-date="${income.date}"
                 data-transaction-payee="${payeeAttr}"
                 data-transaction-amount="${income.amount}"
                 data-transaction-notes="${notesAttr}"
                 onclick="selectTransaction(this)">
                <div class="payee-cell transaction-date-cell text-muted">${formatTransactionDate(income.date)}</div>
                <div class="payee-cell payee-cell-info transaction-info-cell">
                    <span class="transaction-payee-name transaction-name">${payeeName}</span>
                    ${noteMarkup}
                </div>
                <div class="payee-cell transaction-amount-cell text-end">
                    <span class="transaction-amount text-success">${amountDisplay}</span>
                </div>
            </div>
        `;
        container.insertAdjacentHTML('beforeend', transactionHtml);
    });

    // Add expense transactions
    expenseEntries.forEach(expense => {
        const payeeAttr = escapeHtml(expense.payee || '');
        const notesAttr = escapeHtml(expense.notes || '');
        const payeeName = escapeHtml(expense.payee || 'Unnamed Expense');
        const noteMarkup = expense.notes ? `<small class="transaction-note transaction-meta text-muted d-none d-xl-inline">${escapeHtml(expense.notes)}</small>` : '';
        const amountDisplay = escapeHtml(expense.amount_display || `-$${Number(expense.amount || 0).toFixed(2)}`);

        const transactionHtml = `
            <div class="transaction-card transaction-card-data payee-row payee-card" 
                 data-transaction-id="${expense.id}" 
                 data-transaction-type="expense"
                 data-transaction-date="${expense.date}"
                 data-transaction-payee="${payeeAttr}"
                 data-transaction-amount="${expense.amount}"
                 data-transaction-notes="${notesAttr}"
                 onclick="selectTransaction(this)">
                <div class="payee-cell transaction-date-cell text-muted">${formatTransactionDate(expense.date)}</div>
                <div class="payee-cell payee-cell-info transaction-info-cell">
                    <span class="transaction-payee-name transaction-name">${payeeName}</span>
                    ${noteMarkup}
                </div>
                <div class="payee-cell transaction-amount-cell text-end">
                    <span class="transaction-amount text-danger">${amountDisplay}</span>
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
    const detailContent = document.getElementById('transaction-detail-content');

    if (detailContent) {
        detailContent.hidden = false;
    }

    if (detailsPanel) {
        detailsPanel.style.display = 'flex';
    }

    const payeeName = (transactionCard.dataset.transactionPayee || transactionCard.querySelector('.transaction-payee-name')?.textContent || 'Transaction').trim() || 'Transaction';
    const notes = (transactionCard.dataset.transactionNotes || '').trim();
    const rawDate = transactionCard.dataset.transactionDate || '-';
    const type = (transactionCard.dataset.transactionType || '-').toLowerCase();
    const numericAmount = Number(transactionCard.dataset.transactionAmount || 0);
    const formattedAmount = typeof formatCurrency === 'function' ? formatCurrency(Math.abs(numericAmount)) : `$${Math.abs(numericAmount).toFixed(2)}`;
    let amountDisplay = formattedAmount;
    if (type === 'expense' && numericAmount >= 0) {
        amountDisplay = '-' + formattedAmount;
    } else if (type === 'income' && numericAmount >= 0) {
        amountDisplay = '+' + formattedAmount;
    }

    document.getElementById('detail-payee').textContent = payeeName;
    let formattedDate = '-';
    if (rawDate && rawDate !== '-') {
        formattedDate = typeof formatTransactionDate === 'function' ? formatTransactionDate(rawDate) : rawDate;
    }
    document.getElementById('detail-date').textContent = formattedDate || '-';
    document.getElementById('detail-type').textContent = type ? type.charAt(0).toUpperCase() + type.slice(1) : '-';
    document.getElementById('detail-amount').textContent = amountDisplay;
    document.getElementById('detail-notes').textContent = notes || '-';
}

// Function to hide transaction details
function hideTransactionDetails() {
    console.log('Resetting transaction details panel');
    const detailsPanel = document.getElementById('transaction-details-panel');
    const detailContent = document.getElementById('transaction-detail-content');

    if (detailContent) {
        detailContent.hidden = true;
    }

    document.getElementById('detail-payee').textContent = 'Select a transaction';
    document.getElementById('detail-date').textContent = '-';
    document.getElementById('detail-amount').textContent = '$0.00';
    document.getElementById('detail-type').textContent = '-';
    document.getElementById('detail-notes').textContent = '-';

    const editBtn = document.getElementById('edit-transaction-btn');
    const deleteBtn = document.getElementById('delete-transaction-btn');
    if (editBtn) editBtn.disabled = true;
    if (deleteBtn) deleteBtn.disabled = true;

    const activeCards = document.querySelectorAll('.transaction-card-data.selected');
    if (activeCards.length > 0) {
        activeCards.forEach(card => card.classList.remove('selected'));
    }
}

    if (detailsPanel) {
        detailsPanel.style.display = '';
    }

    document.getElementById('detail-payee').textContent = 'Select a transaction';
    document.getElementById('detail-date').textContent = '-';
    document.getElementById('detail-amount').textContent = '$0.00';
    document.getElementById('detail-type').textContent = '-';
    document.getElementById('detail-notes').textContent = '-';

    const editBtn = document.getElementById('edit-transaction-btn');
    const deleteBtn = document.getElementById('delete-transaction-btn');
    if (editBtn) editBtn.disabled = true;
    if (deleteBtn) deleteBtn.disabled = true;

    const activeCards = document.querySelectorAll('.transaction-card-data.selected');
    if (activeCards.length > 0) {
        activeCards.forEach(card => card.classList.remove('selected'));
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