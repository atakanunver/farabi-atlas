# Farabi Atlas

Okulun yerel ağında çalışan Türkiye/dünya harita laboratuvarı ve beş sınıf oyunu.
Çalışma sırasında haricî harita API’si, CDN, çevrimiçi font veya internet bağlantısı kullanmaz.
Tahta veya Wi-Fi istemcisinin Farabi sunucusuna erişmesi gerekir.

## Teknoloji

- Arayüz ve oyun istemcisi: TypeScript, Vite.
- Harita: açılışta doğrudan SVG + D3 küre; MapLibre FULL/LITE motoru ayrıca korunur.
- Küre: WebGL destekli veya GPU gerektirmeyen SVG orthographic görünüm.
- Sunucu: Python/FastAPI, kendi SQLite veritabanı. Dijital Okul’dan bağımsızdır.
- Veri hazırlama: Python/Shapely, MVT ve PMTiles.

## Yerel geliştirme

```sh
npm ci
python3 -m venv .venv
.venv/bin/pip install -r requirements-build.txt
npm run build
.venv/bin/uvicorn backend.server:standalone --factory --host 127.0.0.1 --port 8099
```

`http://127.0.0.1:8099/kure/` geliştirme önizlemesidir. Açıkça işaretli demo sınıfı
kullanır ve sonuçları `var/preview.db` içine yazar. Bu demo sunucusunu okul ağına açmayın;
gerçek kullanım için öğretmen oturumunu doğrulayan Dijital Okul entegrasyonunu kullanın.

Hızlı geliştirmede API sunucusu çalışırken `npm run dev`; Vite `/api/atlas` isteklerini
8099’a yönlendirir. Sadece geliştirme ve ilk veri indirme için internet gerekir.

## Oyunlar

Türkiye’yi Bul, Komşunu Bul, Bölge Avcısı, Dünya Coğrafya Avı ve Tarih Rotası.
Öğretmen sınıf, kategori, soru sayısı, süre ve zorluk seçer. Uygun soru sayısı talep edilenden
azsa aynı turda tekrar yerine mevcut soru sayısı kullanılır.

İlk doğruya 100, ikinci denemede doğruya 50 puan; kalan süreye göre en fazla 50 ve
seri doğruya en fazla 50 ek puan verilir. Çoklu seçim tamamlanınca soru puanı hesaplanır.
İki yanlış, süre aşımı veya pas geçişi soruyu bitirir. XP ve mevcut okul ödülleri değişmez.

## Veri ve yeniden üretim

Kaynaklar `data/source/`, çalışma paketi `public/data/` altında bulunur.
`manifest.json` kaynak lisanslarını, nesne sayılarını ve kaynak SHA-256 değerlerini içerir.

```sh
npm run data
npm run build
```

Natural Earth verileri kamu malıdır. Türkiye il verisi Apache-2.0, geoBoundaries Türkiye
ADM2 kaynağı ODbL-1.0 lisanslıdır (2021 sınırları, 973 ilçe); kaynaklar arayüzde de belirtilir.
İlçeler kaynak `shapeID` üzerinden sabit kimlik alır, il ilişkisi temsil noktasıyla eşlenir.
Güncel idarî değişiklikler için yeni kaynak sürümü ayrıca incelenmelidir.

Doğal unsurların geometrileri eğitim ölçeğinde genelleştirilmiştir. Boğaz ve kanallar
çizilmiş hayalî sınırlar yerine seçilebilir merkez noktalarıyla gösterilir. Küçük ülkeler ve
yoğun hedefler yakınlaştırılarak seçilir. İl komşulukları sadeleştirilmemiş sınırların
ortak çizgi/örtüşmelerinden hesaplanır; yalnız köşe teması komşuluk sayılmaz.

## Bağımsız yerel servis

Üretim adresi: **http://192.168.23.20:8099/kure/** veya `http://farabi.local:8099/kure/`.
Atlas, `farabi-atlas.service` ile ayrı süreçte çalışır. Okulun `smual.app` portalını,
9090 portunu ve internet tünelini kullanmaz. Giriş ekranına yönlendirme yoktur.

```sh
ATLAS_STANDALONE=1 ATLAS_DB=var/atlas.db .venv/bin/uvicorn backend.server:standalone --factory --host 0.0.0.0 --port 8099
```

Kalıcı servis tanımı `deploy/farabi-atlas.service` içindedir. Sonuçlar yalnızca
`var/atlas.db` içine yazılır; okulun öğrenci, öğretmen, XP ve ödül kayıtlarına erişilmez.
Bu sürüm ortak tahta etkinliğidir; bireysel hesap veya okul portalı oturumu gerektirmez.

Önceki portal entegrasyonu kullanıcı talebiyle tamamen geri alındı. Portalın dört dosyası
Atlas öncesi yedekleriyle birebir geri yüklendi; mevcut V38 değişikliği ve güncel okul
verileri korundu. Boş Atlas tablosu kaldırılıp şema sürümü 38’e döndürüldü.
`scripts/integrate_portal.py` ve `backend.server.install` eski entegrasyon araçlarıdır;
aktif kurulumda kullanılmaz ve yeniden uygulanmamalıdır.

API: `GET /api/atlas/context`, `GET/POST /api/atlas/sessions`,
`GET /api/atlas/sessions/{id}`, `POST /api/atlas/sessions/{id}/action`.
Yazma istekleri sunucunun verdiği CSRF alanıyla form olarak gönderilir.
İstemci ham puan göndermez; sunucu seçimlerden hesaplar.

## Doğrulama

```sh
npm run build
npm test
npm run test:browser
node tests/webgl.mjs
```

Tarayıcı testleri 8099’daki önizlemeyi ve kurulu Chromium’u kullanır; dış originlere
istekleri engeller. Beş tam oyun turu, GPU’suz küre, 1440/768/390 piksel ekranlar,
WebGL yolu, byte-range ve SAFE geçişi kontrol edilir. Ekran görüntüleri `test-results/`.

Gerçek i3/3,8 GB tahta üzerinde açılış, FPS ve IR dokunmatik ölçümleri ayrıca yapılmalıdır.
İnternetin kesilmesi desteklenir; Farabi veya yerel ağın tamamen kesilmesinde yeni oyun
başlatılamaz. Sonuçlar yerel sunucuda tutulur; bağımsız tarayıcı/PWA dağıtımı yoktur.
Uydu, terrain, 3D binalar ve iki oyunculu yarış bu sürümün dışındadır.
