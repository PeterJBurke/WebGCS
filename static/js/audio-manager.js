/**
 * WebGCS Audio Manager Module
 * Handles voice announcements and audio feedback
 */

window.AudioManager = (function() {
    'use strict';
    
    // Private variables
    let audioContext = null;
    let voiceEnabled = false;
    let speechSynthesis = null;
    let currentVoice = null;
    let lastAnnouncement = '';
    let announcementQueue = [];
    let isPlaying = false;
    
    // DOM elements
    let elements = {};
    
    // Audio configuration
    const AUDIO_CONFIG = {
        heartbeatFreq: 800,    // Hz
        heartbeatDuration: 0.1, // seconds
        voiceRate: 1.0,        // Speech rate
        voicePitch: 1.0,       // Speech pitch
        voiceVolume: 0.8,      // Speech volume
        maxQueueSize: 5        // Maximum queued announcements
    };
    
    /**
     * Initialize Audio Manager
     */
    function initialize() {
        console.log('Initializing Audio Manager...');
        
        // Cache DOM elements
        cacheElements();
        
        // Initialize audio systems
        initializeAudioContext();
        initializeSpeechSynthesis();
        
        // Setup event listeners
        setupEventListeners();
        
        // Load saved preferences
        loadPreferences();
        
        console.log('Audio Manager initialized');
    }
    
    /**
     * Cache DOM Elements
     */
    function cacheElements() {
        elements = {
            voiceAnnouncements: document.getElementById('voice-announcements'),
            heartbeatSound: document.getElementById('heartbeat-sound')
        };
        
        // Check for missing elements
        Object.entries(elements).forEach(([key, element]) => {
            if (!element) {
                console.warn(`Audio Manager: Element '${key}' not found`);
            }
        });
    }
    
    /**
     * Initialize Web Audio Context
     */
    function initializeAudioContext() {
        try {
            audioContext = new (window.AudioContext || window.webkitAudioContext)();
            console.log('Web Audio Context initialized');
        } catch (error) {
            console.warn('Web Audio Context not supported:', error);
        }
    }
    
    /**
     * Initialize Speech Synthesis
     */
    function initializeSpeechSynthesis() {
        if ('speechSynthesis' in window) {
            speechSynthesis = window.speechSynthesis;
            
            // Wait for voices to load
            const loadVoices = () => {
                const voices = speechSynthesis.getVoices();
                if (voices.length > 0) {
                    // Prefer English voices
                    currentVoice = voices.find(voice => voice.lang.startsWith('en')) || voices[0];
                    console.log('Speech synthesis initialized with voice:', currentVoice.name);
                } else {
                    // Retry after a delay
                    setTimeout(loadVoices, 100);
                }
            };
            
            speechSynthesis.onvoiceschanged = loadVoices;
            loadVoices();
            
        } else {
            console.warn('Speech synthesis not supported');
        }
    }
    
    /**
     * Setup Event Listeners
     */
    function setupEventListeners() {
        // Voice announcements toggle
        if (elements.voiceAnnouncements) {
            elements.voiceAnnouncements.addEventListener('change', handleVoiceToggle);
        }
        
        // Listen for global events
        if (window.WebGCS && window.WebGCS.eventBus) {
            window.WebGCS.eventBus.addEventListener('telemetry_updated', handleTelemetryUpdate);
            window.WebGCS.eventBus.addEventListener('connection_changed', handleConnectionChange);
            window.WebGCS.eventBus.addEventListener('command_result', handleCommandResult);
        }
        
        // Handle audio context resume (required by browsers)
        document.addEventListener('click', resumeAudioContext, { once: true });
        document.addEventListener('keydown', resumeAudioContext, { once: true });
    }
    
    /**
     * Resume Audio Context
     */
    function resumeAudioContext() {
        if (audioContext && audioContext.state === 'suspended') {
            audioContext.resume().then(() => {
                console.log('Audio context resumed');
            }).catch(error => {
                console.warn('Failed to resume audio context:', error);
            });
        }
    }
    
    /**
     * Handle Voice Toggle
     */
    function handleVoiceToggle(event) {
        voiceEnabled = event.target.checked;
        
        console.log('Voice announcements:', voiceEnabled ? 'enabled' : 'disabled');
        
        // Save preference
        localStorage.setItem('webgcs_voice_enabled', voiceEnabled.toString());
        
        // Announce the change
        if (voiceEnabled) {
            announceText('Voice announcements enabled');
        }
        
        // Resume audio context if enabling voice
        if (voiceEnabled) {
            resumeAudioContext();
        }
    }
    
    /**
     * Play Heartbeat Sound
     */
    function playHeartbeatSound() {
        if (!audioContext) return;
        
        try {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(AUDIO_CONFIG.heartbeatFreq, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(0.1, audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + AUDIO_CONFIG.heartbeatDuration);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + AUDIO_CONFIG.heartbeatDuration);
            
        } catch (error) {
            console.warn('Could not play heartbeat sound:', error);
        }
    }
    
    /**
     * Announce Text via Speech Synthesis
     */
    function announceText(text, priority = false) {
        if (!voiceEnabled || !speechSynthesis || !currentVoice) return;
        
        // Avoid duplicate announcements
        if (text === lastAnnouncement && !priority) {
            return;
        }
        
        // Manage announcement queue
        if (priority) {
            // Clear queue for priority announcements
            announcementQueue = [];
            speechSynthesis.cancel();
        } else if (announcementQueue.length >= AUDIO_CONFIG.maxQueueSize) {
            console.log('Announcement queue full, skipping:', text);
            return;
        }
        
        // Add to queue
        announcementQueue.push(text);
        lastAnnouncement = text;
        
        // Process queue if not already playing
        if (!isPlaying) {
            processAnnouncementQueue();
        }
    }
    
    /**
     * Process Announcement Queue
     */
    function processAnnouncementQueue() {
        if (announcementQueue.length === 0) {
            isPlaying = false;
            return;
        }
        
        isPlaying = true;
        const text = announcementQueue.shift();
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.voice = currentVoice;
        utterance.rate = AUDIO_CONFIG.voiceRate;
        utterance.pitch = AUDIO_CONFIG.voicePitch;
        utterance.volume = AUDIO_CONFIG.voiceVolume;
        
        utterance.onend = () => {
            console.log('Announcement completed:', text);
            // Process next in queue
            setTimeout(() => processAnnouncementQueue(), 500);
        };
        
        utterance.onerror = (error) => {
            console.warn('Speech synthesis error:', error);
            // Continue with queue
            setTimeout(() => processAnnouncementQueue(), 500);
        };
        
        try {
            speechSynthesis.speak(utterance);
            console.log('Announcing:', text);
        } catch (error) {
            console.warn('Failed to announce:', text, error);
            setTimeout(() => processAnnouncementQueue(), 500);
        }
    }
    
    /**
     * Announce Connection Status
     */
    function announceConnectionStatus(connected) {
        const status = connected ? 'Drone connected' : 'Drone disconnected';
        announceText(status, true);
    }
    
    /**
     * Announce Arm Status
     */
    function announceArmStatus(armed) {
        const status = armed ? 'Vehicle armed' : 'Vehicle disarmed';
        announceText(status, true);
    }
    
    /**
     * Announce Mode Change
     */
    function announceModeChange(mode) {
        announceText(`Flight mode ${mode}`);
    }
    
    /**
     * Announce Battery Status
     */
    function announceBatteryStatus(voltage) {
        if (voltage < 11.0) {
            announceText(`Low battery warning: ${voltage.toFixed(1)} volts`, true);
        } else if (voltage < 11.5) {
            announceText(`Battery low: ${voltage.toFixed(1)} volts`);
        }
    }
    
    /**
     * Announce GPS Status
     */
    function announceGPSStatus(fixType, satellites) {
        if (fixType >= 3 && satellites >= 6) {
            // Good GPS fix
            announceText('GPS fix acquired');
        } else if (fixType < 2) {
            // No GPS fix
            announceText('GPS fix lost', true);
        }
    }
    
    /**
     * Announce Command Result
     */
    function announceCommandResult(command, success, error = null) {
        if (success) {
            switch (command) {
                case 'arm':
                    announceText('Arm command successful');
                    break;
                case 'disarm':
                    announceText('Disarm command successful');
                    break;
                case 'takeoff':
                    announceText('Takeoff command successful');
                    break;
                case 'land':
                    announceText('Landing command successful');
                    break;
                case 'rtl':
                    announceText('Return to launch initiated');
                    break;
                case 'goto':
                    announceText('Navigation command sent');
                    break;
                default:
                    announceText(`${command} command successful`);
            }
        } else {
            announceText(`${command} command failed`, true);
        }
    }
    
    /**
     * Create Audio Beep
     */
    function playBeep(frequency = 1000, duration = 0.2, volume = 0.1) {
        if (!audioContext) return;
        
        try {
            const oscillator = audioContext.createOscillator();
            const gainNode = audioContext.createGain();
            
            oscillator.connect(gainNode);
            gainNode.connect(audioContext.destination);
            
            oscillator.frequency.setValueAtTime(frequency, audioContext.currentTime);
            gainNode.gain.setValueAtTime(0, audioContext.currentTime);
            gainNode.gain.linearRampToValueAtTime(volume, audioContext.currentTime + 0.01);
            gainNode.gain.exponentialRampToValueAtTime(0.001, audioContext.currentTime + duration);
            
            oscillator.start(audioContext.currentTime);
            oscillator.stop(audioContext.currentTime + duration);
            
        } catch (error) {
            console.warn('Could not play beep:', error);
        }
    }
    
    /**
     * Load Saved Preferences
     */
    function loadPreferences() {
        // Load voice enabled preference
        const voiceSaved = localStorage.getItem('webgcs_voice_enabled');
        if (voiceSaved !== null) {
            voiceEnabled = voiceSaved === 'true';
            if (elements.voiceAnnouncements) {
                elements.voiceAnnouncements.checked = voiceEnabled;
            }
        }
    }
    
    /**
     * Event Handlers
     */
    let lastBatteryWarning = 0;
    let lastGPSStatus = -1;
    
    function handleTelemetryUpdate(event) {
        const data = event.detail;
        
        // Safety check for data
        if (!data) return;
        
        // Battery monitoring
        if (data.battery_voltage && data.battery_voltage > 0) {
            const now = Date.now();
            if (now - lastBatteryWarning > 60000) { // Once per minute
                if (data.battery_voltage < 11.0) {
                    announceBatteryStatus(data.battery_voltage);
                    lastBatteryWarning = now;
                }
            }
        }
        
        // GPS status monitoring
        if (data.gps_fix_type !== undefined && data.gps_fix_type !== lastGPSStatus) {
            announceGPSStatus(data.gps_fix_type, data.satellites_visible || 0);
            lastGPSStatus = data.gps_fix_type;
        }
    }
    
    function handleConnectionChange(event) {
        if (event.detail && event.detail.hasOwnProperty('connected')) {
            announceConnectionStatus(event.detail.connected);
        }
    }
    
    function handleCommandResult(event) {
        const result = event.detail;
        announceCommandResult(result.command, result.success, result.error);
    }
    
    /**
     * Public API
     */
    return {
        initialize: initialize,
        
        // Audio methods
        playHeartbeatSound: playHeartbeatSound,
        playBeep: playBeep,
        announceText: announceText,
        
        // Specific announcements
        announceConnectionStatus: announceConnectionStatus,
        announceArmStatus: announceArmStatus,
        announceModeChange: announceModeChange,
        announceBatteryStatus: announceBatteryStatus,
        announceGPSStatus: announceGPSStatus,
        announceCommandResult: announceCommandResult,
        
        // State getters
        isVoiceEnabled: () => voiceEnabled,
        isAudioContextReady: () => audioContext && audioContext.state === 'running',
        
        // Heartbeat callback for connection manager
        onHeartbeat: playHeartbeatSound,
        
        // Module lifecycle callbacks
        onTelemetryUpdate: handleTelemetryUpdate,
        onConnectionChange: handleConnectionChange,
        onResize: () => {
            // Handle responsive layout changes if needed
        }
    };
})();