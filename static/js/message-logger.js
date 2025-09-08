/**
 * WebGCS Message Logger Module
 * Handles real-time message logging and display
 */

window.MessageLogger = (function() {
    'use strict';
    
    // Private variables
    let messageBuffer = [];
    let maxMessages = 1000;
    let autoScroll = true;
    let messageCounter = 0;
    
    // DOM elements
    let elements = {};
    
    // Message types and their styling
    const MESSAGE_TYPES = {
        'info': { class: 'log-info', icon: 'ℹ️', priority: 1 },
        'success': { class: 'log-success', icon: '✅', priority: 2 },
        'warning': { class: 'log-warning', icon: '⚠️', priority: 3 },
        'error': { class: 'log-error', icon: '❌', priority: 4 },
        'debug': { class: 'log-debug', icon: '🔧', priority: 0 }
    };
    
    /**
     * Initialize Message Logger
     */
    function initialize() {
        console.log('Initializing Message Logger...');
        
        // Cache DOM elements
        cacheElements();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize UI
        initializeUI();
        
        // Add initial message
        addMessage('WebGCS Message Logger initialized', 'info');
        
        console.log('Message Logger initialized');
    }
    
    /**
     * Cache DOM Elements
     */
    function cacheElements() {
        elements = {
            messageLog: document.getElementById('message-log')
        };
        
        // Check for missing elements
        Object.entries(elements).forEach(([key, element]) => {
            if (!element) {
                console.warn(`Message Logger: Element '${key}' not found`);
            }
        });
    }
    
    /**
     * Setup Event Listeners
     */
    function setupEventListeners() {
        // Scroll event for auto-scroll detection
        if (elements.messageLog) {
            elements.messageLog.addEventListener('scroll', handleScroll);
            
            // Double-click to clear log
            elements.messageLog.addEventListener('dblclick', handleDoubleClick);
        }
        
        // Listen for global events
        if (window.WebGCS && window.WebGCS.eventBus) {
            window.WebGCS.eventBus.addEventListener('telemetry_updated', handleTelemetryUpdate);
            window.WebGCS.eventBus.addEventListener('connection_changed', handleConnectionChange);
            window.WebGCS.eventBus.addEventListener('command_result', handleCommandResult);
            window.WebGCS.eventBus.addEventListener('websocket_connected', handleWebSocketConnect);
            window.WebGCS.eventBus.addEventListener('websocket_disconnected', handleWebSocketDisconnect);
        }
        
        // Listen for console messages (for debugging)
        interceptConsole();
    }
    
    /**
     * Initialize UI
     */
    function initializeUI() {
        if (elements.messageLog) {
            elements.messageLog.innerHTML = '';
            elements.messageLog.setAttribute('title', 'Double-click to clear log');
        }
    }
    
    /**
     * Add Message to Log
     */
    function addMessage(text, type = 'info', timestamp = null, metadata = null) {
        if (!text || typeof text !== 'string') return;
        
        const messageTime = timestamp || new Date();
        const messageId = ++messageCounter;
        
        // Create message object
        const message = {
            id: messageId,
            text: text.trim(),
            type: type,
            timestamp: messageTime,
            metadata: metadata
        };
        
        // Add to buffer
        messageBuffer.push(message);
        
        // Trim buffer if too large
        if (messageBuffer.length > maxMessages) {
            messageBuffer = messageBuffer.slice(-maxMessages);
        }
        
        // Update display
        displayMessage(message);
        
        // Auto-scroll if enabled
        if (autoScroll) {
            scrollToBottom();
        }
        
        console.log(`[${type.toUpperCase()}] ${text}`);
    }
    
    /**
     * Display Message in UI
     */
    function displayMessage(message) {
        if (!elements.messageLog) return;
        
        const messageType = MESSAGE_TYPES[message.type] || MESSAGE_TYPES.info;
        
        // Create message element
        const messageElement = document.createElement('div');
        messageElement.className = `log-entry ${messageType.class}`;
        messageElement.setAttribute('data-message-id', message.id);
        
        // Format timestamp
        const timeStr = message.timestamp.toLocaleTimeString('en-US', {
            hour12: false,
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });
        
        // Create message content
        messageElement.innerHTML = `
            <span class="log-time">${timeStr}</span>
            <span class="log-icon">${messageType.icon}</span>
            <span class="log-text">${escapeHtml(message.text)}</span>
        `;
        
        // Add metadata tooltip if available
        if (message.metadata) {
            try {
                const metadataStr = window.WebGCS?.safeStringify ? 
                    window.WebGCS.safeStringify(message.metadata, 2) :
                    JSON.stringify(message.metadata, null, 2);
                messageElement.setAttribute('title', `Metadata:\n${metadataStr}`);
            } catch (e) {
                messageElement.setAttribute('title', `Metadata: [Unable to stringify - ${e.message}]`);
            }
        }
        
        // Add to log container
        elements.messageLog.appendChild(messageElement);
        
        // Remove old messages if too many in DOM
        const entries = elements.messageLog.querySelectorAll('.log-entry');
        if (entries.length > maxMessages) {
            const removeCount = entries.length - maxMessages;
            for (let i = 0; i < removeCount; i++) {
                elements.messageLog.removeChild(entries[i]);
            }
        }
        
        // Add fade-in animation
        messageElement.classList.add('fade-in');
        setTimeout(() => {
            messageElement.classList.remove('fade-in');
        }, 300);
    }
    
    /**
     * Clear Message Log
     */
    function clearLog() {
        messageBuffer = [];
        messageCounter = 0;
        
        if (elements.messageLog) {
            elements.messageLog.innerHTML = '';
        }
        
        addMessage('Message log cleared', 'info');
    }
    
    /**
     * Export Log as Text
     */
    function exportLog() {
        if (messageBuffer.length === 0) {
            addMessage('No messages to export', 'warning');
            return;
        }
        
        let logText = 'WebGCS Message Log Export\n';
        logText += '========================\n';
        logText += `Generated: ${new Date().toISOString()}\n`;
        logText += `Messages: ${messageBuffer.length}\n\n`;
        
        messageBuffer.forEach(message => {
            const timestamp = message.timestamp.toISOString();
            const type = message.type.toUpperCase().padEnd(8);
            logText += `[${timestamp}] ${type} ${message.text}\n`;
        });
        
        // Create and download file
        const blob = new Blob([logText], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `webgcs-log-${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
        
        addMessage(`Exported ${messageBuffer.length} messages to file`, 'success');
    }
    
    /**
     * Filter Messages by Type
     */
    function filterMessages(types = null) {
        if (!elements.messageLog) return;
        
        const entries = elements.messageLog.querySelectorAll('.log-entry');
        
        entries.forEach(entry => {
            if (types === null) {
                // Show all messages
                entry.style.display = '';
            } else {
                // Show only specified types
                const hasMatchingType = types.some(type => 
                    entry.classList.contains(MESSAGE_TYPES[type]?.class)
                );
                entry.style.display = hasMatchingType ? '' : 'none';
            }
        });
    }
    
    /**
     * Scroll to Bottom
     */
    function scrollToBottom() {
        if (elements.messageLog) {
            elements.messageLog.scrollTop = elements.messageLog.scrollHeight;
        }
    }
    
    /**
     * Handle Scroll Event
     */
    function handleScroll() {
        if (!elements.messageLog) return;
        
        const { scrollTop, scrollHeight, clientHeight } = elements.messageLog;
        const isNearBottom = scrollTop + clientHeight >= scrollHeight - 50;
        
        // Update auto-scroll based on user interaction
        autoScroll = isNearBottom;
    }
    
    /**
     * Handle Double-Click (Clear Log)
     */
    function handleDoubleClick(event) {
        event.preventDefault();
        
        // Confirm clear with user
        if (window.WebGCS?.showConfirmation) {
            window.WebGCS.showConfirmation(
                'Clear Message Log',
                'This will clear all messages from the log. Continue?',
                (confirmed) => {
                    if (confirmed) {
                        clearLog();
                    }
                }
            );
        } else {
            if (confirm('Clear message log?')) {
                clearLog();
            }
        }
    }
    
    /**
     * Intercept Console Messages
     */
    function interceptConsole() {
        // Only in debug mode
        if (!window.location.search.includes('debug=true')) return;
        
        const originalLog = console.log;
        const originalWarn = console.warn;
        const originalError = console.error;
        
        console.log = function(...args) {
            originalLog.apply(console, args);
            addMessage(args.join(' '), 'debug');
        };
        
        console.warn = function(...args) {
            originalWarn.apply(console, args);
            addMessage(args.join(' '), 'warning');
        };
        
        console.error = function(...args) {
            originalError.apply(console, args);
            addMessage(args.join(' '), 'error');
        };
    }
    
    /**
     * Escape HTML for safe display
     */
    function escapeHtml(unsafe) {
        return unsafe
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }
    
    /**
     * Event Handlers
     */
    function handleTelemetryUpdate(event) {
        // Only log significant telemetry events to avoid spam
        const data = event.detail;
        
        // Safety check for data
        if (!data) return;
        
        // Log connection state changes
        if (typeof staticVars.lastConnected === 'undefined') staticVars.lastConnected = null;
        if (data.connected !== staticVars.lastConnected) {
            const status = data.connected ? 'connected' : 'disconnected';
            addMessage(`Drone ${status}${data.system_id ? ` (System ${data.system_id})` : ''}`, 
                      data.connected ? 'success' : 'warning');
            staticVars.lastConnected = data.connected;
        }
        
        // Log mode changes
        if (typeof staticVars.lastMode === 'undefined') staticVars.lastMode = null;
        if (data.mode && data.mode !== staticVars.lastMode && data.mode !== 'UNKNOWN') {
            addMessage(`Flight mode changed to ${data.mode}`, 'info');
            staticVars.lastMode = data.mode;
        }
        
        // Log arming state changes
        if (typeof staticVars.lastArmed === 'undefined') staticVars.lastArmed = null;
        if (data.armed !== staticVars.lastArmed && data.connected) {
            const status = data.armed ? 'ARMED' : 'DISARMED';
            addMessage(`Vehicle ${status}`, data.armed ? 'warning' : 'info');
            staticVars.lastArmed = data.armed;
        }
    }
    
    function handleConnectionChange(event) {
        const data = event.detail || event;
        if (!data) return;
        
        const status = data.connected ? 'connected' : 'disconnected';
        const type = data.connected ? 'success' : 'warning';
        addMessage(`Connection ${status}`, type);
    }
    
    function handleCommandResult(event) {
        const result = event.detail;
        const type = result.success ? 'success' : 'error';
        const status = result.success ? 'succeeded' : 'failed';
        
        let message = `Command ${result.command} ${status}`;
        if (!result.success && result.error) {
            message += `: ${result.error}`;
        }
        
        addMessage(message, type, null, result);
    }
    
    function handleWebSocketConnect() {
        addMessage('WebSocket connected to server', 'success');
    }
    
    function handleWebSocketDisconnect() {
        addMessage('WebSocket disconnected from server', 'warning');
    }
    
    /**
     * Static variable simulation (since real static isn't supported in all browsers)
     */
    const staticVars = {};
    
    /**
     * Public API
     */
    return {
        initialize: initialize,
        
        // Logging methods
        addMessage: addMessage,
        clearLog: clearLog,
        exportLog: exportLog,
        
        // Display methods
        filterMessages: filterMessages,
        scrollToBottom: scrollToBottom,
        
        // State getters
        getMessageCount: () => messageBuffer.length,
        getMessages: () => [...messageBuffer],
        isAutoScroll: () => autoScroll,
        
        // Configuration
        setMaxMessages: (max) => { maxMessages = Math.max(100, max); },
        setAutoScroll: (enabled) => { autoScroll = enabled; },
        
        // Module lifecycle callbacks
        onTelemetryUpdate: handleTelemetryUpdate,
        onConnectionChange: handleConnectionChange,
        onResize: () => {
            // Handle responsive layout changes if needed
            if (autoScroll) {
                scrollToBottom();
            }
        }
    };
})();