# Farabi Atlas Harita Laboratuvarı+ Oyun — Yeni MVP Planı

## 1. Amaç

Farabi akıllı tahtalarında, zayıf donanım koşullarında dahi çalışan; tamamen yerel ağdan sunulan; internet kesilse de kullanılabilen; coğrafya ve tarih derslerinde doğrudan oyunlaştırılmış etkinlikler sunan bir **Harita Laboratuvarı + Harita Oyun Motoru** geliştirilecektir.
FARABI ATLAS ISIMLI PROJE
Bu sürüm sadece harita görüntüleyen bir `/kure` sayfası olmayacaktır. Aynı altyapı üzerinde çalışan ilk oyunlar da teslim edilecektir. Mevcut Farabi/DijitalOkul oyun altyapısı, puan/oturum/kullanıcı veya skor servisleri varsa yeniden yazılmayacak; uygun adapter üzerinden kullanılacaktır.

Ana hedef:

- Tahtada link açıldığı anda çalışması
- İnternetsiz kullanılabilmesi
- 2. nesil i3 + 8 GB RAM + eski Intel HD grafik donanımında güvenilir çalışması
- Harita motorunun oyun kodundan ayrılması
- İlk sürümde Türkiye **ve dünya coğrafyası** odaklı oynanabilir içerik sunması
- Dünya ülkeleri, başkentler, önemli nehirler, dağlar, göller, boğazlar, çöller ve deniz/okyanus sorularını desteklemesi
- Daha sonra tarih, YKS ve öğretmen kontrollü oyunlara genişleyebilmesi

---

## 2. Temel Mimari Kararı

MVP'de **globe zorunlu değildir**. Sistem açılışta cihaz yeteneğini ölçer ve uygun render modunu otomatik seçer.

### Render Seviyeleri

#### FULL
WebGL2 kullanılabilir ve performans yeterli.

- MapLibre
- 2D Mercator varsayılan
- İsteğe bağlı globe
- Yumuşak `flyTo`
- Vurgu animasyonları
- Daha yoğun etiket
- Daha yüksek pixelRatio

#### LITE
WebGL2 var ancak GPU zayıf.

- MapLibre
- Sadece 2D Mercator
- pitch = 0
- bearing = 0
- antialias kapalı
- düşük pixelRatio
- sade stil
- düşük etiket yoğunluğu
- minimum animasyon

#### SAFE
WebGL2 yok, MapLibre başlatılamıyor veya render testi başarısız.

- SVG/Canvas tabanlı sade harita
- Türkiye / il / ilçe poligonları
- sade dünya ülkeleri haritası ve seçilmiş dünya coğrafya hedefleri
- Tıklama ve dokunmatik seçim
- Oyun motoru çalışmaya devam eder
- Oyun API sözleşmesi değişmez

**Kural:** Oyun kodu hangi render motorunun çalıştığını bilmez.

---

## 3. Sistem Mimarisi

```text
farabi.local
│
├─ /kure/                         Vite + TypeScript uygulaması
│   ├─ Harita Laboratuvarı
│   ├─ Harita Oyunları
│   └─ Demo / test ekranı
│
├─ /tiles/
│   ├─ turkey.pmtiles             Türkiye odaklı sade taban harita
│   ├─ game-turkey.pmtiles        il, ilçe, bölge, nehir, göl, dağ vb.
│   ├─ world-lite.pmtiles         düşük zoom sade dünya taban haritası
│   └─ game-world.pmtiles         ülke, başkent, önemli nehir/dağ/göl/boğaz/çöl vb.
│
├─ /kure/assets/
│   ├─ fonts/
│   ├─ sprites/
│   └─ sounds/
│
└─ mevcut oyun backend'i
    ├─ kullanıcı / rol
    ├─ oyun oturumu
    ├─ puan
    ├─ skor / liderlik
    └─ kazanım / soru bağlantıları
```

MVP'de uydu raster paketi bulunmayacaktır. Uydu, terrain ve yüksek maliyetli görsel katmanlar **2. faz** kapsamındadır.

---

## 4. Repo Yapısı

Önerilen repo:

