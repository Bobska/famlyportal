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
let leftPanelVisible = false;
let rightPanelVisible = false;

// =============================================================================
// RESPONSIVE PANEL MANAGEMENT
// =============================================================================

/**
 * Initialize responsive panel toggle system
 */
function initResponsivePanels() {
    // Only initialize on page load
    if (window.innerWidth > 1200) {
        return; // Desktop mode - no toggles needed
    }
    
    // Create toggle buttons if they don't exist
    createPanelToggles();
    
    // Create backdrop
    createPanelBackdrop();
    
    // Listen for window resize
    window.addEventListener('resize', handleResponsiveResize);
}

/**
 * Create toggle buttons for side panels
 */
function createPanelToggles() {
    const dashboardGrid = document.querySelector('.dashboard-grid');
    if (!dashboardGrid) return;
    
    const leftPanel = dashboardGrid.querySelector('.tactical-panel:first-child');
    const rightPanel = dashboardGrid.querySelector('.tactical-panel:last-child');
    
    if (!leftPanel || !rightPanel) return;
    
    // Check if toggles already exist
    if (document.querySelector('.panel-toggle.left')) return;
    
    // Create left toggle
    const leftToggle = document.createElement('div');
    leftToggle.className = 'panel-toggle left';
    leftToggle.innerHTML = window.innerWidth <= 768 ? 'STATS ►' : '◄';
    leftToggle.setAttribute('aria-label', 'Toggle left panel');
    leftToggle.onclick = () => togglePanel('left');
    
    // Create right toggle
    const rightToggle = document.createElement('div');
    rightToggle.className = 'panel-toggle right';
    rightToggle.innerHTML = window.innerWidth <= 768 ? '◄ ACTIONS' : '►';
    rightToggle.setAttribute('aria-label', 'Toggle right panel');
    rightToggle.onclick = () => togglePanel('right');
    
    // Insert toggles
    if (window.innerWidth <= 768) {
        // Mobile: Insert as accordion headers
        leftPanel.parentNode.insertBefore(leftToggle, leftPanel);
        rightPanel.parentNode.insertBefore(rightToggle, rightPanel);
    } else {
        // Tablet: Insert as side buttons
        document.body.appendChild(leftToggle);
        document.body.appendChild(rightToggle);
    }
}

/**
 * Create backdrop overlay for panel system
 */
function createPanelBackdrop() {
    if (document.querySelector('.panel-backdrop')) return;
    if (window.innerWidth <= 768) return; // No backdrop on mobile
    
    const backdrop = document.createElement('div');
    backdrop.className = 'panel-backdrop';
    backdrop.onclick = () => {
        if (leftPanelVisible) togglePanel('left');
        if (rightPanelVisible) togglePanel('right');
    };
    document.body.appendChild(backdrop);
}

/**
 * Toggle side panel visibility
 * @param {string} side - 'left' or 'right'
 */
function togglePanel(side) {
    const dashboardGrid = document.querySelector('.dashboard-grid');
    if (!dashboardGrid) return;
    
    const panel = side === 'left' 
        ? dashboardGrid.querySelector('.tactical-panel:first-child')
        : dashboardGrid.querySelector('.tactical-panel:last-child');
    
    const toggle = document.querySelector(`.panel-toggle.${side}`);
    const backdrop = document.querySelector('.panel-backdrop');
    
    if (!panel) return;
    
    // Toggle visibility
    if (side === 'left') {
        leftPanelVisible = !leftPanelVisible;
        panel.classList.toggle('panel-visible', leftPanelVisible);
        if (toggle) toggle.classList.toggle('hidden', leftPanelVisible);
        
        // Close other panel on tablet
        if (window.innerWidth > 768 && window.innerWidth <= 1200 && leftPanelVisible && rightPanelVisible) {
            togglePanel('right');
        }
    } else {
        rightPanelVisible = !rightPanelVisible;
        panel.classList.toggle('panel-visible', rightPanelVisible);
        if (toggle) toggle.classList.toggle('hidden', rightPanelVisible);
        
        // Close other panel on tablet
        if (window.innerWidth > 768 && window.innerWidth <= 1200 && rightPanelVisible && leftPanelVisible) {
            togglePanel('left');
        }
    }
    
    // Show/hide backdrop
    if (backdrop && window.innerWidth > 768) {
        backdrop.classList.toggle('active', leftPanelVisible || rightPanelVisible);
    }
    
    // Update toggle icons on mobile
    if (window.innerWidth <= 768 && toggle) {
        if (side === 'left') {
            toggle.innerHTML = leftPanelVisible ? 'STATS ▼' : 'STATS ►';
        } else {
            toggle.innerHTML = rightPanelVisible ? '▼ ACTIONS' : '◄ ACTIONS';
        }
    }
}

