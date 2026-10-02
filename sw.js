/*
 * ぽよんダンジョンを 電波が なくても 遊べるように する 係（Service Worker）
 * 2026-10-02 つかい手「オフラインで 遊べるようにして」
 *
 * やること
 *  1. 入れた すぐあとに、ゲーム本体（index.html など）を しまう
 *  2. そのあと 裏で 絵を ぜんぶ（assets-list.json の 291件・約40MB）しまう
 *  3. 2回目からは しまってある ものを 先に 返す ＝ 電波が なくても 動く
 *
 * ⚠️ 広告（AdSense）など よその 家の ものは しまわない。
 *    オフラインでは 広告だけ 出ないが、ゲームは ふつうに 遊べる
 */
const CACHE = "poyon-v1";
const CORE = [
  "./",
  "./index.html",
  "./manifest.json",
  "./icon-192.png",
  "./icon-512.png",
  "./assets-list.json",
];

self.addEventListener("install", (e) => {
  e.waitUntil(
    caches.open(CACHE).then((c) => c.addAll(CORE)).then(() => self.skipWaiting())
  );
});

self.addEventListener("activate", (e) => {
  e.waitUntil(
    (async () => {
      // 古い しまい場は かたづける
      const keys = await caches.keys();
      await Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)));
      await self.clients.claim();
      prefetchAssets();            // 裏で 絵を ためる（待たない）
    })()
  );
});

/** 絵を 少しずつ しまう。失敗しても 止まらない */
async function prefetchAssets() {
  try {
    const c = await caches.open(CACHE);
    const list = await (await fetch("./assets-list.json", { cache: "no-store" })).json();
    for (const path of list) {
      const url = new URL(path, self.registration.scope).href;
      if (await c.match(url)) continue;
      try {
        const res = await fetch(url, { cache: "no-store" });
        if (res && res.ok) await c.put(url, res.clone());
      } catch (err) { /* 1枚くらい 落としても 気にしない */ }
    }
    const all = await c.keys();
    broadcast({ type: "poyon-cache", done: all.length, total: list.length + CORE.length });
  } catch (err) { /* 一覧が 読めない時は あきらめる（遊んだ ぶんは たまる） */ }
}

async function broadcast(msg) {
  const cs = await self.clients.matchAll();
  cs.forEach((x) => x.postMessage(msg));
}

self.addEventListener("fetch", (e) => {
  const req = e.request;
  if (req.method !== "GET") return;
  const url = new URL(req.url);
  if (url.origin !== self.location.origin) return;     // よその家の ものは さわらない

  // 画面を ひらく お願いは、電波が なければ しまってある ゲーム本体を 返す
  if (req.mode === "navigate") {
    e.respondWith(
      fetch(req).catch(() => caches.match("./index.html", { ignoreSearch: true }))
    );
    return;
  }

  e.respondWith(
    (async () => {
      const hit = await caches.match(req, { ignoreSearch: true });
      if (hit) return hit;
      try {
        const res = await fetch(req);
        if (res && res.ok) {
          const c = await caches.open(CACHE);
          c.put(req, res.clone());          // 遊んだ ぶんは その場で しまう
        }
        return res;
      } catch (err) {
        return hit || Response.error();
      }
    })()
  );
});
