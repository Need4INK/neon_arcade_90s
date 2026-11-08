// Neon Arcade service worker: keeps the page and its fonts on the phone so it opens offline.
// The page is fetched fresh when online (so updates show up), and the saved copy is used when offline.
var CACHE = 'neon-arcade-v2';
var SLOW_MS = 3000; // slow connection: show the saved page after this long

// Saved copies are kept under the address without ?query (links from apps add ?fbclid=… etc.),
// so there is one copy of the page however it was opened.
function key(u) { return u.split(/[?#]/)[0]; }

// Save the page while installing, so it opens offline even right after an update.
self.addEventListener('install', function (e) {
  self.skipWaiting();
  var page = self.registration.scope;
  e.waitUntil(fetch(page, { cache: 'no-cache' }).then(function (r) {
    if (r.ok) return caches.open(CACHE).then(function (c) { return c.put(page, r); });
  }).catch(function () {}));
});
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
      var same = u.indexOf(self.location.origin) === 0;
      return fetch(u, same ? { mode: 'same-origin', cache: 'no-cache' } : { mode: 'cors' }).then(function (r) {
        if (!r.ok) return;
        var copy = r.clone();
        var save = c.put(same ? key(u) : u, r);
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
  // The page is checked with the server every time (GitHub Pages lets browsers reuse it for 10 minutes,
  // which kept showing the old version after an update); unchanged pages come back as a quick 304.
  var nav = req.mode === 'navigate', stored = Promise.resolve();
  var fresh = fetch(req, nav ? { cache: 'no-cache' } : undefined).then(function (r) {
    if (r.ok) { var copy = r.clone(); stored = caches.open(CACHE).then(function (c) { return c.put(key(url), copy); }); }
    return r;
  });
  // Keep the worker running until the new copy is saved, even if the saved copy was shown first.
  e.waitUntil(fresh.then(function () { return stored; }, function () {}));
  if (!nav) {
    e.respondWith(fresh.catch(function () { return saved(req, false).then(function (r) { return r || Response.error(); }); }));
    return;
  }
  // Opening the page: if the server hasn't answered after 3 s (very slow connection), show the saved copy;
  // the new one is still saved and shows next time. With no saved copy, keep waiting for the server.
  e.respondWith(new Promise(function (resolve) {
    var done = false;
    function give(r) { if (r && !done) { done = true; resolve(r); } }
    var timer = setTimeout(function () { saved(req, true).then(give); }, SLOW_MS);
    fresh.then(function (r) { clearTimeout(timer); give(r); }, function () {
      clearTimeout(timer);
      saved(req, true).then(function (r) { give(r || Response.error()); });
    });
  }));
});

// The saved copy for a request (null if none).
function saved(req, nav) {
  return caches.open(CACHE).then(function (c) {
    return c.match(req, { ignoreSearch: true }).then(function (hit) {
      if (hit || !nav) return hit || null;
      // Opened at a slightly different address (e.g. the folder instead of the file): show the saved page.
      return c.match(self.registration.scope).then(function (home) {
        if (home) return home;
        return c.keys().then(function (keys) {
          var page = keys.filter(function (k) { return /\.html$|\/$/.test(k.url); })[0];
          return page ? c.match(page) : null;
        });
      });
    });
  });
}