/**
 * Handle window resize events
 */
function handleResponsiveResize() {
    const width = window.innerWidth;
    
    // Desktop mode - remove toggles and show panels normally
    if (width > 1200) {
        removePanelToggles();
        removePanelBackdrop();
        
        const dashboardGrid = document.querySelector('.dashboard-grid');
        if (dashboardGrid) {
            const leftPanel = dashboardGrid.querySelector('.tactical-panel:first-child');
            const rightPanel = dashboardGrid.querySelector('.tactical-panel:last-child');
            
            if (leftPanel) leftPanel.classList.remove('panel-visible');
            if (rightPanel) rightPanel.classList.remove('panel-visible');
        }
        
        leftPanelVisible = false;
        rightPanelVisible = false;
    } 
    // Responsive mode - ensure toggles exist
    else {
        createPanelToggles();
        if (width > 768) {
            createPanelBackdrop();
        }
    }
}

/**
 * Remove panel toggle buttons
 */
function removePanelToggles() {
    document.querySelectorAll('.panel-toggle').forEach(toggle => toggle.remove());
}

/**
 * Remove panel backdrop
 */
function removePanelBackdrop() {
    const backdrop = document.querySelector('.panel-backdrop');
    if (backdrop) backdrop.remove();
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Formats a number as currency with thousands separator
 * @param {number} value - The numeric value to format
 * @param {boolean} showCents - Whether to show decimal places (default: false)
 * @returns {string} Formatted currency string (e.g., "$1,234" or "$1,234.56")
 */
function formatCurrency(value, showCents = false) {
    const num = parseFloat(value) || 0;
    const isNegative = num < 0;
    const absNum = Math.abs(num);
    
    // Format with thousands separator
    let formatted;
    if (showCents) {
        formatted = absNum.toLocaleString('en-US', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    } else {
        formatted = absNum.toLocaleString('en-US', {
            minimumFractionDigits: 0,
            maximumFractionDigits: 0
        });
    }
    
    // Add dollar sign and negative if needed
    return (isNegative ? '-' : '') + '$' + formatted;
}

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
    initResponsivePanels(); // Initialize responsive panel system
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
            
            // SPECIAL: Animate command center content if present
            if (element.classList.contains('panel-content')) {
                animateCommandCenter(element);
            }
        }, index * 150); // 150ms between each main content block
    });
}

/**
 * Animates command center home screen content
 * @param {HTMLElement} panelContent - The panel content element
 */
