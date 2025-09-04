/**
 * FamlyPortal Main JavaScript
 * Handles common interactive features and utilities
 */

// Wait for DOM to be ready
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
});

/**
 * Initialize the application
 */
function initializeApp() {
    // Initialize tooltips
    initializeTooltips();
    
    // Initialize animations
    initializeAnimations();
    
    // Initialize form enhancements
    initializeFormEnhancements();
    
    // Initialize common utilities
    initializeUtilities();
    
    console.log('FamlyPortal: Application initialized');
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
 * Initialize page animations
 */
function initializeAnimations() {
    // Animate cards on page load
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            card.style.transition = 'all 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });
    
    // Add hover effects to app cards
    const appCards = document.querySelectorAll('.app-card');
    appCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-8px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
}

/**
 * Enhance forms with better UX
 */
function initializeFormEnhancements() {
    // Add floating labels behavior
    const formControls = document.querySelectorAll('.form-control, .form-select');
    formControls.forEach(control => {
        // Add focus/blur animations
        control.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        control.addEventListener('blur', function() {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });
        
        // Check if field has value on load
        if (control.value) {
            control.parentElement.classList.add('focused');
        }
    });
    
    // Auto-resize textareas
    const textareas = document.querySelectorAll('textarea');
    textareas.forEach(textarea => {
        textarea.addEventListener('input', autoResizeTextarea);
        // Set initial height
        autoResizeTextarea.call(textarea);
    });
}

/**
 * Auto-resize textarea to fit content
 */
function autoResizeTextarea() {
    this.style.height = 'auto';
    this.style.height = this.scrollHeight + 'px';
}

/**
 * Initialize common utilities
 */
function initializeUtilities() {
    // Add copy-to-clipboard functionality
    const copyButtons = document.querySelectorAll('[data-copy]');
    copyButtons.forEach(button => {
        button.addEventListener('click', function() {
            const textToCopy = this.getAttribute('data-copy');
            copyToClipboard(textToCopy);
            showCopyFeedback(this);
        });
    });
    
    // Add smooth scrolling to anchor links
    const anchorLinks = document.querySelectorAll('a[href^="#"]');
    anchorLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                e.preventDefault();
                targetElement.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 */
function copyToClipboard(text) {
    if (navigator.clipboard && window.isSecureContext) {
        // Use modern clipboard API
        return navigator.clipboard.writeText(text);
    } else {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        textArea.style.position = 'fixed';
        textArea.style.left = '-999999px';
        textArea.style.top = '-999999px';
        document.body.appendChild(textArea);
        textArea.focus();
        textArea.select();
        
        try {
            document.execCommand('copy');
            textArea.remove();
            return Promise.resolve();
        } catch (error) {
            textArea.remove();
            return Promise.reject(error);
        }
    }
}

/**
 * Show visual feedback when copying to clipboard
 * @param {Element} button - Button element that was clicked
 */
function showCopyFeedback(button) {
    const originalHTML = button.innerHTML;
    const originalClasses = button.className;
    
    // Show success state
    button.innerHTML = '<i class="bi bi-check"></i>';
    button.className = button.className.replace(/btn-\w+/, 'btn-success');
    
    // Reset after 2 seconds
    setTimeout(() => {
        button.innerHTML = originalHTML;
        button.className = originalClasses;
    }, 2000);
}

/**
 * Show toast notification
 * @param {string} message - Message to show
 * @param {string} type - Type of toast (success, error, warning, info)
 */
function showToast(message, type = 'info') {
    // Create toast container if it doesn't exist
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
    
    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    
    // Initialize and show toast
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove from DOM after hidden
    toast.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

/**
 * Confirm dialog with custom styling
 * @param {string} message - Confirmation message
 * @param {string} title - Dialog title
 * @returns {Promise<boolean>} - User's choice
 */
function confirmDialog(message, title = 'Confirm Action') {
    return new Promise((resolve) => {
        // For now, use browser confirm - can be enhanced with modal
        const result = confirm(`${title}\n\n${message}`);
        resolve(result);
    });
}

/**
 * Format currency values
 * @param {number} amount - Amount to format
 * @param {string} currency - Currency code (default: USD)
 * @returns {string} - Formatted currency string
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Format dates consistently
 * @param {Date|string} date - Date to format
 * @param {string} format - Format type (short, long, relative)
 * @returns {string} - Formatted date string
 */
function formatDate(date, format = 'short') {
    const dateObj = typeof date === 'string' ? new Date(date) : date;
    
    switch (format) {
        case 'long':
            return dateObj.toLocaleDateString('en-US', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric'
            });
        case 'relative':
            return getRelativeTimeString(dateObj);
        default:
            return dateObj.toLocaleDateString('en-US');
    }
}

/**
 * Get relative time string (e.g., "2 hours ago")
 * @param {Date} date - Date to compare
 * @returns {string} - Relative time string
 */
function getRelativeTimeString(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);
    
    const intervals = [
        { label: 'year', seconds: 31536000 },
        { label: 'month', seconds: 2592000 },
        { label: 'week', seconds: 604800 },
        { label: 'day', seconds: 86400 },
        { label: 'hour', seconds: 3600 },
        { label: 'minute', seconds: 60 },
        { label: 'second', seconds: 1 }
    ];
    
    for (const interval of intervals) {
        const count = Math.floor(diffInSeconds / interval.seconds);
        if (count >= 1) {
            return `${count} ${interval.label}${count !== 1 ? 's' : ''} ago`;
        }
    }
    
    return 'just now';
}

/**
 * Debounce function to limit rapid function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} - Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Throttle function to limit function execution frequency
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} - Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function() {
        const args = arguments;
        const context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// Export utilities for global use
window.FamlyPortal = {
    showToast,
    confirmDialog,
    formatCurrency,
    formatDate,
    copyToClipboard,
    debounce,
    throttle
};
