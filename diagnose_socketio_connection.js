#!/usr/bin/env node

/**
 * SocketIO Connection Diagnostic Test
 * Focuses specifically on WebSocket/SocketIO connection establishment
 */

const { chromium } = require('./node_modules/playwright');

(async () => {
  console.log('🔍 SOCKETIO CONNECTION DIAGNOSTIC TEST');
  console.log('======================================');
  
  const browser = await chromium.launch({ 
    headless: false,
    devtools: true  // Open DevTools to see network tab
  });
  const page = await browser.newPage();
  
  // Capture all console messages
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    const location = msg.location();
    console.log(`🖥️ [${type.toUpperCase()}] ${text} (${location.url}:${location.lineNumber})`);
  });
  
  // Capture page errors
  page.on('pageerror', exception => {
    console.log('❌ PAGE ERROR:', exception.message);
    console.log('   Stack:', exception.stack);
  });
  
  // Capture network failures
  page.on('requestfailed', request => {
    console.log(`🌐 NETWORK FAILED: ${request.method()} ${request.url()}`);
    console.log('   Failure:', request.failure().errorText);
  });
  
  // Capture successful requests
  page.on('response', response => {
    if (!response.url().includes('socket.io')) return;
    console.log(`🌐 RESPONSE: ${response.status()} ${response.url()}`);
  });
  
  try {
    console.log('📍 Navigating to WebGCS...');
    await page.goto('http://localhost:5002', { waitUntil: 'networkidle' });
    
    console.log('⏳ Waiting for initial load...');
    await page.waitForTimeout(2000);
    
    // Inject detailed SocketIO diagnostic code
    await page.addInitScript(() => {
      window.socketDiagnostics = {
        events: [],
        socketState: 'unknown',
        connectionAttempts: 0
      };
      
      // Override console.log to capture all logs
      const originalLog = console.log;
      console.log = function(...args) {
        window.socketDiagnostics.events.push({
          type: 'console_log',
          timestamp: new Date().toISOString(),
          message: args.join(' ')
        });
        originalLog.apply(console, args);
      };
      
      // Override console.error to capture errors
      const originalError = console.error;
      console.error = function(...args) {
        window.socketDiagnostics.events.push({
          type: 'console_error',
          timestamp: new Date().toISOString(),
          message: args.join(' ')
        });
        originalError.apply(console, args);
      };
    });
    
    console.log('🔧 Injecting SocketIO diagnostics...');
    await page.evaluate(() => {
      // Wait for page to be fully loaded
      if (document.readyState !== 'complete') {
        return new Promise(resolve => {
          window.addEventListener('load', resolve);
        });
      }
    });
    
    // Wait for WebGCS to initialize
    await page.waitForTimeout(3000);
    
    // Check WebGCS state
    const webgcsState = await page.evaluate(() => {
      return {
        webgcsExists: !!window.WebGCS,
        socketExists: !!window.WebGCS?.socket,
        connectionManagerExists: !!window.WebGCS?.modules?.connection,
        connected: window.WebGCS?.connected,
        droneConnected: window.WebGCS?.droneConnected,
        socketConnected: window.WebGCS?.socket?.connected,
        socketId: window.WebGCS?.socket?.id,
        ioAvailable: typeof window.io !== 'undefined'
      };
    });
    
    console.log('🔍 WEBGCS STATE:');
    console.log('   WebGCS exists:', webgcsState.webgcsExists);
    console.log('   Socket.IO library available:', webgcsState.ioAvailable);
    console.log('   Socket exists:', webgcsState.socketExists);
    console.log('   Connection Manager exists:', webgcsState.connectionManagerExists);
    console.log('   WebGCS connected:', webgcsState.connected);
    console.log('   Socket connected:', webgcsState.socketConnected);
    console.log('   Socket ID:', webgcsState.socketId);
    console.log('   Drone connected:', webgcsState.droneConnected);
    
    if (!webgcsState.webgcsExists) {
      console.log('❌ WebGCS object not found - JavaScript initialization failed');
    } else if (!webgcsState.ioAvailable) {
      console.log('❌ Socket.IO library not loaded');
    } else if (!webgcsState.socketExists) {
      console.log('❌ Socket not created - connection.connect() may not have been called');
    } else if (!webgcsState.socketConnected) {
      console.log('❌ Socket created but not connected - connection establishment failed');
      
      // Try to get more details about the socket
      const socketDetails = await page.evaluate(() => {
        if (!window.WebGCS?.socket) return null;
        
        const socket = window.WebGCS.socket;
        return {
          readyState: socket.connected ? 'connected' : 'disconnected',
          url: socket.io?.uri,
          transport: socket.io?.engine?.transport?.name,
          disconnected: socket.disconnected,
          id: socket.id
        };
      });
      
      console.log('🔍 SOCKET DETAILS:');
      if (socketDetails) {
        console.log('   URL:', socketDetails.url);
        console.log('   Transport:', socketDetails.transport);
        console.log('   Ready State:', socketDetails.readyState);
        console.log('   Disconnected:', socketDetails.disconnected);
      } else {
        console.log('   No socket details available');
      }
    } else {
      console.log('✅ Socket is connected - connection establishment successful');
    }
    
    // Test the actual connect button now
    console.log('\n🖱️ TESTING CONNECT BUTTON...');
    const connectButton = await page.locator('#connect-drone-btn');
    
    if (await connectButton.count() === 0) {
      console.log('❌ Connect button not found');
    } else {
      const buttonText = await connectButton.textContent();
      console.log('✅ Connect button found:', buttonText);
      
      // Try clicking it
      console.log('🖱️ Clicking connect button...');
      await connectButton.click();
      
      // Wait and check what happens
      await page.waitForTimeout(3000);
      
      const newButtonText = await connectButton.textContent();
      console.log('📝 Button text after click:', newButtonText);
      
      // Check if any SocketIO events were sent
      const socketIOEvents = await page.evaluate(() => {
        return window.socketDiagnostics?.events || [];
      });
      
      console.log('📡 Events during test:');
      socketIOEvents.forEach(event => {
        console.log(`   ${event.timestamp}: [${event.type}] ${event.message}`);
      });
    }
    
    console.log('\n🔍 Browser will stay open for manual inspection...');
    await page.waitForTimeout(30000);
    
  } catch (error) {
    console.log('❌ Diagnostic error:', error.message);
  } finally {
    await browser.close();
    console.log('👋 Diagnostic complete');
  }
})();