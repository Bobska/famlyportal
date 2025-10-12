/**
 * FamlyPortal Tactical Theme JavaScript
 * 
 * Purpose: Reusable tactical interface behaviors and animations
 * Used by: Dashboard Tactical, Transactions Tactical
 * 
 * Features:
 * - Tactical boot sequence animations
 * - Panel reveal system
 * - View switching (dashboard/transactions)
 * - Transaction management and filtering
 * - Real-time search and filtering
 * 
 * Dependencies: Requires tactical.css for animation classes
 */

// =============================================================================
// GLOBAL STATE
// =============================================================================

let currentView = 'dashboard';
let allTransactions = [];
let selectedTransaction = null;

// =============================================================================
// TACTICAL BOOT SEQUENCE
// =============================================================================

/**
 * Initializes the tactical boot sequence animation
 * Order: Header → Panels → Content
 */
window.addEventListener('DOMContentLoaded', function() {
    initializeTacticalBootSequence();
    initializeTransactionData();
    initializeRealTimeFiltering();
});

/**
 * Orchestrates the tactical boot animation sequence
 */
function initializeTacticalBootSequence() {
    // Step 1: Animate header
    const header = document.querySelector('.dashboard-header');
    const headerLeft = document.querySelector('.header-left');
    const headerRight = document.querySelector('.header-right');
    
    // Header slides down
    setTimeout(() => {
        if (header) header.classList.add('animate');
    }, 0);
    
    // Header left content appears
    setTimeout(() => {
        if (headerLeft) headerLeft.classList.add('animate');
    }, 300);
    
    // Header right content appears
    setTimeout(() => {
        if (headerRight) {
            headerRight.classList.add('animate');
            
            // Individual stats in header-right
            const headerStats = headerRight.querySelectorAll('.header-stat');
            headerStats.forEach((stat, index) => {
                setTimeout(() => {
                    stat.style.opacity = '0';
                    stat.style.animation = 'contentFadeIn 0.4s ease-out forwards';
                }, index * 100);
            });
        }
    }, 450);
    
    // Step 2: Start panel sequence after header is done
    const panelStartDelay = 800; // Start panels after header completes
    const allPanels = [];
    
    // Collect all tactical panels
    const tacticalPanels = document.querySelectorAll('.tactical-panel');
    tacticalPanels.forEach((panel, index) => {
        const delay = panelStartDelay + (index * 150); // 150ms between each panel
        allPanels.push({
            element: panel,
            delay: delay,
            contentDelay: delay + 800 // Content appears 800ms after panel starts
        });
    });
    
    // Collect bottom panels
    const bottomPanels = document.querySelectorAll('.bottom-panel');
    const bottomStartDelay = panelStartDelay + 500; // Start after main panels begin
    bottomPanels.forEach((panel, index) => {
        const delay = bottomStartDelay + (index * 150);
        allPanels.push({
            element: panel,
            delay: delay,
            contentDelay: delay + 800
        });
    });
    
    // Animate each panel
    allPanels.forEach(panelData => {
        // Start panel grow animation
        setTimeout(() => {
            panelData.element.classList.add('animate');
        }, panelData.delay);
        
        // Reveal content sequentially
        setTimeout(() => {
            revealPanelContent(panelData.element);
        }, panelData.contentDelay);
    });
}

/**
 * Reveals content within a panel with sequential animation
 * @param {HTMLElement} panel - The panel element containing content to reveal
 */
function revealPanelContent(panel) {
    // Get all content elements (excluding corner elements)
    const contentElements = Array.from(panel.children).filter(child => 
        !child.classList.contains('corner-bl') && 
        !child.classList.contains('corner-br')
    );
    
    // Reveal each element with a delay
    contentElements.forEach((element, index) => {
        setTimeout(() => {
            element.classList.add('content-visible');
            
            // For elements with child items (like lists), reveal those too
            const childItems = element.querySelectorAll('.stat-item, .transaction-item, .action-btn, .info-panel-stat, .balance-display');
            childItems.forEach((child, childIndex) => {
                setTimeout(() => {
                    child.classList.add('content-visible');
                }, childIndex * 80); // 80ms between each child item
            });
        }, index * 150); // 150ms between each main content block
    });
}

// =============================================================================
// VIEW SWITCHING SYSTEM
// =============================================================================

/**
 * Switches between dashboard and transactions views
 * @param {string} viewName - Name of view to display ('dashboard' or 'transactions')
 */
