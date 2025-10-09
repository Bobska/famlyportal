/**
 * THE EXPANSE - BOOT SEQUENCE ANIMATION
 * Simulates ship system initialization on page load
 */

(function() {
    'use strict';

    const BOOT_SEQUENCE = [
        { system: 'REACTOR CORE', delay: 100, duration: 800 },
        { system: 'LIFE SUPPORT', delay: 300, duration: 600 },
        { system: 'NAVIGATION', delay: 500, duration: 700 },
        { system: 'COMMUNICATIONS', delay: 700, duration: 500 },
        { system: 'TACTICAL SYSTEMS', delay: 900, duration: 600 },
        { system: 'SENSOR ARRAY', delay: 1100, duration: 500 },
        { system: 'CREW INTERFACE', delay: 1300, duration: 400 }
    ];

    const BOOT_MESSAGES = [
        'Initializing quantum processors...',
        'Calibrating sensor arrays...',
        'Establishing secure communications...',
        'Loading crew profiles...',
        'Synchronizing with central database...',
        'Activating holographic displays...',
        'Systems online. Welcome aboard.'
    ];

    let currentFaction = 'un';

    function createLaunchScreen() {
        const launchScreen = document.createElement('div');
        launchScreen.id = 'launchScreen';
        launchScreen.className = 'launch-screen active';
        launchScreen.innerHTML = `
            <div class="launch-container">
                <div class="launch-logo">
                    <div class="logo-ring-large"></div>
                    <div class="logo-center-large">
                        <div class="logo-text-large">FMLY</div>
                        <div class="logo-subtext-large">PORTAL</div>
                    </div>
                </div>
                
                <div class="launch-title">FAMILY COMMAND INTERFACE</div>
                <div class="launch-subtitle">SHIP MANAGEMENT SYSTEM v5.2.5</div>
                
                <button id="launchButton" class="launch-button">
                    <span class="launch-button-icon">▶</span>
                    <span class="launch-button-text">INITIALIZE SYSTEMS</span>
                </button>
                
                <div class="launch-disclaimer">
                    Click to activate audio systems and begin initialization sequence
                </div>
            </div>
        `;
        
        document.body.appendChild(launchScreen);
        return launchScreen;
    }

    function createBootScreen() {
        const bootScreen = document.createElement('div');
        bootScreen.id = 'bootScreen';
        bootScreen.className = 'boot-screen';
        bootScreen.innerHTML = `
            <div class="boot-container">
                <div class="boot-logo">
                    <div class="logo-ring"></div>
                    <div class="logo-center">
                        <div class="logo-text">FMLY</div>
                        <div class="logo-subtext">PORTAL</div>
                    </div>
                </div>
                
                <div class="boot-designation">
                    <div class="designation-label">SHIP DESIGNATION</div>
                    <div class="designation-value" id="bootDesignation">INITIALIZING...</div>
                </div>
                
                <div class="boot-audio-status" id="bootAudioStatus">
                    <span class="audio-indicator suspended" id="bootAudioIndicator"></span>
                    <span class="audio-text" id="bootAudioStatusText">AUDIO SUSPENDED - Click to activate</span>
                </div>
                
                <div class="boot-progress-container">
                    <div class="boot-systems" id="bootSystems"></div>
                    <div class="boot-progress-bar">
                        <div class="boot-progress-fill" id="bootProgressFill"></div>
                        <div class="boot-progress-percentage" id="bootProgressPercentage">0%</div>
                    </div>
                </div>
                
                <div class="boot-console" id="bootConsole"></div>
                
                <div class="boot-status" id="bootStatus">
                    <span class="status-dot pulsing"></span>
                    <span class="status-text">BOOTING SYSTEMS...</span>
                </div>
            </div>
        `;
        
        document.body.appendChild(bootScreen);
        return bootScreen;
    }

    function addSystemStatus(system, index) {
        const systemsContainer = document.getElementById('bootSystems');
        if (!systemsContainer) return;

        const systemEl = document.createElement('div');
        systemEl.className = 'boot-system';
        systemEl.innerHTML = `
            <div class="system-name">${system.system}</div>
            <div class="system-status" id="systemStatus${index}">
                <span class="status-text">INITIALIZING</span>
                <div class="status-spinner"></div>
            </div>
        `;
        
        systemsContainer.appendChild(systemEl);
        
        // Animate system initialization
        setTimeout(() => {
            systemEl.classList.add('active');
            
            // Play boot system sound if audio is enabled
            if (window.ExpanseAudio && window.ExpanseAudio.isEnabled()) {
                window.ExpanseAudio.play('bootSystem', 0.15);
            }
            
            setTimeout(() => {
                const statusEl = document.getElementById(`systemStatus${index}`);
                if (statusEl) {
                    statusEl.innerHTML = '<span class="status-text success">ONLINE</span><span class="status-check">✓</span>';
                    
                    // Play success beep when system comes online
                    if (window.ExpanseAudio && window.ExpanseAudio.isEnabled()) {
                        window.ExpanseAudio.play('click', 0.1);
                    }
                }
            }, system.duration);
        }, system.delay);
    }

    function updateProgress() {
        const progressFill = document.getElementById('bootProgressFill');
        const progressPercentage = document.getElementById('bootProgressPercentage');
        
        let progress = 0;
        const totalTime = BOOT_SEQUENCE[BOOT_SEQUENCE.length - 1].delay + 
                         BOOT_SEQUENCE[BOOT_SEQUENCE.length - 1].duration;
        const interval = 50;
        const increment = (100 / totalTime) * interval;
        
        const progressInterval = setInterval(() => {
            progress += increment;
            if (progress >= 100) {
                progress = 100;
                clearInterval(progressInterval);
            }
            
            if (progressFill) progressFill.style.width = `${progress}%`;
            if (progressPercentage) progressPercentage.textContent = `${Math.floor(progress)}%`;
        }, interval);
    }

    function addConsoleMessage(message, delay) {
        setTimeout(() => {
            const console = document.getElementById('bootConsole');
            if (!console) return;
            
            const messageEl = document.createElement('div');
            messageEl.className = 'console-message';
            messageEl.textContent = `> ${message}`;
            console.appendChild(messageEl);
            
            // Auto scroll to bottom smoothly
            console.scrollTo({
                top: console.scrollHeight,
                behavior: 'smooth'
            });
        }, delay);
    }

    function updateBootStatus(text, success = false) {
        const statusEl = document.getElementById('bootStatus');
        if (!statusEl) return;
        
        statusEl.innerHTML = `
            <span class="status-dot ${success ? 'success' : 'pulsing'}"></span>
            <span class="status-text">${text}</span>
        `;
    }

    function revealFactionLogo() {
        const logo = document.querySelector('.boot-logo');
        const designation = document.getElementById('bootDesignation');
        
        if (logo) {
            logo.classList.add('revealed');
        }
        
        if (designation) {
            // Get family name from page if available
            const familyName = document.querySelector('.designation-name')?.textContent || 'UNKNOWN';
            designation.textContent = familyName;
            designation.classList.add('revealed');
        }
    }

    function completeBootSequence(bootScreen) {
        updateBootStatus('ALL SYSTEMS OPERATIONAL', true);
        
        setTimeout(() => {
            bootScreen.classList.add('fade-out');
            
            setTimeout(() => {
                bootScreen.remove();
                
                // Ensure main interface is visible
                const spaceInterface = document.querySelector('.space-interface');
                if (spaceInterface) {
                    spaceInterface.style.opacity = '1';
                    spaceInterface.classList.add('revealed');
                }
                
                // Ensure body is not black
                document.body.style.backgroundColor = '';
                
                // Play welcome sound if audio is enabled
                if (window.ExpanseAudio && window.ExpanseAudio.isEnabled()) {
                    window.ExpanseAudio.play('bootComplete');
                }
                
                console.log('✅ Boot sequence complete - Interface revealed');
            }, 800);
        }, 500);
    }

    function runBootSequence() {
        // Get faction from localStorage
        currentFaction = localStorage.getItem('expanseFaction') || 'un';
        
        const bootScreen = createBootScreen();
        bootScreen.setAttribute('data-faction', currentFaction);
        
        // Hide main interface initially
        const spaceInterface = document.querySelector('.space-interface');
        if (spaceInterface) {
            spaceInterface.style.opacity = '0';
        }
        
        // Start boot sequence
        setTimeout(() => {
            bootScreen.classList.add('active');
            
            // Play boot start sound
            if (window.ExpanseAudio && window.ExpanseAudio.isEnabled()) {
                window.ExpanseAudio.play('bootStart', 0.2);
            }
            
            // Add systems
            BOOT_SEQUENCE.forEach((system, index) => {
                addSystemStatus(system, index);
            });
            
            // Update progress bar
            updateProgress();
            
            // Add console messages
            BOOT_MESSAGES.forEach((message, index) => {
                addConsoleMessage(message, index * 400);
            });
            
            // Status updates
            setTimeout(() => updateBootStatus('LOADING CORE SYSTEMS...'), 500);
            setTimeout(() => updateBootStatus('INITIALIZING CREW INTERFACE...'), 2000);
            setTimeout(() => updateBootStatus('FINALIZING STARTUP...'), 3000);
            
            // Reveal logo
            setTimeout(() => revealFactionLogo(), 1500);
            
            // Complete boot sequence
            const totalBootTime = BOOT_SEQUENCE[BOOT_SEQUENCE.length - 1].delay + 
                                 BOOT_SEQUENCE[BOOT_SEQUENCE.length - 1].duration + 1000;
            setTimeout(() => completeBootSequence(bootScreen), totalBootTime);
            
        }, 100);
    }

    function initializeLaunchSequence() {
        // Check if user has seen boot sequence before
        const skipBoot = sessionStorage.getItem('expanseBootSeen');
        if (skipBoot) {
            // Still show interface with fade-in
            const spaceInterface = document.querySelector('.space-interface');
            if (spaceInterface) {
                spaceInterface.style.opacity = '1';
                spaceInterface.classList.add('revealed');
            }
            console.log('⏩ Boot sequence skipped - Already seen this session');
            return;
        }

        // Show launch screen first
        const launchScreen = createLaunchScreen();
        
        // Hide main interface initially
        const spaceInterface = document.querySelector('.space-interface');
        if (spaceInterface) {
            spaceInterface.style.opacity = '0';
        }
        
        // Add click handler to launch button
        const launchButton = document.getElementById('launchButton');
        if (launchButton) {
            launchButton.addEventListener('click', async () => {
                console.log('🚀 Launch button clicked - Initializing systems...');
                
                // Activate audio system immediately
                if (window.ExpanseAudio) {
                    // This click will resume the audio context
                    if (window.ExpanseAudio.isEnabled()) {
                        // Play a launch sound
                        window.ExpanseAudio.play('click', 0.3);
                    }
                }
                
                // Animate button press
                launchButton.classList.add('pressed');
                
                // Wait a moment, then fade out launch screen
                setTimeout(() => {
                    launchScreen.classList.add('fade-out');
                    
                    // Remove launch screen and start boot sequence
                    setTimeout(() => {
                        launchScreen.remove();
                        
                        // Mark boot as seen for this session
                        sessionStorage.setItem('expanseBootSeen', 'true');
                        
                        // Start boot sequence
                        runBootSequence();
                    }, 800);
                }, 300);
            });
        }
    }

    // Public API
    window.ExpanseBoot = {
        run: runBootSequence,
        skip: function() {
            const bootScreen = document.getElementById('bootScreen');
            if (bootScreen) {
                bootScreen.remove();
                const spaceInterface = document.querySelector('.space-interface');
                if (spaceInterface) {
                    spaceInterface.classList.add('revealed');
                }
            }
        }
    };

    // Auto-run on page load if not explicitly disabled
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initializeLaunchSequence);
    } else {
        initializeLaunchSequence();
    }

})();