function animateCommandCenter(panelContent) {
    const commandCenter = panelContent.querySelector('.command-center-home');
    if (!commandCenter) return;
    
    // Animate financial overview section
    const financialSection = commandCenter.querySelector('.financial-overview-section');
    if (financialSection) {
        setTimeout(() => {
            financialSection.classList.add('boot-animate');
            
            // Animate stream items
            const streamItems = financialSection.querySelectorAll('.stream-item');
            streamItems.forEach((item, index) => {
                setTimeout(() => {
                    item.classList.add('boot-animate');
                    
                    // Animate progress bar fill
                    const streamFill = item.querySelector('.stream-fill');
                    if (streamFill) {
                        const targetWidth = streamFill.getAttribute('data-width') || '0';
                        streamFill.style.setProperty('--target-width', targetWidth + '%');
                        setTimeout(() => {
                            streamFill.classList.add('boot-animate');
                        }, 200);
                    }
                }, index * 150);
            });
        }, 200);
    }
    
    // Animate quick actions section
    const quickActionsSection = commandCenter.querySelector('.quick-actions-section');
    if (quickActionsSection) {
        setTimeout(() => {
            quickActionsSection.classList.add('boot-animate');
            
            // Animate action items
            const actionItems = quickActionsSection.querySelectorAll('.action-item');
            actionItems.forEach((item, index) => {
                setTimeout(() => {
                    item.classList.add('boot-animate');
                }, index * 100);
            });
        }, 600);
    }
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

// =============================================================================
// TRANSACTION PAGE INTERACTIONS
// =============================================================================

// Global variables for transaction view state
let transactionView = 'week'; // 'week', 'month', 'year', 'all'
let viewOffset = 0; // For navigating forward/back
let selectedTransactionId = null;

/**
 * Changes the view mode (week/month/year/all)
 * @param {string} view - The view type to switch to
 */
function changeView(view) {
    transactionView = view;
    viewOffset = 0; // Reset to current period
    
    // Update active tab
    document.querySelectorAll('.view-tab').forEach(tab => {
        tab.classList.remove('active');
        if (tab.dataset.view === view) {
            tab.classList.add('active');
        }
    });
    
    // Update view period text
    updateViewPeriodText();
    
    // Filter transactions based on view
    filterTransactionsByView();
}

/**
 * Navigates forward or backward in the current view
 * @param {number} direction - 1 for forward, -1 for backward
 */
function navigateView(direction) {
    viewOffset += direction;
    updateViewPeriodText();
    filterTransactionsByView();
}

/**
 * Updates the view period text display
 */
function updateViewPeriodText() {
    const viewPeriodEl = document.getElementById('viewPeriod');
    if (!viewPeriodEl) return;
    
    const now = new Date();
    let text = '';
    
    if (transactionView === 'all') {
        text = 'All Transactions';
        document.getElementById('prevBtn').disabled = true;
        document.getElementById('nextBtn').disabled = true;
        viewPeriodEl.textContent = text;
        return;
    }
    
    // Enable navigation buttons
    document.getElementById('prevBtn').disabled = false;
    document.getElementById('nextBtn').disabled = viewOffset >= 0;
    
    if (transactionView === 'week') {
        const weekDate = new Date(now);
        weekDate.setDate(weekDate.getDate() + (viewOffset * 7));
        
        const weekStart = new Date(weekDate);
        weekStart.setDate(weekDate.getDate() - weekDate.getDay());
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekStart.getDate() + 6);
        
        const startStr = weekStart.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const endStr = weekEnd.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        
        if (viewOffset === 0) {
            text = `This Week (${startStr} - ${endStr})`;
        } else if (viewOffset === -1) {
            text = `Last Week (${startStr} - ${endStr})`;
        } else if (viewOffset === 1) {
            text = `Next Week (${startStr} - ${endStr})`;
        } else {
            text = `Week of ${startStr} - ${endStr}`;
        }
    } else if (transactionView === 'month') {
        const monthDate = new Date(now.getFullYear(), now.getMonth() + viewOffset, 1);
        const lastDay = new Date(monthDate.getFullYear(), monthDate.getMonth() + 1, 0);
        
        const monthName = monthDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
        const startStr = monthDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const endStr = lastDay.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        
        if (viewOffset === 0) {
            text = `This Month (${monthName})`;
        } else if (viewOffset === -1) {
            text = `Last Month (${monthName})`;
        } else if (viewOffset === 1) {
            text = `Next Month (${monthName})`;
        } else {
            text = `${monthName} (${startStr} - ${endStr})`;
        }
    } else if (transactionView === 'year') {
        const yearDate = new Date(now.getFullYear() + viewOffset, 0, 1);
        const yearNum = yearDate.getFullYear();
        
        const startStr = new Date(yearNum, 0, 1).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
        const endStr = new Date(yearNum, 11, 31).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
        
        if (viewOffset === 0) {
            text = `This Year (${yearNum})`;
        } else {
            text = `${yearNum} (${startStr} - ${endStr})`;
        }
    }
    
    viewPeriodEl.textContent = text;
}

/**
 * Filters transactions based on current view and offset
 */
