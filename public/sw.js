// Minimal service worker: enables "Add to Home Screen" / installability.
// Deliberately does NOT cache API calls (pantry/recipes need to stay fresh),
// it just needs to exist and respond to the install/fetch lifecycle.
self.addEventListener("install", (e) => {
  self.skipWaiting();
});

self.addEventListener("activate", (e) => {
  self.clients.claim();
});

self.addEventListener("fetch", (e) => {
  // Pass-through: always hit the network. No offline caching of API data,
  // since pantry/recipe state must stay accurate.
  return;
});
