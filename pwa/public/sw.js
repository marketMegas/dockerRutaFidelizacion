const CACHE = 'fid-glp-v8'
const SHELL = ['/', '/index.html', '/manifest.webmanifest', '/icon.png']

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()))
})

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  )
})

self.addEventListener('fetch', (e) => {
  const req = e.request
  const url = new URL(req.url)
  if (req.method !== 'GET' || url.origin !== self.location.origin) return

  if (url.pathname.startsWith('/fid-api/')) {
    e.respondWith(fetch(req).catch(() => caches.match(req)))
    return
  }

  e.respondWith(
    fetch(req)
      .then((resp) => {
        const copy = resp.clone()
        caches.open(CACHE).then((c) => c.put(req, copy))
        return resp
      })
      .catch(() => caches.match(req).then((hit) => hit || caches.match('/index.html')))
  )
})
