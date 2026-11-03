"""Record the independent Atlas service; do not re-enable portal integration."""
from pathlib import Path
wiki=Path('/home/ata/llm-cluster-wiki')
node=wiki/'nodes/farabi.md'
text=node.read_text()
heading='## Farabi Atlas (2026-11-01)'
section="""## Farabi Atlas (2026-11-01)

- Kaynak: `/home/ata/farabi/tahtaatlasfarabi`; TypeScript/Vite + Python/FastAPI.
- **Bağımsız servis:** `farabi-atlas.service`, port **8099**, `http://farabi.local:8099/kure/` veya `http://192.168.23.20:8099/kure/`.
- Giriş gerekmez; ortak tahta etkinliği. Sonuç DB: proje `var/atlas.db`; okul DB/kimlik/XP sisteminden bağımsızdır.
- `smual.app`, :9090 ve mevcut cloudflared/cf-edge-relay tüneli Atlas için kullanılmaz.
- Önceki portal entegrasyonu kullanıcının isteğiyle tamamen geri alındı. Dört portal dosyası Atlas öncesi yedeklerine byte-for-byte döndürüldü. Önceden var olan V38 değişikliği ve güncel okul verisi korundu; boş Atlas tablosu kaldırıldı, şema yeniden V38. SQLite bütünlüğü ok.
- 81 il, 973 ilçe (2021), dünya ve fizikî coğrafya verileri yerel GeoJSON/PMTiles. FULL/LITE WebGL ve SAFE SVG; iki yerel küre seçeneği. Çalışma sırasında haricî harita API/CDN isteği yok.
- 17 veri/oyun/API testi ve beş oyun turu, GPU’suz/WebGL küre, byte-range, SAFE fallback test edildi. Gerçek i3 tahta FPS/IR dokunmatik ölçümü bekliyor.
"""
if heading in text:text=text[:text.index(heading)]+section
else:text+='\n'+section
node.write_text(text)
services=wiki/'topology/services.md';lines=services.read_text().splitlines()
for i,line in enumerate(lines):
 if '| `farabi-okul` |' in line and '; Farabi Atlas' in line:lines[i]=line.split('; Farabi Atlas')[0]+' |'
if not any('| `farabi-atlas` |' in l for l in lines):
 at=next(i for i,l in enumerate(lines) if '| `farabi-okul` |' in l);lines.insert(at+1,'| `farabi-atlas` | 8099 | Bağımsız yerel Atlas harita/küre ve beş oyun; `/kure/`, girişsiz tahta modu |')
services.write_text('\n'.join(lines)+'\n')
projects=wiki/'topology/python-projects.md';lines=projects.read_text().splitlines()
for i,l in enumerate(lines):
 if '**Farabi Atlas**' in l:lines[i]='| **Farabi Atlas** | `~/farabi/tahtaatlasfarabi` | Farabi | `farabi-atlas` (bağımsız) | 8099 `/kure/` | Yerel harita/küre ve 5 oyun; okul DB’sinden ayrı |'
projects.write_text('\n'.join(lines)+'\n')
log=wiki/'logs/2026-11-01-farabi-atlas.md';text=log.read_text();marker='## Düzeltme: bağımsız port'
if marker not in text:log.write_text(text+'\n'+marker+'\n\nKullanıcı smual.app üzerinde değişiklik yapılmamasını ve başka port kullanılmasını istedi. Portal entegrasyonu tamamen geri alındı: app.py, db.py, scripts/geri_al.py ve öğretmen ana şablonu Atlas öncesi yedeklerine byte-for-byte döndü; mevcut V38 korundu. Güncel okul veritabanı önce yedeklendi; yalnız boş Atlas tablosu kaldırıldı, user_version=38 ve integrity_check=ok. Atlas artık farabi-atlas.service ile :8099/kure/ yolunda, kendi var/atlas.db dosyasıyla girişsiz çalışır. smual.app giriş sayfası 200; mevcut portal ve tünel servisleri aktif.\n')
print('Wiki, bağımsız 8099 servisi ve portal geri alma bilgisiyle düzeltildi.')