```text
~/okul-kure/
│
├─ kure/
│   ├─ src/
│   │   ├─ app/
│   │   │   ├─ router.ts
│   │   │   └─ bootstrap.ts
│   │   │
│   │   ├─ map/
│   │   │   ├─ api.ts
│   │   │   ├─ capabilities.ts
│   │   │   ├─ maplibreAdapter.ts
│   │   │   ├─ svgAdapter.ts
│   │   │   ├─ style.ts
│   │   │   └─ hitTest.ts
│   │   │
│   │   ├─ game/
│   │   │   ├─ engine.ts
│   │   │   ├─ session.ts
│   │   │   ├─ scoring.ts
│   │   │   ├─ timer.ts
│   │   │   ├─ questionProvider.ts
│   │   │   ├─ backendAdapter.ts
│   │   │   └─ types.ts
│   │   │
│   │   ├─ games/
│   │   │   ├─ turkiyeyiBul/
│   │   │   ├─ komsunuBul/
│   │   │   ├─ bolgeAvcisi/
│   │   │   ├─ dunyaCografyaAvi/
│   │   │   └─ tarihRotasi/
│   │   │
│   │   ├─ ui/
│   │   │   ├─ hud.ts
│   │   │   ├─ scoreboard.ts
│   │   │   ├─ resultCard.ts
│   │   │   └─ teacherControls.ts
│   │   │
│   │   └─ demo/
│   │
│   └─ public/
│
├─ data/
│   ├─ source/
│   ├─ processed/
│   └─ questions/
│
├─ scripts/
│   ├─ build-data.sh
│   ├─ validate-data.py
│   └─ deploy.sh
│
├─ deploy/
│   └─ nginx.conf
│
└─ README.md
```

---

## 5. Harita API Sözleşmesi

Oyunlar hiçbir zaman doğrudan MapLibre çağrısı yapmayacaktır.

### `map/api.ts`

Örnek sözleşme:

```ts
interface FarabiMap {
  ready(): Promise<void>;
  getRenderMode(): 'FULL' | 'LITE' | 'SAFE';

  focus(id: string, opts?: FocusOptions): Promise<void>;
  highlight(id: string, opts?: HighlightOptions): void;
  clearHighlights(): void;

  enableSelection(opts?: SelectionOptions): void;
  disableSelection(): void;
  onFeatureClick(cb: (feature: MapFeature) => void): () => void;

  getFeature(id: string): MapFeature | null;
  featureAt(x: number, y: number): MapFeature | null;

  setLayers(layers: LayerName[]): void;
  showLabels(enabled: boolean): void;
  resetView(): void;
}
```

Oyun kodunda aşağıdakiler yasaktır:

```ts
map.getSource(...)
map.addLayer(...)
map.queryRenderedFeatures(...)
```

Bunun yerine:

```ts
farabiMap.highlight('TR-18')
farabiMap.focus('TR-18')
farabiMap.enableSelection()
```

kullanılır.

Bu karar sayesinde MapLibre sorun çıkarırsa `MapLibreAdapter` yerine `SvgAdapter` kullanılabilir.

---

## 6. Harita Verisi

İlk MVP yalnızca gerçekten gerekli veriyi içerir; ancak kapsam **Türkiye ile sınırlı değildir**. Mevcut ve gelecek soru havuzlarında dünya üzerindeki önemli doğal/coğrafi unsurlar sorulabildiği için dünya verisi ilk teslimin parçasıdır.

### Türkiye veri katmanları

- 81 il
- ilçeler
- coğrafi bölgeler
- komşuluk ilişkileri
- büyük akarsular
- büyük göller
- önemli dağ / zirve noktaları
- önemli boğazlar
- seçilmiş tarihi konumlar

Her özellik en az:

```json
{
  "id": "TR-18",
  "type": "il",
  "name_tr": "Çankırı"
}
```

alanlarını taşır.

İlçeler için sabit ID standardı oluşturulur.

### Dünya veri katmanları — MVP

