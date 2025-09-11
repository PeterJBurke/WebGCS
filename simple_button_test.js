#!/usr/bin/env node

/**
 * Simple Browser Test for Connect Button
 * Tests the button functionality directly in the browser console
 */

const { chromium } = require('./node_modules/playwright');

(async () => {
  console.log('🚀 Starting Simple Connect Button Test...');
  
  const browser = await chromium.launch({ headless: false }); // Show browser
  const page = await browser.newPage();
  
  // Enable console logging from the page
  page.on('console', msg => {
    const type = msg.type();
    const text = msg.text();
    console.log(`🖥️ [${type.toUpperCase()}] ${text}`);
  });
  
  // Listen for page errors
  page.on('pageerror', exception => {
    console.log('❌ PAGE ERROR:', exception.message);
  });
  
  try {
    console.log('📍 Navigating to WebGCS...');
    await page.goto('http://localhost:5002', { waitUntil: 'networkidle' });
    
    console.log('⏳ Waiting for page to fully load...');
    await page.waitForTimeout(3000);
    
    console.log('🔍 Looking for connect button...');
    const connectButton = await page.locator('#connect-drone-btn');
    
    if (await connectButton.count() === 0) {
      console.log('❌ Connect button not found!');
      await browser.close();
      return;
    }
    
    console.log('✅ Connect button found');
    
    // Check button state
    const isVisible = await connectButton.isVisible();
    const isEnabled = await connectButton.isEnabled();
    const buttonText = await connectButton.textContent();
    
    console.log(`👁️ Button visible: ${isVisible}`);
    console.log(`🔓 Button enabled: ${isEnabled}`);
    console.log(`📝 Button text: "${buttonText}"`);
    
    if (!isVisible || !isEnabled) {
      console.log('❌ Button is not clickable');
      await browser.close();
      return;
    }
    
    // Inject a listener for SocketIO events
    await page.addInitScript(() => {
      window.testEvents = [];
      window.addEventListener('load', () => {
        console.log('🌐 Page loaded, checking WebGCS object...');
        console.log('WebGCS object:', window.WebGCS ? 'Found' : 'Not found');
        
        if (window.WebGCS && window.WebGCS.modules) {
          console.log('WebGCS modules:', Object.keys(window.WebGCS.modules));
        }
        
        // Try to intercept socket events if socket exists
        if (window.io && window.WebGCS && window.WebGCS.modules && window.WebGCS.modules.connection) {
          console.log('🔌 SocketIO and connection manager found');
          
          // Override sendCommand to log calls
          const connection = window.WebGCS.modules.connection;
          const originalSendCommand = connection.sendCommand;
          connection.sendCommand = function(command, params) {
            console.log('🚀 COMMAND SENT:', command, params);
            window.testEvents.push({ type: 'command', command, params });
            return originalSendCommand.call(this, command, params);
          };
        }
      });
    });
    
    console.log('🖱️ Clicking connect button...');
    await connectButton.click();
    
    console.log('⏳ Waiting for response...');
    await page.waitForTimeout(5000);
    
    // Check what events were captured
    const events = await page.evaluate(() => window.testEvents || []);
    console.log('📡 Events captured:', JSON.stringify(events, null, 2));
    
    // Check connection status
    const statusElement = await page.locator('#connection-status-text');
    if (await statusElement.count() > 0) {
      const status = await statusElement.textContent();
      console.log('🔗 Connection status:', status);
    } else {
      console.log('🔗 Connection status element not found');
    }
    
    // Check if button text changed
    const newButtonText = await connectButton.textContent();
    console.log(`📝 Button text after click: "${newButtonText}"`);
    
    if (newButtonText !== buttonText) {
      console.log('✅ Button text changed - indicates some response');
    } else {
      console.log('❌ Button text unchanged - may indicate no response');
    }
    
    console.log('✅ Test completed - check browser for visual inspection');
    
    // Keep browser open for manual inspection
    console.log('🔍 Browser will stay open for 30 seconds for manual inspection...');
    await page.waitForTimeout(30000);
    
  } catch (error) {
    console.log('❌ Test error:', error.message);
  } finally {
    await browser.close();
    console.log('👋 Browser closed');
  }
})();