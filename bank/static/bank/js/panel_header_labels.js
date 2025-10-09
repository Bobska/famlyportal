(function (window) {
    const headers = new Set();
    let observer = null;
    let isProcessingResize = false;
    let measurementCache = new Map(); // Cache measurements to avoid re-measuring

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

    function getAvailableWidth(header) {
        // Get the panel width, not the actions container width
        const panel = header.closest('.payee-list-panel, .payee-detail-panel, .transaction-details-panel, .categories-panel, .payees-panel-3, .details-panel');
        if (panel) {
            const panelRect = panel.getBoundingClientRect();
            console.log('🌐 Panel width:', panelRect.width, 'px');
            return panelRect.width;
        }
        
        // Fallback to header width
        const headerRect = header.getBoundingClientRect();
        console.log('📏 Header width fallback:', headerRect.width, 'px');
        return headerRect.width;
    }

    function getElementWidths(header) {
        const headerId = header.dataset.headerId || Math.random().toString(36);
        header.dataset.headerId = headerId;
        
        // Use cached measurements if available and recent (within 1 second)
        const cached = measurementCache.get(headerId);
        if (cached && (Date.now() - cached.timestamp) < 1000) {
            console.log('📋 Using cached measurements');
            return cached.widths;
        }
        
        // Get PANEL width consistently
        const panel = header.closest('.payee-list-panel, .payee-detail-panel, .transaction-details-panel, .categories-panel, .payees-panel-3, .details-panel');
        const panelWidth = panel ? panel.getBoundingClientRect().width : 400; // fallback
        
        console.log('📦 Panel width:', Math.round(panelWidth), 'px');
        
        // Use fixed widths based on typical measurements to avoid measurement loops
        const widths = {
            panelWidth: panelWidth,
            search: {
                full: 200,    // Typical full search width
                compact: 150, // Compact search width  
                icon: 32      // Icon-only width
            },
            button: {
                full: 70,     // Average button with label
                icon: 32      // Icon-only button
            },
            dropdown: {
                full: 70,     // Average dropdown with label
                icon: 32      // Icon-only dropdown
            }
        };
        
        // Cache the measurements
        measurementCache.set(headerId, {
            widths,
            timestamp: Date.now()
        });
        
        return widths;
    }

    function calculateElementStates(header) {
        try {
            const widths = getElementWidths(header);
            const { panelWidth, search, button, dropdown } = widths;
            
            // Count elements
            const searchContainer = header.querySelector('.panel-header-actions > div:has(.form-control)');
            const buttons = header.querySelectorAll('.panel-header-actions .btn:not(.action-btn):not(.mobile-menu-btn)');
            const dropdowns = header.querySelectorAll('.panel-header-actions .dropdown');
            
            const buttonCount = buttons.length;
            const dropdownCount = dropdowns.length;
            
            console.log('🧮 Layout calc for', Math.round(panelWidth), 'px:', {
                buttons: buttonCount,
                dropdowns: dropdownCount, 
                hasSearch: !!searchContainer
            });
            
            // Available width with conservative buffer
            const availableWidth = panelWidth - 40; // Larger buffer for margins/padding
            
            // Calculate total needed widths for different scenarios
            const searchFullWidth = searchContainer ? search.full : 0;
            const searchCompactWidth = searchContainer ? search.compact : 0;
            const searchIconWidth = searchContainer ? search.icon : 0;
            
            const buttonsFullWidth = buttonCount * button.full;
            const buttonsIconWidth = buttonCount * button.icon;
            
            const dropdownsFullWidth = dropdownCount * dropdown.full;
            const dropdownsIconWidth = dropdownCount * dropdown.icon;
            
            // Decision logic with clear logging
            const totalFullWidth = searchFullWidth + buttonsFullWidth + dropdownsFullWidth;
            console.log('💡 Full mode needs:', Math.round(totalFullWidth), 'vs available:', Math.round(availableWidth));
            
            if (totalFullWidth <= availableWidth) {
                console.log('✅ FULL mode - everything with labels');
                return {
                    search: searchContainer ? 'full' : 'hidden',
                    buttons: Array.from(buttons).map(() => 'full'),
                    dropdowns: Array.from(dropdowns).map(() => 'full')
                };
            }
            
            const totalCompactWidth = searchCompactWidth + buttonsFullWidth + dropdownsFullWidth;
            console.log('💡 Compact search needs:', Math.round(totalCompactWidth));
            
            if (totalCompactWidth <= availableWidth) {
                console.log('✅ COMPACT search mode');
                return {
                    search: searchContainer ? 'compact' : 'hidden',
                    buttons: Array.from(buttons).map(() => 'full'),
                    dropdowns: Array.from(dropdowns).map(() => 'full')
                };
            }
            
            const totalIconSearchWidth = searchIconWidth + buttonsFullWidth + dropdownsFullWidth;
            console.log('💡 Icon search needs:', Math.round(totalIconSearchWidth));
            
            if (totalIconSearchWidth <= availableWidth) {
                console.log('✅ ICON search mode');
                return {
                    search: searchContainer ? 'icon' : 'hidden',
                    buttons: Array.from(buttons).map(() => 'full'),
                    dropdowns: Array.from(dropdowns).map(() => 'full')
                };
            }
            
            const totalAllIconsWidth = searchIconWidth + buttonsIconWidth + dropdownsIconWidth;
            console.log('💡 All icons needs:', Math.round(totalAllIconsWidth));
            
            if (totalAllIconsWidth <= availableWidth) {
                console.log('✅ ALL ICONS mode');
                return {
                    search: searchContainer ? 'icon' : 'hidden',
                    buttons: Array.from(buttons).map(() => 'icon'),
                    dropdowns: Array.from(dropdowns).map(() => 'icon')
                };
            }
            
            console.log('⚠️ MINIMAL mode - hide search');
            return {
                search: 'hidden',
                buttons: Array.from(buttons).map(() => 'icon'),
                dropdowns: Array.from(dropdowns).map(() => 'icon')
            };
            
        } catch (error) {
            console.error('❌ Error in calculateElementStates:', error);
            // Safe fallback - show everything
            return {
                search: 'full',
                buttons: ['full', 'full'],
                dropdowns: ['full']
            };
        }
    }

    function refreshHeader(header) {
        if (!header || isProcessingResize) return;
        
        // Prevent feedback loops during measurements
        isProcessingResize = true;
        
        try {
            const states = calculateElementStates(header);
            if (!states) return;

            console.log('🎯 Applying states:', states);

            // Apply states with initial load protection
            const isInitialLoad = !header.dataset.progressiveInitialized;
            if (isInitialLoad) {
                console.log('🚀 Initial load - forcing full mode');
                // Force everything to full mode on initial load
                applySearchState(header, 'full');
                
                const buttons = header.querySelectorAll('.panel-header-actions .btn:not(.action-btn):not(.mobile-menu-btn)');
                buttons.forEach(button => applyButtonState(button, 'full'));
                
                const dropdowns = header.querySelectorAll('.panel-header-actions .dropdown');
                dropdowns.forEach(dropdown => applyDropdownState(dropdown, 'full'));
                
                header.dataset.progressiveInitialized = 'true';
                header.dataset.initialLoadProtection = Date.now().toString();
                return; // Exit early
            }
            
            // Check protection period
            const protectionTime = parseInt(header.dataset.initialLoadProtection || '0');
            const now = Date.now();
            if (now - protectionTime < 200) {
                console.log('⏳ Protection active - remaining:', (200 - (now - protectionTime)) + 'ms');
                return;
            }
            
            // Apply calculated states
            console.log('✅ Applying responsive states');
            applySearchState(header, states.search);
            
            const buttons = Array.from(header.querySelectorAll('.panel-header-actions .btn:not(.action-btn):not(.mobile-menu-btn)'));
            buttons.forEach((button, index) => {
                const state = states.buttons[index] || 'full';
                console.log(`🔧 Button ${index + 1} → ${state}`);
                applyButtonState(button, state);
            });
            
            const dropdowns = Array.from(header.querySelectorAll('.panel-header-actions .dropdown'));
            dropdowns.forEach((dropdown, index) => {
                const state = states.dropdowns[index] || 'full';
                console.log(`📋 Dropdown ${index + 1} → ${state}`);
                applyDropdownState(dropdown, state);
            });
            
        } catch (error) {
            console.error('❌ Error in refreshHeader:', error);
        } finally {
            // Always clear the processing flag
            setTimeout(() => {
                isProcessingResize = false;
            }, 50);
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