- dünya ülkeleri
- başkentler
- önemli nehirler
- önemli dağlar / zirveler
- büyük göller
- önemli boğazlar ve kanallar
- başlıca çöller
- okyanuslar ve önemli denizler
- seçilmiş yarımada / ada / takımada gibi YKS düzeyi hedefler

Dünya verisi tam GIS ayrıntısında olmayacaktır. Oyunlarda sorulması muhtemel, pedagojik değeri yüksek ve dokunmatik ekranda seçilebilir **küratörlü bir çekirdek veri seti** hazırlanacaktır. Örnek hedef büyüklüğü:

- 190+ ülke
- 150+ başkent
- 40–60 önemli nehir
- 40–60 önemli dağ / zirve
- 30–50 önemli göl
- 20–30 boğaz / kanal
- 15–25 çöl
- okyanuslar ve başlıca denizler

Her dünya özelliği de sabit kimlik taşır:

```json
{
  "id": "RIVER-NILE",
  "type": "river",
  "name_tr": "Nil Nehri",
  "aliases": ["Nil", "Nile"],
  "scope": "world"
}
```

### İkinci faz

- dünya tarih noktaları ve ayrıntılı tarih rotaları
- daha yüksek zoom dünya verisi
- uydu görünümü

---

## 7. Dokunmatik Tasarım

Akıllı tahtadaki IR dokunmatik çerçeveler için küçük hedeflere güvenilmeyecektir.

### Alan nesneleri

İl / ilçe gibi poligonlarda gerçek geometri kullanılır.

### Çizgi ve nokta nesneleri

Nehir, sınır, rota, zirve gibi nesnelerde görünmez hitbox katmanı oluşturulur.

Örnek:

```text
river-visible   → gerçek çizgi
river-hitbox    → opacity: 0, geniş tıklama çizgisi
```

### Çakışma çözümü

Bir dokunuş birden fazla hedefe denk gelirse:

1. gerçek polygon containment
2. hedef önceliği
3. dokunma noktasına mesafe
4. ekrandaki görünürlük

sırası uygulanır.

Amaç: sınır çizgisinde yanlış ilin seçilmesini azaltmak.

---

## 8. Harita Oyun Motoru

MVP'ye çalışan oyun altyapısı dahil edilecektir.

### Game Engine görevleri

- oyun başlatma
- soru seçme
- tur yönetimi
- süre yönetimi
- doğru / yanlış kontrolü
- puan hesaplama
- combo
- streak
- seviye / zorluk
- sonuç ekranı
- mevcut oyun backend'ine skor iletme

### Temel oyun sözleşmesi

```ts
interface MapGame {
  id: string;
  title: string;
  minPlayers: number;
  maxPlayers: number;

  start(ctx: GameContext): Promise<void>;
  onMapSelection(feature: MapFeature): Promise<void>;
  nextRound(): Promise<void>;
  finish(): Promise<GameResult>;
}
```

---

## 9. Mevcut Oyun Altyapısıyla Entegrasyon

Projede mevcut başka oyunların altyapısı bulunduğu için yeni sistem kendi kullanıcı/puan/oturum sistemini sıfırdan yazmayacaktır.

İlk geliştirme adımında mevcut altyapı keşfedilir:

- mevcut kullanıcı kimliği nasıl alınıyor?
- öğrenci / öğretmen rolü nasıl belirleniyor?
- oyun oturumu nasıl başlıyor?
- skor hangi endpoint'e gönderiliyor?
- liderlik tablosu var mı?
- rozet / seviye / XP sistemi var mı?
- soru havuzu veya kazanım ilişkisi mevcut mu?

Bunların üzerine tek bir adapter yazılır:

```text
ExistingGameBackendAdapter
```

Harita oyunları doğrudan backend detayını bilmez.

```text
Map Game
   ↓
Game Engine
   ↓
backendAdapter
   ↓
Mevcut Farabi / DijitalOkul oyun servisi
```

Var olan altyapıda eksik olan küçük alanlar varsa sadece uyumluluk katmanı eklenir.

---

## 9.1 Soru Havuzu ve Coğrafi Hedef Eşleme

