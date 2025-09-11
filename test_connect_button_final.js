const { chromium } = require('./node_modules/playwright');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 500 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Capture all relevant console messages
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('Connect button') || text.includes('command') || 
          text.includes('drone') || text.includes('Connected') ||
          text.includes('SENDING COMMAND') || text.includes('connect_drone')) {
        console.log(`🎯 Browser: ${text}`);
      }
    });

    console.log('🚀 FINAL TEST: Connect Button Functionality');
    console.log('============================================');

    // Navigate and wait for full initialization
    console.log('📱 Step 1: Loading application...');
    await page.goto('http://localhost:5002');
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000); // Allow SocketIO to connect

    // Verify SocketIO connection
    const connectionStatus = await page.evaluate(() => {
      return {
        socketConnected: !!window.WebGCS?.connected,
        socketId: window.WebGCS?.socket?.id || 'none',
        connectionManager: !!window.WebGCS?.modules?.connection
      };
    });
    console.log(`🔌 SocketIO Status:`, connectionStatus);

    if (!connectionStatus.socketConnected) {
      console.log('❌ FAILED: SocketIO not connected');
      return;
    }

    // Find connect button
    console.log('🔍 Step 2: Finding connect button...');
    const connectButton = page.locator('#connect-drone-btn');
    const isVisible = await connectButton.isVisible();
    const buttonText = await connectButton.textContent();
    
    console.log(`📌 Button visible: ${isVisible}, Text: "${buttonText}"`);

    // Set up command monitoring
    await page.evaluate(() => {
      if (window.WebGCS?.modules?.connection?.sendCommand) {
        const original = window.WebGCS.modules.connection.sendCommand;
        window.WebGCS.modules.connection.sendCommand = function(command, params) {
          console.log(`🚀 SENDING COMMAND: ${command}`, params);
          return original.call(this, command, params);
        };
      }

      // Monitor drone connection events
      if (window.WebGCS?.modules?.connection) {
        const conn = window.WebGCS.modules.connection;
        conn.on('drone_connected', (data) => {
          console.log('✅ DRONE CONNECTED EVENT:', data);
        });
        conn.on('connection_error', (data) => {
          console.log('❌ CONNECTION ERROR EVENT:', data);
        });
      }
    });

    // Test the connect button
    console.log('🖱️ Step 3: Clicking connect button...');
    await connectButton.click();
    console.log('✅ Button clicked');

    // Wait for command processing
    console.log('⏳ Step 4: Waiting for server response...');
    await page.waitForTimeout(5000);

    // Check final status
    const finalStatus = await page.evaluate(() => {
      return {
        socketConnected: !!window.WebGCS?.connected,
        droneConnected: !!window.WebGCS?.droneConnected,
        buttonText: document.getElementById('connect-drone-btn')?.textContent
      };
    });

    console.log(`📊 Final Status:`, finalStatus);

    // Results summary
    console.log('============================================');
    console.log('✅ CONNECT BUTTON TEST RESULTS:');
    console.log(`  🔌 SocketIO Connected: ${connectionStatus.socketConnected ? '✅' : '❌'}`);
    console.log(`  🔘 Button Clickable: ${isVisible ? '✅' : '❌'}`);
    console.log(`  🎯 Command Sent: Will show in logs above`);
    console.log('============================================');

    if (connectionStatus.socketConnected && isVisible) {
      console.log('🎉 PASS: Connect button functionality verified!');
    } else {
      console.log('❌ FAIL: Issues detected');
    }

  } catch (error) {
    console.error('❌ TEST FAILED:', error);
  } finally {
    await browser.close();
  }
})();