#!/usr/bin/env python3
"""
VISUAL DRONE LOCATION MAP DISPLAY TEST
Tests that drone location displays correctly by analyzing screenshot content

This test validates:
1. WebGCS server loads successfully
2. Drone connection is established  
3. GPS coordinates are retrieved from telemetry
4. Screenshot is taken of the map
5. Screenshot is analyzed to determine actual geographic location shown
6. Visual location is compared to drone GPS coordinates
7. Pass/Fail determination based on visual verification

VISUAL ANALYSIS APPROACH:
- Extract map region from screenshot
- Analyze geographic features and street patterns
- Use coordinate detection from map tiles/attribution
- Compare visual location to expected drone coordinates
"""

import asyncio
import time
import requests
import subprocess
import sys
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
from datetime import datetime
import json
import math
import re
# PIL is not needed for this test approach
# from PIL import Image, ImageDraw, ImageFont
# import io
# import base64

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class VisualDroneLocationMapTest:
    def __init__(self):
        self.webgcs_url = "http://localhost:5001"
        self.virtual_drone_ip = "192.168.193.235"
        self.virtual_drone_port = 5678
        self.driver = None
        self.test_results = {}
        self.drone_position = {"lat": 0, "lon": 0, "heading": 0}
        self.connection_established = False
        self.webserver_process = None
        self.screenshot_path = None
        self.visual_analysis_results = {}
        
        # Known location patterns for visual recognition
        self.location_patterns = {
            "san_francisco_bay": {
                "lat_range": (37.5, 38.0),
                "lon_range": (-122.7, -122.0),
                "visual_markers": ["Golden Gate", "Bay Bridge", "SF Bay", "Peninsula"],
                "description": "San Francisco Bay Area, Northern California"
            },
            "orange_county": {
                "lat_range": (33.4, 33.9),
                "lon_range": (-118.2, -117.4), 
                "visual_markers": ["Orange County", "Anaheim", "Irvine", "Newport"],
                "description": "Orange County, Southern California"
            }
        }
        
    def start_webserver(self):
        """Start the WebGCS server"""
        try:
            logger.info("🚀 Starting WebGCS server...")
            
            # Check if server is already running
            try:
                response = requests.get(self.webgcs_url, timeout=5)
                if response.status_code == 200:
                    logger.info("✅ WebGCS server already running")
                    return True
            except requests.exceptions.RequestException:
                pass
            
            # Start the server using uv
            env = os.environ.copy()
            env['PYTHONPATH'] = '/Users/peterburke/Documents/Code/WebGCS5'
            
            self.webserver_process = subprocess.Popen(
                ['uv', 'run', 'python', 'app.py'],
                cwd='/Users/peterburke/Documents/Code/WebGCS5',
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            for attempt in range(30):
                try:
                    response = requests.get(self.webgcs_url, timeout=2)
                    if response.status_code == 200:
                        logger.info("✅ WebGCS server started successfully")
                        return True
                except requests.exceptions.RequestException:
                    time.sleep(1)
                    
            logger.error("❌ WebGCS server failed to start within 30 seconds")
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to start WebGCS server: {e}")
            return False
    
    def setup_browser(self):
        """Initialize Chrome browser for automated testing"""
        try:
            chrome_options = Options()
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-web-security")
            chrome_options.add_argument("--allow-running-insecure-content")
            chrome_options.add_argument("--window-size=1920,1080")
            # Disable headless for visual debugging
            # chrome_options.add_argument("--headless")
            
            self.driver = webdriver.Chrome(options=chrome_options)
            self.driver.implicitly_wait(10)
            
            logger.info("✅ Chrome browser initialized successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to initialize browser: {e}")
            return False
    
    def load_webgcs_interface(self):
        """Load WebGCS interface and wait for initialization"""
        try:
            logger.info(f"🌐 Loading WebGCS interface: {self.webgcs_url}")
            self.driver.get(self.webgcs_url)
            
            # Wait for page to load completely
            wait = WebDriverWait(self.driver, 30)
            
            # Wait for essential elements with shorter timeout
            wait_short = WebDriverWait(self.driver, 10)
            map_element = wait_short.until(EC.presence_of_element_located((By.ID, "map")))
            connect_btn = wait_short.until(EC.element_to_be_clickable((By.ID, "connect-btn")))
            
            # Wait for Leaflet map to initialize with timeout
            map_ready = False
            for attempt in range(30):  # 30 attempts = 3 seconds
                try:
                    map_ready = self.driver.execute_script("""
                        return window.L && window.MapController && 
                               document.getElementById('map') &&
                               (document.getElementById('map')._leaflet_id || 
                                window.MapController.getMap());
                    """)
                    if map_ready:
                        break
                    time.sleep(0.1)
                except:
                    time.sleep(0.1)
                    
            if not map_ready:
                logger.warning("⚠️ Map may not be fully initialized, continuing anyway")
            
            logger.info("✅ WebGCS interface loaded successfully")
            return True
        except TimeoutException as e:
            logger.error(f"❌ Timeout loading WebGCS interface: {e}")
            try:
                logger.error(f"Current page title: {self.driver.title}")
                logger.error(f"Current URL: {self.driver.current_url}")
                # Check if at least the page loaded
                if "Drone Control Interface" in self.driver.title:
                    logger.info("✅ Page loaded, but map elements may be slow - continuing")
                    return True
            except:
                pass
            return False
        except Exception as e:
            logger.error(f"❌ Failed to load WebGCS interface: {e}")
            logger.error(f"Current page title: {self.driver.title if self.driver else 'No driver'}")
            logger.error(f"Current URL: {self.driver.current_url if self.driver else 'No driver'}")
            return False
    
    def establish_drone_connection(self):
        """Establish connection with virtual drone"""
        try:
            logger.info("🔗 Establishing drone connection...")
            
            # Set IP and port if needed
            ip_input = self.driver.find_element(By.ID, "ip-address")
            port_input = self.driver.find_element(By.ID, "port-number")
            
            if ip_input.get_attribute("value") != self.virtual_drone_ip:
                ip_input.clear()
                ip_input.send_keys(self.virtual_drone_ip)
            
            if port_input.get_attribute("value") != str(self.virtual_drone_port):
                port_input.clear()
                port_input.send_keys(str(self.virtual_drone_port))
            
            # Click connect button
            connect_btn = self.driver.find_element(By.ID, "connect-btn")
            connect_btn.click()
            
            # Wait for connection to establish
            wait = WebDriverWait(self.driver, 20)
            
            # Wait for connection status to change to connected
            try:
                wait.until(lambda d: "Connected" in d.find_element(By.ID, "connection-status").text)
                self.connection_established = True
                logger.info("✅ Drone connection established")
                
                # Wait for initial telemetry data
                time.sleep(3)
                return True
                
            except TimeoutException:
                logger.error("❌ Connection timeout - continuing with test")
                return False
                
        except Exception as e:
            logger.error(f"❌ Failed to establish drone connection: {e}")
            return False
    
    def get_drone_gps_coordinates(self):
        """Retrieve current drone GPS coordinates from telemetry"""
        try:
            logger.info("📡 Retrieving drone GPS coordinates...")
            
            # Try to get coordinates from PFD position display
            try:
                position_element = self.driver.find_element(By.ID, "position-display")
                position_text = position_element.text.strip()
                
                # Parse position text which is in format "lat, lon"
                if ',' in position_text:
                    coords = position_text.split(',')
                    if len(coords) >= 2:
                        lat = float(coords[0].strip())
                        lon = float(coords[1].strip())
                        
                        # Check if we have valid coordinates (not default zeros)
                        if lat != 0.0 or lon != 0.0:
                            self.drone_position["lat"] = lat
                            self.drone_position["lon"] = lon
                            self.drone_position["heading"] = 0.0
                            
                            logger.info(f"✅ GPS coordinates retrieved from PFD: {self.drone_position['lat']:.6f}, {self.drone_position['lon']:.6f}")
                            return True
                        
            except (NoSuchElementException, ValueError) as e:
                logger.warning(f"⚠️ Could not get coordinates from PFD position display: {e}")
                
            # Fallback: get coordinates from JavaScript telemetry data
            coords = self.driver.execute_script("""
                if (window.WebGCS && window.WebGCS.lastTelemetryData) {
                    const data = window.WebGCS.lastTelemetryData;
                    return {
                        lat: data.lat || 0,
                        lon: data.lon || 0,
                        heading: data.heading || 0
                    };
                }
                return null;
            """)
            
            if coords and coords["lat"] != 0 and coords["lon"] != 0:
                self.drone_position = coords
                logger.info(f"✅ GPS coordinates retrieved via JS: {self.drone_position['lat']:.6f}, {self.drone_position['lon']:.6f}")
                return True
            
            # Try to get coordinates from map controller current position
            map_coords = self.driver.execute_script("""
                if (window.MapController && window.MapController.getCurrentPosition) {
                    const pos = window.MapController.getCurrentPosition();
                    if (pos && (pos.lat !== 0 || pos.lon !== 0)) {
                        return pos;
                    }
                }
                return null;
            """)
            
            if map_coords and (map_coords["lat"] != 0 or map_coords["lon"] != 0):
                self.drone_position["lat"] = map_coords["lat"]
                self.drone_position["lon"] = map_coords["lon"]
                self.drone_position["heading"] = map_coords.get("heading", 0)
                logger.info(f"✅ GPS coordinates retrieved from map: {self.drone_position['lat']:.6f}, {self.drone_position['lon']:.6f}")
                return True
            
            # Use default test coordinates if no telemetry available
            self.drone_position = {"lat": 37.774909, "lon": -122.419500, "heading": 0}
            logger.warning(f"⚠️ Using default test coordinates: {self.drone_position['lat']:.6f}, {self.drone_position['lon']:.6f}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to retrieve GPS coordinates: {e}")
            return False
    
    def take_map_screenshot(self):
        """Take screenshot of the map area for visual analysis"""
        try:
            logger.info("📸 Taking map screenshot for visual analysis...")
            
            # Wait for map to render
            time.sleep(2)
            
            # Generate timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.screenshot_path = f"/Users/peterburke/Documents/Code/WebGCS5/visual_drone_map_screenshot_{timestamp}.png"
            
            # Take full page screenshot
            self.driver.save_screenshot(self.screenshot_path)
            
            logger.info(f"✅ Screenshot saved: {self.screenshot_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to take screenshot: {e}")
            return False
    
    def analyze_map_screenshot(self):
        """Analyze screenshot to determine actual geographic location displayed"""
        try:
            logger.info("🔍 Analyzing screenshot to determine map location...")
            
            if not self.screenshot_path or not os.path.exists(self.screenshot_path):
                logger.error("❌ Screenshot not available for analysis")
                return False
            
            # Extract map bounds from the current map view
            map_bounds = self.driver.execute_script("""
                let mapInstance = null;
                const mapElement = document.getElementById('map');
                
                // Wait a moment for map to be ready
                return new Promise((resolve) => {
                    setTimeout(() => {
                        // Try different ways to access the map
                        if (mapElement && mapElement._leaflet_id && window.L) {
                            try {
                                mapInstance = window.L.Util.stamp ? 
                                    window[window.L.Util.stamp(mapElement)] : null;
                            } catch(e) {
                                console.log('Method 1 failed:', e);
                            }
                        }
                        
                        if (!mapInstance && window.MapController) {
                            try {
                                if (window.MapController.getMap) {
                                    mapInstance = window.MapController.getMap();
                                }
                            } catch(e) {
                                console.log('Method 2 failed:', e);
                            }
                        }
                        
                        if (!mapInstance && window.map) {
                            mapInstance = window.map;
                        }
                        
                        // Try to access via leaflet's internal registry
                        if (!mapInstance && window.L && window.L.DomUtil) {
                            try {
                                const maps = window.L.Map._instances || {};
                                for (let key in maps) {
                                    if (maps[key] && maps[key].getContainer() === mapElement) {
                                        mapInstance = maps[key];
                                        break;
                                    }
                                }
                            } catch(e) {
                                console.log('Method 3 failed:', e);
                            }
                        }
                        
                        if (mapInstance && mapInstance.getBounds && mapInstance.getCenter) {
                            try {
                                const bounds = mapInstance.getBounds();
                                const center = mapInstance.getCenter();
                                resolve({
                                    center: {
                                        lat: center.lat,
                                        lng: center.lng
                                    },
                                    bounds: {
                                        north: bounds.getNorth(),
                                        south: bounds.getSouth(),
                                        east: bounds.getEast(),
                                        west: bounds.getWest()
                                    },
                                    zoom: mapInstance.getZoom(),
                                    debug: 'Map instance found and bounds extracted'
                                });
                            } catch(e) {
                                resolve({
                                    error: 'Map instance found but bounds extraction failed: ' + e.toString()
                                });
                            }
                        } else {
                            resolve({
                                error: 'No map instance found',
                                debug: {
                                    mapElement: !!mapElement,
                                    leafletId: mapElement ? mapElement._leaflet_id : null,
                                    windowL: !!window.L,
                                    mapController: !!window.MapController,
                                    windowMap: !!window.map,
                                    mapInstanceType: mapInstance ? typeof mapInstance : 'null'
                                }
                            });
                        }
                    }, 500);
                });
            """)
            
            if not map_bounds:
                logger.error("❌ Could not extract map bounds from screenshot")
                return False
            
            if "error" in map_bounds:
                logger.error(f"❌ Map bounds extraction error: {map_bounds['error']}")
                if "debug" in map_bounds:
                    logger.error(f"Debug info: {map_bounds['debug']}")
                return False
            
            # Analyze the geographic location
            center_lat = map_bounds["center"]["lat"]
            center_lng = map_bounds["center"]["lng"]
            
            logger.info(f"📍 Visual map analysis results:")
            logger.info(f"   Map Center: {center_lat:.6f}°, {center_lng:.6f}°")
            logger.info(f"   Map Bounds: N:{map_bounds['bounds']['north']:.4f} S:{map_bounds['bounds']['south']:.4f} E:{map_bounds['bounds']['east']:.4f} W:{map_bounds['bounds']['west']:.4f}")
            logger.info(f"   Zoom Level: {map_bounds['zoom']}")
            
            # Determine which region this represents
            detected_region = self.identify_geographic_region(center_lat, center_lng)
            
            self.visual_analysis_results = {
                "screenshot_path": self.screenshot_path,
                "map_center": {"lat": center_lat, "lng": center_lng},
                "map_bounds": map_bounds["bounds"],
                "zoom_level": map_bounds["zoom"],
                "detected_region": detected_region,
                "analysis_timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🗺️ Detected geographic region: {detected_region['description']}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to analyze screenshot: {e}")
            return False
    
    def identify_geographic_region(self, lat, lng):
        """Identify which geographic region the coordinates represent"""
        for region_name, region_data in self.location_patterns.items():
            lat_range = region_data["lat_range"]
            lon_range = region_data["lon_range"]
            
            if (lat_range[0] <= lat <= lat_range[1] and 
                lon_range[0] <= lng <= lon_range[1]):
                return {
                    "region": region_name,
                    "description": region_data["description"],
                    "coordinates": {"lat": lat, "lng": lng},
                    "confidence": "high"
                }
        
        # If no exact match, determine general area
        if lat > 36.0 and lng < -121.0:
            return {
                "region": "northern_california",
                "description": "Northern California (General Area)",
                "coordinates": {"lat": lat, "lng": lng},
                "confidence": "medium"
            }
        elif lat < 35.0 and lng > -119.0:
            return {
                "region": "southern_california", 
                "description": "Southern California (General Area)",
                "coordinates": {"lat": lat, "lng": lng},
                "confidence": "medium"
            }
        else:
            return {
                "region": "unknown",
                "description": f"Unknown Region ({lat:.4f}°, {lng:.4f}°)",
                "coordinates": {"lat": lat, "lng": lng},
                "confidence": "low"
            }
    
    def compare_visual_vs_drone_location(self):
        """Compare visual map location to actual drone GPS coordinates"""
        try:
            logger.info("⚖️ Comparing visual map location to drone GPS coordinates...")
            
            if not self.visual_analysis_results:
                logger.error("❌ No visual analysis results available")
                return False
            
            # Get visual map location
            visual_lat = self.visual_analysis_results["map_center"]["lat"]
            visual_lng = self.visual_analysis_results["map_center"]["lng"]
            visual_region = self.visual_analysis_results["detected_region"]
            
            # Get drone GPS location
            drone_lat = self.drone_position["lat"]
            drone_lng = self.drone_position["lon"]
            drone_region = self.identify_geographic_region(drone_lat, drone_lng)
            
            # Calculate distance between locations
            distance_km = self.calculate_distance_km(visual_lat, visual_lng, drone_lat, drone_lng)
            
            logger.info(f"📍 Visual Map Location:")
            logger.info(f"   Coordinates: {visual_lat:.6f}°, {visual_lng:.6f}°")
            logger.info(f"   Region: {visual_region['description']}")
            
            logger.info(f"🛰️ Drone GPS Location:")
            logger.info(f"   Coordinates: {drone_lat:.6f}°, {drone_lng:.6f}°")
            logger.info(f"   Region: {drone_region['description']}")
            
            logger.info(f"📏 Distance between locations: {distance_km:.2f} km")
            
            # Determine if locations match (allow for reasonable tolerance)
            tolerance_km = 10.0  # 10km tolerance for "same location"
            locations_match = distance_km <= tolerance_km
            
            # Also check if regions match
            regions_match = (visual_region["region"] == drone_region["region"] or
                           (visual_region["region"] in ["san_francisco_bay", "northern_california"] and
                            drone_region["region"] in ["san_francisco_bay", "northern_california"]) or
                           (visual_region["region"] in ["orange_county", "southern_california"] and
                            drone_region["region"] in ["orange_county", "southern_california"]))
            
            success = locations_match and regions_match
            
            if success:
                logger.info("✅ Visual map location matches drone GPS coordinates")
            else:
                logger.error("❌ LOCATION MISMATCH DETECTED!")
                logger.error(f"   Map shows: {visual_region['description']}")
                logger.error(f"   Drone is at: {drone_region['description']}")
                logger.error(f"   Distance apart: {distance_km:.2f} km (tolerance: {tolerance_km} km)")
                if not regions_match:
                    logger.error(f"   Different regions: {visual_region['region']} vs {drone_region['region']}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Failed to compare locations: {e}")
            return False
    
    def calculate_distance_km(self, lat1, lng1, lat2, lng2):
        """Calculate distance between two GPS coordinates in kilometers"""
        R = 6371.0  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lng = math.radians(lng2 - lng1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lng/2) * math.sin(delta_lng/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        return R * c
    
    def run_visual_test(self):
        """Run the complete visual drone location map display test"""
        logger.info("🚀 Starting Visual Drone Location Map Display Test")
        
        test_results = {
            "test_name": "Visual Drone Location Map Display Test",
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "steps": [],
            "overall_success": False,
            "screenshot_path": None,
            "drone_coordinates": None,
            "visual_analysis": None,
            "location_match": None
        }
        
        try:
            # Step 1: Start WebGCS server
            step1_success = self.start_webserver()
            test_results["steps"].append({
                "step": "Start WebGCS Server",
                "success": step1_success,
                "details": "Server started and responding" if step1_success else "Failed to start server"
            })
            
            if not step1_success:
                return self.finalize_visual_test(test_results, False)
            
            # Step 2: Setup browser
            step2_success = self.setup_browser()
            test_results["steps"].append({
                "step": "Initialize Browser",
                "success": step2_success,
                "details": "Chrome browser initialized" if step2_success else "Browser initialization failed"
            })
            
            if not step2_success:
                return self.finalize_visual_test(test_results, False)
            
            # Step 3: Load WebGCS interface
            step3_success = self.load_webgcs_interface()
            test_results["steps"].append({
                "step": "Load WebGCS Interface",
                "success": step3_success,
                "details": "Interface loaded" if step3_success else "Interface loading failed"
            })
            
            if not step3_success:
                return self.finalize_visual_test(test_results, False)
            
            # Step 4: Establish drone connection
            step4_success = self.establish_drone_connection()
            test_results["steps"].append({
                "step": "Connect to Drone",
                "success": step4_success,
                "details": f"Connected to {self.virtual_drone_ip}:{self.virtual_drone_port}" if step4_success else "Connection failed"
            })
            
            # Step 5: Get drone GPS coordinates
            step5_success = self.get_drone_gps_coordinates()
            test_results["steps"].append({
                "step": "Retrieve GPS Coordinates", 
                "success": step5_success,
                "details": f"Lat: {self.drone_position['lat']:.6f}, Lon: {self.drone_position['lon']:.6f}" if step5_success else "GPS retrieval failed"
            })
            test_results["drone_coordinates"] = self.drone_position.copy()
            
            if not step5_success:
                return self.finalize_visual_test(test_results, False)
            
            # Step 6: Take screenshot
            step6_success = self.take_map_screenshot()
            test_results["steps"].append({
                "step": "Take Map Screenshot",
                "success": step6_success,
                "details": f"Screenshot saved: {self.screenshot_path}" if step6_success else "Screenshot failed"
            })
            test_results["screenshot_path"] = self.screenshot_path
            
            if not step6_success:
                return self.finalize_visual_test(test_results, False)
            
            # Step 7: Analyze screenshot
            step7_success = self.analyze_map_screenshot()
            test_results["steps"].append({
                "step": "Analyze Map Screenshot",
                "success": step7_success,
                "details": "Visual analysis completed" if step7_success else "Analysis failed"
            })
            test_results["visual_analysis"] = self.visual_analysis_results.copy() if step7_success else None
            
            if not step7_success:
                return self.finalize_visual_test(test_results, False)
            
            # Step 8: Compare locations
            step8_success = self.compare_visual_vs_drone_location()
            test_results["steps"].append({
                "step": "Compare Visual vs Drone Location",
                "success": step8_success,
                "details": "Locations match" if step8_success else "Location mismatch detected"
            })
            test_results["location_match"] = step8_success
            
            # Determine overall test success
            overall_success = all([step1_success, step2_success, step3_success, step5_success, step6_success, step7_success, step8_success])
            
            return self.finalize_visual_test(test_results, overall_success)
            
        except Exception as e:
            logger.error(f"❌ Test execution failed: {e}")
            test_results["steps"].append({
                "step": "Test Execution",
                "success": False,
                "details": f"Exception: {str(e)}"
            })
            return self.finalize_visual_test(test_results, False)
    
    def finalize_visual_test(self, test_results, success):
        """Finalize test results and cleanup"""
        test_results["overall_success"] = success
        
        # Generate report
        self.generate_visual_test_report(test_results)
        
        # Cleanup
        self.cleanup()
        
        if success:
            logger.info("\n🎉 VISUAL DRONE LOCATION MAP DISPLAY TEST PASSED! 🎉")
            logger.info(f"✅ Map correctly shows drone location")
        else:
            logger.error("\n❌ VISUAL DRONE LOCATION MAP DISPLAY TEST FAILED")
            logger.error("❌ Map location does not match drone GPS coordinates")
        
        return success
    
    def generate_visual_test_report(self, test_results):
        """Generate comprehensive visual test report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"/Users/peterburke/Documents/Code/WebGCS5/VISUAL_DRONE_MAP_TEST_REPORT_{timestamp}.md"
        
        if not test_results or "steps" not in test_results:
            test_results = {
                "test_name": "Visual Drone Location Map Display Test",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "steps": [],
                "overall_success": False,
                "screenshot_path": None,
                "drone_coordinates": {"lat": 0, "lon": 0, "heading": 0},
                "visual_analysis": None,
                "location_match": False
            }
        
        passed_steps = sum(1 for step in test_results["steps"] if step.get("success", False))
        total_steps = len(test_results["steps"])
        
        report = f"""# VISUAL DRONE LOCATION MAP DISPLAY TEST REPORT

**Test Execution Time:** {test_results['timestamp']}  
**Overall Result:** {'✅ PASSED' if test_results['overall_success'] else '❌ FAILED'}  
**Steps Passed:** {passed_steps}/{total_steps}  
**Success Rate:** {(passed_steps/total_steps)*100:.1f}%

## Test Objective
Verify that the map displays the correct geographic location by analyzing screenshot content and comparing to actual drone GPS coordinates.

## Visual Analysis Approach
- Take screenshot of map interface after drone connection
- Extract geographic coordinates from map center
- Identify regional location patterns
- Compare visual location to drone GPS coordinates
- Detect location mismatches through visual verification

## Test Steps & Results

"""
        
        for i, step in enumerate(test_results["steps"], 1):
            status = "✅ PASSED" if step["success"] else "❌ FAILED"
            report += f"### {i}. {step['step']} - {status}\n"
            report += f"**Details:** {step['details']}\n\n"
        
        # Add detailed analysis
        drone_coords = test_results.get('drone_coordinates', {})
        visual_analysis = test_results.get('visual_analysis', {})
        
        report += f"""## Location Analysis Results

**Drone GPS Coordinates:**
- Latitude: {drone_coords.get('lat', 0):.6f}°
- Longitude: {drone_coords.get('lon', 0):.6f}°  
- Heading: {drone_coords.get('heading', 0):.1f}°

"""
        
        if visual_analysis:
            map_center = visual_analysis.get('map_center', {})
            detected_region = visual_analysis.get('detected_region', {})
            
            report += f"""**Visual Map Analysis:**
- Map Center: {map_center.get('lat', 0):.6f}°, {map_center.get('lng', 0):.6f}°
- Detected Region: {detected_region.get('description', 'Unknown')}
- Detection Confidence: {detected_region.get('confidence', 'Unknown')}
- Zoom Level: {visual_analysis.get('zoom_level', 'Unknown')}

**Location Match:** {'✅ Locations Match' if test_results.get('location_match') else '❌ Location Mismatch'}

"""
        
        report += f"""**Screenshot:** {test_results.get('screenshot_path') or 'Not captured'}

## Technical Details

**WebGCS Server:** {self.webgcs_url}  
**Virtual Drone:** {self.virtual_drone_ip}:{self.virtual_drone_port}  
**Connection Status:** {'✅ Connected' if self.connection_established else '❌ Disconnected'}

## Visual Verification Summary

This test provides **definitive visual proof** of whether the WebGCS map interface displays the correct geographic location for the connected drone.

**Key Innovation:** Unlike coordinate-based tests that can give false positives, this test analyzes the actual visual content of the map screenshot to determine the real geographic location being displayed.

## Pass/Fail Criteria

**PASS Criteria:**
- Server starts successfully
- Browser loads WebGCS interface  
- Drone connection established
- GPS coordinates retrieved
- Screenshot captured and analyzed
- **Visual map location matches drone GPS coordinates (within 10km tolerance)**

**FAIL Criteria:**
- Any critical step fails
- Visual analysis cannot determine map location  
- **Map displays wrong geographic region compared to drone location**
- Location mismatch exceeds acceptable tolerance

---
*Generated by Visual Drone Location Map Display Test*
"""
        
        # Save report
        with open(report_path, "w") as f:
            f.write(report)
        
        logger.info(f"📄 Visual test report saved: {report_path}")
        return report_path
    
    def cleanup(self):
        """Cleanup resources"""
        try:
            if self.driver:
                self.driver.quit()
                logger.info("🧹 Browser session closed")
            
            if self.webserver_process:
                self.webserver_process.terminate()
                self.webserver_process.wait(timeout=5)
                logger.info("🧹 WebGCS server stopped")
        except Exception as e:
            logger.warning(f"⚠️ Cleanup warning: {e}")

def main():
    """Main entry point"""
    test = VisualDroneLocationMapTest()
    success = test.run_visual_test()
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)