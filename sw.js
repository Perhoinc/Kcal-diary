// Bump VERSION whenever any file below changes, so installed copies fetch the new files.
const VERSION = "v31";
const CACHE = "kcal-diary-" + VERSION;
const FILES = [
  "./",
  "index.html",
  "manifest.webmanifest",
  "icons/apple-touch-icon.png",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "icons/icon-maskable-512.png",
  "fonts/archivo-wght.woff2",
  "fonts/archivo-narrow-500.woff2",
  "fonts/archivo-narrow-600.woff2",
  "fonts/archivo-narrow-700.woff2"
];

self.addEventListener("install", e => {
  e.waitUntil(
    caches.open(CACHE)
      .then(c => c.addAll(FILES.map(f => new Request(f, { cache: "reload" }))))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener("message", e => {
  if (e.data === "skipWaiting") self.skipWaiting();
});

self.addEventListener("activate", e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k.startsWith("kcal-diary-") && k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("fetch", e => {
  const req = e.request;
  if (req.method !== "GET" || new URL(req.url).origin !== location.origin) return;
  // The food databases are updated monthly on their own, so they (and the suggested matches) are fetched fresh when online and kept for offline use.
  if (/\/(foods|products-se|matches)\.json$/.test(new URL(req.url).pathname)) {
    e.respondWith(caches.open(CACHE).then(async c => {
      try { const r = await fetch(req, { cache: "no-cache" }); if (r.ok) c.put(req, r.clone()); return r; }
      catch (_) { return (await c.match(req, { ignoreSearch: true })) || new Response("{}", { status: 503 }); }
    }));
    return;
  }
  e.respondWith(
    caches.open(CACHE).then(async c => {
      const hit = await c.match(req, { ignoreSearch: true });
      if (hit) return hit;
      if (req.mode === "navigate") { const home = await c.match("index.html"); if (home) return home; }
      try { return await fetch(req); } catch (_) { return new Response("Offline", { status: 503 }); }
    })
  );
});
