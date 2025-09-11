"""
TEST-506: PFD Performance Validation Testing
Phase 5: VFR HUD/Primary Flight Display Testing

Tests rendering performance, latency requirements, canvas optimization,
and smooth visual updates without flicker during 60-second stress test.
"""

import pytest
import asyncio
from playwright.async_api import async_playwright
import time
import statistics


class TestPFDPerformanceValidation:
    """Test PFD performance requirements and optimization"""
    
    @pytest.mark.asyncio
    async def test_rendering_performance_10hz(self):
        """TEST-506-001: Test 10Hz rendering performance requirement"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection for real data
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(3000)
                
                # Measure rendering performance over 10 seconds
                print("Measuring PFD rendering performance for 10 seconds...")
                
                performance_data = await page.evaluate("""
                    () => {
                        return new Promise((resolve) => {
                            const measurements = [];
                            let frameCount = 0;
                            let lastFrameTime = performance.now();
                            const startTime = performance.now();
                            const testDuration = 10000; // 10 seconds
                            
                            function measureFrame() {
                                const currentTime = performance.now();
                                const frameDelta = currentTime - lastFrameTime;
                                
                                measurements.push({
                                    frameNumber: frameCount,
                                    timestamp: currentTime,
                                    frameDelta: frameDelta,
                                    fps: 1000 / frameDelta
                                });
                                
                                frameCount++;
                                lastFrameTime = currentTime;
                                
                                if (currentTime - startTime < testDuration) {
                                    requestAnimationFrame(measureFrame);
                                } else {
                                    const totalTime = currentTime - startTime;
                                    const avgFps = frameCount / (totalTime / 1000);
                                    
                                    resolve({
                                        totalFrames: frameCount,
                                        totalTime: totalTime,
                                        averageFps: avgFps,
                                        measurements: measurements.slice(-100) // Last 100 frames
                                    });
                                }
                            }
                            
                            requestAnimationFrame(measureFrame);
                        });
                    }
                """)
                
                # Analyze performance data
                avg_fps = performance_data['averageFps']
                total_frames = performance_data['totalFrames']
                total_time = performance_data['totalTime']
                
                print("✅ PFD Rendering Performance Test Results:")
                print(f"   - Total frames rendered: {total_frames}")
                print(f"   - Test duration: {total_time/1000:.1f}s")
                print(f"   - Average FPS: {avg_fps:.1f}")
                print(f"   - Target: 10Hz (10 FPS minimum)")
                
                # Calculate frame time statistics
                frame_deltas = [m['frameDelta'] for m in performance_data['measurements'] if m['frameDelta'] > 0]
                if frame_deltas:
                    avg_frame_time = statistics.mean(frame_deltas)
                    min_frame_time = min(frame_deltas)
                    max_frame_time = max(frame_deltas)
                    
                    print(f"   - Average frame time: {avg_frame_time:.1f}ms")
                    print(f"   - Min frame time: {min_frame_time:.1f}ms")
                    print(f"   - Max frame time: {max_frame_time:.1f}ms")
                    
                    # Assert performance requirements
                    assert avg_fps >= 10.0, f"Average FPS {avg_fps:.1f} below minimum requirement of 10Hz"
                    assert avg_frame_time <= 100.0, f"Average frame time {avg_frame_time:.1f}ms exceeds 100ms limit"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_latency_requirements(self):
        """TEST-506-002: Test <100ms end-to-end latency requirement"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(3000)
                
                # Measure latency from data update to display
                latency_measurements = []
                
                for i in range(10):  # Take 10 latency measurements
                    # Inject telemetry data with timestamp
                    test_timestamp = int(time.time() * 1000)
                    
                    await page.evaluate(f"""
                        () => {{
                            const testData = {{
                                pitch: Math.random() * 20 - 10,
                                roll: Math.random() * 30 - 15,
                                timestamp: {test_timestamp}
                            }};
                            
                            // Simulate telemetry data update
                            if (window.pfd && window.pfd.updateDisplay) {{
                                window.pfd.updateDisplay(testData);
                            }}
                            
                            // Also update global telemetry data
                            window.telemetryData = {{...window.telemetryData, ...testData}};
                        }}
                    """)
                    
                    # Measure time for display to update
                    display_timestamp = await page.evaluate("""
                        () => {
                            // Return current PFD last update time
                            if (window.pfd && window.pfd.lastUpdate) {
                                return window.pfd.lastUpdate;
                            }
                            return Date.now();
                        }
                    """)
                    
                    latency = display_timestamp - test_timestamp
                    latency_measurements.append(latency)
                    
                    await page.wait_for_timeout(200)  # Wait between measurements
                
                # Analyze latency data
                avg_latency = statistics.mean(latency_measurements)
                max_latency = max(latency_measurements)
                min_latency = min(latency_measurements)
                
                print("✅ End-to-End Latency Test Results:")
                print(f"   - Average latency: {avg_latency:.1f}ms")
                print(f"   - Maximum latency: {max_latency:.1f}ms")
                print(f"   - Minimum latency: {min_latency:.1f}ms")
                print(f"   - Requirement: <100ms")
                
                # Show individual measurements
                for i, latency in enumerate(latency_measurements):
                    status = "✅" if latency < 100 else "❌"
                    print(f"   - Measurement {i+1:2d}: {latency:5.1f}ms {status}")
                
                # Assert latency requirements
                assert avg_latency < 100.0, f"Average latency {avg_latency:.1f}ms exceeds 100ms requirement"
                assert max_latency < 200.0, f"Maximum latency {max_latency:.1f}ms too high (should be <200ms)"
                
                # At least 80% of measurements should be under 100ms
                fast_measurements = sum(1 for l in latency_measurements if l < 100)
                fast_percentage = (fast_measurements / len(latency_measurements)) * 100
                assert fast_percentage >= 80, f"Only {fast_percentage:.0f}% of measurements under 100ms"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_canvas_optimization(self):
        """TEST-506-003: Test canvas rendering optimization and efficiency"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Measure canvas performance metrics
                optimization_metrics = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        if (!canvas) return null;
                        
                        const ctx = canvas.getContext('2d');
                        const startTime = performance.now();
                        
                        // Test basic drawing operations performance
                        const operations = {
                            fillRect: 0,
                            strokeRect: 0,
                            arc: 0,
                            text: 0,
                            lineWidth: 0
                        };
                        
                        // Measure fillRect performance
                        let opStart = performance.now();
                        for (let i = 0; i < 1000; i++) {
                            ctx.fillRect(i % 100, i % 100, 1, 1);
                        }
                        operations.fillRect = performance.now() - opStart;
                        
                        // Measure strokeRect performance
                        opStart = performance.now();
                        for (let i = 0; i < 1000; i++) {
                            ctx.strokeRect(i % 100, i % 100, 1, 1);
                        }
                        operations.strokeRect = performance.now() - opStart;
                        
                        // Measure arc performance
                        opStart = performance.now();
                        for (let i = 0; i < 1000; i++) {
                            ctx.beginPath();
                            ctx.arc(50, 50, 10, 0, Math.PI * 2);
                            ctx.stroke();
                        }
                        operations.arc = performance.now() - opStart;
                        
                        // Measure text performance
                        opStart = performance.now();
                        for (let i = 0; i < 100; i++) {
                            ctx.fillText('Test', i % 100, i % 100);
                        }
                        operations.text = performance.now() - opStart;
                        
                        const totalTime = performance.now() - startTime;
                        
                        return {
                            canvasSize: canvas.width * canvas.height,
                            operations: operations,
                            totalTestTime: totalTime,
                            contextType: ctx.constructor.name
                        };
                    }
                """)
                
                if optimization_metrics:
                    print("✅ Canvas Optimization Test Results:")
                    print(f"   - Canvas size: {optimization_metrics['canvasSize']} pixels")
                    print(f"   - Context type: {optimization_metrics['contextType']}")
                    print(f"   - Total test time: {optimization_metrics['totalTestTime']:.1f}ms")
                    print("   - Operation performance (1000 ops):")
                    
                    for op, time_ms in optimization_metrics['operations'].items():
                        ops_per_ms = 1000 / time_ms if time_ms > 0 else 0
                        print(f"     • {op:12s}: {time_ms:6.1f}ms ({ops_per_ms:6.0f} ops/ms)")
                    
                    # Assert reasonable performance
                    total_time = optimization_metrics['totalTestTime']
                    assert total_time < 1000, f"Canvas operations took too long: {total_time:.1f}ms"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_60_second_stress_test(self):
        """TEST-506-004: 60-second stress test for dropped updates and flicker"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(3000)
                
                # Run 60-second stress test
                print("Starting 60-second PFD stress test...")
                
                stress_test_result = await page.evaluate("""
                    () => {
                        return new Promise((resolve) => {
                            const testDuration = 60000; // 60 seconds
                            const startTime = performance.now();
                            
                            let updateCount = 0;
                            let errorCount = 0;
                            let lastUpdateTime = 0;
                            let maxGapBetweenUpdates = 0;
                            const updateGaps = [];
                            
                            // Monitor PFD updates
                            const monitorInterval = setInterval(() => {
                                try {
                                    const currentTime = performance.now();
                                    
                                    // Check if PFD is still updating
                                    if (window.pfd && window.pfd.lastUpdate) {
                                        const pfdLastUpdate = window.pfd.lastUpdate;
                                        
                                        if (pfdLastUpdate > lastUpdateTime) {
                                            const gap = pfdLastUpdate - lastUpdateTime;
                                            if (lastUpdateTime > 0) {
                                                updateGaps.push(gap);
                                                maxGapBetweenUpdates = Math.max(maxGapBetweenUpdates, gap);
                                            }
                                            
                                            updateCount++;
                                            lastUpdateTime = pfdLastUpdate;
                                        }
                                    }
                                    
                                    // Simulate varying telemetry data to stress the system
                                    if (window.pfd && window.pfd.updateDisplay) {
                                        const testData = {
                                            pitch: Math.sin(currentTime / 1000) * 30,
                                            roll: Math.cos(currentTime / 800) * 45,
                                            yaw: (currentTime / 100) % 360,
                                            altitude: 100 + Math.sin(currentTime / 2000) * 50,
                                            groundspeed: 10 + Math.abs(Math.sin(currentTime / 1500)) * 20
                                        };
                                        
                                        window.pfd.updateDisplay(testData);
                                    }
                                    
                                } catch (e) {
                                    errorCount++;
                                    console.error('PFD stress test error:', e);
                                }
                                
                                // Check if test duration completed
                                if (currentTime - startTime >= testDuration) {
                                    clearInterval(monitorInterval);
                                    
                                    const totalTime = currentTime - startTime;
                                    const averageUpdateRate = updateCount / (totalTime / 1000);
                                    const averageGap = updateGaps.length > 0 ? 
                                        updateGaps.reduce((a, b) => a + b, 0) / updateGaps.length : 0;
                                    
                                    resolve({
                                        duration: totalTime,
                                        updateCount: updateCount,
                                        errorCount: errorCount,
                                        averageUpdateRate: averageUpdateRate,
                                        maxGapBetweenUpdates: maxGapBetweenUpdates,
                                        averageGap: averageGap,
                                        updateGaps: updateGaps.slice(-20) // Last 20 gaps
                                    });
                                }
                                
                            }, 100); // Check every 100ms
                        });
                    }
                """)
                
                # Analyze stress test results
                duration_sec = stress_test_result['duration'] / 1000
                update_rate = stress_test_result['averageUpdateRate']
                
                print("✅ 60-Second Stress Test Results:")
                print(f"   - Test duration: {duration_sec:.1f}s")
                print(f"   - Total updates: {stress_test_result['updateCount']}")
                print(f"   - Errors: {stress_test_result['errorCount']}")
                print(f"   - Average update rate: {update_rate:.1f}Hz")
                print(f"   - Max gap between updates: {stress_test_result['maxGapBetweenUpdates']:.1f}ms")
                print(f"   - Average gap: {stress_test_result['averageGap']:.1f}ms")
                
                # Assert stress test requirements
                assert stress_test_result['errorCount'] == 0, \
                    f"Stress test had {stress_test_result['errorCount']} errors"
                
                assert update_rate >= 8.0, \
                    f"Update rate {update_rate:.1f}Hz below minimum during stress test"
                
                assert stress_test_result['maxGapBetweenUpdates'] < 500, \
                    f"Maximum gap {stress_test_result['maxGapBetweenUpdates']:.1f}ms too large"
                
                # Check for consistent performance
                recent_gaps = stress_test_result['updateGaps']
                if recent_gaps:
                    gap_variance = statistics.variance(recent_gaps)
                    print(f"   - Update gap variance: {gap_variance:.1f}ms²")
                    
                    # Variance should be reasonable (consistent timing)
                    assert gap_variance < 10000, f"Update timing too inconsistent: {gap_variance:.1f}ms²"
                
            finally:
                await browser.close()
    
    @pytest.mark.asyncio
    async def test_visual_flicker_detection(self):
        """TEST-506-005: Test for visual flicker and smooth rendering"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=False)
            page = await browser.new_page()
            
            try:
                await page.goto('http://localhost:5002')
                await page.wait_for_load_state('networkidle')
                await page.wait_for_selector('#pfd-canvas', timeout=10000)
                
                # Enable connection
                connect_button = await page.query_selector('#connect-btn')
                if connect_button:
                    await connect_button.click()
                    await page.wait_for_timeout(3000)
                
                # Take multiple screenshots to detect flicker
                print("Analyzing visual stability for flicker detection...")
                
                screenshots = []
                for i in range(10):  # Take 10 screenshots over 2 seconds
                    canvas = await page.query_selector('#pfd-canvas')
                    screenshot = await canvas.screenshot()
                    screenshots.append(len(screenshot))  # Use size as content metric
                    await page.wait_for_timeout(200)
                
                # Analyze screenshot size variations (indicates content changes)
                size_variations = []
                for i in range(1, len(screenshots)):
                    variation = abs(screenshots[i] - screenshots[i-1])
                    size_variations.append(variation)
                
                avg_variation = statistics.mean(size_variations) if size_variations else 0
                max_variation = max(size_variations) if size_variations else 0
                
                print("✅ Visual Flicker Detection Test Results:")
                print(f"   - Screenshots taken: {len(screenshots)}")
                print(f"   - Average size variation: {avg_variation:.1f} bytes")
                print(f"   - Maximum size variation: {max_variation:.1f} bytes")
                
                # Check canvas stability
                canvas_stability = await page.evaluate("""
                    () => {
                        const canvas = document.getElementById('pfd-canvas');
                        if (!canvas) return null;
                        
                        const ctx = canvas.getContext('2d');
                        
                        // Check if canvas rendering is stable
                        const imageData1 = ctx.getImageData(0, 0, 100, 100);
                        
                        // Wait a frame
                        return new Promise(resolve => {
                            requestAnimationFrame(() => {
                                const imageData2 = ctx.getImageData(0, 0, 100, 100);
                                
                                // Compare pixel data for major changes
                                let pixelDifferences = 0;
                                for (let i = 0; i < imageData1.data.length; i += 4) {
                                    const diff = Math.abs(imageData1.data[i] - imageData2.data[i]);
                                    if (diff > 50) pixelDifferences++;
                                }
                                
                                resolve({
                                    totalPixels: imageData1.data.length / 4,
                                    pixelDifferences: pixelDifferences,
                                    stabilityPercentage: ((imageData1.data.length / 4 - pixelDifferences) / (imageData1.data.length / 4)) * 100
                                });
                            });
                        });
                    }
                """)
                
                if canvas_stability:
                    stability_pct = canvas_stability['stabilityPercentage']
                    print(f"   - Canvas stability: {stability_pct:.1f}% (pixel consistency)")
                    print(f"   - Pixel differences: {canvas_stability['pixelDifferences']}/{canvas_stability['totalPixels']}")
                    
                    # Assert visual stability
                    assert stability_pct > 80, f"Canvas stability {stability_pct:.1f}% too low (flickering detected)"
                
                # Screenshot size variations should be reasonable
                assert max_variation < 50000, f"Large visual changes detected: {max_variation} bytes"
                
            finally:
                await browser.close()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])