function filterTransactionsByView() {
    const transactions = document.querySelectorAll('.transaction-item');
    const now = new Date();
    
    // Track visible items for animation
    let visibleIndex = 0;
    
    transactions.forEach(item => {
        const dateStr = item.dataset.date; // Assumes transaction items have data-date attribute
        if (!dateStr) {
            item.style.display = ''; // Show if no date
            animateTransactionItem(item, visibleIndex++);
            return;
        }
        
        const txDate = new Date(dateStr);
        let show = false;
        
        if (transactionView === 'all') {
            show = true;
        } else if (transactionView === 'week') {
            const weekStart = new Date(now);
            weekStart.setDate(now.getDate() - now.getDay() + (viewOffset * 7));
            const weekEnd = new Date(weekStart);
            weekEnd.setDate(weekStart.getDate() + 6);
            
            show = txDate >= weekStart && txDate <= weekEnd;
        } else if (transactionView === 'month') {
            const targetMonth = now.getMonth() + viewOffset;
            const targetYear = now.getFullYear() + Math.floor(targetMonth / 12);
            const monthIndex = ((targetMonth % 12) + 12) % 12;
            
            show = txDate.getMonth() === monthIndex && txDate.getFullYear() === targetYear;
        } else if (transactionView === 'year') {
            const targetYear = now.getFullYear() + viewOffset;
            show = txDate.getFullYear() === targetYear;
        }
        
        if (show) {
            item.style.display = '';
            animateTransactionItem(item, visibleIndex++);
        } else {
            item.style.display = 'none';
            // Reset animation for hidden items
            item.classList.remove('boot-animate');
            item.style.opacity = '0';
            item.style.transform = 'translateX(-15px)';
            item.style.visibility = 'hidden';
        }
    });
    
    // Update summary counts
    updateSummaryCounts();
}

/**
 * Animates a transaction item sliding in
 * @param {HTMLElement} item - Transaction item to animate
 * @param {number} index - Index for staggered delay
 */
function animateTransactionItem(item, index) {
    // Reset any existing animation
    item.classList.remove('boot-animate');
    item.style.opacity = '0';
    item.style.transform = 'translateX(-15px)';
    item.style.visibility = 'hidden';
    
    // Trigger animation with delay (100ms stagger for better visibility)
    setTimeout(() => {
        item.style.visibility = 'visible';
        item.classList.add('boot-animate');
    }, index * 100);
}

/**
 * Updates summary stats based on visible transactions
 */
function updateSummaryCounts() {
    const visibleItems = document.querySelectorAll('.transaction-item[style=""], .transaction-item:not([style])');
    let income = 0, expenses = 0, count = 0;
    
    visibleItems.forEach(item => {
        const type = item.dataset.type;
        const amount = parseFloat(item.dataset.amount) || 0;
        
        if (type === 'income') {
            income += amount;
        } else if (type === 'expense') {
            expenses += amount;
        }
        count++;
    });
    
    document.getElementById('summaryIncome').textContent = formatCurrency(income);
    document.getElementById('summaryExpenses').textContent = formatCurrency(expenses);
    document.getElementById('summaryNet').textContent = formatCurrency(income - expenses);
    document.getElementById('summaryCount').textContent = count;
}

/**
 * Shows the add transaction form
 * @param {string} type - 'income' or 'expense'
 */
function showAddTransaction(type) {
    // Hide empty state and details
    document.getElementById('detailsView').style.display = 'none';
    document.getElementById('transactionDetails').style.display = 'none';
    
    // Show form
    document.getElementById('transactionForm').style.display = 'block';
    
    // Set form type
    document.getElementById('formType').value = type;
    
    // Set today's date
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('formDate').value = today;
    
    // Clear other fields
    document.getElementById('formPayee').value = '';
    document.getElementById('formAmount').value = '';
    document.getElementById('formCategory').value = '';
    document.getElementById('formNotes').value = '';
    
    // Clear selection
    selectedTransactionId = null;
    document.querySelectorAll('.transaction-item').forEach(item => {
        item.classList.remove('selected');
    });
}

/**
 * Selects a transaction and shows its details
 * @param {HTMLElement} element - The clicked transaction element
 * @param {number} id - Transaction ID
 * @param {string} type - Transaction type
 */
