# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Farabi Atlas (`tahtaatlasfarabi/`)
Okul yerel ağında çalışan Türkiye/dünya harita laboratuvarı + 5 sınıf oyunu (Türkiye'yi Bul, Komşunu Bul,
Bölge Avcısı, Dünya Coğrafya Avı, Tarih Rotası). Çalışma anında internet/CDN/haricî harita API'si YOK.
Ortak kurallar üst dizindeki `../CLAUDE.md`'de. Ayrıntılı ürün planı `atlasplan.md` (tarihsel; çelişkide kod ve README esas).

## Canlı durum
- `farabi-atlas.service` (birim kopyası `deploy/farabi-atlas.service`) bu dizinden koşar: `0.0.0.0:8099`,
  `ATLAS_STANDALONE=1`, DB `var/atlas.db`. Adres `http://farabi.local:8099/kure/`. Giriş yok; ortak tahta etkinliği.
- Portal (`okul/`, :9090, smual.app) Atlas'ı yalnız iframe ile gösterir (2026-11-04): `/ogretmen/atlas` sayfası, `okul/rotalar/atlas.py`
  `/kure/*` ve `/api/atlas/*`'ı öğretmen girişiyle :8099'a proxy'ler. Bu yüzden frontend mutlak `/kure/` ve `/api/atlas` yollarını korumalı.
- Bunun dışında okul portalından TAMAMEN bağımsız. Eski tam portal entegrasyonu kullanıcı isteğiyle geri alındı:
  `backend.server.install`, `scripts/integrate_portal.py` eski araçlardır, yeniden UYGULAMA. Okul DB/öğrenci/XP'ye dokunulmaz.
  `scripts/detach_portal.py` (geri alma) ve `scripts/update_wiki.py` (wiki'ye yazar) tek seferlik, çalıştırılmış betiklerdir.
  README'deki "Dijital Okul entegrasyonu" cümlesi bu yüzden eskidir (README yalnız Atakan isterse güncellenir).
- `docs/` = GitHub Pages tanıtım sayfası (statik, uygulamadan bağımsız; build'e girmez).
- Kendi git deposu: `atakanunver/farabi-atlas` (PUBLIC, dal `main`); üst `farabi` deposunda izlenmez.
  Public olduğu için okul verisi, wiki içeriği, `var/*.db` commit'lenmez.
- Üretime alma: ön yüz değişikliği → `npm run build` (servis `dist/`'i sunar, restart gerekmez);
  backend veya `public/data` değişikliği → build + `sudo systemctl restart farabi-atlas`.

## Komutlar
```sh
npm run build                 # tsc --noEmit + vite build → dist/ (base '/kure/')
npm test                      # .venv/bin/python -m pytest tests/test_atlas.py -q
.venv/bin/python -m pytest tests/test_atlas.py::test_catalog -q   # tek test
npm run test:browser          # tests/browser.mjs (Playwright + /usr/bin/chromium-browser)
node tests/webgl.mjs          # ayrıca zoom.mjs, visual.mjs; ekran görüntüleri test-results/
npm run data                  # data/source → public/data (build_data.py + build_tiles.py)
npm run dev                   # Vite :5173, /api/atlas → 127.0.0.1:8099 proxy
```
- ⚠️ Tarayıcı testleri sabit `http://127.0.0.1:8099`'a gider = CANLI servis; oturumları `var/atlas.db`'ye yazar.
  Önizleme (`var/preview.db`, "Demo sınıfı") için servisi geçici durdurup
  `.venv/bin/uvicorn backend.server:standalone --factory --host 127.0.0.1 --port 8099` (ATLAS_STANDALONE'suz) kullan, ya da önce sor.
- Tarayıcı testleri 127.0.0.1 dışı tüm istekleri engeller ve dış origin isteği varsa düşer (offline garantisi).

## Mimari
- **Veri hattı:** `data/source/*.json` (Natural Earth, alpers il, geoBoundaries 973 ilçe) → `scripts/build_data.py`
  → `public/data/catalog.json` (tüm nesneler; id `TR-06` gibi, `neighbors`, `region`, `parentId`, `countryId`),
  `questions.json` (Tarih Rotası soruları), `manifest.json` (lisans/sayım/SHA-256) → `build_tiles.py` → `*.pmtiles`.
  Vite `public/` → `dist/data/`. İl komşulukları ham sınır çizgisi/örtüşmesinden; köşe teması komşu sayılmaz.
- **Backend** (`backend/`, FastAPI + SQLite, tek tablo `atlas_session`, durum JSON olarak `state` sütununda):
  - `atlas.py` = oyun kuralları. `catalog.json`/`questions.json`'u import anında yükler (veri değişince restart).
    `make_questions` soru üretir (istenenden az varsa tekrar yok, mevcut sayı kullanılır); `act` cevap/pas/duraklat
    işler, puanı SUNUCU hesaplar (ilk doğru 100, ikinci 50, + süre ≤50, + seri ≤50; iki yanlış/süre/pas soruyu bitirir).
    `public()` istemciye `targetIds`'i göstermez. `revision` ile idempotent eylem.
  - `server.py::make_router(identity, connect, classes, ...)` kimlik/DB/sınıf yetkisini dışarıdan alır;
    `standalone()` sabit kimlik ve süreç başına CSRF token'ı verir. Yazmalar form + `csrf` alanı ile.
- **Frontend** (`src/`, TypeScript, framework yok): `main.ts` tüm arayüz/oyun akışı; `map/api.ts` `FarabiMap`
  arayüzü ve `MapBase`. Render seviyeleri: `SAFE` = `svgAdapter.ts` (D3 orthographic küre, GPU'suz, açılış varsayılanı),
  `FULL`/`LITE` = `maplibreAdapter.ts` (dinamik import, PMTiles; hata olursa SAFE'e düşer). `capabilities.ts` WebGL/FPS ölçer.
  `game/backendAdapter.ts` `/api/atlas` istemcisi; aktif oturum id'si `localStorage['atlas-session']`.
- Hedef cihaz: i3 / 3,8 GB RAM tahta, IR dokunmatik. Ağırlık eklerken SAFE yolunu koru.

## Kod stili
Mevcut kod yoğun/sıkıştırılmış yazılmış (Python'da 1 boşluk girinti, tek satırda çoklu ifade; TS'de uzun tek satırlar).
Dokunduğun yerde bu stile uy; dosyayı yeniden biçimlendirme. Arayüz metinleri Türkçe.
