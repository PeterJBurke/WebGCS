const { chromium } = require('./node_modules/playwright');

(async () => {
  const browser = await chromium.launch({ headless: false, slowMo: 1000 });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Enable console logging
    page.on('console', msg => {
      const text = msg.text();
      if (text.includes('socket') || text.includes('SocketIO') || text.includes('Connected') || 
          text.includes('command') || text.includes('drone') || text.includes('WebGCS')) {
        console.log(`📱 Browser: ${text}`);
      }
    });

    console.log('🌐 TEST: WebGCS SocketIO Connect Button Flow');
    console.log('================================================');

    // Navigate to the application
    console.log('🚀 Step 1: Loading WebGCS application...');
    await page.goto('http://localhost:5002');
    await page.waitForLoadState('networkidle');
    console.log('✅ Application loaded');

    // Wait for SocketIO to initialize
    console.log('🔌 Step 2: Waiting for SocketIO initialization...');
    await page.waitForTimeout(2000);

    // Check SocketIO connection status
    const socketStatus = await page.evaluate(() => {
      return {
        socketExists: !!window.WebGCS?.socket,
        socketConnected: !!window.WebGCS?.connected,
        droneConnected: !!window.WebGCS?.droneConnected,
        connectionManagerExists: !!window.WebGCS?.modules?.connection
      };
    });

    console.log(`📊 SocketIO Status:`, socketStatus);

    // Find and check the connect button
    console.log('🔍 Step 3: Checking connect button...');
    const connectButton = page.locator('#connect-drone-btn');
    const isVisible = await connectButton.isVisible();
    const buttonText = await connectButton.textContent();
    
    console.log(`🔘 Button visible: ${isVisible}`);
    console.log(`📝 Button text: "${buttonText}"`);

    if (!isVisible) {
      console.log('❌ FAILED: Connect button not found');
      return;
    }

    // Test button click with detailed monitoring
    console.log('🖱️ Step 4: Testing button click...');
    
    // Set up monitoring for SocketIO events
    await page.evaluate(() => {
      // Override the sendCommand function to log activity
      if (window.WebGCS?.modules?.connection?.sendCommand) {
        const originalSend = window.WebGCS.modules.connection.sendCommand;
        window.WebGCS.modules.connection.sendCommand = function(command, params) {
          console.log(`🚀 SENDING COMMAND: ${command}`, params);
          return originalSend.call(this, command, params);
        };
      }

      // Monitor SocketIO events if socket exists
      if (window.WebGCS?.socket) {
        const socket = window.WebGCS.socket;
        socket.onAny((eventName, ...args) => {
          console.log(`🔄 SocketIO Event: ${eventName}`, args);
        });
      }
    });

    // Click the button
    await connectButton.click();
    console.log('✅ Button clicked');

    // Wait for response
    console.log('⏳ Step 5: Waiting for server response...');
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

    // Test results
    console.log('===============================================');
    if (socketStatus.socketExists && socketStatus.socketConnected) {
      console.log('✅ PASS: SocketIO connection established');
    } else {
      console.log('❌ FAIL: SocketIO connection issues');
    }

    if (socketStatus.connectionManagerExists) {
      console.log('✅ PASS: Connection manager available');
    } else {
      console.log('❌ FAIL: Connection manager missing');
    }

    console.log('✅ TEST COMPLETED');

  } catch (error) {
    console.error('❌ TEST FAILED:', error);
  } finally {
    await browser.close();
  }
})();