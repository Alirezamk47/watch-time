const CACHE='watch-time-shell-v1.49';
const SHELL=['./','./index.html','./manifest.json'];
self.addEventListener('install',event=>{self.skipWaiting();event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(['./index.html']).catch(()=>{})))});
self.addEventListener('activate',event=>{event.waitUntil((async()=>{for(const key of await caches.keys()){if(key.startsWith('watch-time-shell-')&&key!==CACHE)await caches.delete(key)}await self.clients.claim()})())});
self.addEventListener('fetch',event=>{
 const request=event.request;
 if(request.method!=='GET'||new URL(request.url).origin!==self.location.origin)return;
 const url=new URL(request.url);
 if(request.mode==='navigate'||url.pathname.endsWith('/index.html')){
  event.respondWith((async()=>{try{const response=await fetch(request,{cache:'no-store'});if(response.ok){const cache=await caches.open(CACHE);cache.put('./index.html',response.clone())}return response}catch(e){return (await caches.match('./index.html'))||Response.error()}})());return;
 }
 if(url.pathname.endsWith('/version.json')||url.pathname.endsWith('/sw.js'))return;
 if(/\.(?:png|jpg|jpeg|webp|svg|ico|css|js)$/i.test(url.pathname)){
  event.respondWith((async()=>{const cached=await caches.match(request);if(cached)return cached;const response=await fetch(request);if(response.ok){const cache=await caches.open(CACHE);cache.put(request,response.clone())}return response})());
 }
});