Dünya sorularında serbest metinden haritada hedef tahmini yapılmayacaktır. Her soru önceden tanımlı `targetId` ile gerçek harita nesnesine bağlanır. Böylece “Nil”, “Nile”, “Nil Nehri” gibi ad farkları render/cevap kontrolünü bozmaz.

Örnek:

```json
{
  "id": "geo-world-river-001",
  "mode": "world-river",
  "prompt": "Nil Nehri'ni haritada göster.",
  "targetIds": ["RIVER-NILE"],
  "difficulty": 1,
  "grade": [9, 10, 11, 12],
  "tags": ["dunya", "akarsu"]
}
```

Mevcut başka oyunların soru/puan altyapısı varsa bu format ona adapter ile dönüştürülür; ikinci bir paralel soru sistemi oluşturulmaz.

Dünya coğrafyası için başlangıç soru paketi veri setiyle birlikte oluşturulur. Amaç yalnızca haritada nesneyi göstermek değil, aynı veriyle farklı soru biçimleri üretmektir:

- adı verileni bul
- ipucundan bul
- kıta/bölge ilişkisine göre bul
- iki unsur arasında seçim yap
- sırayla birden fazla hedef seç

---

## 10. MVP ile Birlikte Yapılacak Oyunlar

### Oyun 1 — Türkiye'yi Bul

Farabi soru sorar:

> Çankırı'yı haritada bul.

Öğrenci dokunur.

Doğru seçim:

- yeşil vurgu
- +100 puan
- hızlı cevap bonusu
- sonraki soru

Yanlış seçim:

- kısa kırmızı vurgu
- doğru cevabı hemen göstermeme
- ikinci deneme

10 soruluk tur.

#### Zorluk

**Kolay:** il adı verilir.

**Orta:** ipucu verilir.

> İç Anadolu'da yer alır, Kastamonu ve Ankara ile komşudur.

**Zor:** bilgi / kazanım sorusu.

> Ilgaz Dağı'nın bir bölümünün bulunduğu ili seç.

---

### Oyun 2 — Komşunu Bul

Bir il vurgulanır.

Örnek:

> Çankırı'nın komşularından birini seç.

Öğrenci geçerli komşulardan birine dokunur.

Zincir modu:

```text
Çankırı → Kastamonu → Sinop → Samsun
```

Her doğru cevap combo puanını artırır.

---

### Oyun 3 — Bölge Avcısı

Örnek görev:

> İç Anadolu Bölgesi'nde bulunan 5 ili seç.

Öğrenci art arda illeri işaretler.

Oyun;

- coğrafi bölge
- kıyı / iç kesim
- komşuluk
- bölge karşılaştırma

konularında kullanılabilir.

---

### Oyun 4 — Dünya Coğrafya Avı

Dünya üzerindeki önemli coğrafi unsurlar doğrudan sorulabilir.

Örnekler:

> Nil Nehri'ni haritada göster.

> Amazon Nehri hangi bölgede? Haritada seç.

> Himalayalar'ı göster.

> Everest'in bulunduğu dağ kuşağını seç.

> Baykal Gölü'nü bul.

> Cebelitarık Boğazı'nı göster.

> Sahra Çölü'nü seç.

> Japonya'yı ve ardından başkenti Tokyo'yu bul.

Soru tipleri:

- ülke bul
- başkent bul
- nehir bul
- dağ / zirve bul
- göl bul
- boğaz / kanal bul
- çöl bul
- deniz / okyanus bul
- ipucundan coğrafi unsur bul

Çizgi nesneleri (nehirler) ve küçük nokta nesneleri (zirveler/başkentler) görünmez geniş hitbox ile seçilir. Geniş coğrafi alanlarda doğru cevap, gerçek geometri veya tanımlanmış cevap bölgesi üzerinden doğrulanır.

### Oyun 5 — Tarih Rotası

Harita motorunun tarih dersinde kullanılmasını sağlar.

Örnek sorular:

> Mustafa Kemal'in 19 Mayıs 1919'da ulaştığı şehri seç.

> Sakarya Meydan Muharebesi'nin gerçekleştiği bölgeyi seç.

> Büyük Taarruz ile ilişkili konumu göster.

İlk sürümde 10–20 doğrulanmış tarih noktası yeterlidir.

