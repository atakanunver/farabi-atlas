"""Reproducible local catalog; never downloads data at runtime."""
import hashlib
import json
import re
import unicodedata
from pathlib import Path
from collections import Counter
from shapely.geometry import shape, mapping, Polygon, MultiPolygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'data/source'
OUT = ROOT / 'public/data'
OUT.mkdir(parents=True, exist_ok=True)

REGIONS = {
 'Marmara': [10,11,16,17,22,34,39,41,54,59,77],
 'Ege': [3,9,20,35,43,45,48,64],
 'Akdeniz': [1,7,15,31,32,33,46,80],
 'İç Anadolu': [6,18,26,38,40,42,50,51,58,66,68,70,71],
 'Karadeniz': [5,8,14,19,28,29,37,52,53,55,57,60,61,67,69,74,78,81],
 'Doğu Anadolu': [4,12,13,23,24,25,30,36,44,49,62,65,75,76],
 'Güneydoğu Anadolu': [2,21,27,47,56,63,72,73,79],
}

def read(name):
 return json.loads((SOURCE / f'{name}.json').read_text())['features']

def slug(name):
 return re.sub(r'[^A-Z0-9]+', '-', unicodedata.normalize('NFKD',name).encode('ascii','ignore').decode().upper()).strip('-')

def geometry(g, tolerance=.015):
 g = g.simplify(tolerance, preserve_topology=True)
 if isinstance(g, Polygon): g = orient(g, sign=-1)
 elif isinstance(g, MultiPolygon): g=MultiPolygon([orient(p,sign=-1) for p in g.geoms])
 return json.loads(json.dumps(mapping(g)))

features=[]
def add(id, name, kind, scope, g, **extra):
 if any(x['id']==id for x in features): return
 g=shape(g) if isinstance(g,dict) else g
 if not g.is_valid: g=g.buffer(0)
 point=g.representative_point()
 features.append({'type':'Feature','id':id,'properties':{'id':id,'name_tr':name,'type':kind,'scope':scope,'center':[round(point.x,4),round(point.y,4)],**extra},'geometry':geometry(g)})

provinces=read('turkey')
for f in provinces:
 p=f['properties']; number=p['number']; region=next(n for n,ids in REGIONS.items() if number in ids)
 add(f'TR-{number:02}',p['name'],'province','turkey',f['geometry'],region=region,aliases=[p['name']])
originals={f'TR-{f["properties"]["number"]:02}':shape(f['geometry']) for f in provinces}
for f in features[:]:
 g=originals[f['id']]; f['properties']['neighbors']=[id for id,other in originals.items() if id!=f['id'] and g.intersection(other).length>.005]
if (SOURCE/'districts.json').exists():
 for f in read('districts'):
  p=f['properties']; g=shape(f['geometry']); point=g.representative_point()
  containing=[id for id,province in originals.items() if province.covers(point)]
  parent=containing[0] if containing else min(originals,key=lambda id:originals[id].distance(point))
  add('DISTRICT-'+p['shapeID'],p['shapeName'],'district','turkey',g,parentId=parent,region=next(x['properties']['region'] for x in features if x['id']==parent),aliases=[p['shapeName']])

for f in read('world'):
 p=f['properties']; code=p['ADM0_A3']; name=p.get('NAME_TR') or p['NAME']
 add('COUNTRY-'+code,name,'country','world',f['geometry'],iso=code,continent=p.get('CONTINENT'),aliases=[p['NAME'],p['ADMIN']])
for f in read('places'):
 p=f['properties']
 if p.get('adm0cap')==1:
  add('CAPITAL-'+str(p['ne_id']),p['name'],'capital','world',f['geometry'],countryId='COUNTRY-'+p['adm0_a3'],aliases=[p['name']])

river_names={'Nile':'Nil Nehri','Amazonas':'Amazon Nehri','Amazon':'Amazon Nehri','Danube':'Tuna Nehri','Volga':'Volga Nehri','Yangtze':'Yangtze Nehri','Ganges':'Ganj Nehri','Indus':'İndus Nehri','Al Furat':'Fırat Nehri','Dicle':'Dicle Nehri','Tigris':'Dicle Nehri','Kizilirmak':'Kızılırmak','Sakarya':'Sakarya','Yesilirmak':'Yeşilırmak'}
groups={}
for f in read('rivers'):
 p=f['properties']; n=p.get('name')
 if n: groups.setdefault(n,[]).append(f)
chosen=sorted(groups, key=lambda n:(n not in river_names,min(x['properties']['scalerank'] for x in groups[n]),n))[:60]
for n in chosen:
 add('RIVER-'+slug(n),river_names.get(n,n),'river','world',unary_union([shape(f['geometry']) for f in groups[n]]),aliases=[n])
for f in sorted([f for f in read('lakes') if f['properties'].get('name')],key=lambda f:f['properties']['scalerank'])[:50]:
 p=f['properties']; add('LAKE-'+slug(p['name']),p.get('name_tr') or p['name'],'lake','world',f['geometry'],aliases=[p['name']])
for cls,kind,limit in [('Range/mtn','mountain',60),('Desert','desert',25),('Island','island',20),('Peninsula','peninsula',10)]:
 for f in sorted([f for f in read('regions') if f['properties']['FEATURECLA']==cls],key=lambda f:f['properties'].get('SCALERANK') or 0)[:limit]:
  p=f['properties']; add(kind.upper()+'-'+str(p['NE_ID']),p.get('NAME_TR') or p['NAME'],kind,'world',f['geometry'],aliases=[p['NAME']])