function switchView(viewName) {
    const dashboardView = document.getElementById('dashboardView');
    const transactionsView = document.getElementById('transactionsView');
    const centerPanelTitle = document.getElementById('centerPanelTitle');
    
    // Hide all views
    if (dashboardView) dashboardView.style.display = 'none';
    if (transactionsView) transactionsView.style.display = 'none';

    // Show selected view
    if (viewName === 'dashboard') {
        if (dashboardView) dashboardView.style.display = 'block';
        if (centerPanelTitle) centerPanelTitle.textContent = 'Recent Activity';
        currentView = 'dashboard';
    } else if (viewName === 'transactions') {
        if (transactionsView) transactionsView.style.display = 'block';
        if (centerPanelTitle) centerPanelTitle.textContent = 'Transaction Management';
        currentView = 'transactions';
    }

    // Update button states
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.classList.remove('active');
    });
}

// =============================================================================
// TRANSACTION MANAGEMENT
// =============================================================================

/**
 * Initializes transaction data from DOM for filtering
 */
function initializeTransactionData() {
    const txItems = document.querySelectorAll('#allTransactionsList .transaction-item');
    allTransactions = [];
    
    txItems.forEach(item => {
        allTransactions.push({
            element: item,
            id: item.dataset.id,
            type: item.dataset.type,
            payee: item.dataset.payee.toLowerCase(),
            category: item.dataset.category
        });
    });
}

/**
 * Applies current filter settings to transaction list
 * Updates visibility and statistics for filtered results
 */
function applyTransactionFilters() {
    const searchInput = document.getElementById('txSearch');
    const typeSelect = document.getElementById('txType');
    const categorySelect = document.getElementById('txCategory');
    
    if (!searchInput || !typeSelect || !categorySelect) return;
    
    const search = searchInput.value.toLowerCase();
    const type = typeSelect.value;
    const category = categorySelect.value;

    let visibleCount = 0;
    let visibleSum = 0;

    allTransactions.forEach(tx => {
        let show = true;

        if (search && !tx.payee.includes(search)) show = false;
        if (type !== 'all' && tx.type !== type) show = false;
        if (category !== 'all' && tx.category !== category) show = false;

        tx.element.style.display = show ? 'flex' : 'none';

        // Update stats for visible transactions
        if (show) {
            visibleCount++;
            const amountElement = tx.element.querySelector('.transaction-amount');
            if (amountElement) {
                const amount = parseFloat(amountElement.textContent.replace(/[^0-9.-]+/g, ''));
                visibleSum += tx.type === 'income' ? amount : -amount;
            }
        }
    });

    // Update filtered view stats in extended panel
    updateFilteredStats(visibleCount, visibleSum);
}

/**
 * Updates the filtered statistics display
 * @param {number} count - Number of visible transactions
 * @param {number} sum - Sum of visible transactions
 */
function updateFilteredStats(count, sum) {
    const countEl = document.getElementById('filteredCount');
    const sumEl = document.getElementById('filteredSum');
    
    if (countEl) countEl.textContent = count;
    if (sumEl) {
        sumEl.textContent = '$' + Math.abs(sum).toFixed(2);
        sumEl.style.color = sum >= 0 ? '#00ff88' : '#ff4444';
    }
}

/**
 * Clears all transaction filters and shows all transactions
 */
function clearTransactionFilters() {
    const searchInput = document.getElementById('txSearch');
    const typeSelect = document.getElementById('txType');
    const categorySelect = document.getElementById('txCategory');
    
    if (searchInput) searchInput.value = '';
    if (typeSelect) typeSelect.value = 'all';
    if (categorySelect) categorySelect.value = 'all';
    
    allTransactions.forEach(tx => {
        tx.element.style.display = 'flex';
    });
    
    applyTransactionFilters(); // Update stats
}

/**
 * Selects a transaction and displays its details
 * @param {HTMLElement} element - The transaction item element
 * @param {number} id - Transaction ID
 * @param {string} type - Transaction type ('income' or 'expense')
 */
function selectTransaction(element, id, type) {
    // Remove previous selection
    if (selectedTransaction) {
        selectedTransaction.classList.remove('selected');
    }
    element.classList.add('selected');
    selectedTransaction = element;

    // Extract transaction data from the element
    const payeeElement = element.querySelector('.transaction-payee');
    const dateElement = element.querySelector('.transaction-date');
    const categoryElement = element.querySelector('.transaction-category');
    const amountElement = element.querySelector('.transaction-amount');
    
    if (!payeeElement || !dateElement || !categoryElement || !amountElement) return;
    
    const payee = payeeElement.textContent;
    const date = dateElement.textContent;
    const category = categoryElement.textContent;
    const amount = amountElement.textContent;

    // Update details panel
    updateTransactionDetailsPanel(id, type, payee, date, category, amount);
}

/**
 * Updates the transaction details panel with selected transaction info
 * @param {number} id - Transaction ID
 * @param {string} type - Transaction type
 * @param {string} payee - Payee name
 * @param {string} date - Transaction date
 * @param {string} category - Transaction category
 * @param {string} amount - Transaction amount (formatted)
 */
