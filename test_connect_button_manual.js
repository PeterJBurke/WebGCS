const { chromium } = require('./node_modules/playwright');

(async () => {
  const browser = await chromium.launch({ headless: false });
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to the application
    console.log('🌐 Navigating to WebGCS application...');
    await page.goto('http://localhost:5002');
    
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    console.log('✅ Page loaded successfully');

    // Check if connect button exists
    const connectButton = await page.locator('#connect-drone-btn');
    const isVisible = await connectButton.isVisible();
    console.log(`🔍 Connect button visible: ${isVisible}`);

    if (isVisible) {
      // Check button text
      const buttonText = await connectButton.textContent();
      console.log(`📝 Button text: "${buttonText}"`);

      // Listen for SocketIO events in the console
      page.on('console', msg => {
        if (msg.text().includes('socket') || msg.text().includes('SocketIO') || msg.text().includes('Connected')) {
          console.log(`🔌 Browser console: ${msg.text()}`);
        }
      });

      // Click the connect button
      console.log('🖱️ Clicking connect button...');
      await connectButton.click();

      // Wait a moment for any responses
      await page.waitForTimeout(3000);

      // Check if button text changed
      const newButtonText = await connectButton.textContent();
      console.log(`📝 Button text after click: "${newButtonText}"`);

      // Check for any SocketIO related messages in the console
      const consoleLogs = await page.evaluate(() => {
        return window.consoleLogs || [];
      });

      console.log('✅ Button click test completed successfully');
    } else {
      console.log('❌ Connect button not found');
    }

  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
})();