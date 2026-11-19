// Never cache authenticated APIs or snapshots. Only a neutral offline explanation.
const CACHE='living-town-shell-v1';
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['./offline.html'])).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(names=>Promise.all(names.filter(n=>n.startsWith('living-town-shell-')&&n!==CACHE).map(n=>caches.delete(n)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
 if(e.request.mode!=='navigate'||!e.request.url.startsWith(self.registration.scope))return;
 e.respondWith(fetch(e.request).catch(()=>caches.match(new URL('./offline.html',self.registration.scope).href)));
});