function selectTransaction(element, id, type) {
    selectedTransactionId = id;
    
    // Update selected state
    document.querySelectorAll('.transaction-item').forEach(item => {
        item.classList.remove('selected');
    });
    element.classList.add('selected');
    
    // Get transaction data from data attributes
    const payee = element.dataset.payee || '-';
    const amount = element.dataset.amount || '0';
    const date = element.dataset.date || '-';
    const category = element.dataset.category || 'Uncategorized';
    const notes = element.dataset.notes || 'No additional notes';
    
    // Populate details
    document.getElementById('detailType').textContent = type.toUpperCase();
    document.getElementById('detailPayee').textContent = payee;
    document.getElementById('detailAmount').textContent = formatCurrency(amount, true);
    
    // Format date nicely
    if (date && date !== '-') {
        const dateObj = new Date(date);
        document.getElementById('detailDate').textContent = dateObj.toLocaleDateString('en-US', { 
            weekday: 'short', 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric' 
        });
    } else {
        document.getElementById('detailDate').textContent = '-';
    }
    
    document.getElementById('detailCategory').textContent = category;
    document.getElementById('detailNotes').textContent = notes;
    
    // Show details, hide others
    document.getElementById('detailsView').style.display = 'none';
    document.getElementById('transactionForm').style.display = 'none';
    document.getElementById('transactionDetails').style.display = 'block';
}

/**
 * Clears the transaction selection
 */