if (SOURCE/'peaks.json').exists():
 peaks=[f for f in read('peaks') if f['properties']['featurecla']=='mountain']
 for f in sorted(peaks,key=lambda f:(f['properties'].get('scalerank',10),-f['properties'].get('elevation',0)))[:20]:
  p=f['properties'];add('PEAK-'+str(p['ne_id']),p.get('name_tr') or p['name'],'mountain','world',f['geometry'],elevation=p['elevation'],aliases=[p['name']])

# Small waterways are represented by explicit, touch-friendly center points, not invented borders.
straits=[('BOSPORUS','İstanbul Boğazı',29.05,41.12),('DARDANELLES','Çanakkale Boğazı',26.4,40.2),('GIBRALTAR','Cebelitarık Boğazı',-5.6,35.96),('HORMUZ','Hürmüz Boğazı',56.4,26.6),('MALACCA','Malakka Boğazı',100.4,3.8),('BAB-EL-MANDEB','Babülmendep Boğazı',43.3,12.6),('BERING','Bering Boğazı',-168.9,65.8),('DOVER','Dover Boğazı',1.5,51),('MAGELLAN','Macellan Boğazı',-70.8,-53.1),('DRAKE','Drake Geçidi',-66,-57),('SUEZ','Süveyş Kanalı',32.35,30.5),('PANAMA','Panama Kanalı',-79.7,9.1),('KIEL','Kiel Kanalı',9.7,54.2),('CORINTH','Korint Kanalı',23,37.94),('SUNDA','Sunda Boğazı',105.9,-5.9),('LOMBOK','Lombok Boğazı',115.7,-8.5),('TORRES','Torres Boğazı',142,-10.5),('BASS','Bass Boğazı',146,-39.8),('TAIWAN','Tayvan Boğazı',119.5,24.5),('KOREA','Kore Boğazı',129,34.5)]
for id,n,x,y in straits: add('STRAIT-'+id,n,'strait','world',{'type':'Point','coordinates':[x,y]},selection='center',aliases=[n])
if (SOURCE/'marine.json').exists():
 for f in read('marine'):
  p=f['properties']; p={k.lower():v for k,v in p.items()}
  if (p.get('scalerank') or 0)<=3:
   add('SEA-'+str(p.get('ne_id') or slug(p['name'])),p.get('name_tr') or p['name'],'sea','world',f['geometry'],aliases=[p['name']])

history=[('SAMSUN','19 Mayıs 1919’da Mustafa Kemal’in ulaştığı şehri bul.','TR-55'),('AMASYA','Millî Mücadele’nin gerekçesinin açıklandığı Amasya Genelgesi’nin yayımlandığı ili bul.','TR-05'),('ERZURUM','23 Temmuz 1919’da kongrenin toplandığı Erzurum’u bul.','TR-25'),('SIVAS','4 Eylül 1919’da ulusal kongrenin toplandığı ili bul.','TR-58'),('ANKARA','23 Nisan 1920’de TBMM’nin açıldığı ili bul.','TR-06'),('AFYON','Büyük Taarruz’un başladığı Kocatepe’nin bulunduğu ili bul.','TR-03'),('KUTAHYA','Dumlupınar’ın bulunduğu ili bul.','TR-43'),('IZMIR','9 Eylül 1922’de kurtarılan İzmir’i bul.','TR-35'),('CANAKKALE','1915’teki Çanakkale Muharebeleri ile ilişkili ili bul.','TR-17'),('MUDANYA','Mudanya Ateşkes Antlaşması’nın imzalandığı ilçenin bağlı olduğu ili bul.','TR-16'),('SAKARYA','Sakarya Meydan Muharebesi’nin Polatlı–Haymana çevresinde gerçekleştiği ili bul.','TR-06'),('ANITKABIR','Anıtkabir’in bulunduğu ili bul.','TR-06')]
questions=[{'id':'HISTORY-'+i,'prompt':p,'targetIds':[target],'difficulty':1,'source':'MEB T.C. İnkılap Tarihi ve Atatürkçülük: Millî Mücadele kronolojisi'} for i,p,target in history]
for f in features:
 p=f['properties']; questions.append({'id':'FIND-'+f['id'],'prompt':p['name_tr']+' — haritada bul.','targetIds':[f['id']],'difficulty':1,'kind':p['type']})
def write(n,data): (OUT/n).write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')))
write('catalog.json',{'type':'FeatureCollection','features':features})
write('questions.json',questions)
write('manifest.json',{'version':1,'counts':dict(Counter(f['properties']['type'] for f in features)),'sources':[{'name':'Natural Earth','url':'https://www.naturalearthdata.com/','license':'Public domain'},{'name':'alpers/Turkey-Maps-GeoJSON','url':'https://github.com/alpers/Turkey-Maps-GeoJSON','license':'Apache-2.0'},{'name':'geoBoundaries TUR ADM2 (2021)','url':'https://www.geoboundaries.org/','license':'ODbL-1.0; geoBoundaries CC BY 4.0 attribution'}],'sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in SOURCE.glob('*.json')}})
print(Counter(f['properties']['type'] for f in features))