function updateTransactionDetailsPanel(id, type, payee, date, category, amount) {
    const detailsPanel = document.getElementById('transactionDetailsPanel');
    if (!detailsPanel) return;
    
    const panelContent = detailsPanel.querySelector('.panel-content');
    if (!panelContent) return;
    
    panelContent.innerHTML = `
        <div style="padding: 20px;">
            <div style="margin-bottom: 20px;">
                <div style="font-size: 10px; color: rgba(0, 217, 255, 0.6); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Type</div>
                <div style="font-size: 14px; color: #00d9ff; font-weight: 600; text-transform: uppercase;">${type}</div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <div style="font-size: 10px; color: rgba(0, 217, 255, 0.6); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Payee</div>
                <div style="font-size: 14px; color: #00d9ff;">${payee}</div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <div style="font-size: 10px; color: rgba(0, 217, 255, 0.6); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Date</div>
                <div style="font-size: 14px; color: #00d9ff;">${date}</div>
            </div>
            
            <div style="margin-bottom: 20px;">
                <div style="font-size: 10px; color: rgba(0, 217, 255, 0.6); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Category</div>
                <div style="font-size: 14px; color: #00d9ff;">${category}</div>
            </div>
            
            <div style="margin-bottom: 25px;">
                <div style="font-size: 10px; color: rgba(0, 217, 255, 0.6); text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px;">Amount</div>
                <div style="font-size: 24px; color: ${type === 'income' ? '#00ff88' : '#ff4444'}; font-weight: 600;">${amount}</div>
            </div>
            
            <div style="display: flex; gap: 10px; margin-top: 30px;">
                <button class="action-btn primary" style="flex: 1;" onclick="editTransaction(${id}, '${type}')">EDIT</button>
                <button class="action-btn" style="flex: 1; background: rgba(255, 68, 68, 0.1); border-color: rgba(255, 68, 68, 0.3); color: #ff4444;" onclick="deleteTransaction(${id}, '${type}')">DELETE</button>
            </div>
        </div>
    `;
}

/**
 * Navigates to edit page for selected transaction
 * Reads URLs from data attributes set by Django template
 * @param {number} id - Transaction ID
 * @param {string} type - Transaction type ('income' or 'expense')
 */
function editTransaction(id, type) {
    const urlData = document.getElementById('tacticalUrlData');
    if (!urlData) {
        console.error('URL data not found');
        return;
    }
    
    const editIncomeUrl = urlData.dataset.editIncomeUrl;
    const editExpenseUrl = urlData.dataset.editExpenseUrl;
    
    // Replace placeholder with actual ID
    const url = type === 'income' ? 
        editIncomeUrl.replace('0', id) : 
        editExpenseUrl.replace('0', id);
    
    window.location.href = url;
}

/**
 * Navigates to delete confirmation page for selected transaction
 * Reads URLs from data attributes set by Django template
 * @param {number} id - Transaction ID
 * @param {string} type - Transaction type ('income' or 'expense')
 */
function deleteTransaction(id, type) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }
    
    const urlData = document.getElementById('tacticalUrlData');
    if (!urlData) {
        console.error('URL data not found');
        return;
    }
    
    const deleteIncomeUrl = urlData.dataset.deleteIncomeUrl;
    const deleteExpenseUrl = urlData.dataset.deleteExpenseUrl;
    
    // Replace placeholder with actual ID
    const url = type === 'income' ? 
        deleteIncomeUrl.replace('0', id) : 
        deleteExpenseUrl.replace('0', id);
    
    window.location.href = url;
}

/**
 * Navigates to add transaction page
 * Reads URL from data attributes set by Django template
 */
function showAddTransaction() {
    const urlData = document.getElementById('tacticalUrlData');
    if (!urlData) {
        console.error('URL data not found');
        return;
    }
    
    const transactionsUrl = urlData.dataset.transactionsUrl;
    window.location.href = transactionsUrl;
}

// =============================================================================
// REAL-TIME FILTERING
// =============================================================================

/**
 * Initializes real-time filtering on search input
 */
function initializeRealTimeFiltering() {
    const searchInput = document.getElementById('txSearch');
    if (searchInput) {
        searchInput.addEventListener('input', applyTransactionFilters);
    }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Formats a number as currency
 * @param {number} amount - Amount to format
 * @returns {string} Formatted currency string
 */
function formatCurrency(amount) {
    return '$' + Math.abs(amount).toFixed(2);
}

/**
 * Gets the color for a transaction type
 * @param {string} type - Transaction type ('income' or 'expense')
 * @returns {string} CSS color value
 */
function getTransactionColor(type) {
    return type === 'income' ? '#00ff88' : '#ff4444';
}