function clearSelection() {
    selectedTransactionId = null;
    
    document.querySelectorAll('.transaction-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Show empty state
    document.getElementById('detailsView').style.display = 'block';
    document.getElementById('transactionDetails').style.display = 'none';
    document.getElementById('transactionForm').style.display = 'none';
}

/**
 * Edits the currently selected transaction
 */
function editTransaction() {
    if (!selectedTransactionId) return;
    
    // Get the selected transaction element to access all data
    const selectedElement = document.querySelector('.transaction-item.selected');
    if (!selectedElement) return;
    
    const type = selectedElement.dataset.type;
    const payee = selectedElement.dataset.payee;
    const amount = selectedElement.dataset.amount;
    const date = selectedElement.dataset.date;
    const categoryId = selectedElement.dataset.categoryId;
    const notes = selectedElement.dataset.notes;
    
    // Populate form with current values
    document.getElementById('formType').value = type;
    document.getElementById('formPayee').value = payee;
    document.getElementById('formAmount').value = amount;
    document.getElementById('formDate').value = date;
    document.getElementById('formCategory').value = categoryId || '';
    document.getElementById('formNotes').value = notes || '';
    
    // Transform: Hide details, show form
    document.getElementById('transactionDetails').style.display = 'none';
    document.getElementById('transactionForm').style.display = 'block';
}

/**
 * Deletes the currently selected transaction
 */
function deleteTransaction() {
    if (!selectedTransactionId) return;
    
    if (confirm('Are you sure you want to delete this transaction?')) {
        // TODO: Implement AJAX delete
        console.log('Delete transaction:', selectedTransactionId);
        
        // For now, just clear selection
        clearSelection();
        
        // Remove from list (temporary until AJAX implemented)
        const selectedItem = document.querySelector('.transaction-item.selected');
        if (selectedItem) {
            selectedItem.remove();
            updateSummaryCounts();
        }
    }
}

/**
 * Saves the transaction (add or edit)
 */
function saveTransaction() {
    // Get form values
    const type = document.getElementById('formType').value;
    const payee = document.getElementById('formPayee').value.trim();
    const amount = document.getElementById('formAmount').value;
    const date = document.getElementById('formDate').value;
    const category = document.getElementById('formCategory').value;
    const notes = document.getElementById('formNotes').value.trim();
    
    // Validate
    if (!payee) {
        alert('Please enter a payee name');
        return;
    }
    if (!amount || parseFloat(amount) <= 0) {
        alert('Please enter a valid amount');
        return;
    }
    if (!date) {
        alert('Please select a date');
        return;
    }
    
    // TODO: Implement AJAX save
    console.log('Save transaction:', { type, payee, amount, date, category, notes });
    
    // For now, just show success and clear form
    alert('Transaction saved successfully!');
    cancelForm();
}

/**
 * Cancels the form and returns to appropriate view
 */
function cancelForm() {
    // If we were editing a transaction, go back to details view
    if (selectedTransactionId) {
        const selectedElement = document.querySelector('.transaction-item.selected');
        if (selectedElement) {
            // Re-populate details from the selected element
            selectTransaction(selectedElement, selectedTransactionId, selectedElement.dataset.type);
        } else {
            // If element not found, just clear
            clearSelection();
        }
    } else {
        // We were adding a new transaction, clear everything
        clearSelection();
    }
}

/**
 * Applies filters to the transaction list
 */
function applyFilters() {
    const searchText = document.getElementById('txSearch').value.toLowerCase();
    const typeFilter = document.getElementById('txType').value;
    const categoryFilter = document.getElementById('txCategory').value;
    
    const transactions = document.querySelectorAll('.transaction-item');
    
    transactions.forEach(item => {
        const payee = item.querySelector('.tx-payee')?.textContent.toLowerCase() || '';
        const type = item.dataset.type;
        const category = item.dataset.categoryId;
        
        let show = true;
        
        // Search filter
        if (searchText && !payee.includes(searchText)) {
            show = false;
        }
        
        // Type filter
        if (typeFilter !== 'all' && type !== typeFilter) {
            show = false;
        }
        
        // Category filter
        if (categoryFilter !== 'all' && category !== categoryFilter) {
            show = false;
        }
        
        // Also respect view filter
        if (show && transactionView !== 'all') {
            const dateStr = item.dataset.date;
            if (dateStr) {
                const txDate = new Date(dateStr);
                const now = new Date();
                
                if (transactionView === 'week') {
                    const weekStart = new Date(now);
                    weekStart.setDate(now.getDate() - now.getDay() + (viewOffset * 7));
                    const weekEnd = new Date(weekStart);
                    weekEnd.setDate(weekStart.getDate() + 6);
                    show = txDate >= weekStart && txDate <= weekEnd;
                } else if (transactionView === 'month') {
                    const targetMonth = now.getMonth() + viewOffset;
                    const targetYear = now.getFullYear() + Math.floor(targetMonth / 12);
                    const monthIndex = ((targetMonth % 12) + 12) % 12;
                    show = txDate.getMonth() === monthIndex && txDate.getFullYear() === targetYear;
                } else if (transactionView === 'year') {
                    const targetYear = now.getFullYear() + viewOffset;
                    show = txDate.getFullYear() === targetYear;
                }
            }
        }
        
        item.style.display = show ? '' : 'none';
    });
    
    updateSummaryCounts();
}

/**
 * Clears all filters
 */
function clearFilters() {
    document.getElementById('txSearch').value = '';
    document.getElementById('txType').value = 'all';
    document.getElementById('txCategory').value = 'all';
    
    applyFilters();
}

// =============================================================================
// INITIALIZATION
// =============================================================================

// Initialize view period text on page load
document.addEventListener('DOMContentLoaded', function() {
    if (document.getElementById('viewPeriod')) {
        updateViewPeriodText();
        filterTransactionsByView();
    }
});

// =============================================================================
// PAYEE QUICK-ADD FUNCTIONALITY
// =============================================================================

/**
 * Shows a simple prompt to add a new payee via AJAX
 */
function showPayeeQuickAdd() {
    const payeeName = prompt('Enter new payee/merchant name:');
    
    if (!payeeName || payeeName.trim() === '') {
        return; // User cancelled or entered nothing
    }
    
    const trimmedName = payeeName.trim();
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Send AJAX request to create payee
    fetch('/bank/payees/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `name=${encodeURIComponent(trimmedName)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add to dropdown
            const payeeDropdown = document.getElementById('formPayee');
            if (payeeDropdown) {
                const option = document.createElement('option');
                option.value = trimmedName;
                option.textContent = trimmedName;
                option.selected = true;
                payeeDropdown.appendChild(option);
            }
            
            alert(`Payee "${trimmedName}" created successfully!`);
        } else {
            alert(`Error: ${data.error || 'Failed to create payee'}`);
        }
    })
    .catch(error => {
        console.error('Error creating payee:', error);
        alert('Failed to create payee. Please try again.');
    });
}

/**
 * Shows a simple prompt to add a new category via AJAX
 */