---

## 11. İkinci Aşama Oyunları

**Başkent Avı, Dünya Ülkeleri, Nehir Nerede? ve Dağ/Göl Avı artık MVP içindeki `Dünya Coğrafya Avı` oyununun modlarıdır.** MVP doğrulandıktan sonra ayrıca:

- Türkiye'nin Komşuları
- Tarihi Sefer Rotası
- YKS Coğrafya Challenge
- sınıf turnuvası
- takım oyunu
- iki öğrencili hızlı dokunma yarışı

eklenebilir.

---

## 12. İki Oyunculu Akıllı Tahta Modu

Mevcut oyun altyapısı uygunsa ikinci faza beklemeden MVP'ye eklenebilir.

Ekran:

```text
┌──────────────────────────────────────────────┐
│ Oyuncu A: 400                  Oyuncu B: 350 │
│                                              │
│               HARİTA                         │
│                                              │
│        “Konya'yı ilk kim bulacak?”           │
└──────────────────────────────────────────────┘
```

İlk doğru dokunuş puan kazanır.

Dokunmatik donanım aynı anda iki bağımsız touch noktası sağlamıyorsa tur bazlı veya sırayla oynanan mod kullanılır.

---

## 13. Öğretmen Modu

MVP'de basit öğretmen kontrol paneli bulunacaktır.

Öğretmen:

- oyunu seçer
- soru sayısını belirler
- zorluk seçer
- süreyi açar/kapatır
- il / ilçe / bölge / dünya ülkeleri / nehir / dağ / göl / boğaz / çöl içerik grubunu seçer
- oyunu başlatır
- sonuçları görür

İleri aşamada:

- sınıf seçme
- kazanım seçme
- öğrenci grubu seçme
- özel soru listesi hazırlama

mevcut DijitalOkul/Farabi altyapısıyla birleştirilebilir.

---

## 14. Performans Bütçesi

Tahta hedefi:

- açılışta cihaz testi: < 2 saniye
- oyun ekranı hazır: mümkünse < 4 saniye
- LITE mod hedefi: 25–30 FPS ve üzeri
- SAFE mod: akıcı dokunmatik tepki
- hiçbir oyun için 3D zorunlu değil

### Performans kuralları

- varsayılan Mercator
- terrain yok
- uydu yok
- gereksiz POI yok
- bina 3D yok
- blur / heavy shadow yok
- yoğun animasyon yok
- görünmeyen katmanlar render edilmez
- mümkün olduğunca az draw call
- düşük pixelRatio fallback

---

## 15. Nginx ve Offline Dağıtım

```text
http://farabi.local/kure
```

üzerinden açılır.

Nginx:

- `.pmtiles` için HTTP byte-range
- cache headers
- gzip/brotli uygun statik dosyalarda
- tek origin
- CDN yok
- internet zorunluluğu yok

Tahtaya kurulum yapılmaz. Tarayıcı yeterlidir.

---

## 16. Uygulama Adımları

| # | İş | Doğrulama |
|---|---|---|
| 0 | Mevcut oyun altyapısını ve backend endpointlerini keşfet | kullanıcı/puan/oturum entegrasyon şeması çıkar |
| 1 | Tahtada WebGL2 + MapLibre testi, FULL/LITE/SAFE capability sistemi | her test cihazı doğru moda düşüyor |
| 2 | Türkiye veri hattı ve `game-turkey.pmtiles` | 81 il, ilçe, bölge, sabit ID, Türkçe ad |
| 3 | Dünya veri hattı, `world-lite.pmtiles` + `game-world.pmtiles` | ülke/başkent + küratörlü nehir/dağ/göl/boğaz/çöl verileri doğrulanıyor |
| 4 | Map API + MapLibreAdapter + SvgAdapter | aynı API ile iki motor çalışıyor |
| 5 | dokunmatik hit-test sistemi | il/sınır/nehir/zirve testleri başarılı |
| 6 | Game Engine + mevcut backend adapter | skor mevcut sisteme yazılıyor |
| 7 | Türkiye'yi Bul | 10 soruluk tam tur çalışıyor |
| 8 | Komşunu Bul | komşuluk verisi doğrulanıyor |
| 9 | Bölge Avcısı | çoklu seçim ve combo çalışıyor |
| 10 | Dünya Coğrafya Avı | en az ülke, başkent, nehir, dağ, göl, boğaz ve çöl modları çalışıyor |
| 11 | Tarih Rotası | en az 10 doğrulanmış tarih sorusu |
| 12 | öğretmen kontrol ekranı | oyun/zorluk/soru sayısı seçilebiliyor |
| 13 | performans optimizasyonu | eski i3 tahtada kullanılabilir FPS |
| 14 | offline deploy + README | internet kesikken tüm MVP çalışıyor |

