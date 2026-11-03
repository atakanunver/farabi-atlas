"""Exercise the real portal auth and migration in an isolated temporary copy."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PORTAL=ROOT.parent/'okul'
with tempfile.TemporaryDirectory(prefix='atlas-portal-test-') as directory:
 sandbox=Path(directory)
 for source in PORTAL.glob('*.py'):shutil.copy2(source,sandbox/source.name)
 for folder in ['rotalar','kaynaklar','templates','scripts']:
  shutil.copytree(PORTAL/folder,sandbox/folder,ignore=shutil.ignore_patterns('__pycache__'))
 (sandbox/'static').symlink_to(PORTAL/'static',target_is_directory=True)
 subprocess.run([sys.executable,str(ROOT/'scripts/integrate_portal.py'),'--okul',str(sandbox),'--apply'],check=True,stdout=subprocess.DEVNULL)
 sys.path.insert(0,str(sandbox));sys.path.insert(1,str(ROOT))
 import db,auth,zaman
 from ayarlar import AYAR
 AYAR.db_yolu=sandbox/'test.db'
 AYAR.program_yolu=sandbox/'program.json';AYAR.zil_yolu=sandbox/'zil.json';AYAR.takvim_yolu=sandbox/'takvim.json'
 AYAR.vapid_ozel='';AYAR.vapid_acik=''
 from app import app
 from fastapi.testclient import TestClient
 with TestClient(app) as client:
  c=db.baglanti()
  assert c.execute('PRAGMA user_version').fetchone()[0]==len(db.GOCLER)
  cur=c.execute("INSERT INTO kullanici(rol,ad_soyad,kullanici_adi,sifre_degismeli,olusturma) VALUES('ogretmen','Atlas test öğretmeni','atlas-test',0,?)",(zaman.simdi_str(),));teacher=cur.lastrowid
  c.execute("INSERT INTO ogretmen_gorev(ogretmen_id,sinif,ders) VALUES(?,'9-A','cografya')",(teacher,));c.commit()
  token=auth.oturum_ac(c,teacher);c.close()
  assert client.get('/api/atlas/context',follow_redirects=False).status_code in (302,303)
  client.cookies.set(auth.COOKIE_ADI,token)
  context=client.get('/api/atlas/context').json();assert context['classes']==['9-A'] and not context['demo']
  assert client.get('/kure/').status_code==200
  data={'csrf':context['csrf'],'className':'9-A','config':json.dumps({'game':'turkiye','category':'country','count':5,'seconds':0,'difficulty':'easy'})}
  response=client.post('/api/atlas/sessions',data=data);assert response.status_code==200,response.text
  s=response.json();assert s['className']=='9-A'
  data['className']='9-B';assert client.post('/api/atlas/sessions',data=data).status_code==404
  response=client.get('/kure/data/world-lite.pmtiles',headers={'Range':'bytes=0-126'});assert response.status_code==206,response.status_code
  assert response.content[:7]==b'PMTiles'
  c=db.baglanti();assert c.execute('SELECT COUNT(*) FROM atlas_session').fetchone()[0]==1;c.close()
 print('PASS: real portal migration, teacher cookie, class permissions, CSRF and PMTiles byte ranges; production data untouched')
