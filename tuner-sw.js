---
permalink: /tuner/sw.js
---
const CACHE = 'tuner-v1';
const ASSETS = ['/tuner/', '/tuner/manifest.webmanifest', '/tuner/icon-192.png', '/tuner/icon-512.png'];

self.addEventListener('install', e => {
    e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
    self.skipWaiting();
});

self.addEventListener('activate', e => {
    e.waitUntil(caches.keys()
        .then(keys => Promise.all(keys.filter(k => k.startsWith('tuner-') && k !== CACHE).map(k => caches.delete(k))))
        .then(() => self.clients.claim()));
});

// network first so updates land; cached copy when offline
self.addEventListener('fetch', e => {
    e.respondWith(
        fetch(e.request).then(res => {
            const copy = res.clone();
            caches.open(CACHE).then(c => c.put(e.request, copy));
            return res;
        }).catch(() => caches.match(e.request, { ignoreSearch: true }))
    );
});
