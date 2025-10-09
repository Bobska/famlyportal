/**
 * THE EXPANSE - AUDIO SYSTEM
 * Manages UI sounds and ambient ship audio
 */

(function() {
    'use strict';

    // Audio state
    const STATE = {
        enabled: false,
        volume: 0.3,
        ambientVolume: 0.1,
        initialized: false,
        audioContext: null,
        sounds: {}
    };

    // Sound definitions (using Web Audio API oscillators for now)
    // In production, these would be actual audio files
    const SOUND_DEFS = {
        click: { freq: 800, duration: 50, type: 'sine' },
        hover: { freq: 600, duration: 30, type: 'sine' },
        factionChange: { freq: 400, duration: 200, type: 'square' },
        bootComplete: { freq: [400, 600, 800], duration: 300, type: 'sine' },
        bootStart: { freq: [300, 400], duration: 200, type: 'sine' },
        bootSystem: { freq: 500, duration: 80, type: 'sine' },
        notification: { freq: [600, 800], duration: 150, type: 'triangle' },
        error: { freq: [300, 200], duration: 200, type: 'sawtooth' },
        success: { freq: [400, 600], duration: 150, type: 'sine' }
    };

    // Initialize Audio Context
    function init() {
        if (STATE.initialized) return;

        // Check localStorage for audio preference
        const savedPreference = localStorage.getItem('expanseAudioEnabled');
        STATE.enabled = savedPreference === 'true';

        const savedVolume = localStorage.getItem('expanseAudioVolume');
        if (savedVolume) {
            STATE.volume = parseFloat(savedVolume);
        }

        // Create AudioContext immediately (will be suspended by browser)
        initAudioContext();

        // Only these gestures are recognized by Chrome as "user gestures"
        // mousemove, wheel, and scroll are NOT valid for AudioContext.resume()
        const validGestures = [
            'click',      // Mouse click - valid
            'contextmenu', // Right-click - valid
            'auxclick',   // Middle-click - valid
            'dblclick',   // Double-click - valid
            'mouseup',    // Mouse button release - valid
            'pointerup',  // Pointer release - valid
            'touchend',   // Touch end - valid
            'keydown',    // Keyboard press - valid
            'keyup'       // Keyboard release - valid
        ];
        
        validGestures.forEach(event => {
            document.addEventListener(event, resumeAudioContext, { passive: true });
        });

        STATE.initialized = true;
        console.log('🔊 Audio system initialized (enabled:', STATE.enabled, ')');
        console.log('🎵 Audio will activate on first user gesture (click, key press, touch)');
    }

    function initAudioContext() {
        if (STATE.audioContext) return;
        
        try {
            STATE.audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('🎵 Audio Context created, state:', STATE.audioContext.state);
            
            // Listen for state changes and update visual indicators
            STATE.audioContext.addEventListener('statechange', () => {
                console.log('🎵 Audio Context state changed to:', STATE.audioContext.state);
                updateAudioStatusIndicators();
            });
            
            // Initial update
            updateAudioStatusIndicators();
            
        } catch (error) {
            console.error('Failed to create audio context:', error);
        }
    }

    // Update audio status visual indicators
    function updateAudioStatusIndicators() {
        const state = STATE.audioContext?.state || 'suspended';
        const enabled = STATE.enabled;
        
        // Update dashboard indicators
        const dashboardStatus = document.getElementById('audioStatus');
        const dashboardIndicator = document.getElementById('audioIndicator');
        const dashboardText = document.getElementById('audioStatusText');
        
        if (dashboardStatus && dashboardIndicator && dashboardText) {
            // Remove all state classes
            dashboardStatus.classList.remove('running', 'disabled');
            dashboardIndicator.classList.remove('running', 'suspended', 'disabled');
            
            if (!enabled) {
                dashboardStatus.classList.add('disabled');
                dashboardIndicator.classList.add('disabled');
                dashboardText.textContent = 'AUDIO DISABLED';
            } else if (state === 'running') {
                dashboardStatus.classList.add('running');
                dashboardIndicator.classList.add('running');
                dashboardText.textContent = 'AUDIO ONLINE';
            } else {
                dashboardIndicator.classList.add('suspended');
                dashboardText.textContent = 'AUDIO SUSPENDED';
            }
        }
        
        // Update boot screen indicators
        const bootStatus = document.getElementById('bootAudioStatus');
        const bootIndicator = document.getElementById('bootAudioIndicator');
        const bootText = document.getElementById('bootAudioStatusText');
        
        if (bootStatus && bootIndicator && bootText) {
            // Remove all state classes
            bootStatus.classList.remove('running', 'disabled');
            bootIndicator.classList.remove('running', 'suspended', 'disabled');
            
            if (!enabled) {
                bootStatus.classList.add('disabled');
                bootIndicator.classList.add('disabled');
                bootText.textContent = 'AUDIO DISABLED';
            } else if (state === 'running') {
                bootStatus.classList.add('running');
                bootIndicator.classList.add('running');
                bootText.textContent = 'AUDIO ONLINE';
            } else {
                bootIndicator.classList.add('suspended');
                bootText.textContent = 'AUDIO SUSPENDED - Click to activate';
            }
        }
    }

    // Resume audio context on user interaction
    async function resumeAudioContext() {
        if (!STATE.audioContext) return;
        if (STATE.audioContext.state === 'suspended') {
            try {
                await STATE.audioContext.resume();
                console.log('🎵 Audio Context resumed on user interaction');
            } catch (err) {
                console.warn('Could not resume audio context:', err);
            }
        }
    }

    // Play a sound
    function playSound(soundName, volumeOverride = null) {
        if (!STATE.enabled) {
            console.log('🔇 Audio disabled, not playing:', soundName);
            return;
        }
        
        if (!STATE.audioContext) {
            console.warn('⏳ Audio context not yet created');
            return;
        }
        
        if (STATE.audioContext.state !== 'running') {
            console.log('⏸️  Audio context not running (state:', STATE.audioContext.state + '), sound will play after user interaction');
            return;
        }
        
        const soundDef = SOUND_DEFS[soundName];
        if (!soundDef) {
            console.warn('Sound not found:', soundName);
            return;
        }

        const volume = volumeOverride !== null ? volumeOverride : STATE.volume;

        try {
            if (Array.isArray(soundDef.freq)) {
                // Multi-tone sound
                playMultiTone(soundDef.freq, soundDef.duration, soundDef.type, volume);
            } else {
                // Single tone
                playSingleTone(soundDef.freq, soundDef.duration, soundDef.type, volume);
            }
            console.log('🔊 Playing sound:', soundName);
        } catch (error) {
            console.warn('Error playing sound:', error);
        }
    }

    function playSingleTone(frequency, duration, type, volume) {
        const context = STATE.audioContext;
        const oscillator = context.createOscillator();
        const gainNode = context.createGain();

        oscillator.connect(gainNode);
        gainNode.connect(context.destination);

        oscillator.type = type;
        oscillator.frequency.value = frequency;

        // Envelope
        gainNode.gain.setValueAtTime(0, context.currentTime);
        gainNode.gain.linearRampToValueAtTime(volume, context.currentTime + 0.01);
        gainNode.gain.exponentialRampToValueAtTime(0.01, context.currentTime + duration / 1000);

        oscillator.start(context.currentTime);
        oscillator.stop(context.currentTime + duration / 1000);
    }

    function playMultiTone(frequencies, duration, type, volume) {
        const context = STATE.audioContext;
        const interval = duration / frequencies.length;

        frequencies.forEach((freq, index) => {
            setTimeout(() => {
                playSingleTone(freq, interval, type, volume);
            }, index * interval);
        });
    }

    // Ambient ship sounds (placeholder for future implementation)
    function startAmbient() {
        if (!STATE.enabled || !STATE.audioContext) return;
        
        // TODO: Load and loop ambient audio file
        console.log('🌌 Starting ambient ship sounds...');
    }

    function stopAmbient() {
        // TODO: Stop ambient audio
        console.log('🔇 Stopping ambient sounds...');
    }

    // Volume control
    function setVolume(volume) {
        STATE.volume = Math.max(0, Math.min(1, volume));
        localStorage.setItem('expanseAudioVolume', STATE.volume.toString());
        console.log('🔊 Volume set to:', STATE.volume);
    }

    function setAmbientVolume(volume) {
        STATE.ambientVolume = Math.max(0, Math.min(1, volume));
        console.log('🌌 Ambient volume set to:', STATE.ambientVolume);
    }

    // Enable/disable audio
    function enable() {
        STATE.enabled = true;
        localStorage.setItem('expanseAudioEnabled', 'true');
        
        // Ensure audio context exists and is ready
        if (!STATE.audioContext || STATE.audioContext.state === 'closed') {
            initAudioContext();
        }
        
        console.log('🔊 Audio enabled, context state:', STATE.audioContext?.state);
        updateAudioStatusIndicators();
        
        // Play confirmation sound (will play if context is running)
        setTimeout(() => playSound('success'), 100);
    }

    function disable() {
        STATE.enabled = false;
        localStorage.setItem('expanseAudioEnabled', 'false');
        stopAmbient();
        console.log('🔇 Audio disabled');
        updateAudioStatusIndicators();
    }

    function toggle() {
        if (STATE.enabled) {
            disable();
        } else {
            enable();
        }
        return STATE.enabled;
    }

    // Reinitialize (useful when returning to page)
    function reinit() {
        console.log('🔄 Reinitializing audio system...');
        
        // Don't reset initialized flag - just ensure context is ready
        if (!STATE.audioContext || STATE.audioContext.state === 'closed') {
            initAudioContext();
        }
        
        // Update visual indicators
        updateAudioStatusIndicators();
        
        // If audio is enabled and context is suspended, set up resume listeners again
        if (STATE.enabled && STATE.audioContext && STATE.audioContext.state === 'suspended') {
            console.log('🎵 Audio context suspended, will resume on user interaction');
        }
    }

    // Public API
    window.ExpanseAudio = {
        init,
        reinit,
        play: playSound,
        startAmbient,
        stopAmbient,
        setVolume,
        setAmbientVolume,
        enable,
        disable,
        toggle,
        updateStatus: updateAudioStatusIndicators,
        isEnabled: () => STATE.enabled,
        getVolume: () => STATE.volume
    };

    // Auto-initialize
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
