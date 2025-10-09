/**
 * MULTI-STYLE DASHBOARD JavaScript
 * Handles switching between three completely different dashboard styles
 */

(function() {
    'use strict';

    // Configuration
    const STYLE_STORAGE_KEY = 'dashboard_style';
    const DEFAULT_STYLE = 'quantum';
    
    const STYLE_CLASSES = {
        quantum: 'layout-quantum',
        terminal: 'layout-terminal',
        neon: 'layout-neon'
    };

    /**
     * Initialize the dashboard style system
     */
    function initializeStyle() {
        const savedStyle = localStorage.getItem(STYLE_STORAGE_KEY) || DEFAULT_STYLE;
        const styleSelector = document.getElementById('styleSelect');
        
        if (styleSelector) {
            // Set the selector to saved style
            styleSelector.value = savedStyle;
            
            // Apply the saved style
            applyStyle(savedStyle);
            
            // Listen for style changes
            styleSelector.addEventListener('change', function() {
                const newStyle = this.value;
                applyStyle(newStyle);
                localStorage.setItem(STYLE_STORAGE_KEY, newStyle);
            });
        } else {
            // Fallback: apply saved style even if selector not found
            applyStyle(savedStyle);
        }
    }

    /**
     * Apply a style by showing/hiding layout containers
     * @param {string} styleName - Name of the style (quantum, terminal, neon)
     */
    function applyStyle(styleName) {
        const container = document.getElementById('dashboardContainer');
        if (!container) return;

        // Update container data attribute
        container.setAttribute('data-style', styleName);

        // Hide all layouts
        document.querySelectorAll('.layout').forEach(layout => {
            layout.classList.remove('active');
        });

        // Show the selected layout
        const selectedLayout = document.querySelector(`.layout-${styleName}`);
        if (selectedLayout) {
            // Small delay to allow fade out animation
            setTimeout(() => {
                selectedLayout.classList.add('active');
            }, 50);
        }

        // Initialize style-specific features
        switch(styleName) {
            case 'quantum':
                initQuantumEffects();
                break;
            case 'terminal':
                initTerminalEffects();
                break;
            case 'neon':
                initNeonEffects();
                break;
        }
    }

    /**
     * Initialize Quantum Glass style effects
     */
    function initQuantumEffects() {
        // Add mouse tracking for glow effects
        const appCards = document.querySelectorAll('.app-card-quantum');
        
        appCards.forEach(card => {
            card.addEventListener('mousemove', function(e) {
                const rect = this.getBoundingClientRect();
                const x = ((e.clientX - rect.left) / rect.width) * 100;
                const y = ((e.clientY - rect.top) / rect.height) * 100;
                
                this.style.setProperty('--mouse-x', `${x}%`);
                this.style.setProperty('--mouse-y', `${y}%`);
            });
        });

        // Update weather if available
        updateWeather('quantum');
    }

    /**
     * Initialize Terminal Matrix style effects
     */
    function initTerminalEffects() {
        // Start terminal clock
        updateTerminalClock();
        setInterval(updateTerminalClock, 1000);

        // Add typing effect to terminal lines (on first load)
        const lines = document.querySelectorAll('.terminal-line');
        lines.forEach((line, index) => {
            line.style.animation = `typeIn 0.5s ease-out ${index * 0.1}s both`;
        });

        // Add CSS animation for typing effect
        if (!document.getElementById('terminal-animations')) {
            const style = document.createElement('style');
            style.id = 'terminal-animations';
            style.textContent = `
                @keyframes typeIn {
                    from {
                        opacity: 0;
                        transform: translateX(-10px);
                    }
                    to {
                        opacity: 1;
                        transform: translateX(0);
                    }
                }
            `;
            document.head.appendChild(style);
        }
    }

    /**
     * Update terminal clock
     */
    function updateTerminalClock() {
        const clockElement = document.getElementById('terminalClock');
        if (!clockElement) return;

        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        clockElement.textContent = `${hours}:${minutes}:${seconds}`;
    }

    /**
     * Initialize Neon Synthwave style effects
     */
    function initNeonEffects() {
        // Add hover animation to neon cards
        const neonCards = document.querySelectorAll('.neon-app-card');
        
        neonCards.forEach(card => {
            card.addEventListener('mouseenter', function() {
                this.style.animation = 'neonPulse 0.5s ease-out';
            });
            
            card.addEventListener('animationend', function() {
                this.style.animation = '';
            });
        });

        // Add neon pulse animation
        if (!document.getElementById('neon-animations')) {
            const style = document.createElement('style');
            style.id = 'neon-animations';
            style.textContent = `
                @keyframes neonPulse {
                    0%, 100% { 
                        filter: brightness(1);
                    }
                    50% { 
                        filter: brightness(1.5);
                    }
                }
            `;
            document.head.appendChild(style);
        }

        // Update weather if available
        updateWeather('neon');
    }

    /**
     * Update weather data for quantum style
     * @param {string} style - The current style name
     */
    function updateWeather(style) {
        // Check if weather data is available in the page
        const tempElement = document.getElementById(`${style}Temp`);
        const weatherElement = document.getElementById(`${style}Weather`);
        
        if (!tempElement || !weatherElement) return;

        // Try to get weather from Django context (if available)
        // This would need to be passed from the backend
        // For now, we'll just ensure the elements exist
        
        // You could add AJAX call here to fetch weather data
        // or read it from data attributes set by Django template
    }

    /**
     * Add keyboard shortcuts for quick style switching
     */
    function initKeyboardShortcuts() {
        document.addEventListener('keydown', function(e) {
            // Ctrl + 1/2/3 for quick style switching
            if (e.ctrlKey) {
                let style = null;
                
                switch(e.key) {
                    case '1':
                        style = 'quantum';
                        break;
                    case '2':
                        style = 'terminal';
                        break;
                    case '3':
                        style = 'neon';
                        break;
                }

                if (style) {
                    e.preventDefault();
                    const styleSelector = document.getElementById('styleSelect');
                    if (styleSelector) {
                        styleSelector.value = style;
                    }
                    applyStyle(style);
                    localStorage.setItem(STYLE_STORAGE_KEY, style);
                }
            }
        });
    }

    /**
     * Log system initialization
     */
    function logInitialization() {
        const currentStyle = localStorage.getItem(STYLE_STORAGE_KEY) || DEFAULT_STYLE;
        const styleNames = {
            quantum: 'Quantum Glass',
            terminal: 'Terminal Matrix',
            neon: 'Neon Synthwave'
        };
        
        console.log(`%c✨ MULTI-DASHBOARD SYSTEM INITIALIZED`, 'color: #667eea; font-weight: bold; font-size: 14px');
        console.log(`  Current Style: ${styleNames[currentStyle]}`);
        console.log(`  Keyboard shortcuts: Ctrl+1 (Quantum), Ctrl+2 (Terminal), Ctrl+3 (Neon)`);
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
        initializeStyle();
        initKeyboardShortcuts();
        logInitialization();
    }

    // Start initialization
    init();

})();