function showCategoryQuickAdd() {
    const categoryName = prompt('Enter new category name:');
    
    if (!categoryName || categoryName.trim() === '') {
        return; // User cancelled or entered nothing
    }
    
    const trimmedName = categoryName.trim();
    
    // Get CSRF token
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // Send AJAX request to create category
    fetch('/bank/category/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: `name=${encodeURIComponent(trimmedName)}`
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add to dropdown
            const categoryDropdown = document.getElementById('formCategory');
            if (categoryDropdown) {
                const option = document.createElement('option');
                option.value = data.category.id;
                option.textContent = trimmedName;
                option.selected = true;
                categoryDropdown.appendChild(option);
            }
            
            alert(`Category "${trimmedName}" created successfully!`);
        } else {
            alert(`Error: ${data.error || 'Failed to create category'}`);
        }
    })
    .catch(error => {
        console.error('Error creating category:', error);
        alert('Failed to create category. Please try again.');
    });
}

// =============================================================================
// CUSTOM DROPDOWN FUNCTIONALITY
// =============================================================================

/**
 * Initialize custom dropdowns
 * Converts select elements with .custom-dropdown class into styled dropdowns
 */
function initCustomDropdowns() {
    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.custom-dropdown')) {
            document.querySelectorAll('.custom-dropdown-content.show').forEach(dropdown => {
                dropdown.classList.remove('show');
                const button = dropdown.previousElementSibling;
                if (button) button.classList.remove('active');
            });
        }
    });
}

/**
 * Toggle custom dropdown visibility
 * @param {string} dropdownId - The ID of the dropdown to toggle
 */
function toggleCustomDropdown(dropdownId) {
    const dropdown = document.getElementById(dropdownId);
    const button = dropdown.previousElementSibling;
    
    // Close all other dropdowns
    document.querySelectorAll('.custom-dropdown-content.show').forEach(dd => {
        if (dd.id !== dropdownId) {
            dd.classList.remove('show');
            const btn = dd.previousElementSibling;
            if (btn) btn.classList.remove('active');
        }
    });
    
    // Toggle this dropdown
    dropdown.classList.toggle('show');
    button.classList.toggle('active');
}

/**
 * Select an item from custom dropdown
 * @param {HTMLElement} element - The clicked link element
 * @param {string} dropdownId - The ID of the dropdown
 * @param {string} buttonId - The ID of the button to update
 * @param {string} hiddenInputId - The ID of the hidden input to update (optional)
 */
function selectCustomDropdownItem(element, dropdownId, buttonId, hiddenInputId = null) {
    const dropdown = document.getElementById(dropdownId);
    const button = document.getElementById(buttonId);
    const value = element.getAttribute('data-value');
    const text = element.textContent;
    
    // Update button text
    button.childNodes[0].textContent = text;
    
    // Update hidden input if provided
    if (hiddenInputId) {
        const hiddenInput = document.getElementById(hiddenInputId);
        if (hiddenInput) {
            hiddenInput.value = value;
        }
    }
    
    // Update selected state
    dropdown.querySelectorAll('a').forEach(a => a.classList.remove('selected'));
    element.classList.add('selected');
    
    // Close dropdown
    dropdown.classList.remove('show');
    button.classList.remove('active');
    
    // Prevent default link behavior
    return false;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    initCustomDropdowns();
    convertFilterSelectsToCustomDropdowns();
    initTacticalDatePickers();
});

// =============================================================================
// AUTO-CONVERT NATIVE SELECTS TO CUSTOM DROPDOWNS
// =============================================================================

/**
 * Automatically convert all .filter-select elements to custom tactical dropdowns
 */
