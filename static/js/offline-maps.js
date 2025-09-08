/**
 * WebGCS Offline Maps Module
 * Handles map tile downloading and caching for offline operation
 */

window.OfflineMaps = (function() {
    'use strict';
    
    // Private variables
    let isDownloading = false;
    let downloadProgress = 0;
    let totalTiles = 0;
    let downloadedTiles = 0;
    let downloadAborted = false;
    let cacheStats = { street: 0, satellite: 0, total: 0 };
    
    // DOM elements
    let elements = {};
    
    // Download configuration
    const DOWNLOAD_CONFIG = {
        maxConcurrentRequests: 4,
        requestDelay: 100, // ms between requests
        retryAttempts: 3,
        tileSize: 256 // average tile size in bytes
    };
    
    /**
     * Initialize Offline Maps
     */
    function initialize() {
        console.log('Initializing Offline Maps...');
        
        // Cache DOM elements
        cacheElements();
        
        // Setup event listeners
        setupEventListeners();
        
        // Initialize UI state
        updateUIState();
        
        // Check internet connection
        checkInternetConnection();
        
        // Load cache statistics
        loadCacheStats();
        
        console.log('Offline Maps initialized');
    }
    
    /**
     * Cache DOM Elements
     */
    function cacheElements() {
        elements = {
            // Panel elements
            offlineMapsPanel: document.getElementById('offline-maps-panel'),
            closeOfflinePanel: document.getElementById('close-offline-panel'),
            internetStatus: document.getElementById('internet-status'),
            
            // Coordinate inputs
            northLat: document.getElementById('north-lat'),
            southLat: document.getElementById('south-lat'),
            westLon: document.getElementById('west-lon'),
            eastLon: document.getElementById('east-lon'),
            useCurrentView: document.getElementById('use-current-view'),
            
            // Zoom inputs
            minZoom: document.getElementById('min-zoom'),
            maxZoom: document.getElementById('max-zoom'),
            
            // Map type checkboxes
            downloadStreet: document.getElementById('download-street'),
            downloadSatellite: document.getElementById('download-satellite'),
            
            // Download info and controls
            estimatedTiles: document.getElementById('estimated-tiles'),
            estimatedSize: document.getElementById('estimated-size'),
            downloadTilesBtn: document.getElementById('download-tiles-btn'),
            stopDownloadBtn: document.getElementById('stop-download-btn'),
            
            // Progress elements
            downloadProgress: document.getElementById('download-progress'),
            progressFill: elements.downloadProgress?.querySelector('.progress-fill'),
            progressText: document.getElementById('progress-text'),
            
            // Cache statistics
            streetCount: document.getElementById('street-count'),
            satelliteCount: document.getElementById('satellite-count'),
            totalCount: document.getElementById('total-count'),
            clearCacheBtn: document.getElementById('clear-cache-btn')
        };
        
        // Fix progress fill reference
        if (elements.downloadProgress) {
            elements.progressFill = elements.downloadProgress.querySelector('.progress-fill');
        }
        
        // Check for missing elements
        Object.entries(elements).forEach(([key, element]) => {
            if (!element && key !== 'progressFill') {
                console.warn(`Offline Maps: Element '${key}' not found`);
            }
        });
    }
    
    /**
     * Setup Event Listeners
     */
    function setupEventListeners() {
        // Close panel button
        if (elements.closeOfflinePanel) {
            elements.closeOfflinePanel.addEventListener('click', closePanel);
        }
        
        // Use current view button
        if (elements.useCurrentView) {
            elements.useCurrentView.addEventListener('click', useCurrentMapView);
        }
        
        // Download controls
        if (elements.downloadTilesBtn) {
            elements.downloadTilesBtn.addEventListener('click', startDownload);
        }
        
        if (elements.stopDownloadBtn) {
            elements.stopDownloadBtn.addEventListener('click', stopDownload);
        }
        
        // Clear cache button
        if (elements.clearCacheBtn) {
            elements.clearCacheBtn.addEventListener('click', clearCache);
        }
        
        // Input change listeners for estimation updates
        const estimationInputs = [
            elements.northLat, elements.southLat, elements.westLon, elements.eastLon,
            elements.minZoom, elements.maxZoom, elements.downloadStreet, elements.downloadSatellite
        ];
        
        estimationInputs.forEach(input => {
            if (input) {
                input.addEventListener('input', updateDownloadEstimation);
                input.addEventListener('change', updateDownloadEstimation);
            }
        });
        
        // Internet connection monitoring
        window.addEventListener('online', () => checkInternetConnection());
        window.addEventListener('offline', () => checkInternetConnection());
        
        // Periodic connection check
        setInterval(checkInternetConnection, 30000); // Every 30 seconds
    }
    
    /**
     * Close Offline Maps Panel
     */
    function closePanel() {
        if (elements.offlineMapsPanel) {
            elements.offlineMapsPanel.classList.remove('active');
        }
    }
    
    /**
     * Use Current Map View
     */
    function useCurrentMapView() {
        if (window.WebGCS?.modules?.MapController?.getMapBounds) {
            const bounds = window.WebGCS.modules.MapController.getMapBounds();
            
            if (bounds) {
                if (elements.northLat) elements.northLat.value = bounds.north.toFixed(6);
                if (elements.southLat) elements.southLat.value = bounds.south.toFixed(6);
                if (elements.westLon) elements.westLon.value = bounds.west.toFixed(6);
                if (elements.eastLon) elements.eastLon.value = bounds.east.toFixed(6);
                
                // Update zoom to current zoom level
                if (elements.maxZoom) elements.maxZoom.value = Math.min(bounds.zoom + 2, 20);
                
                updateDownloadEstimation();
                window.WebGCS?.showMessage('Download area set to current map view', 'info');
            }
        } else {
            window.WebGCS?.showMessage('Map controller not available', 'error');
        }
    }
    
    /**
     * Update Download Estimation
     */
    function updateDownloadEstimation() {
        const coords = getDownloadCoordinates();
        const zooms = getZoomRange();
        const mapTypes = getSelectedMapTypes();
        
        if (!coords || !zooms || mapTypes.length === 0) {
            updateEstimationDisplay(0, 0);
            return;
        }
        
        const tiles = estimateTileCount(coords, zooms, mapTypes);
        const sizeBytes = tiles * DOWNLOAD_CONFIG.tileSize;
        const sizeMB = sizeBytes / (1024 * 1024);
        
        updateEstimationDisplay(tiles, sizeMB);
    }
    
    /**
     * Estimate Tile Count
     */
    function estimateTileCount(coords, zooms, mapTypes) {
        let totalTiles = 0;
        
        for (let zoom = zooms.min; zoom <= zooms.max; zoom++) {
            const tilesForZoom = calculateTilesForZoom(coords, zoom);
            totalTiles += tilesForZoom * mapTypes.length;
        }
        
        return totalTiles;
    }
    
    /**
     * Calculate Tiles for Zoom Level
     */
    function calculateTilesForZoom(coords, zoom) {
        const tileSize = 256;
        const n = Math.pow(2, zoom);
        
        // Convert lat/lon to tile coordinates
        const minTileX = Math.floor((coords.west + 180) / 360 * n);
        const maxTileX = Math.floor((coords.east + 180) / 360 * n);
        const minTileY = Math.floor((1 - Math.log(Math.tan(coords.north * Math.PI / 180) + 1 / Math.cos(coords.north * Math.PI / 180)) / Math.PI) / 2 * n);
        const maxTileY = Math.floor((1 - Math.log(Math.tan(coords.south * Math.PI / 180) + 1 / Math.cos(coords.south * Math.PI / 180)) / Math.PI) / 2 * n);
        
        const tilesX = Math.abs(maxTileX - minTileX) + 1;
        const tilesY = Math.abs(maxTileY - minTileY) + 1;
        
        return tilesX * tilesY;
    }
    
    /**
     * Update Estimation Display
     */
    function updateEstimationDisplay(tiles, sizeMB) {
        if (elements.estimatedTiles) {
            elements.estimatedTiles.textContent = tiles.toLocaleString();
        }
        
        if (elements.estimatedSize) {
            elements.estimatedSize.textContent = sizeMB.toFixed(1);
        }
        
        // Enable/disable download button based on estimation
        if (elements.downloadTilesBtn) {
            elements.downloadTilesBtn.disabled = tiles === 0 || tiles > 50000; // Reasonable limit
        }
    }
    
    /**
     * Start Download Process
     */
    function startDownload() {
        const coords = getDownloadCoordinates();
        const zooms = getZoomRange();
        const mapTypes = getSelectedMapTypes();
        
        if (!coords || !zooms || mapTypes.length === 0) {
            window.WebGCS?.showMessage('Please configure download parameters', 'error');
            return;
        }
        
        // Estimate total tiles
        totalTiles = estimateTileCount(coords, zooms, mapTypes);
        
        if (totalTiles > 50000) {
            window.WebGCS?.showMessage('Download area too large. Please reduce area or zoom levels.', 'error');
            return;
        }
        
        if (totalTiles === 0) {
            window.WebGCS?.showMessage('No tiles to download', 'warning');
            return;
        }
        
        // Confirm download
        const message = `Download ${totalTiles.toLocaleString()} tiles?\nThis may take several minutes.`;
        
        if (window.WebGCS?.showConfirmation) {
            window.WebGCS.showConfirmation('Start Download', message, (confirmed) => {
                if (confirmed) {
                    executeDownload(coords, zooms, mapTypes);
                }
            });
        } else {
            if (confirm(message)) {
                executeDownload(coords, zooms, mapTypes);
            }
        }
    }
    
    /**
     * Execute Download
     */
    async function executeDownload(coords, zooms, mapTypes) {
        console.log('Starting tile download...', { coords, zooms, mapTypes, totalTiles });
        
        // Set download state
        isDownloading = true;
        downloadedTiles = 0;
        downloadAborted = false;
        downloadProgress = 0;
        
        // Update UI
        updateDownloadUI(true);
        updateProgressDisplay(0, 'Starting download...');
        
        try {
            // Generate tile list
            const tileList = generateTileList(coords, zooms, mapTypes);
            
            // Download tiles in batches
            await downloadTileBatches(tileList);
            
            if (!downloadAborted) {
                updateProgressDisplay(100, 'Download completed!');
                window.WebGCS?.showMessage(`Downloaded ${downloadedTiles} tiles successfully`, 'success');
                
                // Update cache statistics
                loadCacheStats();
            }
            
        } catch (error) {
            console.error('Download failed:', error);
            updateProgressDisplay(downloadProgress, `Download failed: ${error.message}`);
            window.WebGCS?.showMessage(`Download failed: ${error.message}`, 'error');
        } finally {
            // Reset download state
            isDownloading = false;
            updateDownloadUI(false);
        }
    }
    
    /**
     * Generate Tile List
     */
    function generateTileList(coords, zooms, mapTypes) {
        const tiles = [];
        
        mapTypes.forEach(mapType => {
            for (let zoom = zooms.min; zoom <= zooms.max; zoom++) {
                const tilesForZoom = generateTilesForZoom(coords, zoom, mapType);
                tiles.push(...tilesForZoom);
            }
        });
        
        return tiles;
    }
    
    /**
     * Generate Tiles for Zoom Level
     */
    function generateTilesForZoom(coords, zoom, mapType) {
        const tiles = [];
        const n = Math.pow(2, zoom);
        
        const minTileX = Math.floor((coords.west + 180) / 360 * n);
        const maxTileX = Math.floor((coords.east + 180) / 360 * n);
        const minTileY = Math.floor((1 - Math.log(Math.tan(coords.north * Math.PI / 180) + 1 / Math.cos(coords.north * Math.PI / 180)) / Math.PI) / 2 * n);
        const maxTileY = Math.floor((1 - Math.log(Math.tan(coords.south * Math.PI / 180) + 1 / Math.cos(coords.south * Math.PI / 180)) / Math.PI) / 2 * n);
        
        for (let x = minTileX; x <= maxTileX; x++) {
            for (let y = minTileY; y <= maxTileY; y++) {
                tiles.push({
                    x, y, z: zoom, mapType,
                    url: getTileUrl(x, y, zoom, mapType)
                });
            }
        }
        
        return tiles;
    }
    
    /**
     * Get Tile URL
     */
    function getTileUrl(x, y, z, mapType) {
        if (mapType === 'street') {
            return `https://tile.openstreetmap.org/${z}/${x}/${y}.png`;
        } else if (mapType === 'satellite') {
            return `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}`;
        }
        return null;
    }
    
    /**
     * Download Tile Batches
     */
    async function downloadTileBatches(tileList) {
        const batchSize = DOWNLOAD_CONFIG.maxConcurrentRequests;
        
        for (let i = 0; i < tileList.length; i += batchSize) {
            if (downloadAborted) break;
            
            const batch = tileList.slice(i, i + batchSize);
            const downloadPromises = batch.map(tile => downloadTile(tile));
            
            try {
                await Promise.allSettled(downloadPromises);
            } catch (error) {
                console.warn('Batch download error:', error);
            }
            
            // Update progress
            downloadProgress = Math.min((downloadedTiles / totalTiles) * 100, 100);
            updateProgressDisplay(downloadProgress, `Downloaded ${downloadedTiles}/${totalTiles} tiles`);
            
            // Add delay between batches
            if (!downloadAborted && i + batchSize < tileList.length) {
                await new Promise(resolve => setTimeout(resolve, DOWNLOAD_CONFIG.requestDelay));
            }
        }
    }
    
    /**
     * Download Single Tile
     */
    async function downloadTile(tile) {
        if (downloadAborted) return;
        
        let attempts = 0;
        while (attempts < DOWNLOAD_CONFIG.retryAttempts) {
            try {
                const response = await fetch(tile.url);
                if (response.ok) {
                    const blob = await response.blob();
                    
                    // Store tile in IndexedDB cache
                    await cacheTile(tile, blob);
                    
                    downloadedTiles++;
                    return;
                }
            } catch (error) {
                attempts++;
                if (attempts >= DOWNLOAD_CONFIG.retryAttempts) {
                    console.warn(`Failed to download tile after ${attempts} attempts:`, tile, error);
                }
            }
        }
    }
    
    /**
     * Cache Tile in IndexedDB
     */
    async function cacheTile(tile, blob) {
        // This would typically use IndexedDB
        // For now, we'll simulate caching
        const cacheKey = `tile_${tile.mapType}_${tile.z}_${tile.x}_${tile.y}`;
        
        try {
            // Simulate cache storage
            if (typeof(Storage) !== "undefined") {
                // Convert blob to base64 for localStorage simulation
                const base64 = await blobToBase64(blob);
                localStorage.setItem(cacheKey, JSON.stringify({
                    data: base64,
                    timestamp: Date.now(),
                    mapType: tile.mapType,
                    z: tile.z, x: tile.x, y: tile.y
                }));
            }
        } catch (error) {
            console.warn('Failed to cache tile:', cacheKey, error);
        }
    }
    
    /**
     * Convert Blob to Base64
     */
    function blobToBase64(blob) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });
    }
    
    /**
     * Stop Download
     */
    function stopDownload() {
        if (isDownloading) {
            downloadAborted = true;
            updateProgressDisplay(downloadProgress, 'Download stopped');
            window.WebGCS?.showMessage('Download stopped by user', 'info');
        }
    }
    
    /**
     * Clear Cache
     */
    function clearCache() {
        const message = 'This will delete all cached map tiles. Continue?';
        
        if (window.WebGCS?.showConfirmation) {
            window.WebGCS.showConfirmation('Clear Cache', message, (confirmed) => {
                if (confirmed) {
                    executeClearCache();
                }
            });
        } else {
            if (confirm(message)) {
                executeClearCache();
            }
        }
    }
    
    /**
     * Execute Clear Cache
     */
    function executeClearCache() {
        try {
            // Clear tile cache from localStorage (simulation)
            const keys = Object.keys(localStorage);
            let cleared = 0;
            
            keys.forEach(key => {
                if (key.startsWith('tile_')) {
                    localStorage.removeItem(key);
                    cleared++;
                }
            });
            
            // Reset cache stats
            cacheStats = { street: 0, satellite: 0, total: 0 };
            updateCacheStatsDisplay();
            
            window.WebGCS?.showMessage(`Cleared ${cleared} cached tiles`, 'success');
        } catch (error) {
            console.error('Cache clear failed:', error);
            window.WebGCS?.showMessage('Cache clear failed', 'error');
        }
    }
    
    /**
     * Load Cache Statistics
     */
    function loadCacheStats() {
        try {
            const keys = Object.keys(localStorage);
            cacheStats = { street: 0, satellite: 0, total: 0 };
            
            keys.forEach(key => {
                if (key.startsWith('tile_')) {
                    const data = JSON.parse(localStorage.getItem(key) || '{}');
                    if (data.mapType === 'street') {
                        cacheStats.street++;
                    } else if (data.mapType === 'satellite') {
                        cacheStats.satellite++;
                    }
                    cacheStats.total++;
                }
            });
            
            updateCacheStatsDisplay();
        } catch (error) {
            console.warn('Failed to load cache stats:', error);
        }
    }
    
    /**
     * Update Cache Statistics Display
     */
    function updateCacheStatsDisplay() {
        if (elements.streetCount) {
            elements.streetCount.textContent = cacheStats.street.toLocaleString();
        }
        if (elements.satelliteCount) {
            elements.satelliteCount.textContent = cacheStats.satellite.toLocaleString();
        }
        if (elements.totalCount) {
            elements.totalCount.textContent = cacheStats.total.toLocaleString();
        }
    }
    
    /**
     * Update Progress Display
     */
    function updateProgressDisplay(percent, text) {
        if (elements.progressFill) {
            elements.progressFill.style.width = `${percent}%`;
        }
        if (elements.progressText) {
            elements.progressText.textContent = text;
        }
    }
    
    /**
     * Update Download UI State
     */
    function updateDownloadUI(downloading) {
        if (elements.downloadTilesBtn) {
            elements.downloadTilesBtn.disabled = downloading;
            elements.downloadTilesBtn.textContent = downloading ? 'Downloading...' : 'Download Tiles';
        }
        
        if (elements.stopDownloadBtn) {
            elements.stopDownloadBtn.disabled = !downloading;
        }
    }
    
    /**
     * Update UI State
     */
    function updateUIState() {
        updateDownloadEstimation();
        updateDownloadUI(false);
    }
    
    /**
     * Check Internet Connection
     */
    function checkInternetConnection() {
        const online = navigator.onLine;
        
        if (elements.internetStatus) {
            const indicator = elements.internetStatus.querySelector('.status-indicator');
            const text = elements.internetStatus.querySelector('.status-text');
            
            if (online) {
                elements.internetStatus.className = 'internet-status online';
                if (indicator) indicator.textContent = '🌐';
                if (text) text.textContent = 'Online';
            } else {
                elements.internetStatus.className = 'internet-status offline';
                if (indicator) indicator.textContent = '📡';
                if (text) text.textContent = 'Offline';
            }
        }
    }
    
    /**
     * Helper Functions
     */
    function getDownloadCoordinates() {
        const north = parseFloat(elements.northLat?.value);
        const south = parseFloat(elements.southLat?.value);
        const west = parseFloat(elements.westLon?.value);
        const east = parseFloat(elements.eastLon?.value);
        
        if (isNaN(north) || isNaN(south) || isNaN(west) || isNaN(east)) {
            return null;
        }
        
        return { north, south, west, east };
    }
    
    function getZoomRange() {
        const min = parseInt(elements.minZoom?.value) || 2;
        const max = parseInt(elements.maxZoom?.value) || 16;
        
        if (min > max) return null;
        
        return { min, max };
    }
    
    function getSelectedMapTypes() {
        const types = [];
        if (elements.downloadStreet?.checked) types.push('street');
        if (elements.downloadSatellite?.checked) types.push('satellite');
        return types;
    }
    
    /**
     * Public API
     */
    return {
        initialize: initialize,
        
        // Update methods for external use
        updateCurrentMapView: (bounds, zoom) => {
            // This is called by MapController when map view changes
            // Could be used to auto-update download area
        },
        
        // State getters
        isDownloading: () => isDownloading,
        getCacheStats: () => ({ ...cacheStats }),
        
        // Module lifecycle callbacks
        onResize: () => {
            // Handle responsive layout changes if needed
        }
    };
})();