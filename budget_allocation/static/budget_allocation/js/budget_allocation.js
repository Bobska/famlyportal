/* ==========================================================================
   Budget Allocation App JavaScript
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {
    
    // ==========================================================================
    // Account Tree Toggle Functionality
    // ==========================================================================
    
    function initializeAccountTree() {
        const toggleButtons = document.querySelectorAll('.toggle-account');
        
        toggleButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                e.preventDefault();
                
                const targetId = this.getAttribute('data-bs-target');
                const targetElement = document.querySelector(targetId);
                const icon = this.querySelector('i');
                
                if (targetElement) {
                    if (targetElement.style.display === 'none' || targetElement.style.display === '') {
                        targetElement.style.display = 'block';
                        icon.style.transform = 'rotate(0deg)';
                        this.setAttribute('aria-expanded', 'true');
                    } else {
                        targetElement.style.display = 'none';
                        icon.style.transform = 'rotate(-90deg)';
                        this.setAttribute('aria-expanded', 'false');
                    }
                }
            });
        });
    }
    
    // ==========================================================================
    // Form Validation and Enhancement
    // ==========================================================================
    
    function initializeFormValidation() {
        const forms = document.querySelectorAll('.needs-validation');
        
        forms.forEach(form => {
            form.addEventListener('submit', function(e) {
                if (!form.checkValidity()) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    // Find first invalid field and focus it
                    const firstInvalidField = form.querySelector(':invalid');
                    if (firstInvalidField) {
                        firstInvalidField.focus();
                        firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
                
                form.classList.add('was-validated');
            });
            
            // Real-time validation feedback
            const inputs = form.querySelectorAll('input, select, textarea');
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    if (this.checkValidity()) {
                        this.classList.remove('is-invalid');
                        this.classList.add('is-valid');
                    } else {
                        this.classList.remove('is-valid');
                        this.classList.add('is-invalid');
                    }
                });
            });
        });
    }
    
    // ==========================================================================
    // Color Picker Enhancement
    // ==========================================================================
    
    function initializeColorPicker() {
        const colorInputs = document.querySelectorAll('input[type="color"]');
        
        colorInputs.forEach(input => {
            // Add color preview
            const preview = document.createElement('div');
            preview.className = 'account-color-indicator me-2';
            preview.style.backgroundColor = input.value;
            
            input.parentNode.insertBefore(preview, input);
            
            input.addEventListener('change', function() {
                preview.style.backgroundColor = this.value;
            });
        });
    }
    
    // ==========================================================================
    // Loading States
    // ==========================================================================
    
    function initializeLoadingStates() {
        const forms = document.querySelectorAll('form');
        
        forms.forEach(form => {
            const submitButton = form.querySelector('.btn[type="submit"]');
            if (submitButton) {
                // Store original text
                submitButton.dataset.originalText = submitButton.innerHTML;
                
                form.addEventListener('submit', function(e) {
                    // Only show loading if form validation passes
                    if (form.checkValidity()) {
                        submitButton.disabled = true;
                        submitButton.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';
                        
                        // Re-enable after 10 seconds as failsafe
                        setTimeout(() => {
                            submitButton.disabled = false;
                            submitButton.innerHTML = submitButton.dataset.originalText || 'Submit';
                        }, 10000);
                    }
                });
            }
        });
    }
    
    // ==========================================================================
    // Account Balance Formatting
    // ==========================================================================
    
    function formatCurrency(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(amount);
    }
    
    function initializeBalanceFormatting() {
        const balanceElements = document.querySelectorAll('.balance-amount');
        
        balanceElements.forEach(element => {
            const amount = parseFloat(element.textContent.replace(/[^-\d.]/g, ''));
            if (!isNaN(amount)) {
                element.textContent = formatCurrency(amount);
                
                // Add color coding
                if (amount > 0) {
                    element.classList.add('text-success');
                } else if (amount < 0) {
                    element.classList.add('text-danger');
                } else {
                    element.classList.add('text-muted');
                }
            }
        });
    }
    
    // ==========================================================================
    // Tooltip Enhancement
    // ==========================================================================
    
    function initializeTooltips() {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
    
    // ==========================================================================
    // Confirmation Dialogs
    // ==========================================================================
    
    function initializeConfirmations() {
        const deleteButtons = document.querySelectorAll('[data-confirm]');
        
        deleteButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                const message = this.dataset.confirm || 'Are you sure you want to delete this item?';
                
                if (!confirm(message)) {
                    e.preventDefault();
                    return false;
                }
            });
        });
    }
    
    // ==========================================================================
    // Quick Actions
    // ==========================================================================
    
    function initializeQuickActions() {
        const quickActionBtns = document.querySelectorAll('.quick-action-btn');
        
        quickActionBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                // Add loading state
                this.classList.add('loading');
                
                // Add some visual feedback
                this.style.transform = 'scale(0.95)';
                setTimeout(() => {
                    this.style.transform = 'scale(1)';
                }, 150);
            });
        });
    }
    
    // ==========================================================================
    // Auto-save functionality for forms
    // ==========================================================================
    
    function initializeAutoSave() {
        const autoSaveForms = document.querySelectorAll('[data-auto-save]');
        
        autoSaveForms.forEach(form => {
            const inputs = form.querySelectorAll('input, select, textarea');
            let timeout;
            
            inputs.forEach(input => {
                input.addEventListener('input', function() {
                    clearTimeout(timeout);
                    
                    // Show saving indicator
                    const indicator = document.createElement('small');
                    indicator.className = 'text-muted ms-2';
                    indicator.textContent = 'Saving...';
                    
                    // Remove existing indicators
                    const existingIndicators = form.querySelectorAll('.auto-save-indicator');
                    existingIndicators.forEach(ind => ind.remove());
                    
                    indicator.className += ' auto-save-indicator';
                    this.parentNode.appendChild(indicator);
                    
                    timeout = setTimeout(() => {
                        // Here you would typically make an AJAX call
                        indicator.textContent = 'Saved';
                        indicator.className = 'text-success ms-2 auto-save-indicator';
                        
                        setTimeout(() => {
                            indicator.remove();
                        }, 2000);
                    }, 1000);
                });
            });
        });
    }
    
    // ==========================================================================
    // Search and Filter Functionality
    // ==========================================================================
    
    function initializeSearch() {
        const searchInputs = document.querySelectorAll('[data-search-target]');
        
        searchInputs.forEach(input => {
            const targetSelector = input.dataset.searchTarget;
            const targets = document.querySelectorAll(targetSelector);
            
            input.addEventListener('input', function() {
                const searchTerm = this.value.toLowerCase().trim();
                
                targets.forEach(target => {
                    const text = target.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        target.style.display = '';
                        target.classList.remove('d-none');
                    } else {
                        target.style.display = 'none';
                        target.classList.add('d-none');
                    }
                });
                
                // Show "no results" message if all hidden
                const visibleTargets = Array.from(targets).filter(t => t.style.display !== 'none');
                const noResultsMsg = document.querySelector('.no-results-message');
                
                if (visibleTargets.length === 0 && searchTerm) {
                    if (!noResultsMsg) {
                        const msg = document.createElement('div');
                        msg.className = 'no-results-message text-center text-muted py-4';
                        msg.innerHTML = '<i class="fas fa-search me-2"></i>No accounts found matching your search.';
                        targets[0].parentNode.appendChild(msg);
                    }
                } else if (noResultsMsg) {
                    noResultsMsg.remove();
                }
            });
        });
    }
    
    // ==========================================================================
    // Keyboard Shortcuts
    // ==========================================================================
    
    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl/Cmd + N for new account
            if ((e.ctrlKey || e.metaKey) && e.key === 'n') {
                e.preventDefault();
                const newAccountBtn = document.querySelector('[href*="account/new"]');
                if (newAccountBtn) {
                    newAccountBtn.click();
                }
            }
            
            // Escape to close modals
            if (e.key === 'Escape') {
                const openModals = document.querySelectorAll('.modal.show');
                openModals.forEach(modal => {
                    const modalInstance = bootstrap.Modal.getInstance(modal);
                    if (modalInstance) {
                        modalInstance.hide();
                    }
                });
            }
        });
    }
    
    // ==========================================================================
    // Progress Bars and Animations
    // ==========================================================================
    
    function initializeProgressBars() {
        const progressBars = document.querySelectorAll('.progress-bar');
        
        // Animate progress bars on page load
        progressBars.forEach(bar => {
            const width = bar.style.width;
            bar.style.width = '0%';
            
            setTimeout(() => {
                bar.style.width = width;
            }, 300);
        });
    }
    
    // ==========================================================================
    // Accessibility Enhancements
    // ==========================================================================
    
    function initializeAccessibility() {
        // Add skip links
        const skipLink = document.createElement('a');
        skipLink.href = '#main-content';
        skipLink.className = 'skip-link visually-hidden-focusable';
        skipLink.textContent = 'Skip to main content';
        document.body.insertBefore(skipLink, document.body.firstChild);
        
        // Ensure all buttons have proper labels
        const buttons = document.querySelectorAll('button:not([aria-label]):not([title])');
        buttons.forEach(button => {
            if (!button.textContent.trim()) {
                const icon = button.querySelector('i');
                if (icon && icon.className.includes('fa-')) {
                    const iconClass = icon.className.match(/fa-([a-z-]+)/);
                    if (iconClass) {
                        button.setAttribute('aria-label', iconClass[1].replace('-', ' '));
                    }
                }
            }
        });
        
        // Add focus indicators for better keyboard navigation
        document.addEventListener('keydown', function(e) {
            if (e.key === 'Tab') {
                document.body.classList.add('keyboard-navigation');
            }
        });
        
        document.addEventListener('mousedown', function() {
            document.body.classList.remove('keyboard-navigation');
        });
    }
    
    // ==========================================================================
    // Mobile Touch Enhancements
    // ==========================================================================
    
    function initializeMobileEnhancements() {
        if ('ontouchstart' in window) {
            // Add touch-friendly classes
            document.body.classList.add('touch-device');
            
            // Improve touch targets
            const smallButtons = document.querySelectorAll('.btn-sm');
            smallButtons.forEach(btn => {
                btn.style.minHeight = '44px';
                btn.style.minWidth = '44px';
            });
        }
    }
    
    // ==========================================================================
    // Error Handling
    // ==========================================================================
    
    function initializeErrorHandling() {
        window.addEventListener('error', function(e) {
            console.error('JavaScript error:', e.error);
            
            // Show user-friendly error message
            const errorAlert = document.createElement('div');
            errorAlert.className = 'alert alert-danger alert-dismissible fade show';
            errorAlert.innerHTML = `
                <strong>Something went wrong!</strong> Please refresh the page and try again.
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            `;
            
            const container = document.querySelector('.container, .container-fluid');
            if (container) {
                container.insertBefore(errorAlert, container.firstChild);
            }
        });
    }
    
    // ==========================================================================
    // Initialize All Features
    // ==========================================================================
    
    function initializeAll() {
        try {
            initializeAccountTree();
            initializeFormValidation();
            initializeColorPicker();
            initializeLoadingStates();
            initializeBalanceFormatting();
            initializeTooltips();
            initializeConfirmations();
            initializeQuickActions();
            initializeAutoSave();
            initializeSearch();
            initializeKeyboardShortcuts();
            initializeProgressBars();
            initializeAccessibility();
            initializeMobileEnhancements();
            initializeErrorHandling();
            
            console.log('Budget Allocation app JavaScript initialized successfully');
        } catch (error) {
            console.error('Error initializing Budget Allocation app:', error);
        }
    }
    
    // Start initialization
    initializeAll();
    
    // Re-initialize on dynamic content updates
    document.addEventListener('htmx:afterSwap', initializeAll);
    document.addEventListener('turbo:load', initializeAll);
});

// ==========================================================================
// Utility Functions (Global Scope)
// ==========================================================================

window.BudgetAllocation = {
    // Format currency for display
    formatCurrency: function(amount) {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
            minimumFractionDigits: 2
        }).format(amount);
    },
    
    // Show loading state on element
    showLoading: function(element) {
        element.classList.add('loading');
        element.style.pointerEvents = 'none';
    },
    
    // Hide loading state
    hideLoading: function(element) {
        element.classList.remove('loading');
        element.style.pointerEvents = '';
    },
    
    // Show toast notification
    showToast: function(message, type = 'info') {
        const toastContainer = document.querySelector('.toast-container') || document.body;
        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;
        
        toastContainer.appendChild(toast);
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
        
        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', function() {
            toast.remove();
        });
    }
};