---

## 17. Testler

### Veri testleri

- 81 il mevcut
- ID'ler benzersiz
- `name_tr` boş değil
- komşuluk çiftleri tutarlı
- il → bölge ilişkisi doğru
- ilçe → il ilişkisi doğru
- dünya ülke/başkent eşleşmeleri doğru
- seçilmiş nehir/dağ/göl/boğaz/çöl hedeflerinde `id`, `name_tr`, `type`, `scope` eksiksiz
- aynı isimli/alternatif isimli dünya hedeflerinde `aliases` doğrulanmış

### Harita testleri

- FULL başlatma
- LITE başlatma
- SAFE fallback
- zoom / focus
- highlight
- dokunmatik seçim
- sınır çizgisi seçimi

### Oyun testleri

- doğru cevap
- yanlış cevap
- ikinci deneme
- zaman aşımı
- skor
- combo
- tur bitişi
- backend skor gönderimi

### Offline test

WAN bağlantısı kesilir.

Aşağıdakilerin tamamı çalışmaya devam etmelidir:

- `/kure`
- harita
- oyun
- ses dosyaları
- font
- sprite
- soru setleri

---

## 18. MVP Teslim Kriteri

Proje tamamlanmış sayılmak için:

1. `http://farabi.local/kure` tahtada açılmalı.
2. İnternet kapalıyken çalışmalı.
3. MapLibre başarısız olursa SAFE harita açılmalı.
4. Türkiye'nin 81 ili seçilebilir olmalı.
5. En az 5 oyun oynanabilir olmalı.
6. Türkiye'yi Bul oyunu baştan sona hatasız tamamlanmalı.
7. Dünya Coğrafya Avı içinde ülke, başkent, nehir, dağ, göl, boğaz ve çöl soruları oynanabilmeli.
8. Puan ve sonuç mevcut oyun altyapısına aktarılmalı veya adapter üzerinden hazır olmalı.
9. Öğretmen oyun ve coğrafya kategorisi seçebilmeli.
10. Dokunmatik seçimler eski tahtada kullanılabilir olmalı.
11. Harita motoru ile oyun motoru bağımsız olmalı.

---

## 19. MVP Dışında Tutulanlar

İlk teslimde yapılmayacak:

- yüksek çözünürlüklü uydu
- terrain
- 3D bina
- zorunlu globe
- dünya çapında yüksek zoom ayrıntılı veri
- gerçek zamanlı hava
- Cesium
- canlı bulut / rüzgâr
- ağır WebGL efektleri

Bunlar temel sistem stabil olduktan sonra modül olarak eklenebilir.

---

## 20. Son Hedef

Bu proje yalnızca "harita açan bir Farabi modülü" olmayacaktır.

Hedef ürün:

# Farabi Harita Laboratuvarı

Altında ortak bir motor:

```text
Harita Motoru
    +
Oyun Motoru
    +
Mevcut Farabi/DijitalOkul Oyun Altyapısı
    +
Ders İçeriği
```

Bunun üzerine zamanla:

```text
Coğrafya
Tarih
YKS
Sınıf Yarışmaları
Takım Oyunları
Dünya Haritası
Uydu / Globe
```

eklenebilir.

Öncelik sırası nettir:

**Önce eski tahtada sorunsuz çalışan 2D Türkiye + sade dünya haritası + oynanabilir Türkiye ve dünya coğrafya oyunları. Sonra görsel zenginlik.**
