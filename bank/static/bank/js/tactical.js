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
    
    // Store full category and payee lists on page load
    storeFullCategoryList();
    storeFullPayeeList();
    
    // Track selection states (user vs auto)
    window.payeeSelectionState = 'none'; // 'none', 'user', 'auto'
    window.categorySelectionState = 'none'; // 'none', 'user', 'auto'
    
    // Setup payee add button toggle and category filtering
    const payeeSelect = document.getElementById('formPayee');
    if (payeeSelect) {
        // Initial state
        togglePayeeAddButton();
        
        let previousPayeeValue = '';
        
        // Listen for changes
        payeeSelect.addEventListener('change', function() {
            // Skip if we're in the middle of resetting the form
            if (window.isResettingForm) return;
            
            // Check if this is auto-selection from category filtering
            const isAutoSelect = window.isFilteringFromCategory;
            
            // Skip if this change was triggered by category filtering payees
            // But still update the tracking value
            if (isAutoSelect) {
                previousPayeeValue = payeeSelect.value;
                return;
            }
            
            togglePayeeAddButton();
            
            // If payee is unselected, clear state and restore full category list
            if (!payeeSelect.value) {
                clearPayeeSelectionState();
                hidePayeeError();
                hideCategoryError();
                restoreFullCategoryListKeepSelection();
                previousPayeeValue = '';
                return;
            }
            
            // Check if value actually changed
            const valueChanged = payeeSelect.value !== previousPayeeValue;
            
            // Check if state is changing from auto to user (clicking same value to turn green)
            const wasAutoSelected = window.payeeSelectionState === 'auto';
            
            previousPayeeValue = payeeSelect.value;
            
            // Mark as user-selected (not auto-selected)
            markPayeeUserSelected();
            
            // Filter if value changed OR if transitioning from auto to user selection
            if (valueChanged || wasAutoSelected) {
                // Payee is selected - filter categories based on payee
                filterCategoriesByPayee();
            }
        });
    }
    
    // Setup payee filtering when category changes
    const categorySelect = document.getElementById('formCategory');
    if (categorySelect) {
        let previousCategoryValue = '';
        
        categorySelect.addEventListener('change', function() {
            // Skip if we're in the middle of resetting the form
            if (window.isResettingForm) return;
            
            // Check if this is auto-selection from payee filtering
            const isAutoSelect = window.isFilteringFromPayee;
            
            // Skip if this change was triggered by payee filtering categories (auto-select)
            // But still update the tracking value
            if (isAutoSelect) {
                previousCategoryValue = categorySelect.value;
                return;
            }
            
            const categoryValue = categorySelect.value;
            const payeeSelect = document.getElementById('formPayee');
            const payeeValue = payeeSelect?.value;
            
            if (!categoryValue) {
                // User unselected category - clear state and restore full payee list
                clearCategorySelectionState();
                hideCategoryError();
                hidePayeeError();
                restoreFullPayeeListKeepSelection();
                previousCategoryValue = '';
                return;
            }
            
            // Check if value actually changed
            const valueChanged = categoryValue !== previousCategoryValue;
            
            // Check if state is changing from auto to user (clicking same value to turn green)
            const wasAutoSelected = window.categorySelectionState === 'auto';
            
            previousCategoryValue = categoryValue;
            
            // Mark as user-selected (not auto-selected)
            markCategoryUserSelected();
            
            // Filter if value changed OR if transitioning from auto to user selection
            if (valueChanged || wasAutoSelected) {
                // Category is selected - filter payees
                filterPayeesByCategory();
            }
        });
    }
    
    // Setup transaction type change listener to update payee/merchant label
    const formTypeSelect = document.getElementById('formType');
    if (formTypeSelect) {
        formTypeSelect.addEventListener('change', function() {
            updatePayeeMerchantLabel();
        });
    }
});

/**
 * Update the Payee/Merchant label based on transaction type
 */
function updatePayeeMerchantLabel() {
    const formTypeSelect = document.getElementById('formType');
    const label = document.getElementById('payeeMerchantLabel');
    const payeeSelect = document.getElementById('formPayee');
    const payeeButton = document.getElementById('formPayee_button');
    
    if (!formTypeSelect) return;
    
    const transactionType = formTypeSelect.value;
    let labelText, placeholderText;
    
    if (transactionType === 'income') {
        labelText = 'Payee Name';
        placeholderText = 'Select payee...';
    } else if (transactionType === 'expense') {
        labelText = 'Merchant Name';
        placeholderText = 'Select merchant...';
    } else {
        labelText = 'Payee / Merchant Name';
        placeholderText = 'Select payee or merchant...';
    }
    
    // Update label
    if (label) {
        label.textContent = labelText;
    }
    
    // Update placeholder option in select
    if (payeeSelect && payeeSelect.options && payeeSelect.options[0]) {
        payeeSelect.options[0].textContent = placeholderText;
    }
    
    // Update button text if nothing selected
    if (payeeButton && payeeButton.childNodes && payeeButton.childNodes[0]) {
        if (!payeeSelect || !payeeSelect.value) {
            payeeButton.childNodes[0].textContent = placeholderText;
        }
    }
}

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
 * Hides all panel views in the right panel
 */
function hideAllViews() {
    const views = [
        'detailsView',
        'transactionDetails',
        'transactionForm',
        'deleteConfirmView',
        'addPayeeView',
        'addCategoryView',
        'linkPayeeCategoryView'
    ];
    
    views.forEach(viewId => {
        const view = document.getElementById(viewId);
        if (view) {
            view.style.display = 'none';
        }
    });
}

/**
 * Selects a transaction and displays its details
 * @param {HTMLElement} element - The transaction item element
 * @param {number} id - Transaction ID
 * @param {string} type - Transaction type ('income' or 'expense')
 */
