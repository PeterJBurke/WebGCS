#!/usr/bin/env python3
"""
CONNECT BUTTON TEST WITH TIMING FIX
===================================

This test addresses the SocketIO connection timing issue found in the
ultra-comprehensive test. It waits longer for the SocketIO connection
to establish before proceeding with button tests.
"""

import asyncio
import logging
import sys
import time
from playwright.async_api import async_playwright, Page, BrowserContext
import requests

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ConnectButtonTimingTest:
    """Connect button test with SocketIO timing fix"""
    
    def __init__(self):
        self.test_url = "http://localhost:5002"
        self.page = None
        
    async def setup_browser(self):
        """Initialize browser"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context()
        self.page = await self.context.new_page()
        
        # Monitor console logs
        self.page.on('console', lambda msg: logger.info(f"Console: [{msg.type}] {msg.text}"))

    async def cleanup(self):
        """Clean up"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def test_with_socketio_wait(self):
        """Test connect button with proper SocketIO wait"""
        logger.info("🚀 Testing connect button with SocketIO timing fix")
        
        # Load page
        await self.page.goto(self.test_url)
        await self.page.wait_for_load_state('networkidle')
        logger.info("✅ Page loaded")
        
        # Wait for WebGCS to initialize
        await self.page.wait_for_function("window.WebGCS !== undefined", timeout=10000)
        logger.info("✅ WebGCS initialized")
        
        # Wait for SocketIO library
        await self.page.wait_for_function("window.io !== undefined", timeout=5000)
        logger.info("✅ SocketIO library loaded")
        
        # Wait longer for SocketIO connection with multiple checks
        logger.info("⏳ Waiting for SocketIO connection...")
        
        for attempt in range(10):  # Try for 10 seconds
            await self.page.wait_for_timeout(1000)
            
            socket_connected = await self.page.evaluate("""
                window.WebGCS.socket && window.WebGCS.socket.connected
            """)
            
            webgcs_connected = await self.page.evaluate("window.WebGCS.connected")
            
            logger.info(f"Attempt {attempt + 1}: socket.connected={socket_connected}, WebGCS.connected={webgcs_connected}")
            
            if socket_connected and webgcs_connected:
                logger.info("✅ SocketIO connected successfully!")
                break
        else:
            # If still not connected, try manual connection debugging
            logger.warning("⚠️ SocketIO not connected yet, checking connection details...")
            
            connection_details = await self.page.evaluate("""
                ({
                    socketExists: !!window.WebGCS.socket,
                    socketConnected: window.WebGCS.socket && window.WebGCS.socket.connected,
                    socketId: window.WebGCS.socket && window.WebGCS.socket.id,
                    webgcsConnected: window.WebGCS.connected,
                    socketReadyState: window.WebGCS.socket && window.WebGCS.socket.readyState,
                    connectionState: window.WebGCS.socket && window.WebGCS.socket.connection && window.WebGCS.socket.connection.readyState
                })
            """)
            
            logger.info(f"Connection details: {connection_details}")
            
            # Try to force reconnection
            logger.info("🔄 Attempting to force SocketIO reconnection...")
            await self.page.evaluate("""
                if (window.WebGCS.socket) {
                    console.log('Forcing SocketIO reconnection...');
                    window.WebGCS.socket.disconnect();
                    setTimeout(() => {
                        window.WebGCS.socket.connect();
                    }, 1000);
                }
            """)
            
            # Wait for reconnection
            await self.page.wait_for_timeout(3000)
            
            final_check = await self.page.evaluate("""
                window.WebGCS.socket && window.WebGCS.socket.connected
            """)
            
            if final_check:
                logger.info("✅ SocketIO connected after forced reconnection!")
            else:
                logger.error("❌ SocketIO connection failed even after forced reconnection")
                return False
        
        # Now test the connect button
        logger.info("🔘 Testing connect button functionality...")
        
        # Find connect button
        connect_btn = await self.page.query_selector('#connect-drone-btn')
        if not connect_btn:
            logger.error("❌ Connect button not found!")
            return False
        
        logger.info("✅ Connect button found")
        
        # Check button text
        btn_text = await connect_btn.text_content()
        logger.info(f"✅ Button text: '{btn_text}'")
        
        # Check button enabled state
        is_disabled = await connect_btn.is_disabled()
        if is_disabled:
            logger.error("❌ Connect button is disabled!")
            return False
        
        logger.info("✅ Connect button is enabled")
        
        # Set up monitoring for sendCommand
        await self.page.evaluate("""
            window.testResults = {
                clickDetected: false,
                sendCommandCalled: false,
                commandType: null,
                socketEmitted: false,
                emittedData: null
            };
            
            // Monitor button clicks
            document.getElementById('connect-drone-btn').addEventListener('click', () => {
                window.testResults.clickDetected = true;
                console.log('🔘 Connect button click detected');
            });
            
            // Monitor sendCommand calls
            if (window.WebGCS.modules && window.WebGCS.modules.connection) {
                const originalSendCommand = window.WebGCS.modules.connection.sendCommand;
                window.WebGCS.modules.connection.sendCommand = function(command, params) {
                    window.testResults.sendCommandCalled = true;
                    window.testResults.commandType = command;
                    console.log('📤 sendCommand called:', command, params);
                    return originalSendCommand.call(this, command, params);
                };
            }
            
            // Monitor SocketIO emissions
            if (window.WebGCS.socket) {
                const originalEmit = window.WebGCS.socket.emit;
                window.WebGCS.socket.emit = function(event, data) {
                    if (event === 'send_command') {
                        window.testResults.socketEmitted = true;
                        window.testResults.emittedData = data;
                        console.log('🚀 SocketIO emit detected:', event, data);
                    }
                    return originalEmit.call(this, event, data);
                };
            }
        """)
        
        # Click the connect button
        logger.info("🖱️ Clicking connect button...")
        await connect_btn.click()
        
        # Wait for processing
        await self.page.wait_for_timeout(2000)
        
        # Check test results
        test_results = await self.page.evaluate("window.testResults")
        logger.info(f"Test results: {test_results}")
        
        # Validate each step
        success = True
        
        if test_results['clickDetected']:
            logger.info("✅ Button click detected")
        else:
            logger.error("❌ Button click NOT detected")
            success = False
        
        if test_results['sendCommandCalled']:
            logger.info(f"✅ sendCommand called: {test_results['commandType']}")
            if test_results['commandType'] == 'connect_drone':
                logger.info("✅ Correct command type: connect_drone")
            else:
                logger.error(f"❌ Wrong command type: {test_results['commandType']}")
                success = False
        else:
            logger.error("❌ sendCommand NOT called")
            success = False
        
        if test_results['socketEmitted']:
            logger.info(f"✅ SocketIO emit detected: {test_results['emittedData']}")
        else:
            logger.error("❌ SocketIO emit NOT detected")
            success = False
        
        # Wait for backend response
        logger.info("⏳ Waiting for backend response...")
        await self.page.wait_for_timeout(5000)
        
        # Check for connection state changes
        final_drone_state = await self.page.evaluate("window.WebGCS.droneConnected")
        final_btn_text = await connect_btn.text_content()
        
        logger.info(f"Final drone connected state: {final_drone_state}")
        logger.info(f"Final button text: '{final_btn_text}'")
        
        if final_drone_state:
            logger.info("✅ Drone connection state updated!")
        else:
            logger.warning("⚠️ Drone connection state not updated (may be expected if connection failed)")
        
        if "Disconnect" in final_btn_text:
            logger.info("✅ Button text changed to Disconnect!")
        else:
            logger.warning(f"⚠️ Button text not changed: '{final_btn_text}'")
        
        return success

    async def run_test(self):
        """Run the complete test"""
        try:
            await self.setup_browser()
            success = await self.test_with_socketio_wait()
            
            if success:
                logger.info("\n🎉 CONNECT BUTTON TEST: PASSED")
                logger.info("The connect button functionality is working!")
                return True
            else:
                logger.error("\n💥 CONNECT BUTTON TEST: FAILED")
                logger.error("Connect button functionality has issues.")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test crashed: {e}")
            return False
        finally:
            await self.cleanup()

async def main():
    """Main test execution"""
    test = ConnectButtonTimingTest()
    success = await test.run_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    asyncio.run(main())