/**
 * Offline Maps Module
 * 
 * This module provides functionality to download and cache map tiles
 * for offline use when internet connectivity is not available.
 */

class OfflineMapManager {
    constructor() {
        this.db = null;
        this.isInitialized = false;
        this.downloadQueue = [];
        this.isDownloading = false;
        this.downloadProgress = {
            total: 0,
            completed: 0,
            failed: 0
        };
        this.maxConcurrentDownloads = 6;
        this.activeDownloads = 0;
        this.callbacks = {};
        
        // Initialize IndexedDB
        this.initDB();
    }

    // Initialize IndexedDB for storing map tiles
    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('OfflineMapTiles', 1);
            
            request.onerror = () => {
                console.error('Failed to open IndexedDB');
                reject(request.error);
            };
            
            request.onsuccess = () => {
                this.db = request.result;
                this.isInitialized = true;
                console.log('OfflineMapManager: IndexedDB initialized');
                resolve();
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Create object stores for different tile sources
                if (!db.objectStoreNames.contains('osmTiles')) {
                    db.createObjectStore('osmTiles', { keyPath: 'key' });
                }
                
                if (!db.objectStoreNames.contains('satelliteTiles')) {
                    db.createObjectStore('satelliteTiles', { keyPath: 'key' });
                }
                
                // Store for metadata
                if (!db.objectStoreNames.contains('metadata')) {
                    db.createObjectStore('metadata', { keyPath: 'key' });
                }
            };
        });
    }

    // Generate tile key for storage
    getTileKey(source, z, x, y) {
        return `${source}_${z}_${x}_${y}`;
    }

    // Calculate tiles needed for a given bounding box and zoom range
    calculateTilesForArea(bounds, minZoom, maxZoom) {
        const tiles = [];
        
        for (let z = minZoom; z <= maxZoom; z++) {
            const nwTile = this.latLngToTile(bounds.getNorth(), bounds.getWest(), z);
            const seTile = this.latLngToTile(bounds.getSouth(), bounds.getEast(), z);
            
            for (let x = nwTile.x; x <= seTile.x; x++) {
                for (let y = nwTile.y; y <= seTile.y; y++) {
                    tiles.push({ z, x, y });
                }
            }
        }
        
        return tiles;
    }

    // Convert lat/lng to tile coordinates
    latLngToTile(lat, lng, zoom) {
        const x = Math.floor((lng + 180) / 360 * Math.pow(2, zoom));
        const y = Math.floor((1 - Math.log(Math.tan(lat * Math.PI / 180) + 1 / Math.cos(lat * Math.PI / 180)) / Math.PI) / 2 * Math.pow(2, zoom));
        return { x, y };
    }

    // Download and cache tiles for a specific area
    async downloadTilesForArea(bounds, options = {}) {
        if (!this.isInitialized) {
            await this.initDB();
        }

        const {
            minZoom = 2,
            maxZoom = 16,
            sources = ['osm', 'satellite'],
            onProgress = null,
            onComplete = null,
            onError = null
        } = options;

        // Calculate all tiles needed
        const tiles = this.calculateTilesForArea(bounds, minZoom, maxZoom);
        const totalTiles = tiles.length * sources.length;

        this.downloadProgress = {
            total: totalTiles,
            completed: 0,
            failed: 0
        };

        console.log(`Starting download of ${totalTiles} tiles for offline use`);

        // Add tiles to download queue
        for (const source of sources) {
            for (const tile of tiles) {
                this.downloadQueue.push({ source, ...tile });
            }
        }

        // Start downloading
        this.isDownloading = true;
        this.callbacks.onProgress = onProgress;
        this.callbacks.onComplete = onComplete;
        this.callbacks.onError = onError;

        // Process download queue
        for (let i = 0; i < this.maxConcurrentDownloads; i++) {
            this.processDownloadQueue();
        }
    }

    // Process the download queue
    async processDownloadQueue() {
        while (this.downloadQueue.length > 0 && this.isDownloading) {
            const tile = this.downloadQueue.shift();
            this.activeDownloads++;

            try {
                await this.downloadTile(tile.source, tile.z, tile.x, tile.y);
                this.downloadProgress.completed++;
            } catch (error) {
                console.error(`Failed to download tile ${tile.source}_${tile.z}_${tile.x}_${tile.y}:`, error);
                this.downloadProgress.failed++;
            }

            this.activeDownloads--;

            // Notify progress
            if (this.callbacks.onProgress) {
                this.callbacks.onProgress(this.downloadProgress);
            }

            // Check if download is complete
            if (this.downloadProgress.completed + this.downloadProgress.failed >= this.downloadProgress.total) {
                this.isDownloading = false;
                if (this.callbacks.onComplete) {
                    this.callbacks.onComplete(this.downloadProgress);
                }
                break;
            }
        }
    }

    // Download a single tile
    async downloadTile(source, z, x, y) {
        const key = this.getTileKey(source, z, x, y);
        
        // Check if tile already exists
        const existingTile = await this.getTileFromCache(source, z, x, y);
        if (existingTile) {
            return; // Already cached
        }

        const url = this.getTileUrl(source, z, x, y);
        
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const blob = await response.blob();
        const arrayBuffer = await blob.arrayBuffer();

        // Store in IndexedDB
        const transaction = this.db.transaction([source === 'osm' ? 'osmTiles' : 'satelliteTiles'], 'readwrite');
        const store = transaction.objectStore(source === 'osm' ? 'osmTiles' : 'satelliteTiles');
        
        await new Promise((resolve, reject) => {
            const request = store.put({
                key: key,
                data: arrayBuffer,
                timestamp: Date.now(),
                z: z,
                x: x,
                y: y
            });
            
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    // Get tile URL based on source
    getTileUrl(source, z, x, y) {
        if (source === 'osm') {
            const subdomains = ['a', 'b', 'c'];
            const subdomain = subdomains[Math.floor(Math.random() * subdomains.length)];
            return `https://${subdomain}.tile.openstreetmap.org/${z}/${x}/${y}.png`;
        } else if (source === 'satellite') {
            return `https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/${z}/${y}/${x}`;
        }
        throw new Error(`Unknown tile source: ${source}`);
    }

    // Get tile from cache
    async getTileFromCache(source, z, x, y) {
        if (!this.isInitialized) {
            return null;
        }

        const key = this.getTileKey(source, z, x, y);
        const storeName = source === 'osm' ? 'osmTiles' : 'satelliteTiles';
        
        return new Promise((resolve) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(key);
            
            request.onsuccess = () => {
                resolve(request.result);
            };
            
            request.onerror = () => {
                resolve(null);
            };
        });
    }

    // Create offline tile layer for Leaflet
    createOfflineTileLayer(source, options = {}) {
        const self = this;
        
        const OfflineTileLayer = L.TileLayer.extend({
            createTile: function(coords, done) {
                const tile = document.createElement('img');
                
                // Try to load from cache first
                self.getTileFromCache(source, coords.z, coords.x, coords.y)
                    .then(cachedTile => {
                        if (cachedTile) {
                            // Load from cache
                            const blob = new Blob([cachedTile.data]);
                            const url = URL.createObjectURL(blob);
                            tile.onload = () => {
                                URL.revokeObjectURL(url);
                                done(null, tile);
                            };
                            tile.onerror = () => {
                                URL.revokeObjectURL(url);
                                done(new Error('Failed to load cached tile'), tile);
                            };
                            tile.src = url;
                        } else {
                            // Fallback to online if not cached
                            const url = self.getTileUrl(source, coords.z, coords.x, coords.y);
                            tile.onload = () => done(null, tile);
                            tile.onerror = () => done(new Error('Failed to load online tile'), tile);
                            tile.src = url;
                        }
                    })
                    .catch(() => {
                        // Fallback to online if cache fails
                        const url = self.getTileUrl(source, coords.z, coords.x, coords.y);
                        tile.onload = () => done(null, tile);
                        tile.onerror = () => done(new Error('Failed to load online tile'), tile);
                        tile.src = url;
                    });
                
                return tile;
            }
        });
        
        return new OfflineTileLayer(null, options);
    }

    // Get cache statistics
    async getCacheStats() {
        if (!this.isInitialized) {
            return { osmTiles: 0, satelliteTiles: 0, totalSize: 0 };
        }

        const stats = { osmTiles: 0, satelliteTiles: 0, totalSize: 0 };
        
        // Count OSM tiles
        await new Promise((resolve) => {
            const transaction = this.db.transaction(['osmTiles'], 'readonly');
            const store = transaction.objectStore('osmTiles');
            const request = store.count();
            
            request.onsuccess = () => {
                stats.osmTiles = request.result;
                resolve();
            };
            
            request.onerror = () => resolve();
        });

        // Count satellite tiles
        await new Promise((resolve) => {
            const transaction = this.db.transaction(['satelliteTiles'], 'readonly');
            const store = transaction.objectStore('satelliteTiles');
            const request = store.count();
            
            request.onsuccess = () => {
                stats.satelliteTiles = request.result;
                resolve();
            };
            
            request.onerror = () => resolve();
        });

        return stats;
    }

    // Clear cache
    async clearCache() {
        if (!this.isInitialized) {
            return;
        }

        const storeNames = ['osmTiles', 'satelliteTiles'];
        
        for (const storeName of storeNames) {
            await new Promise((resolve) => {
                const transaction = this.db.transaction([storeName], 'readwrite');
                const store = transaction.objectStore(storeName);
                const request = store.clear();
                
                request.onsuccess = () => resolve();
                request.onerror = () => resolve();
            });
        }
    }

    // Stop current download
    stopDownload() {
        this.isDownloading = false;
        this.downloadQueue = [];
    }
}

// Create global instance
window.offlineMapManager = new OfflineMapManager(); 