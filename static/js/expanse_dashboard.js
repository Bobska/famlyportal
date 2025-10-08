/**
 * THE EXPANSE DASHBOARD - Command System JavaScript
 * Handles theme switching, mission clock, and UI enhancements
 */

(function() {
    'use strict';

    // Configuration
    const THEME_STORAGE_KEY = 'expanse_theme';
    const THEME_CLASSES = {
        earth: 'expanse-earth',
        mars: 'expanse-mars',
        opa: 'expanse-opa'
    };
    const DEFAULT_THEME = 'earth';

    /**
     * Initialize theme system on page load
     */
    function initializeTheme() {
        const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) || DEFAULT_THEME;
        const themeSelector = document.getElementById('themeSelector');
        
        if (themeSelector) {
            // Set the selector to saved theme
            themeSelector.value = savedTheme;
            
            // Apply the saved theme
            applyTheme(savedTheme);
            
            // Listen for theme changes
            themeSelector.addEventListener('change', function() {
                const newTheme = this.value;
                applyTheme(newTheme);
                localStorage.setItem(THEME_STORAGE_KEY, newTheme);
            });
        }
    }

    /**
     * Apply theme to the body and viewport
     * @param {string} themeName - Name of the theme (earth, mars, opa)
     */
    function applyTheme(themeName) {
        const body = document.body;
        const viewport = document.querySelector('[data-expanse-theme]');
        
        if (!body) return;

        // Remove all theme classes
        Object.values(THEME_CLASSES).forEach(themeClass => {
            body.classList.remove(themeClass);
        });

        // Add the new theme class
        const themeClass = THEME_CLASSES[themeName] || THEME_CLASSES[DEFAULT_THEME];
        body.classList.add(themeClass);

        // Update data attribute for potential CSS targeting
        if (viewport) {
            viewport.setAttribute('data-expanse-theme', themeName);
        }
    }

    /**
     * Initialize and update the mission time clock
     */
    function initializeClock() {
        const clockElement = document.getElementById('missionClock');
        if (!clockElement) return;

        function updateClock() {
            const now = new Date();
            
            // Format time with leading zeros
            const hours = String(now.getHours()).padStart(2, '0');
            const minutes = String(now.getMinutes()).padStart(2, '0');
            const seconds = String(now.getSeconds()).padStart(2, '0');
            
            clockElement.textContent = `${hours}:${minutes}:${seconds}`;
        }

        // Update immediately
        updateClock();
        
        // Update every second
        setInterval(updateClock, 1000);
    }

    /**
     * Calculate stardate for mission brief
     * Format: YYYY.DDD (year and day of year)
     */
    function calculateStardate() {
        const stardateElement = document.getElementById('stardate');
        if (!stardateElement) return;

        const now = new Date();
        const year = now.getFullYear();
        const start = new Date(year, 0, 0);
        const diff = now - start;
        const oneDay = 1000 * 60 * 60 * 24;
        const dayOfYear = Math.floor(diff / oneDay);
        
        const stardate = `${year}.${String(dayOfYear).padStart(3, '0')}`;
        stardateElement.textContent = stardate;
    }

    /**
     * Add subtle animation effects to operation cards
     */
    function enhanceOperationCards() {
        const cards = document.querySelectorAll('.operation-card--active');
        
        cards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                // Add subtle pulse to status indicator
                const indicator = this.querySelector('.status-indicator--active');
                if (indicator) {
                    indicator.style.animation = 'pulse-glow 1.5s ease-in-out infinite';
                }
            });

            card.addEventListener('mouseleave', function() {
                const indicator = this.querySelector('.status-indicator--active');
                if (indicator) {
                    indicator.style.animation = '';
                }
            });
        });
    }

    /**
     * Add CSS animation for status indicator pulse
     */
    function addAnimations() {
        const style = document.createElement('style');
        style.textContent = `
            @keyframes pulse-glow {
                0%, 100% {
                    box-shadow: 0 0 12px currentColor;
                    transform: scale(1);
                }
                50% {
                    box-shadow: 0 0 20px currentColor;
                    transform: scale(1.1);
                }
            }

            @keyframes terminal-blink {
                0%, 100% { opacity: 1; }
                50% { opacity: 0.5; }
            }

            .offline-terminal::after {
                content: "█";
                animation: terminal-blink 1s step-end infinite;
                display: inline-block;
                margin-left: 0.25em;
            }
        `;
        document.head.appendChild(style);
    }

    /**
     * Handle keyboard shortcuts
     */
    function initializeKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Alt + 1/2/3 for quick theme switching
            if (e.altKey) {
                let theme = null;
                
                switch(e.key) {
                    case '1':
                        theme = 'earth';
                        break;
                    case '2':
                        theme = 'mars';
                        break;
                    case '3':
                        theme = 'opa';
                        break;
                }

                if (theme) {
                    e.preventDefault();
                    const themeSelector = document.getElementById('themeSelector');
                    if (themeSelector) {
                        themeSelector.value = theme;
                        applyTheme(theme);
                        localStorage.setItem(THEME_STORAGE_KEY, theme);
                    }
                }
            }
        });
    }

    /**
     * Initialize dashboard tooltips for operations
     */
    function initializeTooltips() {
        const metaItems = document.querySelectorAll('.meta-item');
        
        metaItems.forEach(item => {
            if (item.textContent.includes('CLEARANCE')) {
                item.title = 'Access level required for this operation';
            } else if (item.textContent.includes('INTEGRATED')) {
                item.title = 'Operation is active and integrated';
            }
        });
    }

    /**
     * Add visual feedback for theme changes
     */
    function addThemeTransitionEffect() {
        const viewport = document.querySelector('.expanse-viewport');
        if (!viewport) return;

        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.attributeName === 'data-expanse-theme') {
                    // Add brief flash effect
                    viewport.style.transition = 'opacity 150ms ease-in-out';
                    viewport.style.opacity = '0.8';
                    
                    setTimeout(() => {
                        viewport.style.opacity = '1';
                    }, 150);
                }
            });
        });

        observer.observe(viewport, { attributes: true });
    }

    /**
     * Log system initialization (for debugging)
     */
    function logInitialization() {
        const currentTheme = localStorage.getItem(THEME_STORAGE_KEY) || DEFAULT_THEME;
        console.log(`%c▸ EXPANSE COMMAND SYSTEM ONLINE`, 'color: #4a9eff; font-weight: bold; font-size: 14px');
        console.log(`  Theme: ${currentTheme.toUpperCase()}`);
        console.log(`  Keyboard shortcuts: Alt+1 (Earth), Alt+2 (Mars), Alt+3 (OPA)`);
    }

    /**
     * Main initialization function
     */
    function init() {
        // Wait for DOM to be fully loaded
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', init);
            return;
        }

        // Initialize all systems
        initializeTheme();
        initializeClock();
        calculateStardate();
        enhanceOperationCards();
        addAnimations();
        initializeKeyboardShortcuts();
        initializeTooltips();
        addThemeTransitionEffect();
        logInitialization();
    }

    // Start initialization
    init();

})();
