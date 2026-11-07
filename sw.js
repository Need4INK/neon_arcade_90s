// Neon Arcade service worker: keeps the page and its fonts on the phone so it opens offline.
// The page is fetched fresh when online (so updates show up), and the saved copy is used when offline.
var CACHE = 'neon-arcade-v1';

self.addEventListener('install', function () { self.skipWaiting(); });
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (keys) {
    return Promise.all(keys.filter(function (k) { return k !== CACHE; }).map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

// The page sends its own address and font stylesheets on first load, so they are saved straight away.
self.addEventListener('message', function (e) {
  var urls = (e.data && e.data.cache) || [];
  e.waitUntil(caches.open(CACHE).then(function (c) {
    return Promise.all(urls.map(function (u) {
      return fetch(u, { mode: u.indexOf(self.location.origin) === 0 ? 'same-origin' : 'cors' }).then(function (r) {
        if (!r.ok) return;
        var copy = r.clone();
        var save = c.put(u, r);
        // Also save the font files the stylesheet points to.
        if (/fonts\.googleapis\.com/.test(u)) {
          return copy.text().then(function (css) {
            var files = (css.match(/url\(([^)]+)\)/g) || []).map(function (m) { return m.slice(4, -1).replace(/["']/g, ''); });
            return Promise.all([save].concat(files.map(function (f) {
              return fetch(f, { mode: 'cors' }).then(function (fr) { if (fr.ok) return c.put(f, fr); }).catch(function () {});
            })));
          });
        }
        return save;
      }).catch(function () {});
    }));
  }));
});

function isFont(url) { return /fonts\.(googleapis|gstatic)\.com/.test(url); }

self.addEventListener('fetch', function (e) {
  var req = e.request, url = req.url;
  if (req.method !== 'GET') return;
  var same = url.indexOf(self.location.origin) === 0;
  if (!same && !isFont(url)) return;

  // Fonts never change: use the saved copy, fetch and save it the first time.
  if (isFont(url)) {
    e.respondWith(caches.open(CACHE).then(function (c) {
      return c.match(url).then(function (hit) {
        return hit || fetch(req).then(function (r) { if (r.ok || r.type === 'opaque') c.put(url, r.clone()); return r; });
      });
    }));
    return;
  }

  // Page and other files: network first, saved copy when offline.
  e.respondWith(fetch(req).then(function (r) {
    if (r.ok) { var copy = r.clone(); caches.open(CACHE).then(function (c) { c.put(req.url.split('#')[0], copy); }); }
    return r;
  }).catch(function () {
    return caches.open(CACHE).then(function (c) {
      return c.match(req, { ignoreSearch: true }).then(function (hit) {
        if (hit) return hit;
        // Opened offline at a slightly different address (e.g. the folder instead of the file): show the saved page.
        if (req.mode === 'navigate') return c.keys().then(function (keys) {
          var page = keys.filter(function (k) { return /\.html$|\/$/.test(k.url.split('?')[0]); })[0];
          return page ? c.match(page) : Response.error();
        });
        return Response.error();
      });
    });
  }));
});
