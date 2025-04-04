// 캐시 이름 설정
const CACHE_NAME = 'youtube-downloader-cache-v1';
const urlsToCache = [
  '/',
  '/static/manifest.json',
  '/static/images/icons/icon-192x192.png',
  '/static/images/icons/icon-512x512.png'
];

// 서비스 워커 설치 시
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('캐시 열림');
        return cache.addAll(urlsToCache);
      })
  );
});

// 서비스 워커 활성화 시
self.addEventListener('activate', function(event) {
  const cacheWhitelist = [CACHE_NAME];
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheWhitelist.indexOf(cacheName) === -1) {
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// 페이지 요청 처리
self.addEventListener('fetch', function(event) {
  event.respondWith(
    // 네트워크 요청 먼저 시도하고 실패하면 캐시에서 가져옴
    fetch(event.request).catch(function() {
      return caches.match(event.request);
    })
  );
});