(function (window) {
    const headers = new Set();
    let observer = null;
    let isProcessingResize = false;
    
    // Minimum comfortable widths for elements (in pixels)
    const ELEMENT_CONSTRAINTS = {
        SEARCH_FULL: 180,      // Full search bar with comfortable input
        SEARCH_COMPACT: 120,   // Compact search bar minimum  
        SEARCH_ICON: 40,       // Icon-only search (just icon)
        BUTTON_WITH_LABEL: 80, // Button with text label
        BUTTON_ICON_ONLY: 36,  // Icon-only button
        DROPDOWN_WITH_LABEL: 80, // Dropdown with text
        DROPDOWN_ICON_ONLY: 36   // Icon-only dropdown
    };

    function ensureTooltip(btn, label) {
        if (!label) return;
        
        if (!btn.getAttribute('title')) {
            btn.setAttribute('title', label);
        }
        if (!btn.hasAttribute('data-bs-toggle')) {
            btn.setAttribute('data-bs-toggle', 'tooltip');
            if (!btn.hasAttribute('data-bs-placement')) {
                btn.setAttribute('data-bs-placement', 'top');
            }
        }
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            bootstrap.Tooltip.getInstance(btn) || new bootstrap.Tooltip(btn);
        }
    }

    function removeTooltip(btn) {
        btn.removeAttribute('title');
        if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
            const tooltipInstance = bootstrap.Tooltip.getInstance(btn);
            if (tooltipInstance) {
                tooltipInstance.dispose();
            }
        }
    }

    function getAvailableWidth(actionsContainer) {
        const containerRect = actionsContainer.getBoundingClientRect();
        return containerRect.width;
    }

    function calculateElementStates(header) {
        const actionsContainer = header.querySelector('.panel-header-actions');
        if (!actionsContainer) return null;

        const availableWidth = getAvailableWidth(actionsContainer);
        const searchContainer = header.querySelector('.panel-header-actions > div:has(.form-control)');
        const buttons = header.querySelectorAll('.panel-header-actions .btn:not(.action-btn):not(.mobile-menu-btn)');
        const dropdowns = header.querySelectorAll('.panel-header-actions .dropdown');
        
        console.log('calculateElementStates:', {
            availableWidth,
            buttonsCount: buttons.length,
            dropdownsCount: dropdowns.length,
            hasSearch: !!searchContainer
        });
        
        let remainingWidth = availableWidth;
        const states = {
            search: 'hidden',
            buttons: new Map(),
            dropdowns: new Map(),
        };

        // Account for action buttons (these stay as icons)
        const actionButtons = header.querySelectorAll('.panel-header-actions .action-btn');
        const actionButtonSpace = actionButtons.length * ELEMENT_CONSTRAINTS.BUTTON_ICON_ONLY;
        remainingWidth -= actionButtonSpace;

        // Be more conservative - start with showing buttons as full if there's reasonable space
        const totalElementsNeeded = (buttons.length * ELEMENT_CONSTRAINTS.BUTTON_WITH_LABEL) + 
                                   (dropdowns.length * ELEMENT_CONSTRAINTS.DROPDOWN_WITH_LABEL) + 
                                   ELEMENT_CONSTRAINTS.SEARCH_FULL;

        console.log('Space calc:', {
            available: Math.round(availableWidth),
            needed: totalElementsNeeded,
            ratio: Math.round((remainingWidth / totalElementsNeeded) * 100) + '%'
        });

        // If we have plenty of space, show everything in full (with generous buffer)
        if (availableWidth > 350) { // More reasonable threshold - panels >350px show labels
            console.log('Full mode - wide panel (expanding back to full)');
            
            // Show everything in full mode
            if (searchContainer) states.search = 'full';
            buttons.forEach(btn => states.buttons.set(btn, 'full'));
            dropdowns.forEach(dropdown => states.dropdowns.set(dropdown, 'full'));
            
            return states;
        }

        console.log('Progressive mode - limited space');
        
        // Priority: Search converts to icon BEFORE buttons convert
        if (availableWidth > 280) {
            // Medium space - keep buttons full, but compact search
            console.log('Medium space - compact search only (expanding from icon)');
            if (searchContainer) states.search = 'compact';
            buttons.forEach(btn => states.buttons.set(btn, 'full'));
            dropdowns.forEach(dropdown => states.dropdowns.set(dropdown, 'full'));
            return states;
        } else if (availableWidth > 250) {
            // Smaller space - search to ICON first, buttons still full
            console.log('Search to icon, buttons still full (expanding buttons)');
            if (searchContainer) states.search = 'icon';
            buttons.forEach(btn => states.buttons.set(btn, 'full'));
            dropdowns.forEach(dropdown => states.dropdowns.set(dropdown, 'full'));
            return states;
        } else if (availableWidth > 200) {
            // Even smaller - search icon, buttons to icons
            console.log('Small space - buttons to icons (shrinking buttons)');
            if (searchContainer) states.search = 'icon';
            buttons.forEach(btn => states.buttons.set(btn, 'icon'));
            dropdowns.forEach(dropdown => states.dropdowns.set(dropdown, 'icon'));
            return states;
        } else {
            // Very tight space - everything to icons (same as before)
            console.log('Tight space - all icons');
            if (searchContainer) states.search = 'icon';
            buttons.forEach(btn => states.buttons.set(btn, 'icon'));
            dropdowns.forEach(dropdown => states.dropdowns.set(dropdown, 'icon'));
            return states;
        }

        console.log('States:', states);
        return states;
    }

    function refreshHeader(header) {
        if (!header || isProcessingResize) return;
        
        const panel = header.closest('.payee-list-panel, .payee-detail-panel, .transaction-details-panel, .categories-panel, .payees-panel-3, .details-panel');
        if (!panel) return;
        
        isProcessingResize = true;
        
        try {
            const states = calculateElementStates(header);
            if (!states) return;

            const width = panel.getBoundingClientRect().width;
            console.log(`Progressive resize: width=${width}px, states:`, {
                search: states.search,
                buttonCount: states.buttons.size,
                dropdownCount: states.dropdowns.size
            });

            // Apply states with safety check - don't convert to icons immediately on load
            const isInitialLoad = !header.dataset.progressiveInitialized;
            if (isInitialLoad) {
                console.log('🚀 Initial load - forcing full mode');
                // On initial load, force everything to full mode regardless of calculated states
                applySearchState(header, 'full');
                states.buttons.forEach((state, button) => applyButtonState(button, 'full'));
                states.dropdowns.forEach((state, dropdown) => applyDropdownState(dropdown, 'full'));
                header.dataset.progressiveInitialized = 'true';
                
                // Very short protection period - 100ms only
                header.dataset.initialLoadProtection = Date.now().toString();
                return; // Exit early, don't apply calculated states
            } else {
                // Check if we're still in initial load protection period
                const protectionTime = parseInt(header.dataset.initialLoadProtection || '0');
                const now = Date.now();
                if (now - protectionTime < 100) { // Much shorter protection period
                    console.log('⏳ Protection active - remaining:', (100 - (now - protectionTime)) + 'ms');
                    return; // Don't apply progressive states yet
                }
                
                // Normal responsive behavior after initial load protection expires
                console.log('✅ Applying states - search:', states.search, 'button states:', Array.from(states.buttons.values()));
                console.log('🔄 EXPANSION CHECK: Available width =', getAvailableWidth(header.querySelector('.panel-header-actions')), 'px');
                
                applySearchState(header, states.search);
                states.buttons.forEach((state, button) => {
                    console.log('🔧 Setting button state:', button.textContent?.trim(), 'to', state);
                    applyButtonState(button, state);
                });
                states.dropdowns.forEach((state, dropdown) => applyDropdownState(dropdown, state));
            }
        } finally {
            isProcessingResize = false;
        }
    }

    function applySearchState(header, state) {
        const searchContainer = header.querySelector('.panel-header-actions > div:has(.form-control)');
        if (!searchContainer) return;

        searchContainer.classList.remove('search-full', 'search-compact', 'search-icon', 'search-hidden');
        
        console.log('Search state:', state);
        
        switch (state) {
            case 'full':
                searchContainer.classList.add('search-full');
                searchContainer.style.display = 'block';
                break;
            case 'compact':
                searchContainer.classList.add('search-compact');
                searchContainer.style.display = 'block';
                break;
            case 'icon':
                searchContainer.classList.add('search-icon');
                searchContainer.style.display = 'block';
                break;
            case 'hidden':
                searchContainer.classList.add('search-hidden');
                searchContainer.style.display = 'none';
                break;
        }
    }

    function applyButtonState(button, state) {
        const labelSpan = button.querySelector('span');
        
        console.log('🔧 applyButtonState:', button.textContent?.trim(), 'from current classes:', button.className, 'to state:', state);
        
        button.classList.remove('btn-full', 'btn-icon', 'btn-hidden');
        button.classList.remove('d-none', 'd-lg-none', 'd-lg-inline-flex');
        
        if (!button.dataset.fullLabel && labelSpan) {
            button.dataset.fullLabel = labelSpan.textContent.trim();
        }
        
        switch (state) {
            case 'full':
                console.log('✅ Setting button to FULL mode - showing label');
                button.classList.add('btn-full');
                button.style.display = 'inline-flex';
                if (labelSpan) {
                    labelSpan.style.display = '';
                    console.log('📝 Label span display set to empty (visible)');
                }
                removeTooltip(button);
                break;
            case 'icon':
                console.log('🎯 Setting button to ICON mode - hiding label');
                button.classList.add('btn-icon');
                button.style.display = 'inline-flex';
                if (labelSpan) {
                    labelSpan.style.display = 'none';
                    console.log('🚫 Label span display set to none (hidden)');
                }
                ensureTooltip(button, button.dataset.fullLabel);
                console.log('Button → icon mode');
                break;
            case 'hidden':
                button.classList.add('btn-hidden');
                button.style.display = 'none';
                break;
        }
    }

    function applyDropdownState(dropdown, state) {
        const dropdownBtn = dropdown.querySelector('.btn');
        const labelSpan = dropdownBtn ? dropdownBtn.querySelector('span:not(.visually-hidden)') : null;
        
        if (!dropdownBtn) return;
        
        dropdown.classList.remove('dropdown-full', 'dropdown-icon', 'dropdown-hidden');
        
        if (!dropdownBtn.dataset.fullLabel && labelSpan) {
            dropdownBtn.dataset.fullLabel = labelSpan.textContent.trim();
        }
        
        switch (state) {
            case 'full':
                dropdown.classList.add('dropdown-full');
                dropdown.style.display = 'block';
                if (labelSpan) labelSpan.style.display = '';
                removeTooltip(dropdownBtn);
                break;
            case 'icon':
                dropdown.classList.add('dropdown-icon');
                dropdown.style.display = 'block';
                if (labelSpan) labelSpan.style.display = 'none';
                ensureTooltip(dropdownBtn, dropdownBtn.dataset.fullLabel || 'Filter');
                break;
            case 'hidden':
                dropdown.classList.add('dropdown-hidden');
                dropdown.style.display = 'none';
                break;
        }
    }

    function refreshAll() {
        headers.forEach(header => {
            if (header && document.contains(header)) {
                refreshHeader(header);
            }
        });
    }

    function init() {
        console.log('Progressive responsive system init');
        
        // Find all panel headers
        document.querySelectorAll('.panel-header').forEach(header => {
            headers.add(header);
            
            // Force all buttons to be visible initially (override Bootstrap)
            const buttons = header.querySelectorAll('.btn:not(.action-btn):not(.mobile-menu-btn)');
            buttons.forEach(btn => {
                btn.classList.remove('d-none', 'd-lg-none');
                btn.classList.add('btn-full'); // Start in full mode
                btn.style.display = 'inline-flex';
            });
            
            // Force all dropdowns to be visible initially
            const dropdowns = header.querySelectorAll('.dropdown');
            dropdowns.forEach(dropdown => {
                dropdown.classList.add('dropdown-full'); // Start in full mode
                dropdown.style.display = 'block';
            });
            
            // Force search to be visible
            const searchContainer = header.querySelector('.panel-header-actions > div:has(.form-control)');
            if (searchContainer) {
                searchContainer.classList.add('search-full');
                searchContainer.style.display = 'block';
            }
            
            // Delay the progressive calculation to let layout settle
            setTimeout(() => {
                refreshHeader(header);
            }, 250); // Increased delay to allow layout to fully settle
        });

        // Set up ResizeObserver for panels
        if (window.ResizeObserver) {
            observer = new ResizeObserver((entries) => {
                const throttledCallback = (() => {
                    if (isProcessingResize) return;
                    
                    window.requestAnimationFrame(() => {
                        entries.forEach(entry => {
                            const header = entry.target.querySelector('.panel-header') || 
                                          (entry.target.classList.contains('panel-header') ? entry.target : null);
                            if (header && !isProcessingResize) {
                                refreshHeader(header);
                            }
                        });
                    });
                });
                
                setTimeout(throttledCallback, 100);
            });
            
            // Observe panel containers
            headers.forEach(header => {
                const panel = header.closest('.payee-list-panel, .payee-detail-panel, .transaction-details-panel, .categories-panel, .payees-panel-3, .details-panel');
                if (panel && observer) {
                    observer.observe(panel);
                }
            });
        }

        // Window resize handler
        let windowResizeTimer;
        window.addEventListener('resize', () => {
            clearTimeout(windowResizeTimer);
            windowResizeTimer = setTimeout(() => {
                if (!isProcessingResize) {
                    window.requestAnimationFrame(refreshAll);
                }
            }, 100);
        });
    }

    window.PanelHeaderLabelManager = {
        init,
        refresh: refreshAll,
        test: function() {
            console.log('Testing progressive responsive behavior...');
            refreshAll();
        },
        forceExpand: function() {
            console.log('Force expanding all panels to full mode...');
            headers.forEach(header => {
                // Remove protection to allow immediate changes
                delete header.dataset.initialLoadProtection;
                header.dataset.progressiveInitialized = 'true';
                
                // Force full mode
                const searchContainer = header.querySelector('.panel-header-actions > div:has(.form-control)');
                const buttons = header.querySelectorAll('.panel-header-actions .btn:not(.action-btn):not(.mobile-menu-btn)');
                const dropdowns = header.querySelectorAll('.panel-header-actions .dropdown');
                
                if (searchContainer) applySearchState(header, 'full');
                buttons.forEach(btn => applyButtonState(btn, 'full'));
                dropdowns.forEach(dropdown => applyDropdownState(dropdown, 'full'));
            });
        },
        debugWidth: function() {
            headers.forEach(header => {
                const actionsContainer = header.querySelector('.panel-header-actions');
                if (actionsContainer) {
                    const width = getAvailableWidth(actionsContainer);
                    console.log('Panel width:', width + 'px', header);
                }
            });
        }
    };

    // Expose test functions to global scope for debugging
    window.testProgressiveExpansion = function() {
        console.log('=== MANUAL PROGRESSIVE TEST ===');
        const headers = document.querySelectorAll('.panel-header-actions');
        headers.forEach(header => {
            console.log('Manual trigger for header:', header);
            header.dataset.initialLoadProtection = '0'; // Clear protection
            updateProgressiveElements(header);
        });
    };

    window.forceProgressiveUpdate = function() {
        console.log('=== FORCE PROGRESSIVE RESET ===');
        const headers = document.querySelectorAll('.panel-header-actions');
        headers.forEach(header => {
            // Clear all protection and states
            delete header.dataset.progressiveInitialized;
            delete header.dataset.initialLoadProtection;
            
            // Reset all elements to full mode first
            const searchContainer = header.querySelector('.panel-header-actions > div:has(.form-control)');
            if (searchContainer) {
                searchContainer.classList.remove('search-full', 'search-compact', 'search-icon', 'search-hidden');
                searchContainer.classList.add('search-full');
                searchContainer.style.display = 'block';
            }
            
            const buttons = header.querySelectorAll('.btn:not(.dropdown-toggle)');
            buttons.forEach(btn => {
                btn.classList.remove('btn-full', 'btn-icon', 'btn-hidden');
                btn.classList.add('btn-full');
                btn.style.display = 'inline-flex';
                const labelSpan = btn.querySelector('span');
                if (labelSpan) labelSpan.style.display = '';
                removeTooltip(btn);
            });
            
            // Now apply proper states
            console.log('Resetting complete, applying states in 100ms...');
            setTimeout(() => updateProgressiveElements(header), 100);
        });
    };

    // Auto-initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})(window);