function convertFilterSelectsToCustomDropdowns() {
    const selects = document.querySelectorAll('.filter-select');
    
    selects.forEach(select => {
        // Skip if already converted
        if (select.dataset.customDropdownConverted) return;
        
        // Create wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'custom-dropdown';
        
        // Create button
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'custom-dropdown-button';
        button.id = `${select.id}_button`;
        
        // Set initial text from selected option or placeholder
        const selectedOption = select.options[select.selectedIndex];
        button.textContent = selectedOption ? selectedOption.text : 'Select...';
        
        // Create dropdown content
        const content = document.createElement('div');
        content.className = 'custom-dropdown-content';
        content.id = `${select.id}_dropdown`;
        
        // Add all options as links
        Array.from(select.options).forEach(option => {
            const link = document.createElement('a');
            link.href = '#';
            link.textContent = option.text;
            link.dataset.value = option.value;
            
            if (option.selected) {
                link.classList.add('selected');
            }
            
            if (option.disabled) {
                link.style.opacity = '0.5';
                link.style.pointerEvents = 'none';
            }
            
            link.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Update the original select element
                select.value = this.dataset.value;
                
                // Trigger change event on original select
                const event = new Event('change', { bubbles: true });
                select.dispatchEvent(event);
                
                // Update button text
                button.childNodes[0].textContent = this.textContent;
                
                // Update selected state
                content.querySelectorAll('a').forEach(a => a.classList.remove('selected'));
                this.classList.add('selected');
                
                // Close dropdown
                content.classList.remove('show');
                button.classList.remove('active');
            });
            
            content.appendChild(link);
        });
        
        // Add click handler to button
        button.addEventListener('click', function(e) {
            e.stopPropagation();
            
            // Close all other dropdowns
            document.querySelectorAll('.custom-dropdown-content.show').forEach(dd => {
                if (dd.id !== content.id) {
                    dd.classList.remove('show');
                    const btn = dd.previousElementSibling;
                    if (btn) btn.classList.remove('active');
                }
            });
            
            // Toggle this dropdown
            content.classList.toggle('show');
            button.classList.toggle('active');
        });
        
        // Hide original select
        select.style.display = 'none';
        select.dataset.customDropdownConverted = 'true';
        
        // Insert custom dropdown
        select.parentNode.insertBefore(wrapper, select);
        wrapper.appendChild(button);
        wrapper.appendChild(content);
        wrapper.appendChild(select);
    });
}

/**
 * Initialize Flatpickr date pickers with tactical theme
 */
function initTacticalDatePickers() {
    // Check if Flatpickr is loaded
    if (typeof flatpickr === 'undefined') {
        console.error('Flatpickr library not loaded');
        return;
    }
    
    // Find all date inputs
    const dateInputs = document.querySelectorAll('input[type="date"]');
    
    console.log(`Found ${dateInputs.length} date inputs to initialize`);
    
    dateInputs.forEach(input => {
        // Skip if already initialized
        if (input._flatpickr) {
            console.log('Date input already initialized:', input.id || input.name);
            return;
        }
        
        // Get any existing value
        const existingValue = input.value;
        
        try {
            // Initialize Flatpickr
            const picker = flatpickr(input, {
                dateFormat: 'Y-m-d',
                defaultDate: existingValue || null,
                allowInput: true,
                clickOpens: true,
                
                // Prevent scroll on mobile
                disableMobile: false,
                
                // Position calendar properly
                position: 'auto',
                
                // Tactical theme configuration
                prevArrow: '◄',
                nextArrow: '►',
                
                // Format the display
                altInput: false,
                
                // Change month/year with dropdowns
                static: false,
                
                // Week numbers (optional - set to false if not needed)
                weekNumbers: false,
                
                // Callbacks for tactical effects
                onReady: function(selectedDates, dateStr, instance) {
                    // Add tactical class to calendar
                    if (instance.calendarContainer) {
                        instance.calendarContainer.classList.add('tactical-calendar');
                        console.log('Tactical calendar initialized for:', input.id || input.name);
                    }
                },
                
                onChange: function(selectedDates, dateStr, instance) {
                    // Trigger change event for existing listeners
                    const event = new Event('change', { bubbles: true });
                    input.dispatchEvent(event);
                },
                
                onOpen: function(selectedDates, dateStr, instance) {
                    console.log('Calendar opened');
                },
                
                onClose: function(selectedDates, dateStr, instance) {
                    console.log('Calendar closed');
                }
            });
            
            // Prevent default behavior on click
            input.addEventListener('click', function(e) {
                if (input._flatpickr) {
                    e.preventDefault();
                    e.stopPropagation();
                    input._flatpickr.open();
                }
            });
            
            console.log('Flatpickr initialized successfully for:', input.id || input.name);
        } catch (error) {
            console.error('Error initializing Flatpickr:', error);
        }
    });
}

