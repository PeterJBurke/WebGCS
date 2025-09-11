const { chromium } = require('./node_modules/playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Capture ALL console messages
    page.on('console', msg => {
      console.log(`[${msg.type().toUpperCase()}] ${msg.text()}`);
    });

    // Capture page errors
    page.on('pageerror', error => {
      console.error('🚨 PAGE ERROR:', error.message);
    });

    // Capture request failures
    page.on('requestfailed', request => {
      console.error(`🚨 REQUEST FAILED: ${request.url()} - ${request.failure().errorText}`);
    });

    console.log('🔍 DEBUG: WebGCS SocketIO Connection Issues');
    console.log('=============================================');

    // Navigate to the application
    await page.goto('http://localhost:5002');
    
    // Wait for everything to load
    await page.waitForTimeout(5000);

    // Check WebGCS initialization
    const webgcsStatus = await page.evaluate(() => {
      return {
        webgcsExists: typeof window.WebGCS !== 'undefined',
        webgcsKeys: window.WebGCS ? Object.keys(window.WebGCS) : [],
        socketIOExists: typeof io !== 'undefined',
        connectionModuleExists: !!(window.WebGCS?.modules?.connection),
        socketExists: !!(window.WebGCS?.socket),
        socketConnected: !!(window.WebGCS?.connected)
      };
    });

    console.log('📊 WebGCS Status:', JSON.stringify(webgcsStatus, null, 2));

    // Try manual connection
    console.log('🔌 Attempting manual SocketIO connection...');
    const connectionResult = await page.evaluate(() => {
      try {
        if (window.WebGCS?.modules?.connection) {
          // Try to connect manually
          const connectionManager = window.WebGCS.modules.connection;
          connectionManager.connect();
          return { success: true, message: 'Connection initiated' };
        } else {
          return { success: false, message: 'Connection manager not found' };
        }
      } catch (error) {
        return { success: false, message: error.message };
      }
    });

    console.log('📊 Manual Connection Result:', connectionResult);

    // Wait for connection events
    await page.waitForTimeout(3000);

    // Final status check
    const finalStatus = await page.evaluate(() => {
      return {
        socketExists: !!(window.WebGCS?.socket),
        socketConnected: !!(window.WebGCS?.connected),
        socketId: window.WebGCS?.socket?.id || 'none'
      };
    });

    console.log('📊 Final Status:', finalStatus);

    console.log('✅ DEBUG COMPLETE');

  } catch (error) {
    console.error('❌ DEBUG FAILED:', error);
  } finally {
    await browser.close();
  }
})();