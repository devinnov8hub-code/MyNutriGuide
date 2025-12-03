self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open('healthscanner-v1').then((cache) => {
      return cache.addAll([
        '/',
        '/static/css/styles.css',
        '/static/js/camera.js',
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
        'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
      ]);
    })
  );
});

self.addEventListener('fetch', (event) => {
  event.respondWith(
    caches.match(event.request).then((response) => {
      return response || fetch(event.request);
    })
  );
});
