"""
Test 005: Web Interface Loading and Component Rendering
Validates web interface loads and components render correctly.
"""

import pytest
import requests
import time
import threading
from bs4 import BeautifulSoup
from src.web.app_factory import initialize_app


class TestWebInterfaceLoading:
    """Test web interface loading and component rendering."""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test fixtures."""
        self.app, self.socketio = initialize_app()
        self.app.config['TESTING'] = True
        
        # Start server in background thread
        self.server_thread = threading.Thread(
            target=lambda: self.socketio.run(
                self.app,
                host='127.0.0.1',
                port=5004,  # Use different port for testing
                debug=False,
                allow_unsafe_werkzeug=True
            )
        )
        self.server_thread.daemon = True
        self.server_thread.start()
        
        # Give server time to start
        time.sleep(2)
        
        self.base_url = 'http://127.0.0.1:5004'
        
        yield
    
    def test_main_page_loads(self):
        """Test that main page loads successfully."""
        response = requests.get(f'{self.base_url}/')
        
        assert response.status_code == 200, "Main page should return 200 OK"
        assert 'WebGCS - Ground Control Station' in response.text, "Page should contain title"
        
        print("✅ Main page loads successfully")
    
    def test_required_javascript_files_included(self):
        """Test that all required JavaScript files are included."""
        response = requests.get(f'{self.base_url}/')
        soup = BeautifulSoup(response.text, 'html.parser')
        
        required_js_files = [
            'main.js',
            'connection.js', 
            'telemetry.js',
            'controls.js',
            'pfd.js',
            'validation.js'
        ]
        
        script_tags = soup.find_all('script', src=True)
        script_sources = [tag.get('src') for tag in script_tags]
        
        for js_file in required_js_files:
            found = any(js_file in src for src in script_sources)
            assert found, f"JavaScript file {js_file} should be included"
        
        print("✅ All required JavaScript files included")
    
    def test_component_panels_present(self):
        """Test that all component panels are present."""
        response = requests.get(f'{self.base_url}/')
        soup = BeautifulSoup(response.text, 'html.parser')
        
        required_panels = [
            'connection-panel',
            'flight-controls',
            'navigation-panel', 
            'pfd-display',
            'map-container'
        ]
        
        for panel_class in required_panels:
            panel = soup.find('div', class_=panel_class)
            assert panel is not None, f"Panel {panel_class} should be present"
        
        print("✅ All component panels present")
    
    def test_critical_buttons_present(self):
        """Test that critical flight control buttons are present."""
        response = requests.get(f'{self.base_url}/')
        soup = BeautifulSoup(response.text, 'html.parser')
        
        critical_buttons = [
            'connect-drone-btn',
            'arm-btn',
            'disarm-btn', 
            'takeoff-btn',
            'emergency-stop-btn',
            'goto-btn'
        ]
        
        for button_id in critical_buttons:
            button = soup.find('button', id=button_id)
            assert button is not None, f"Button {button_id} should be present"
        
        print("✅ All critical buttons present")
    
    def test_pfd_canvas_present(self):
        """Test that PFD canvas element is present."""
        response = requests.get(f'{self.base_url}/')
        soup = BeautifulSoup(response.text, 'html.parser')
        
        canvas = soup.find('canvas', id='pfd-canvas')
        assert canvas is not None, "PFD canvas should be present"
        
        # Check canvas dimensions
        width = canvas.get('width')
        height = canvas.get('height')
        assert width == '800', "Canvas width should be 800"
        assert height == '600', "Canvas height should be 600"
        
        print("✅ PFD canvas present with correct dimensions")
    
    def test_input_validation_attributes(self):
        """Test that input fields have validation attributes."""
        response = requests.get(f'{self.base_url}/')
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Check coordinate inputs
        lat_input = soup.find('input', id='goto-latitude')
        lon_input = soup.find('input', id='goto-longitude')
        alt_input = soup.find('input', id='goto-altitude')
        
        assert lat_input is not None, "Latitude input should be present"
        assert lon_input is not None, "Longitude input should be present"
        assert alt_input is not None, "Altitude input should be present"
        
        # Check validation attributes
        assert lat_input.get('data-validation') == 'latitude', "Latitude validation attribute"
        assert lon_input.get('data-validation') == 'longitude', "Longitude validation attribute"
        assert alt_input.get('data-validation') == 'altitude', "Altitude validation attribute"
        
        print("✅ Input validation attributes present")
    
    def test_status_api_endpoint(self):
        """Test that status API endpoint is available."""
        response = requests.get(f'{self.base_url}/api/status')
        
        assert response.status_code == 200, "Status API should return 200 OK"
        
        # Should return JSON
        data = response.json()
        assert isinstance(data, dict), "Status API should return JSON object"
        
        print("✅ Status API endpoint working")
    
    def test_static_assets_accessible(self):
        """Test that static assets are accessible."""
        # Test CSS file
        css_response = requests.get(f'{self.base_url}/static/css/styles.css')
        assert css_response.status_code == 200, "CSS file should be accessible"
        
        # Test JavaScript files
        js_files = ['main.js', 'connection.js', 'controls.js', 'pfd.js']
        for js_file in js_files:
            js_response = requests.get(f'{self.base_url}/static/js/{js_file}')
            assert js_response.status_code == 200, f"JS file {js_file} should be accessible"
        
        print("✅ Static assets accessible")


if __name__ == "__main__":
    # Run specific test
    pytest.main([__file__ + "::TestWebInterfaceLoading::test_main_page_loads", "-v"])