function selectTransaction(element, id, type) {
    // Store the selected transaction ID and type for delete/edit functions
    window.currentTransactionId = id;
    window.currentTransactionType = type;
    
    // Remove previous selection
    if (selectedTransaction) {
        selectedTransaction.classList.remove('selected');
    }
    element.classList.add('selected');
    selectedTransaction = element;
    selectedTransactionId = id;
    
    // Get transaction data from element attributes
    const payee = element.dataset.payee || 'Unknown';
    const date = element.dataset.date || '';
    const category = element.dataset.category || 'Uncategorized';
    const amount = element.dataset.amount || '0';
    const notes = element.dataset.notes || 'No additional notes';
    
    // Populate detail panel
    const detailType = document.getElementById('detailType');
    const detailDate = document.getElementById('detailDate');
    const detailPayee = document.getElementById('detailPayee');
    const detailCategory = document.getElementById('detailCategory');
    const detailAmount = document.getElementById('detailAmount');
    const detailNotes = document.getElementById('detailNotes');
    
    if (detailType) {
        detailType.textContent = type.toUpperCase();
        detailType.className = `detail-value ${type}`;
    }
    if (detailDate) detailDate.textContent = formatDateFromISO(date);
    if (detailPayee) detailPayee.textContent = payee;
    if (detailCategory) detailCategory.textContent = category;
    if (detailAmount) {
        detailAmount.textContent = `$${parseFloat(amount).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
        detailAmount.className = `detail-value large ${type}`;
    }
    if (detailNotes) detailNotes.textContent = notes;
    
    // CRITICAL: Hide ALL other panels first
    document.getElementById('detailsView').style.display = 'none';
    const deleteConfirmView = document.getElementById('deleteConfirmView');
    if (deleteConfirmView) deleteConfirmView.style.display = 'none';
    
    // Hide form and reset it (in that order)
    const transactionForm = document.getElementById('transactionForm');
    if (transactionForm && transactionForm.style.display !== 'none') {
        transactionForm.style.display = 'none';
        // Only reset if form was actually visible
        resetTransactionForm();
    } else if (transactionForm) {
        transactionForm.style.display = 'none';
    }
    
    // Show ONLY the transaction details panel
    document.getElementById('transactionDetails').style.display = 'block';
}

/**
 * Helper function to format date from YYYY-MM-DD to readable format
 */
function formatDateFromISO(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr + 'T00:00:00');
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    return `${days[date.getDay()]}, ${date.getDate()} ${months[date.getMonth()]} ${date.getFullYear()}`;
}

/**
 * Navigates to edit page for selected transaction
 * @param {number} id - Transaction ID (optional, uses stored if not provided)
 * @param {string} type - Transaction type (optional, uses stored if not provided)
 */
function editTransaction(id, type) {
    // Use stored values if parameters not provided
    id = id || window.currentTransactionId;
    type = type || window.currentTransactionType;
    
    if (!id || !type) {
        console.error('No transaction selected');
        return;
    }
    
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
 * Shows delete confirmation in the detail panel for selected transaction
 * @param {number} id - Transaction ID (optional, uses stored if not provided)
 * @param {string} type - Transaction type (optional, uses stored if not provided)
 */
function deleteTransaction(id, type) {
    // Use stored values if parameters not provided
    id = id || window.currentTransactionId;
    type = type || window.currentTransactionType;
    
    if (!id || !type) {
        console.error('No transaction selected');
        return;
    }
    
    // Store transaction info for deletion
    window.pendingDelete = { id, type };
    
    // Get transaction details from the selected transaction item
    const transactionItem = document.querySelector(`.transaction-item[data-id="${id}"]`);
    
    if (!transactionItem) {
        console.error('Transaction item not found for id:', id);
        return;
    }
    
    // Get data from element attributes
    const payee = transactionItem.dataset.payee || 'Unknown';
    const category = transactionItem.dataset.category || 'Uncategorized';
    const amount = transactionItem.dataset.amount || '0';
    const date = transactionItem.dataset.date || '';
    const notes = transactionItem.dataset.notes || 'No notes';
    
    // Format amount for display
    const formattedAmount = `$${parseFloat(amount).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}`;
    
    // Format date for display
    const formattedDate = formatDateFromISO(date);
    
    // Populate delete confirmation panel
    const deleteConfirmType = document.getElementById('deleteConfirmType');
    const deleteConfirmDate = document.getElementById('deleteConfirmDate');
    const deleteConfirmPayee = document.getElementById('deleteConfirmPayee');
    const deleteConfirmCategory = document.getElementById('deleteConfirmCategory');
    const deleteConfirmAmount = document.getElementById('deleteConfirmAmount');
    const deleteConfirmNotes = document.getElementById('deleteConfirmNotes');
    
    if (deleteConfirmType) {
        deleteConfirmType.textContent = type.toUpperCase();
        deleteConfirmType.className = `detail-value ${type}`;
    }
    if (deleteConfirmDate) deleteConfirmDate.textContent = formattedDate;
    if (deleteConfirmPayee) deleteConfirmPayee.textContent = payee;
    if (deleteConfirmCategory) deleteConfirmCategory.textContent = category;
    if (deleteConfirmAmount) {
        deleteConfirmAmount.textContent = formattedAmount;
        deleteConfirmAmount.className = `detail-value large ${type}`;
    }
    if (deleteConfirmNotes) deleteConfirmNotes.textContent = notes;
    
    // Hide details and form, show delete confirmation
    const detailsView = document.getElementById('detailsView');
    const transactionDetails = document.getElementById('transactionDetails');
    const transactionForm = document.getElementById('transactionForm');
    const deleteConfirmView = document.getElementById('deleteConfirmView');
    
    if (detailsView) detailsView.style.display = 'none';
    if (transactionDetails) transactionDetails.style.display = 'none';
    if (transactionForm) transactionForm.style.display = 'none';
    if (deleteConfirmView) deleteConfirmView.style.display = 'block';
}

/**
 * Cancels delete and returns to detail view
 */
function cancelDelete() {
    window.pendingDelete = null;
    
    // CRITICAL: Hide ALL panels first
    document.getElementById('detailsView').style.display = 'none';
    document.getElementById('transactionForm').style.display = 'none';
    const deleteConfirmView = document.getElementById('deleteConfirmView');
    if (deleteConfirmView) deleteConfirmView.style.display = 'none';
    
    // Show ONLY the transaction details panel
    document.getElementById('transactionDetails').style.display = 'block';
}

/**
 * Confirms and executes the deletion via AJAX
 */
function confirmDelete() {
    if (!window.pendingDelete) return;
    
    const { id, type } = window.pendingDelete;
    
    // Get CSRF token
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        csrfToken = cookieValue;
    }
    
    if (!csrfToken) {
        alert('Security token not found. Please reload the page and try again.');
        cancelDelete();
        return;
    }
    
    // Determine delete URL
    const url = type === 'income' 
        ? `/bank/income/${id}/delete/`
        : `/bank/expense/${id}/delete/`;
    
    // Submit delete request via AJAX
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove transaction from DOM with animation
            const transactionItem = document.querySelector(`.transaction-item[data-id="${id}"]`);
            if (transactionItem) {
                transactionItem.style.transition = 'all 0.3s ease';
                transactionItem.style.opacity = '0';
                transactionItem.style.transform = 'translateX(-20px)';
                setTimeout(() => {
                    transactionItem.remove();
                    // Update summary counts
                    updateSummaryCounts();
                }, 300);
            }
            
            // Hide delete confirmation and show empty state
            const deleteConfirmView = document.getElementById('deleteConfirmView');
            const detailsView = document.getElementById('detailsView');
            
            if (deleteConfirmView) deleteConfirmView.style.display = 'none';
            if (detailsView) detailsView.style.display = 'block';
            
            // Clear selection
            window.pendingDelete = null;
            selectedTransactionId = null;
            if (selectedTransaction) {
                selectedTransaction.classList.remove('selected');
                selectedTransaction = null;
            }
        } else {
            alert('Error: ' + (data.error || 'Failed to delete transaction'));
            cancelDelete();
        }
    })
    .catch(error => {
        console.error('Error deleting transaction:', error);
        alert('An error occurred while deleting the transaction');
        cancelDelete();
    });
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
    now.setHours(0, 0, 0, 0); // Normalize to start of day for comparisons
    
    // Track visible items for animation
    let visibleIndex = 0;
    
    transactions.forEach(item => {
        const dateStr = item.dataset.date; // Assumes transaction items have data-date attribute (YYYY-MM-DD)
        if (!dateStr) {
            item.style.display = ''; // Show if no date
            animateTransactionItem(item, visibleIndex++);
            return;
        }
        
        // Parse date string (YYYY-MM-DD) and normalize to start of day
        const txDate = new Date(dateStr + 'T00:00:00');
        let show = false;
        
        if (transactionView === 'all') {
            show = true;
        } else if (transactionView === 'week') {
            // Calculate week start (Sunday) and end (Saturday)
            const weekStart = new Date(now);
            weekStart.setDate(now.getDate() - now.getDay() + (viewOffset * 7));
            weekStart.setHours(0, 0, 0, 0);
            
            const weekEnd = new Date(weekStart);
            weekEnd.setDate(weekStart.getDate() + 6);
            weekEnd.setHours(23, 59, 59, 999);
            
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
    
    // Hide date group containers if all items within are hidden
    document.querySelectorAll('.transaction-date-group').forEach(group => {
        const items = group.querySelectorAll('.transaction-item');
        const hasVisible = Array.from(items).some(item => item.style.display !== 'none');
        group.style.display = hasVisible ? '' : 'none';
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
 * Resets all transaction form fields to their default empty state
 * and scrolls the form to the top
 */
function resetTransactionForm() {
    // Set flag to prevent change event handlers from running during reset
    window.isResettingForm = true;
    
    // Reset all form fields (original select elements)
    document.getElementById('formType').value = 'income'; // Default to income
    document.getElementById('formDate').value = new Date().toISOString().split('T')[0]; // Today's date
    document.getElementById('formPayee').value = '';
    document.getElementById('formAmount').value = '';
    document.getElementById('formCategory').value = '';
    document.getElementById('formNotes').value = '';
    
    // Update custom dropdown buttons to show placeholder text
    // formType
    const formTypeButton = document.getElementById('formType_button');
    if (formTypeButton) {
        const formTypeSelect = document.getElementById('formType');
        const selectedOption = formTypeSelect.options[formTypeSelect.selectedIndex];
        formTypeButton.childNodes[0].textContent = selectedOption ? selectedOption.text : 'Select...';
        
        // Update selected state in dropdown
        const formTypeDropdown = document.getElementById('formType_dropdown');
        if (formTypeDropdown) {
            formTypeDropdown.querySelectorAll('a').forEach(link => {
                link.classList.toggle('selected', link.dataset.value === formTypeSelect.value);
            });
        }
    }
    
    // formPayee
    const formPayeeButton = document.getElementById('formPayee_button');
    if (formPayeeButton) {
        formPayeeButton.childNodes[0].textContent = 'Select payee or merchant...';
        
        // Update selected state in dropdown
        const formPayeeDropdown = document.getElementById('formPayee_dropdown');
        if (formPayeeDropdown) {
            formPayeeDropdown.querySelectorAll('a').forEach(link => {
                link.classList.remove('selected');
            });
        }
    }
    
    // formCategory
    const formCategoryButton = document.getElementById('formCategory_button');
    if (formCategoryButton) {
        formCategoryButton.childNodes[0].textContent = 'Select category...';
        
        // Update selected state in dropdown
        const formCategoryDropdown = document.getElementById('formCategory_dropdown');
        if (formCategoryDropdown) {
            formCategoryDropdown.querySelectorAll('a').forEach(link => {
                link.classList.remove('selected');
            });
        }
    }
    
    // Scroll the form panel to the top
    const formPanel = document.getElementById('transactionForm');
    if (formPanel) {
        formPanel.scrollTop = 0;
    }
    
    // Also scroll the right panel container to top if it exists
    const rightPanel = document.querySelector('.split-right');
    if (rightPanel) {
        rightPanel.scrollTop = 0;
    }
    
    // Update payee add button visibility (show it since payee is now empty)
    togglePayeeAddButton();
    
    // Restore full category and payee lists since nothing is selected
    restoreFullCategoryList();
    restoreFullPayeeList();
    
    // Clear flag to allow change event handlers to run normally
    window.isResettingForm = false;
}

/**
 * Sync a custom dropdown's visible UI (button text and selected state)
 * to match the current value of its underlying <select> element.
 *
 * @param {string} selectId - The id of the original select element
 * @param {string} [placeholderText] - Optional placeholder to show when no option selected
 */
function syncCustomDropdown(selectId, placeholderText) {
    const select = document.getElementById(selectId);
    if (!select) return;

    const button = document.getElementById(`${selectId}_button`);
    const dropdown = document.getElementById(`${selectId}_dropdown`);

    // Ensure we have a selected option (fallback to empty option if value not found)
    let selectedOption = select.options[select.selectedIndex];
    if (!selectedOption) {
        const emptyIdx = Array.from(select.options).findIndex(o => o.value === '');
        if (emptyIdx >= 0) {
            select.selectedIndex = emptyIdx;
            selectedOption = select.options[select.selectedIndex];
        }
    }

    // Update button label
    if (button) {
        const text = (selectedOption && selectedOption.text) ? selectedOption.text : (placeholderText || 'Select...');
        if (button.childNodes && button.childNodes[0]) {
            button.childNodes[0].textContent = text;
        } else {
            button.textContent = text;
        }
    }

    // Update selected state in dropdown list
    if (dropdown) {
        dropdown.querySelectorAll('a').forEach(link => {
            const isSelected = link.dataset.value === select.value;
            if (isSelected) link.classList.add('selected'); else link.classList.remove('selected');
        });
    }
}

/**
 * Ensure the given value exists as an option on a select, adding it if missing.
 * If the custom dropdown has been created, also add a corresponding link.
 * Returns true if the option exists (either pre-existing or added), false otherwise.
 *
 * @param {string} selectId
 * @param {string} value
 * @param {string} text
 */
function ensureSelectOption(selectId, value, text) {
    const select = document.getElementById(selectId);
    if (!select) return false;

    // Does an option with this value already exist?
    let option = Array.from(select.options).find(o => o.value === value);
    if (!option) {
        // Add new option to the select
        option = document.createElement('option');
        option.value = value;
        option.text = text || value || '';
        select.appendChild(option);

        // If custom dropdown exists, add a matching link item
        const dropdown = document.getElementById(`${selectId}_dropdown`);
        if (dropdown) {
            const link = document.createElement('a');
            link.href = '#';
            link.textContent = option.text;
            link.dataset.value = option.value;

            link.addEventListener('click', function(e) {
                e.preventDefault();
                select.value = this.dataset.value;
                const event = new Event('change', { bubbles: true });
                select.dispatchEvent(event);

                const button = document.getElementById(`${selectId}_button`);
                if (button) {
                    if (button.childNodes && button.childNodes[0]) {
                        button.childNodes[0].textContent = this.textContent;
                    } else {
                        button.textContent = this.textContent;
                    }
                }

                dropdown.querySelectorAll('a').forEach(a => a.classList.remove('selected'));
                link.classList.add('selected');
                dropdown.classList.remove('show');
                const btnEl = document.getElementById(`${selectId}_button`);
                if (btnEl) btnEl.classList.remove('active');
            });

            dropdown.appendChild(link);
        }
    }

    return true;
}

// Quick-add inline handlers for transaction form
function showPayeeQuickAdd() {
    // Hide all other views
    hideAllViews();
    
    // Show the add payee view
    var view = document.getElementById('addPayeeView');
    if (view) {
        view.style.display = 'flex';
        var input = document.getElementById('quickPayeeName');
        if (input) {
            input.value = '';
            setTimeout(function() {
                input.focus();
            }, 100);
        }
    }
}

function cancelPayeeQuickAdd() {
    var view = document.getElementById('addPayeeView');
    if (view) {
        view.style.display = 'none';
    }
    
    var input = document.getElementById('quickPayeeName');
    if (input) input.value = '';
    
    // Return to form view
    var formView = document.getElementById('transactionForm');
    if (formView) {
        formView.style.display = 'flex';
    }
}

/**
 * Toggle the visibility of the payee add/link buttons based on selection
 */
function togglePayeeAddButton() {
    const payeeSelect = document.getElementById('formPayee');
    const addBtn = document.getElementById('payeeAddBtn');
    const linkBtn = document.getElementById('payeeLinkBtn');
    
    if (payeeSelect && addBtn && linkBtn) {
        // Show add button only when no payee is selected
        // Show link button only when a payee is selected
        if (payeeSelect.value === '') {
            addBtn.style.display = 'block';
            linkBtn.style.display = 'none';
        } else {
            addBtn.style.display = 'none';
            linkBtn.style.display = 'block';
        }
    }
}

// =============================================================================
// CATEGORY FILTERING BY PAYEE
// =============================================================================

// Global storage for full category list
let fullCategoryList = [];

/**
 * Store the full category list on page load
 */
function storeFullCategoryList() {
    const categorySelect = document.getElementById('formCategory');
    if (!categorySelect) return;
    
    fullCategoryList = [];
    Array.from(categorySelect.options).forEach(option => {
        if (option.value) { // Skip empty placeholder option
            fullCategoryList.push({
                value: option.value,
                text: option.textContent
            });
        }
    });
}

/**
 * Filter category dropdown based on selected payee's linked categories
 * If payee has linked categories, show only those
 * If no linked categories, show full list
 */
function filterCategoriesByPayee() {
    const payeeSelect = document.getElementById('formPayee');
    const categorySelect = document.getElementById('formCategory');
    
    if (!payeeSelect || !categorySelect) return;
    
    const payeeId = payeeSelect.value.trim();
    
    // If no payee selected, restore full category list
    if (!payeeId) {
        restoreFullCategoryList();
        return;
    }
    
    // Get the payee name from the selected option
    const selectedOption = payeeSelect.options[payeeSelect.selectedIndex];
    if (!selectedOption || !selectedOption.textContent) {
        restoreFullCategoryList();
        return;
    }
    
    const payeeName = selectedOption.textContent.trim();
    
    // Get URL template and replace placeholder
    const urlData = document.getElementById('tacticalUrlData');
    if (!urlData) {
        console.error('URL data not found');
        restoreFullCategoryList();
        return;
    }
    
    const urlTemplate = urlData.dataset.getPayeeCategoriesUrl;
    if (!urlTemplate) {
        console.error('Get payee categories URL not found');
        restoreFullCategoryList();
        return;
    }
    
    const url = urlTemplate.replace('PAYEE_NAME', encodeURIComponent(payeeName));
    
    // Fetch linked categories for this payee
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.has_linked_categories && data.categories.length > 0) {
                    // Payee has linked categories - show only those
                    hideCategoryError();
                    updateCategoryList(data.categories, true);
                } else {
                    // No linked categories - show error and keep dropdown empty
                    showCategoryError('This payee has no linked categories. Please create a link.');
                    clearCategoryDropdown();
                }
            } else {
                console.error('Error fetching payee categories:', data.error);
                showCategoryError('Error loading categories. Please try again.');
                clearCategoryDropdown();
            }
        })
        .catch(error => {
            console.error('Error fetching payee categories:', error);
            showCategoryError('Error loading categories. Please try again.');
            clearCategoryDropdown();
        });
}

/**
 * Update the category dropdown with specific categories
 * @param {Array} categories - Array of category objects {id, name} or {value, text}
 * @param {boolean} isFiltered - Whether this is a filtered list
 */
function updateCategoryList(categories, isFiltered = false) {
    const categorySelect = document.getElementById('formCategory');
    if (!categorySelect) return;
    
    // Always hide pills, always show dropdown
    const quickSelectContainer = document.getElementById('categoryQuickSelect');
    const dropdownContainer = document.getElementById('categoryDropdownContainer');
    if (quickSelectContainer) quickSelectContainer.style.display = 'none';
    if (dropdownContainer) dropdownContainer.style.display = 'flex';
    
    // Store current value
    const currentValue = categorySelect.value;
    
    // Clear and rebuild options
    categorySelect.innerHTML = '<option value="">Select category...</option>';
    
    // Add categories to select
    categories.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.id || cat.value;
        option.textContent = cat.name || cat.text;
        categorySelect.appendChild(option);
    });
    
    // Auto-select if only one category and this is a filtered list
    // BUT only if category is not already selected (respect existing user selection)
    if (isFiltered && categories.length === 1 && !currentValue) {
        // Set flag to prevent category change from triggering payee filtering
        window.isFilteringFromPayee = true;
        
        categorySelect.value = categories[0].id || categories[0].value;
        
        // Trigger change event to update any dependent logic (but prevent circular filtering)
        const event = new Event('change', { bubbles: true });
        categorySelect.dispatchEvent(event);
        
        // Mark as auto-selected
        markCategoryAutoSelected();
        
        // Clear flag after a short delay
        setTimeout(function() {
            window.isFilteringFromPayee = false;
        }, 10);
    } else if (isFiltered && currentValue) {
        // Category already selected - keep it if it's in the filtered list
        const categoryValue = (cat) => (cat.id || cat.value).toString();
        const categoryExists = categories.some(c => categoryValue(c) === currentValue);
        if (categoryExists) {
            categorySelect.value = currentValue;
            // Preserve the current selection state (don't change user to auto)
            if (window.categorySelectionState === 'user') {
                markCategoryUserSelected();
            } else if (window.categorySelectionState === 'auto') {
                markCategoryAutoSelected();
            }
        } else {
            // Current selection not in filtered list - reset
            categorySelect.value = '';
            clearCategorySelectionState();
        }
    } else if (isFiltered) {
        // Multiple categories in filtered list - reset to empty to force user selection
        categorySelect.value = '';
        clearCategorySelectionState();
    } else {
        // Restoring full list (payee has no linked categories) - always reset to empty
        categorySelect.value = '';
        clearCategorySelectionState();
    }
    
    // Rebuild custom dropdown to reflect changes
    rebuildCustomDropdown('formCategory');
    
    // Update the button text to match the current selection
    const categoryButton = document.getElementById('formCategory_button');
    if (categoryButton && categoryButton.childNodes && categoryButton.childNodes[0]) {
        if (categorySelect.value) {
            const selectedOption = categorySelect.options[categorySelect.selectedIndex];
            if (selectedOption) {
                categoryButton.childNodes[0].textContent = selectedOption.text;
            }
        } else {
            categoryButton.childNodes[0].textContent = 'Select category...';
        }
    }
}

/**
 * Restore the full category list
 */
function restoreFullCategoryList() {
    if (fullCategoryList.length > 0) {
        hideCategoryError();
        updateCategoryList(fullCategoryList, false);
    }
}

/**
 * Restore the full category list while preserving current selection
 */
function restoreFullCategoryListKeepSelection() {
    const categorySelect = document.getElementById('formCategory');
    if (!categorySelect || fullCategoryList.length === 0) return;
    
    const currentValue = categorySelect.value;
    
    hideCategoryError();
    
    // Rebuild the dropdown with full list
    categorySelect.innerHTML = '<option value="">Select category...</option>';
    fullCategoryList.forEach(cat => {
        const option = document.createElement('option');
        option.value = cat.id || cat.value;
        option.textContent = cat.name || cat.text;
        categorySelect.appendChild(option);
    });
    
    // Restore previous selection if it exists in the full list
    if (currentValue) {
        categorySelect.value = currentValue;
    }
    
    // Rebuild custom dropdown
    rebuildCustomDropdown('formCategory');
    
    // Preserve the selection state color (AFTER rebuild)
    if (currentValue && window.categorySelectionState === 'user') {
        markCategoryUserSelected();
    } else if (currentValue && window.categorySelectionState === 'auto') {
        markCategoryAutoSelected();
    }
    
    // Update button text
    const categoryButton = document.getElementById('formCategory_button');
    if (categoryButton && categoryButton.childNodes && categoryButton.childNodes[0]) {
        if (categorySelect.value) {
            const selectedOption = categorySelect.options[categorySelect.selectedIndex];
            if (selectedOption) {
                categoryButton.childNodes[0].textContent = selectedOption.text;
            }
        } else {
            categoryButton.childNodes[0].textContent = 'Select category...';
        }
    }
}

/**
 * Show category error message
 */
function showCategoryError(message) {
    const errorDiv = document.getElementById('categoryErrorMsg');
    if (errorDiv) {
        if (message) {
            errorDiv.querySelector('strong').nextSibling.textContent = ' - ' + message + ' ';
        }
        errorDiv.style.display = 'block';
    }
}

/**
 * Hide category error message
 */
function hideCategoryError() {
    const errorDiv = document.getElementById('categoryErrorMsg');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

/**
 * Clear category dropdown (keep only placeholder)
 */
function clearCategoryDropdown() {
    const categorySelect = document.getElementById('formCategory');
    if (categorySelect) {
        categorySelect.innerHTML = '<option value="">Select category...</option>';
        categorySelect.value = '';
        rebuildCustomDropdown('formCategory');
        
        // Update button text
        const categoryButton = document.getElementById('formCategory_button');
        if (categoryButton && categoryButton.childNodes && categoryButton.childNodes[0]) {
            categoryButton.childNodes[0].textContent = 'Select category...';
        }
    }
}

/**
 * Set selection state styling for a field
 * @param {string} fieldId - 'formPayee' or 'formCategory'
 * @param {string} state - 'auto', 'user', 'error', or 'none'
 */
function setSelectionState(fieldId, state) {
    const select = document.getElementById(fieldId);
    const button = document.getElementById(`${fieldId}_button`);
    
    if (!select || !button) return;
    
    // Track state globally
    if (fieldId === 'formPayee') {
        window.payeeSelectionState = state;
    } else if (fieldId === 'formCategory') {
        window.categorySelectionState = state;
    }
    
    // Remove all state classes
    select.classList.remove('auto-selected', 'user-selected', 'has-error');
    button.classList.remove('auto-selected', 'user-selected', 'has-error');
    
    // Add appropriate class
    if (state === 'auto') {
        select.classList.add('auto-selected');
        button.classList.add('auto-selected');
    } else if (state === 'user') {
        select.classList.add('user-selected');
        button.classList.add('user-selected');
    } else if (state === 'error') {
        select.classList.add('has-error');
        button.classList.add('has-error');
    }
}

/**
 * Mark payee as auto-selected
 */
function markPayeeAutoSelected() {
    setSelectionState('formPayee', 'auto');
}

/**
 * Mark payee as user-selected
 */
function markPayeeUserSelected() {
    setSelectionState('formPayee', 'user');
}

/**
 * Mark category as auto-selected
 */
function markCategoryAutoSelected() {
    setSelectionState('formCategory', 'auto');
}

/**
 * Mark category as user-selected
 */
function markCategoryUserSelected() {
    setSelectionState('formCategory', 'user');
}

/**
 * Clear selection state styling
 */
function clearPayeeSelectionState() {
    setSelectionState('formPayee', 'none');
}

function clearCategorySelectionState() {
    setSelectionState('formCategory', 'none');
}

/**
 * Show payee error message
 */
function showPayeeError(message) {
    const errorDiv = document.getElementById('payeeErrorMsg');
    if (errorDiv) {
        if (message) {
            errorDiv.querySelector('strong').nextSibling.textContent = ' - ' + message + ' ';
        }
        errorDiv.style.display = 'block';
    }
}

/**
 * Hide payee error message
 */
function hidePayeeError() {
    const errorDiv = document.getElementById('payeeErrorMsg');
    if (errorDiv) {
        errorDiv.style.display = 'none';
    }
}

/**
 * Clear payee dropdown (keep only placeholder)
 */
function clearPayeeDropdown() {
    const payeeSelect = document.getElementById('formPayee');
    if (payeeSelect) {
        payeeSelect.innerHTML = '<option value="">Select payee or merchant...</option>';
        payeeSelect.value = '';
        rebuildCustomDropdown('formPayee');
        
        // Update button text
        const payeeButton = document.getElementById('formPayee_button');
        if (payeeButton && payeeButton.childNodes && payeeButton.childNodes[0]) {
            payeeButton.childNodes[0].textContent = 'Select payee or merchant...';
        }
    }
}

/**
 * Rebuild custom dropdown after options change
 * @param {string} selectId - The ID of the select element
 */
function rebuildCustomDropdown(selectId) {
    const select = document.getElementById(selectId);
    if (!select) return;
    
    const dropdown = document.getElementById(`${selectId}_dropdown`);
    if (!dropdown) return;
    
    // Clear existing dropdown links
    dropdown.innerHTML = '';
    
    // Rebuild from current select options
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
            select.value = this.dataset.value;
            const event = new Event('change', { bubbles: true });
            select.dispatchEvent(event);
            
            const button = document.getElementById(`${selectId}_button`);
            if (button) {
                if (button.childNodes && button.childNodes[0]) {
                    button.childNodes[0].textContent = this.textContent;
                } else {
                    button.textContent = this.textContent;
                }
            }
            
            dropdown.querySelectorAll('a').forEach(a => a.classList.remove('selected'));
            link.classList.add('selected');
            dropdown.classList.remove('show');
            const btnEl = document.getElementById(`${selectId}_button`);
            if (btnEl) btnEl.classList.remove('active');
        });
        
        dropdown.appendChild(link);
    });
}

/**
 * Store full payee list for later restoration
 */
let fullPayeeList = [];

function storeFullPayeeList() {
    const payeeSelect = document.getElementById('formPayee');
    if (!payeeSelect) return;
    
    fullPayeeList = [];
    Array.from(payeeSelect.options).forEach(option => {
        if (option.value) { // Skip empty placeholder option
            fullPayeeList.push({
                value: option.value,
                text: option.textContent
            });
        }
    });
}

/**
 * Filter payee dropdown based on selected category's linked payees
 * If category has linked payees, show only those
 * If no linked payees, show full list
 */
function filterPayeesByCategory() {
    const categorySelect = document.getElementById('formCategory');
    const payeeSelect = document.getElementById('formPayee');
    
    if (!categorySelect || !payeeSelect) return;
    
    const categoryId = categorySelect.value;
    
    if (!categoryId) {
        restoreFullPayeeList();
        return;
    }
    
    // Get URL from data attribute
    const urlData = document.getElementById('tacticalUrlData');
    if (!urlData) {
        console.error('URL data not found');
        restoreFullPayeeList();
        return;
    }
    
    const getCategoryPayeesUrl = urlData.dataset.getCategoryPayeesUrl;
    if (!getCategoryPayeesUrl) {
        console.error('Category payees URL not found');
        restoreFullPayeeList();
        return;
    }
    
    // Replace placeholder with actual category ID
    const url = getCategoryPayeesUrl.replace('0', categoryId);
    
    // Fetch linked payees
    fetch(url)
        .then(response => response.json())
        .then(data => {
            if (data.success && data.has_linked_payees && data.payees.length > 0) {
                // Filter to show only linked payees
                hidePayeeError();
                updatePayeeList(data.payees, true);
            } else {
                // No linked payees - show error and keep dropdown empty
                showPayeeError('This category has no linked payees. Please create a link.');
                clearPayeeDropdown();
            }
        })
        .catch(error => {
            console.error('Error fetching category payees:', error);
            showPayeeError('Error loading payees. Please try again.');
            clearPayeeDropdown();
        });
}

/**
 * Update payee dropdown with new list
 * @param {Array} payees - Array of payee objects {id, name} or {value, text}
 * @param {boolean} isFiltered - Whether this is a filtered list
 */
function updatePayeeList(payees, isFiltered) {
    const payeeSelect = document.getElementById('formPayee');
    if (!payeeSelect) return;
    
    // Store current value
    const currentValue = payeeSelect.value;
    
    // Clear and rebuild options
    payeeSelect.innerHTML = '<option value="">Select Payee...</option>';
    
    payees.forEach(payee => {
        const option = document.createElement('option');
        // Use NAME as value to match the original template format
        option.value = payee.name || payee.text;
        option.textContent = payee.name || payee.text;
        payeeSelect.appendChild(option);
    });
    
    // Auto-select if only one payee and this is a filtered list
    // BUT only if payee is not already selected (respect existing user selection)
    if (isFiltered && payees.length === 1 && !currentValue) {
        // Set flag to prevent payee change from triggering category filtering
        window.isFilteringFromCategory = true;
        
        payeeSelect.value = payees[0].name || payees[0].text;
        
        // Trigger change event to update any dependent logic
        const event = new Event('change', { bubbles: true });
        payeeSelect.dispatchEvent(event);
        
        // Mark as auto-selected
        markPayeeAutoSelected();
        
        // Clear flag after a short delay to allow event to complete
        setTimeout(function() {
            window.isFilteringFromCategory = false;
        }, 10);
    } else if (isFiltered && currentValue) {
        // Payee already selected - keep it if it's in the filtered list
        const payeeValue = (p) => (p.name || p.text);
        const payeeExists = payees.some(p => payeeValue(p) === currentValue);
        if (payeeExists) {
            payeeSelect.value = currentValue;
            // Preserve the current selection state (don't change user to auto)
            if (window.payeeSelectionState === 'user') {
                markPayeeUserSelected();
            } else if (window.payeeSelectionState === 'auto') {
                markPayeeAutoSelected();
            }
        } else {
            // Current selection not in filtered list - reset and check for auto-select
            payeeSelect.value = '';
            clearPayeeSelectionState();
            
            // If only one payee in new filtered list, auto-select it
            if (payees.length === 1) {
                window.isFilteringFromCategory = true;
                
                payeeSelect.value = payees[0].name || payees[0].text;
                
                const event = new Event('change', { bubbles: true });
                payeeSelect.dispatchEvent(event);
                
                markPayeeAutoSelected();
                
                setTimeout(function() {
                    window.isFilteringFromCategory = false;
                }, 10);
            }
        }
    } else if (isFiltered) {
        // Multiple payees in filtered list - reset to empty to force user selection
        payeeSelect.value = '';
        clearPayeeSelectionState();
    } else {
        // Restoring full list (category has no linked payees) - always reset to empty
        payeeSelect.value = '';
        clearPayeeSelectionState();
    }
    
    // Rebuild custom dropdown to reflect changes
    rebuildCustomDropdown('formPayee');
    
    // Update the button text to match the current selection
    const payeeButton = document.getElementById('formPayee_button');
    if (payeeButton && payeeButton.childNodes && payeeButton.childNodes[0]) {
        if (payeeSelect.value) {
            const selectedOption = payeeSelect.options[payeeSelect.selectedIndex];
            if (selectedOption) {
                payeeButton.childNodes[0].textContent = selectedOption.text;
            }
        } else {
            payeeButton.childNodes[0].textContent = 'Select payee or merchant...';
        }
    }
}

/**
 * Restore full payee list (remove filtering)
 */
function restoreFullPayeeList() {
    if (fullPayeeList.length > 0) {
        hidePayeeError();
        updatePayeeList(fullPayeeList, false);
    }
}

/**
 * Restore the full payee list while preserving current selection
 */
function restoreFullPayeeListKeepSelection() {
    const payeeSelect = document.getElementById('formPayee');
    if (!payeeSelect || fullPayeeList.length === 0) return;
    
    const currentValue = payeeSelect.value;
    const currentState = window.payeeSelectionState;
    
    hidePayeeError();
    
    // Rebuild the dropdown with full list
    payeeSelect.innerHTML = '<option value="">Select payee or merchant...</option>';
    fullPayeeList.forEach(payee => {
        const option = document.createElement('option');
        // Use NAME as value to match template format (value and text are the same)
        option.value = payee.value || payee.text;
        option.textContent = payee.value || payee.text;
        payeeSelect.appendChild(option);
    });
    
    // Restore previous selection if it exists in the full list
    if (currentValue) {
        payeeSelect.value = currentValue;
    }
    
    // Rebuild custom dropdown
    rebuildCustomDropdown('formPayee');
    
    // Preserve the selection state color (AFTER rebuild)
    if (currentValue && currentState === 'user') {
        markPayeeUserSelected();
    } else if (currentValue && currentState === 'auto') {
        markPayeeAutoSelected();
    }
    
    // Update button text
    const payeeButton = document.getElementById('formPayee_button');
    if (payeeButton && payeeButton.childNodes && payeeButton.childNodes[0]) {
        if (payeeSelect.value) {
            const selectedOption = payeeSelect.options[payeeSelect.selectedIndex];
            if (selectedOption) {
                payeeButton.childNodes[0].textContent = selectedOption.text;
            }
        } else {
            payeeButton.childNodes[0].textContent = 'Select payee or merchant...';
        }
    }
}

function submitPayeeQuickAdd() {
    var input = document.getElementById('quickPayeeName');
    if (!input) return;
    var name = input.value.trim();
    if (!name) {
        input.focus();
        return;
    }

    // Get URLs from data attributes
    var urlData = document.getElementById('tacticalUrlData');
    if (!urlData) {
        console.error('URL data not found');
        return;
    }
    var addPayeeUrl = urlData.dataset.addPayeeUrl;

    // Get CSRF token
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        var cookieValue = document.cookie.split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        csrfToken = cookieValue;
    }

    // Determine transaction type from the form
    var formType = document.getElementById('formType');
    var transactionType = formType ? formType.value : 'expense';
    
    // Get optional category
    var categorySelect = document.getElementById('quickPayeeCategory');
    var categoryId = categorySelect ? categorySelect.value : '';

    // Create form data
    var formData = new FormData();
    formData.append('name', name);
    formData.append('transaction_type', transactionType);
    if (categoryId) {
        formData.append('category_id', categoryId);
    }

    // Call API
    fetch(addPayeeUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Use ensureSelectOption to add the option to both select and custom dropdown
            ensureSelectOption('formPayee', data.payee.name, data.payee.name);
            
            // Set the select value
            var select = document.getElementById('formPayee');
            if (select) {
                select.value = data.payee.name;
            }
            
            // Sync the custom dropdown UI to update the button text
            syncCustomDropdown('formPayee', 'Select payee or merchant...');

            // Hide quick-add and return to form
            cancelPayeeQuickAdd();
        } else {
            // Show error message
            alert(data.error || 'Failed to add payee');
            input.focus();
        }
    })
    .catch(error => {
        console.error('Error adding payee:', error);
        alert('An error occurred while adding payee');
        input.focus();
    });
}

function showCategoryQuickAdd() {
    // Hide all other views
    hideAllViews();
    
    // Show the add category view
    var view = document.getElementById('addCategoryView');
    if (view) {
        view.style.display = 'flex';
        var input = document.getElementById('quickCategoryName');
        if (input) {
            input.value = '';
            setTimeout(function() {
                input.focus();
            }, 100);
        }
    }
}

/**
 * Show category quick-add from within payee quick-add (navigation)
 * Stores the payee name temporarily so we can return
 */
function showCategoryQuickAddFromPayee() {
    // Store the payee name temporarily
    var payeeInput = document.getElementById('quickPayeeName');
    var payeeCategorySelect = document.getElementById('quickPayeeCategory');
    if (payeeInput) {
        // Store in sessionStorage so we can restore it
        sessionStorage.setItem('tempPayeeName', payeeInput.value);
        if (payeeCategorySelect) {
            sessionStorage.setItem('tempPayeeCategoryValue', payeeCategorySelect.value);
        }
    }
    
    // Hide payee view and show category view
    var payeeView = document.getElementById('addPayeeView');
    var categoryView = document.getElementById('addCategoryView');
    
    if (payeeView) payeeView.style.display = 'none';
    if (categoryView) {
        categoryView.style.display = 'flex';
        var input = document.getElementById('quickCategoryName');
        if (input) {
            input.value = '';
            setTimeout(function() {
                input.focus();
            }, 100);
        }
    }
    
    // Set a flag so we know to return to payee view after adding category
    sessionStorage.setItem('returnToPayeeAdd', 'true');
}

function cancelCategoryQuickAdd() {
    var view = document.getElementById('addCategoryView');
    if (view) {
        view.style.display = 'none';
    }
    
    var input = document.getElementById('quickCategoryName');
    if (input) input.value = '';
    
    // Check if we should return to payee add view
    var returnToPayeeAdd = sessionStorage.getItem('returnToPayeeAdd');
    
    if (returnToPayeeAdd === 'true') {
        // Return to payee add view
        var payeeView = document.getElementById('addPayeeView');
        if (payeeView) {
            payeeView.style.display = 'flex';
            
            // Restore the payee data
            var payeeInput = document.getElementById('quickPayeeName');
            var payeeCategorySelect = document.getElementById('quickPayeeCategory');
            
            if (payeeInput) {
                payeeInput.value = sessionStorage.getItem('tempPayeeName') || '';
            }
            if (payeeCategorySelect) {
                payeeCategorySelect.value = sessionStorage.getItem('tempPayeeCategoryValue') || '';
                syncCustomDropdown('quickPayeeCategory', 'No default category');
            }
            
            // Focus the payee input
            setTimeout(function() {
                if (payeeInput) payeeInput.focus();
            }, 100);
        }
        
        // Clear session storage
        sessionStorage.removeItem('returnToPayeeAdd');
        sessionStorage.removeItem('tempPayeeName');
        sessionStorage.removeItem('tempPayeeCategoryValue');
    } else {
        // Check if we should return to payee-category link view
        var returnToLink = sessionStorage.getItem('returnToPayeeCategoryLink');
        
        if (returnToLink === 'true') {
            // Return to link view
            var linkView = document.getElementById('linkPayeeCategoryView');
            if (linkView) {
                linkView.style.display = 'flex';
                
                // Restore category selection
                var linkCategorySelect = document.getElementById('linkCategorySelect');
                if (linkCategorySelect) {
                    linkCategorySelect.value = sessionStorage.getItem('tempLinkCategoryValue') || '';
                    syncCustomDropdown('linkCategorySelect', 'Select category to link...');
                }
            }
            
            // Clear session storage
            sessionStorage.removeItem('returnToPayeeCategoryLink');
            sessionStorage.removeItem('tempLinkCategoryValue');
        } else {
            // Return to form view
            var formView = document.getElementById('transactionForm');
            if (formView) {
                formView.style.display = 'flex';
            }
        }
    }
}

function submitCategoryQuickAdd() {
    var input = document.getElementById('quickCategoryName');
    if (!input) return;
    var name = input.value.trim();
    if (!name) {
        input.focus();
        return;
    }

    // Get URLs from data attributes
    var urlData = document.getElementById('tacticalUrlData');
    if (!urlData) {
        console.error('URL data not found');
        return;
    }
    var addCategoryUrl = urlData.dataset.addCategoryUrl;

    // Get CSRF token
    var csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        var cookieValue = document.cookie.split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        csrfToken = cookieValue;
    }

    // Determine category type from the form
    var formType = document.getElementById('formType');
    var categoryType = formType ? formType.value : 'expense';

    // Create form data
    var formData = new FormData();
    formData.append('name', name);
    formData.append('category_type', categoryType);

    // Call API
    fetch(addCategoryUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Add to form category dropdown
            ensureSelectOption('formCategory', String(data.category.id), data.category.name);
            
            // Check if we should return to payee add view
            var returnToPayeeAdd = sessionStorage.getItem('returnToPayeeAdd');
            
            if (returnToPayeeAdd === 'true') {
                // Add category to the payee quick-add dropdown
                ensureSelectOption('quickPayeeCategory', String(data.category.id), data.category.name);
                
                // Hide category view and show payee view
                var categoryView = document.getElementById('addCategoryView');
                var payeeView = document.getElementById('addPayeeView');
                
                if (categoryView) categoryView.style.display = 'none';
                if (payeeView) {
                    payeeView.style.display = 'flex';
                    
                    // Restore the payee name and select the new category
                    var payeeInput = document.getElementById('quickPayeeName');
                    var payeeCategorySelect = document.getElementById('quickPayeeCategory');
                    
                    if (payeeInput) {
                        payeeInput.value = sessionStorage.getItem('tempPayeeName') || '';
                    }
                    if (payeeCategorySelect) {
                        payeeCategorySelect.value = data.category.id;
                        // Sync custom dropdown if it exists
                        syncCustomDropdown('quickPayeeCategory', 'No default category');
                    }
                    
                    // Focus the payee input
                    setTimeout(function() {
                        if (payeeInput) payeeInput.focus();
                    }, 100);
                }
                
                // Clear the session storage
                sessionStorage.removeItem('returnToPayeeAdd');
                sessionStorage.removeItem('tempPayeeName');
                sessionStorage.removeItem('tempPayeeCategoryValue');
            } else {
                // Check if we should return to payee-category link view
                var returnToLink = sessionStorage.getItem('returnToPayeeCategoryLink');
                
                if (returnToLink === 'true') {
                    // Add category to link dropdown
                    ensureSelectOption('linkCategorySelect', String(data.category.id), data.category.name);
                    
                    // Hide category view and show link view
                    var categoryView = document.getElementById('addCategoryView');
                    var linkView = document.getElementById('linkPayeeCategoryView');
                    
                    if (categoryView) categoryView.style.display = 'none';
                    if (linkView) {
                        linkView.style.display = 'flex';
                        
                        // Select the new category
                        var linkCategorySelect = document.getElementById('linkCategorySelect');
                        if (linkCategorySelect) {
                            linkCategorySelect.value = data.category.id;
                            syncCustomDropdown('linkCategorySelect', 'Select category to link...');
                        }
                    }
                    
                    // Clear session storage
                    sessionStorage.removeItem('returnToPayeeCategoryLink');
                    sessionStorage.removeItem('tempLinkCategoryValue');
                } else {
                    // Normal flow: set in form and return to form view
                    var select = document.getElementById('formCategory');
                    if (select) {
                        select.value = data.category.id;
                    }
                    
                    // Sync the custom dropdown UI to update the button text
                    syncCustomDropdown('formCategory', 'Select category...');

                    // Hide quick-add and return to form
                    cancelCategoryQuickAdd();
                }
            }
        } else {
            // Show error message
            alert(data.error || 'Failed to add category');
            input.focus();
        }
    })
    .catch(error => {
        console.error('Error adding category:', error);
        alert('An error occurred while adding category');
        input.focus();
    });
}

// =============================================================================
// PAYEE-CATEGORY LINKING
// =============================================================================

/**
 * Show the link category to payee modal
 */
function showPayeeCategoryLink() {
    const payeeSelect = document.getElementById('formPayee');
    const payeeName = payeeSelect ? payeeSelect.value : '';
    
    if (!payeeName) {
        alert('Please select a payee first');
        return;
    }
    
    // Hide all views and show link view
    hideAllViews();
    
    const linkView = document.getElementById('linkPayeeCategoryView');
    const linkPayeeNameDisplay = document.getElementById('linkPayeeName');
    const linkCategorySelect = document.getElementById('linkCategorySelect');
    
    if (linkView) {
        linkView.style.display = 'flex';
        
        // Display the payee name
        if (linkPayeeNameDisplay) {
            linkPayeeNameDisplay.textContent = payeeName;
        }
        
        // Reset category selection
        if (linkCategorySelect) {
            linkCategorySelect.value = '';
            syncCustomDropdown('linkCategorySelect', 'Select category to link...');
        }
        
        // Focus on category select
        setTimeout(function() {
            const linkCategoryButton = document.getElementById('linkCategorySelect_button');
            if (linkCategoryButton) linkCategoryButton.focus();
        }, 100);
    }
}

/**
 * Cancel payee-category linking and return to form
 */
function cancelPayeeCategoryLink() {
    const linkView = document.getElementById('linkPayeeCategoryView');
    if (linkView) {
        linkView.style.display = 'none';
    }
    
    // Reset the select
    const linkCategorySelect = document.getElementById('linkCategorySelect');
    if (linkCategorySelect) {
        linkCategorySelect.value = '';
    }
    
    // Return to transaction form
    const formView = document.getElementById('transactionForm');
    if (formView) {
        formView.style.display = 'flex';
    }
}

/**
 * Submit the payee-category link
 */
function submitPayeeCategoryLink() {
    const payeeSelect = document.getElementById('formPayee');
    const linkCategorySelect = document.getElementById('linkCategorySelect');
    
    const payeeName = payeeSelect ? payeeSelect.value.trim() : '';
    const categoryId = linkCategorySelect ? linkCategorySelect.value : '';
    
    if (!payeeName) {
        alert('No payee selected');
        return;
    }
    
    if (!categoryId) {
        alert('Please select a category to link');
        const linkCategoryButton = document.getElementById('linkCategorySelect_button');
        if (linkCategoryButton) linkCategoryButton.focus();
        return;
    }
    
    // Get URLs from data attributes
    const urlData = document.getElementById('tacticalUrlData');
    if (!urlData) {
        console.error('URL data not found');
        return;
    }
    const linkUrl = urlData.dataset.linkPayeeCategoryUrl;
    
    if (!linkUrl) {
        console.error('Link URL not found');
        return;
    }
    
    // Get CSRF token
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        const cookieValue = document.cookie.split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        csrfToken = cookieValue;
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('payee_name', payeeName);
    formData.append('category_id', categoryId);
    
    // Call API
    fetch(linkUrl, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Show success message (you could add a toast notification here)
            console.log(`Successfully linked ${payeeName} to category`);
            
            // Return to form
            cancelPayeeCategoryLink();
        } else {
            alert(data.error || 'Failed to link category to payee');
        }
    })
    .catch(error => {
        console.error('Error linking category:', error);
        alert('An error occurred while linking category');
    });
}

/**
 * Show category quick-add from link view (to create new category and link it)
 */
function showCategoryQuickAddFromLink() {
    const linkCategorySelect = document.getElementById('linkCategorySelect');
    
    // Store the current state
    sessionStorage.setItem('returnToPayeeCategoryLink', 'true');
    if (linkCategorySelect) {
        sessionStorage.setItem('tempLinkCategoryValue', linkCategorySelect.value);
    }
    
    // Hide link view and show category add view
    const linkView = document.getElementById('linkPayeeCategoryView');
    const categoryView = document.getElementById('addCategoryView');
    
    if (linkView) linkView.style.display = 'none';
    if (categoryView) {
        categoryView.style.display = 'flex';
        const input = document.getElementById('quickCategoryName');
        if (input) {
            input.value = '';
            setTimeout(function() {
                input.focus();
            }, 100);
        }
    }
}

/**
 * Shows the add transaction form
 * @param {string} type - 'income' or 'expense'
 */
function showAddTransaction(type) {
    // CRITICAL: Hide ALL other panels first
    document.getElementById('detailsView').style.display = 'none';
    document.getElementById('transactionDetails').style.display = 'none';
    const deleteConfirmView = document.getElementById('deleteConfirmView');
    if (deleteConfirmView) deleteConfirmView.style.display = 'none';
    
    // Show ONLY the form
    document.getElementById('transactionForm').style.display = 'block';
    
    // Reset ALL form fields and scroll to top
    resetTransactionForm();
    
    // IMPORTANT: Set form type AFTER reset completes
    // Use setTimeout to ensure reset has fully completed before updating
    setTimeout(function() {
        // Set form type to the requested type
        const formTypeSelect = document.getElementById('formType');
        if (formTypeSelect) {
            formTypeSelect.value = type;
            
            // Update the payee/merchant label based on type
            updatePayeeMerchantLabel();
            
            // Update the custom dropdown button for formType to match
            const formTypeButton = document.getElementById('formType_button');
            if (formTypeButton && formTypeButton.childNodes && formTypeButton.childNodes[0]) {
                const selectedOption = formTypeSelect.options[formTypeSelect.selectedIndex];
                if (selectedOption) {
                    formTypeButton.childNodes[0].textContent = selectedOption.text;
                }
            }
            
            // Update selected state in dropdown
            const formTypeDropdown = document.getElementById('formType_dropdown');
            if (formTypeDropdown) {
                formTypeDropdown.querySelectorAll('a').forEach(link => {
                    link.classList.toggle('selected', link.dataset.value === type);
                });
            }
        }
    }, 0);
    
    // Clear selection state
    selectedTransactionId = null;
    document.querySelectorAll('.transaction-item').forEach(item => {
        item.classList.remove('selected');
    });
}

/**
 * Resets all form fields to empty/default values
 */
/**
 * Clears the transaction selection
 */
function clearSelection() {
    selectedTransactionId = null;
    
    document.querySelectorAll('.transaction-item').forEach(item => {
        item.classList.remove('selected');
    });
    
    // Show empty state, hide all other views
    document.getElementById('detailsView').style.display = 'block';
    document.getElementById('transactionDetails').style.display = 'none';
    document.getElementById('transactionForm').style.display = 'none';
    
    // CRITICAL: Reset form fields whenever form is hidden
    resetTransactionForm();
    
    const deleteConfirmView = document.getElementById('deleteConfirmView');
    if (deleteConfirmView) deleteConfirmView.style.display = 'none';
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
    
    // Populate form with current values (data layer)
    document.getElementById('formType').value = type;
    // Ensure Payee exists in the list; if not, add it so selection succeeds
    if (payee) ensureSelectOption('formPayee', payee, payee);
    document.getElementById('formPayee').value = payee || '';
    document.getElementById('formAmount').value = amount;
    document.getElementById('formDate').value = date;
    // Ensure Category option exists before selecting (usually it will)
    if (categoryId) ensureSelectOption('formCategory', categoryId, selectedElement.dataset.category || '');
    document.getElementById('formCategory').value = categoryId || '';
    document.getElementById('formNotes').value = notes || '';

    // Sync custom dropdown UI (visible layer)
    syncCustomDropdown('formType');
    syncCustomDropdown('formPayee', 'Select payee or merchant...');
    syncCustomDropdown('formCategory', 'Select category...');
    
    // Update payee add button visibility (hide it since a payee is selected)
    togglePayeeAddButton();
    
    // Transform: Hide details, show form
    document.getElementById('transactionDetails').style.display = 'none';
    document.getElementById('transactionForm').style.display = 'block';
}

/**
 * Deletes the currently selected transaction
 */
/**
 * Saves the transaction (add or edit)
 */
function saveTransaction() {
    // Get form values
    const type = document.getElementById('formType').value;
    const payee = document.getElementById('formPayee').value.trim();
    let amount = document.getElementById('formAmount').value;
    const date = document.getElementById('formDate').value;
    const category = document.getElementById('formCategory').value;
    const notes = document.getElementById('formNotes').value.trim();
    
    // Validate
    if (!payee) {
        alert('Please enter a payee name');
        return;
    }
    
    // Remove commas and validate amount
    amount = amount.replace(/,/g, '');
    if (!amount || parseFloat(amount) <= 0) {
        alert('Please enter a valid amount');
        return;
    }
    if (!date) {
        alert('Please select a date');
        return;
    }
    
    // Prepare form data
    const formData = new FormData();
    formData.append('payee_choice', payee);
    formData.append('amount', amount);
    formData.append('date', date);
    formData.append('notes', notes);
    
    // Get CSRF token - try multiple methods
    let csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    
    // If not found in form, try to get from cookie
    if (!csrfToken) {
        const cookieValue = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='))
            ?.split('=')[1];
        csrfToken = cookieValue;
    }
    
    // Add token to form data if found
    if (csrfToken) {
        formData.append('csrfmiddlewaretoken', csrfToken);
    } else {
        console.error('CSRF token not found!');
        alert('Security token not found. Please reload the page and try again.');
        return;
    }
    
    // Determine URL based on type and whether we're editing
    let url;
    const isEditing = !!selectedTransactionId;
    if (isEditing) {
        // Editing existing transaction
        url = type === 'income' 
            ? `/bank/income/${selectedTransactionId}/edit/`
            : `/bank/expense/${selectedTransactionId}/edit/`;
    } else {
        // Adding new transaction
        url = type === 'income' 
            ? '/bank/income/add/'
            : '/bank/expense/add/';
    }
    
    // Submit via AJAX
    fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (isEditing) {
                // If editing, reload to update the list
                window.location.reload();
            } else {
                // If adding new, insert into list without reload
                addTransactionToList({
                    id: data.income_id || data.expense_id,
                    type: type,
                    payee: payee,
                    amount: parseFloat(amount),
                    date: date,
                    category: category,
                    notes: notes
                });
                
                // Reset ALL form fields immediately after successful save
                resetTransactionForm();
                
                // Clear form and return to empty state
                cancelForm();
                
                // Update summary counts
                updateSummaryCounts();
            }
        } else {
            alert('Error: ' + (data.error || 'Unknown error occurred'));
        }
    })
    .catch(error => {
        console.error('Error saving transaction:', error);
        alert('An error occurred while saving the transaction');
    });
}

/**
 * Add a new transaction to the list without page reload
 */
function addTransactionToList(transaction) {
    const transactionList = document.querySelector('.transaction-list');
    if (!transactionList) return;
    
    // Format amount with commas and 2 decimals
    const formattedAmount = formatAmountWithDecimals(transaction.amount);
    
    // Format date
    const dateObj = new Date(transaction.date + 'T00:00:00'); // Ensure proper date parsing
    const dateFull = dateObj.toLocaleDateString('en-US', { weekday: 'short', day: 'numeric', month: 'short', year: 'numeric' });
    const dateShort = dateObj.toLocaleDateString('en-US', { day: 'numeric', month: 'short' });
    const dateCompact = `${dateObj.getDate()}/${dateObj.getMonth() + 1}`;
    
    // Escape strings for HTML
    const escapedPayee = transaction.payee.replace(/'/g, "\\'").replace(/"/g, '&quot;');
    const escapedNotes = (transaction.notes || '').replace(/'/g, "\\'").replace(/"/g, '&quot;');
    const escapedCategory = (transaction.category || 'Uncategorized').replace(/'/g, "\\'").replace(/"/g, '&quot;');
    
    // Create transaction element matching the template structure exactly
    const transactionHtml = `
        <div class="transaction-item boot-animate" 
             data-id="${transaction.id}"
             data-type="${transaction.type}"
             data-amount="${transaction.amount}"
             data-payee="${transaction.payee.toLowerCase()}"
             data-category="${transaction.category || 'none'}"
             data-date-full="${dateFull}"
             data-date-short="${dateShort}"
             data-date-compact="${dateCompact}"
             onclick="selectTransaction(this, ${transaction.id}, '${transaction.type}', '${escapedPayee}', '${dateFull}', '${escapedCategory}', '${transaction.amount}', '${escapedNotes}')">
            <span class="transaction-icon ${transaction.type}">
                ${transaction.type === 'income' ? '▲' : '▼'}
            </span>
            <div class="transaction-info">
                <div class="transaction-date" data-full="${dateFull}" data-short="${dateShort}" data-compact="${dateCompact}">
                    <span class="date-full">${dateFull}</span>
                    <span class="date-short">${dateShort}</span>
                    <span class="date-compact">${dateCompact}</span>
                </div>
                <div class="transaction-payee">${transaction.payee}</div>
                <div class="transaction-category">${transaction.category || 'Uncategorized'}</div>
            </div>
            <div class="transaction-amount ${transaction.type}">
                ${transaction.type === 'income' ? '+' : '-'}$${formattedAmount}
            </div>
        </div>
    `;
    
    // Insert at the top of the list
    transactionList.insertAdjacentHTML('afterbegin', transactionHtml);
}

/**
 * Format amount with thousands separator and always 2 decimal places
 */
function formatAmountWithDecimals(amount) {
    const num = parseFloat(amount);
    if (isNaN(num)) return '0.00';
    
    // Format with 2 decimal places and thousands separator
    return num.toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

/**
 * Format amount input field as user types
 */
function setupAmountFormatting() {
    const amountInput = document.getElementById('formAmount');
    if (!amountInput) return;
    
    amountInput.addEventListener('blur', function() {
        let value = this.value.replace(/,/g, '');
        if (value && !isNaN(value)) {
            this.value = formatAmountWithDecimals(value);
        }
    });
    
    amountInput.addEventListener('focus', function() {
        // Remove formatting when focused for easier editing
        let value = this.value.replace(/,/g, '');
        if (value && !isNaN(value)) {
            this.value = value;
        }
    });
}

/**
 * Cancels the form and returns to appropriate view
 */
function cancelForm() {
    // Reset ALL form fields first (before hiding)
    resetTransactionForm();
    
    // Hide the form
    const transactionForm = document.getElementById('transactionForm');
    if (transactionForm) {
        transactionForm.style.display = 'none';
    }
    
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
// PAYEE & CATEGORY QUICK-ADD - Using inline forms (old prompt-based removed)
// =============================================================================
// Quick-add functions are now defined earlier in this file (around line 1281)
// and show inline forms instead of prompt dialogs.

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
    setupAmountFormatting();
    
    // Add escape key handler for delete confirmation panel
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            const deleteConfirmView = document.getElementById('deleteConfirmView');
            if (deleteConfirmView && deleteConfirmView.style.display === 'block') {
                cancelDelete();
            }
        }
    });
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
