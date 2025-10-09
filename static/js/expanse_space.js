/**
 * THE EXPANSE - SPACESHIP INTERFACE SYSTEM
 * Controls faction switching, mission clock, and holographic effects
 */

(function() {
    'use strict';

    // ==========================================================================
    // STATE MANAGEMENT
    // ==========================================================================
    
    const STATE = {
        currentFaction: 'un',
        clockInterval: null,
        initialized: false
    };

    const FACTIONS = {
        un: {
            name: 'UN NAVY',
            desc: 'United Nations Naval Command',
            color: '#3b82f6'
        },
        belter: {
            name: 'BELTER OPS',
            desc: 'Outer Planets Alliance Engineering',
            color: '#fb923c'
        },
        proto: {
            name: 'PROTOMOLECULE',
            desc: 'Alien Technology Interface',
            color: '#06b6d4'
        }
    };

    // ==========================================================================
    // INITIALIZATION
    // ==========================================================================

    function init() {
        if (STATE.initialized) return;
        
        console.log('🚀 Initializing Expanse Spaceship Interface...');
        
        // Initialize audio first
        if (window.ExpanseAudio) {
            window.ExpanseAudio.init();
        }
        
        // Load saved faction preference
        loadFactionPreference();
        
        // Initialize faction selector
        initFactionSelector();
        
        // Initialize audio toggle
        initAudioToggle();
        
        // Start mission clock
        initMissionClock();
        
        // Add holographic effects
        initHolographicEffects();
        
        // Add keyboard shortcuts
        initKeyboardShortcuts();
        
        STATE.initialized = true;
        console.log('✅ Expanse Interface Online');
    }

    // ==========================================================================
    // FACTION MANAGEMENT
    // ==========================================================================

    function loadFactionPreference() {
        const saved = localStorage.getItem('expanseFaction');
        if (saved && FACTIONS[saved]) {
            STATE.currentFaction = saved;
            applyFaction(saved, false);
        } else {
            applyFaction('un', false);
        }
    }

    function initFactionSelector() {
        const selector = document.getElementById('factionSelector');
        console.log('🔍 Looking for faction selector...', selector);
        if (!selector) {
            console.error('❌ Faction selector not found!');
            return;
        }
        
        console.log('✅ Faction selector found, current faction:', STATE.currentFaction);
        selector.value = STATE.currentFaction;
        selector.addEventListener('change', handleFactionChange);
        console.log('✅ Change event listener added');
    }

    function handleFactionChange(e) {
        const faction = e.target.value;
        console.log('🔄 Faction change requested:', faction);
        if (!FACTIONS[faction]) {
            console.error('❌ Invalid faction:', faction);
            return;
        }
        
        // Play faction change sound
        if (window.ExpanseAudio) {
            window.ExpanseAudio.play('factionChange');
        }
        
        applyFaction(faction, true);
        saveFactionPreference(faction);
    }

    function applyFaction(faction, animate = true) {
        const interfaceEl = document.querySelector('.space-interface');
        console.log('🎨 Applying faction:', faction, 'Interface element:', interfaceEl);
        if (!interfaceEl) {
            console.error('❌ Space interface element not found!');
            return;
        }
        
        // Update data attribute
        const oldFaction = interfaceEl.getAttribute('data-faction');
        interfaceEl.setAttribute('data-faction', faction);
        console.log(`🎯 Faction changed from ${oldFaction} to ${faction}`);
        
        // Force a reflow to ensure the CSS updates
        void interfaceEl.offsetHeight;
        
        // Update state
        STATE.currentFaction = faction;
        
        // Log faction change
        console.log(`✅ Faction applied: ${FACTIONS[faction].name}`);
        console.log(`   Color: ${FACTIONS[faction].color}`);
        
        // Update the selector if it's out of sync
        const selector = document.getElementById('factionSelector');
        if (selector && selector.value !== faction) {
            selector.value = faction;
        }
        
        // Update debug display
        const debugEl = document.getElementById('debugFaction');
        if (debugEl) {
            debugEl.textContent = `Active: ${FACTIONS[faction].name} (data-faction="${faction}")`;
        }
    }

    function saveFactionPreference(faction) {
        try {
            localStorage.setItem('expanseFaction', faction);
            console.log(`💾 Saved faction preference: ${faction}`);
        } catch (e) {
            console.warn('Failed to save faction preference:', e);
        }
    }

    // ==========================================================================
    // MISSION CLOCK
    // ==========================================================================

    function initMissionClock() {
        updateMissionClock();
        STATE.clockInterval = setInterval(updateMissionClock, 1000);
    }

    function updateMissionClock() {
        const clockDisplay = document.getElementById('missionClock');
        if (!clockDisplay) return;
        
        const now = new Date();
        const hours = String(now.getHours()).padStart(2, '0');
        const minutes = String(now.getMinutes()).padStart(2, '0');
        const seconds = String(now.getSeconds()).padStart(2, '0');
        
        clockDisplay.textContent = `${hours}:${minutes}:${seconds}`;
    }

    function stopMissionClock() {
        if (STATE.clockInterval) {
            clearInterval(STATE.clockInterval);
            STATE.clockInterval = null;
        }
    }

    // ==========================================================================
    // HOLOGRAPHIC EFFECTS
    // ==========================================================================

    function initHolographicEffects() {
        // Add hover sound effects preparation (if you want audio)
        const modules = document.querySelectorAll('.holo-module');
        modules.forEach(module => {
            module.addEventListener('mouseenter', handleModuleHover);
            module.addEventListener('mouseleave', handleModuleLeave);
            module.addEventListener('click', handleModuleClick);
        });
        
        // Add scanline animation variations
        addScanlineVariations();
        
        // Add random flicker effects to readouts
        addReadoutFlickers();
    }

    function handleModuleHover(e) {
        // Play hover sound
        if (window.ExpanseAudio) {
            window.ExpanseAudio.play('hover');
        }
        
        // Add ripple effect
        const module = e.currentTarget;
        const ripple = document.createElement('div');
        ripple.className = 'module-ripple';
        module.appendChild(ripple);
        
        setTimeout(() => {
            ripple.remove();
        }, 600);
        
        // Show expanded details
        expandModuleDetails(module);
    }

    function handleModuleClick(e) {
        // Play click sound
        if (window.ExpanseAudio) {
            window.ExpanseAudio.play('click');
        }
        
        const module = e.currentTarget;
        module.style.transform = 'scale(0.98)';
        setTimeout(() => {
            module.style.transform = '';
        }, 150);
    }
    
    function expandModuleDetails(module) {
        // Check if details already exist
        if (module.querySelector('.module-expanded-details')) return;
        
        const detailsEl = document.createElement('div');
        detailsEl.className = 'module-expanded-details';
        detailsEl.innerHTML = `
            <div class="expanded-stats">
                <div class="stat-item-small">
                    <div class="stat-label-small">LAST ACCESSED</div>
                    <div class="stat-value-small">2 hours ago</div>
                </div>
                <div class="stat-item-small">
                    <div class="stat-label-small">STATUS</div>
                    <div class="stat-value-small">Active</div>
                </div>
            </div>
            <div class="expanded-actions">
                <button class="action-btn action-btn-primary">
                    <i class="bi bi-box-arrow-up-right"></i> Open
                </button>
                <button class="action-btn action-btn-secondary">
                    <i class="bi bi-info-circle"></i> Details
                </button>
            </div>
        `;
        
        module.appendChild(detailsEl);
    }
    
    function collapseModuleDetails(module) {
        const details = module.querySelector('.module-expanded-details');
        if (details) {
            details.remove();
        }
    }
    
    // Add mouse leave handler to collapse details
    function handleModuleLeave(e) {
        collapseModuleDetails(e.currentTarget);
    }

    // ==========================================================================
    // AUDIO CONTROL
    // ==========================================================================

    function initAudioToggle() {
        const toggleBtn = document.getElementById('audioToggle');
        const iconEl = document.getElementById('audioIcon');
        
        if (!toggleBtn || !iconEl) return;
        
        // Set initial state
        updateAudioIcon(iconEl, toggleBtn);
        
        // Add click handler
        toggleBtn.addEventListener('click', () => {
            if (window.ExpanseAudio) {
                const enabled = window.ExpanseAudio.toggle();
                updateAudioIcon(iconEl, toggleBtn);
                // Update visual status indicators
                window.ExpanseAudio.updateStatus();
            }
        });
    }

    function updateAudioIcon(iconEl, btnEl) {
        if (!window.ExpanseAudio) return;
        
        const enabled = window.ExpanseAudio.isEnabled();
        
        if (enabled) {
            iconEl.className = 'bi bi-volume-up-fill';
            btnEl.classList.add('enabled');
            btnEl.title = 'Audio Enabled - Click to Mute';
        } else {
            iconEl.className = 'bi bi-volume-mute-fill';
            btnEl.classList.remove('enabled');
            btnEl.title = 'Audio Disabled - Click to Enable';
        }
    }

    function addScanlineVariations() {
        const scanlines = document.querySelector('.holo-scanlines');
        if (!scanlines) return;
        
        // Randomly adjust scanline opacity for subtle variation
        setInterval(() => {
            const opacity = 0.03 + (Math.random() * 0.02);
            scanlines.style.opacity = opacity;
        }, 3000);
    }

    function addReadoutFlickers() {
        const readouts = document.querySelectorAll('.readout-value, .stat-value');
        
        readouts.forEach(readout => {
            setInterval(() => {
                if (Math.random() > 0.97) { // 3% chance every interval
                    readout.style.opacity = '0.7';
                    setTimeout(() => {
                        readout.style.opacity = '1';
                    }, 100);
                }
            }, 2000);
        });
    }

    // ==========================================================================
    // KEYBOARD SHORTCUTS
    // ==========================================================================

    function initKeyboardShortcuts() {
        document.addEventListener('keydown', handleKeyPress);
    }

    function handleKeyPress(e) {
        // Only activate if not typing in an input
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA') {
            return;
        }
        
        // Faction shortcuts: 1, 2, 3
        if (e.key === '1') {
            switchToFaction('un');
        } else if (e.key === '2') {
            switchToFaction('belter');
        } else if (e.key === '3') {
            switchToFaction('proto');
        }
    }

    function switchToFaction(faction) {
        if (!FACTIONS[faction]) return;
        
        const selector = document.getElementById('factionSelector');
        if (selector) {
            selector.value = faction;
            applyFaction(faction, true);
            saveFactionPreference(faction);
            
            // Show brief notification
            showFactionNotification(faction);
        }
    }

    function showFactionNotification(faction) {
        // Remove existing notification if any
        const existing = document.querySelector('.faction-notification');
        if (existing) {
            existing.remove();
        }
        
        // Create notification
        const notification = document.createElement('div');
        notification.className = 'faction-notification';
        notification.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%) scale(0);
            padding: 2rem 3rem;
            background: rgba(0, 0, 0, 0.95);
            border: 2px solid ${FACTIONS[faction].color};
            box-shadow: 0 0 40px ${FACTIONS[faction].color}80;
            backdrop-filter: blur(20px);
            z-index: 9999;
            font-family: 'Orbitron', sans-serif;
            font-size: 1.5rem;
            font-weight: 700;
            letter-spacing: 0.2em;
            color: ${FACTIONS[faction].color};
            text-shadow: 0 0 20px ${FACTIONS[faction].color}80;
            text-align: center;
            clip-path: polygon(10px 0, calc(100% - 10px) 0, 100% 10px, 100% calc(100% - 10px), calc(100% - 10px) 100%, 10px 100%, 0 calc(100% - 10px), 0 10px);
            transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.3s ease;
            opacity: 0;
        `;
        notification.innerHTML = `
            <div>${FACTIONS[faction].name}</div>
            <div style="font-size: 0.8rem; margin-top: 0.5rem; opacity: 0.7; letter-spacing: 0.15em;">
                ${FACTIONS[faction].desc}
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        requestAnimationFrame(() => {
            notification.style.transform = 'translate(-50%, -50%) scale(1)';
            notification.style.opacity = '1';
        });
        
        // Animate out
        setTimeout(() => {
            notification.style.transform = 'translate(-50%, -50%) scale(0)';
            notification.style.opacity = '0';
            
            setTimeout(() => {
                notification.remove();
            }, 300);
        }, 2000);
    }

    // ==========================================================================
    // CLEANUP
    // ==========================================================================

    function cleanup() {
        stopMissionClock();
        document.removeEventListener('keydown', handleKeyPress);
        
        const modules = document.querySelectorAll('.holo-module');
        modules.forEach(module => {
            module.removeEventListener('mouseenter', handleModuleHover);
            module.removeEventListener('click', handleModuleClick);
        });
        
        STATE.initialized = false;
        console.log('🛑 Expanse Interface Shutdown');
    }

    // ==========================================================================
    // PUBLIC API
    // ==========================================================================

    window.ExpanseInterface = {
        init,
        cleanup,
        switchFaction: switchToFaction,
        getCurrentFaction: () => STATE.currentFaction,
        getFactions: () => FACTIONS
    };

    // ==========================================================================
    // AUTO-INITIALIZE
    // ==========================================================================

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Cleanup on page unload
    window.addEventListener('beforeunload', cleanup);

    // Reinitialize when page becomes visible again (e.g., back button navigation)
    document.addEventListener('visibilitychange', () => {
        if (!document.hidden) {
            console.log('👁️ Page visible again, checking audio system...');
            if (window.ExpanseAudio) {
                window.ExpanseAudio.reinit();
            }
        }
    });

    // Also reinitialize on pageshow event (handles bfcache)
    window.addEventListener('pageshow', (event) => {
        if (event.persisted) {
            console.log('🔄 Page restored from cache, reinitializing audio...');
            if (window.ExpanseAudio) {
                window.ExpanseAudio.reinit();
            }
        }
    });

    // ==========================================================================
    // ADDITIONAL FEATURES (Optional Enhancement)
    // ==========================================================================

    /**
     * Add more advanced effects here:
     * - Sound effects for UI interactions
     * - Particle effects on hover
     * - Advanced animations for faction transitions
     * - Real-time system status updates
     * - Weather data integration
     * - Notification system for alerts
     */

    // Example: Add weather data if available
    function updateWeatherData() {
        const weatherIcon = document.getElementById('weatherIcon');
        const weatherTemp = document.getElementById('weatherTemp');
        const weatherCondition = document.getElementById('weatherCondition');
        
        if (!weatherIcon || !weatherTemp || !weatherCondition) return;
        
        // This would normally fetch real weather data
        // For now, it's static in the template
        
        // You can integrate with weather APIs here if needed
        console.log('Weather system ready for integration');
    }

    // Example: System log simulation
    function simulateSystemLog() {
        const logContainer = document.querySelector('.system-log');
        if (!logContainer) return;
        
        const logs = [
            'Comms array aligned',
            'Reactor core nominal',
            'Life support stable',
            'Navigation systems online',
            'Sensor sweep complete',
            'Data sync successful'
        ];
        
        setInterval(() => {
            if (Math.random() > 0.8) { // 20% chance
                const logEntry = document.createElement('div');
                logEntry.className = 'log-entry';
                
                const now = new Date();
                const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}`;
                
                const randomLog = logs[Math.floor(Math.random() * logs.length)];
                
                logEntry.innerHTML = `
                    <span class="log-time">${timeStr}</span>
                    <span>${randomLog}</span>
                `;
                
                logContainer.insertBefore(logEntry, logContainer.firstChild);
                
                // Keep only last 5 entries
                while (logContainer.children.length > 5) {
                    logContainer.removeChild(logContainer.lastChild);
                }
            }
        }, 5000);
    }

    // Initialize additional features
    setTimeout(() => {
        updateWeatherData();
        simulateSystemLog();
    }, 1000);

})();
