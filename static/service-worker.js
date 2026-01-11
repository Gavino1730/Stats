// Service Worker for offline support and caching
const CACHE_NAME = 'vc-stats-v1.1';  // Updated version for page state support
const urlsToCache = [
    '/',
    '/games',
    '/players', 
    '/trends',
    '/analysis',
    '/ai-insights',
    '/static/style.css',
    '/static/main.js',
    '/static/dashboard.js',
    '/static/games.js',
    '/static/players.js',
    '/static/trends.js',
    '/static/ai-insights.js',
];

// Install: cache static assets
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
            .then(() => self.skipWaiting())
    );
});

// Activate: clean up old caches
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => self.clients.claim())
    );
});

// Fetch: network first, fallback to cache
self.addEventListener('fetch', event => {
    // Skip API calls that need fresh data
    if (event.request.url.includes('/api/') && !event.request.url.includes('/api/season-analysis')) {
        return;
    }

    event.respondWith(
        caches.match(event.request)
            .then(response => {
                if (response) {
                    return response;
                }
                return fetch(event.request).then(response => {
                    // Cache successful responses
                    if (!response || response.status !== 200 || response.type === 'error') {
                        return response;
                    }
                    const responseToCache = response.clone();
                    caches.open(CACHE_NAME)
                        .then(cache => {
                            cache.put(event.request, responseToCache);
                        });
                    return response;
                });
            })
            .catch(() => {
                // Return offline page if needed
                if (event.request.destination === 'document') {
                    return caches.match('/');
                }
            })
    );
});
