"""Atlas game rules and SQLite persistence. No runtime internet dependencies."""
import json
import random
import sqlite3
import time
import uuid
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=json.loads((ROOT/'public/data/catalog.json').read_text())['features']
FEATURES={f['properties']['id']:f['properties'] for f in CATALOG}
QUESTIONS=json.loads((ROOT/'public/data/questions.json').read_text())
GAMES={'turkiye','komsu','bolge','dunya','tarih'}
KINDS={'province','district','country','capital','river','mountain','lake','strait','desert','sea','island','peninsula'}

class GameError(ValueError): pass

def initialize(c):
 c.execute('CREATE TABLE IF NOT EXISTS atlas_session (id TEXT PRIMARY KEY, teacher_id INTEGER NOT NULL, class_name TEXT NOT NULL, created REAL NOT NULL, finished REAL, score INTEGER NOT NULL DEFAULT 0, state TEXT NOT NULL)')
 c.execute('CREATE INDEX IF NOT EXISTS atlas_teacher ON atlas_session(teacher_id,created)')
 c.commit()

def make_questions(config):
 game=config['game']; kind=config.get('category','country'); count=config.get('count',10)
 if game not in GAMES or kind not in KINDS or not isinstance(count,int) or not 1<=count<=30: raise GameError('Geçersiz oyun ayarları.')
 if config.get('difficulty','easy') not in {'easy','medium','hard'}: raise GameError('Geçersiz zorluk.')
 seconds=config.get('seconds',30)
 if seconds not in (0,15,30,45,60): raise GameError('Geçersiz süre.')
 provinces=[p for p in FEATURES.values() if p['type']=='province']
 out=[]
 if game=='tarih':
  out=[dict(q,layers=['province'],scope='turkey') for q in QUESTIONS if q['id'].startswith('HISTORY-')]
 elif game=='komsu':
  for p in provinces:
   if p['neighbors']: out.append({'id':'NEIGHBOR-'+p['id'],'prompt':p['name_tr']+' ilinin komşularından birini seç.','targetIds':p['neighbors'],'anchor':p['id'],'layers':['province'],'scope':'turkey'})
 elif game=='bolge':
  regions=sorted({p['region'] for p in provinces})
  for region in regions:
   targets=[p['id'] for p in provinces if p['region']==region]
   out.append({'id':'REGION-'+region,'prompt':region+' Bölgesi’nden 5 farklı il seç.','targetIds':targets,'required':5,'layers':['province'],'scope':'turkey'})
 else:
  desired='province' if game=='turkiye' else kind
  pool=[p for p in FEATURES.values() if p['type']==desired and (game=='turkiye' or p['scope']=='world')]
  for p in pool:
   prompt=p['name_tr']+' — haritada bul.'
   if config.get('difficulty')=='medium' and p.get('countryId') in FEATURES: prompt=FEATURES[p['countryId']]['name_tr']+' ülkesinin başkentini bul.'
   elif config.get('difficulty')=='medium' and p.get('region'): prompt=p['region']+' Bölgesi’nde, adı “'+p['name_tr'][:3]+'” ile başlayan ili bul.'
   elif config.get('difficulty')=='hard' and desired=='province' and p.get('neighbors'): prompt=FEATURES[p['neighbors'][0]]['name_tr']+' ile komşu, adı “'+p['name_tr'][:3]+'” ile başlayan ili bul.'
   out.append({'id':'FIND-'+p['id'],'prompt':prompt,'targetIds':[p['id']],'layers':[desired],'scope':'turkey' if game=='turkiye' else 'world'})
 if not out: raise GameError('Bu kategori için doğrulanmış soru bulunamadı.')
 random.SystemRandom().shuffle(out)
 # Avoid repeats within a round; UI reports the actual available count.
 return out[:count]

def remaining(s,now=None):
 limit=s['config']['seconds']
 if not limit:return None
 now=now or time.time()
 elapsed=(s.get('paused_at') or now)-s['round_start']-s.get('paused_total',0)
 return max(0,limit-elapsed)

def public(s):
 q=s['questions'][s['index']] if s['index']<len(s['questions']) else None
 visible={k:v for k,v in q.items() if k not in ('targetIds',)} if q else None
 return {'id':s['id'],'config':s['config'],'className':s['className'],'index':s['index'],'total':len(s['questions']),'question':visible,'score':s['score'],'streak':s['streak'],'attempts':s['attempts'],'selected':s['selected'],'revision':s['revision'],'paused':bool(s.get('paused_at')),'remaining':remaining(s),'done':q is None,'feedback':s.get('feedback'),'events':s['events'] if q is None else []}

def save(c,s):
 c.execute('UPDATE atlas_session SET state=?, score=?, finished=? WHERE id=?',(json.dumps(s,ensure_ascii=False),s['score'],time.time() if s['index']>=len(s['questions']) else None,s['id']))

def start(c,teacher,class_name,config):
 config={**config,'seconds':config.get('seconds',30),'difficulty':config.get('difficulty','easy')}
 qs=make_questions(config); now=time.time(); id=uuid.uuid4().hex
 s={'id':id,'className':class_name,'config':config,'questions':qs,'index':0,'score':0,'streak':0,'attempts':0,'selected':[],'round_start':now,'paused_total':0,'paused_at':None,'revision':0,'events':[]}
 with c:c.execute('INSERT INTO atlas_session(id,teacher_id,class_name,created,state) VALUES(?,?,?,?,?)',(id,teacher,class_name,now,json.dumps(s,ensure_ascii=False)))
 return public(s)

def load(c,id,teacher):
 row=c.execute('SELECT state FROM atlas_session WHERE id=? AND teacher_id=?',(id,teacher)).fetchone()
 if not row:raise KeyError(id)
 return json.loads(row[0])

def act(c,id,teacher,action,revision,selected=None):
 c.execute('BEGIN IMMEDIATE')
 try:
  s=load(c,id,teacher)
  if s['index']>=len(s['questions']) or revision!=s['revision']:
   c.rollback();return public(s)
  q=s['questions'][s['index']]; now=time.time(); feedback=None
  if action=='pause':
   if not s['paused_at']:s['paused_at']=now
  elif action=='resume':
   if s['paused_at']:s['paused_total']+=now-s['paused_at'];s['paused_at']=None
  elif action=='finish':
   s['index']=len(s['questions']);s['paused_at']=None
  elif action in ('answer','skip','timeout'):
   if s['paused_at']:raise GameError('Oyun duraklatıldı.')
   left=remaining(s,now);expired=left is not None and left<=0
   if action=='timeout' and not expired:raise GameError('Süre henüz dolmadı.')
   correct=action=='answer' and not expired and selected in q['targetIds']
   if selected in s['selected']:c.rollback();return public(s)
   if action=='answer' and selected not in FEATURES:raise GameError('Geçersiz coğrafi hedef.')
   advance=False;points=0
   if correct:
    s['selected'].append(selected);feedback={'status':'correct','selected':selected,'message':'Doğru seçim!'}
    advance=len(s['selected'])>=q.get('required',1)
    if advance:
     s['streak']=s['streak']+1 if s['attempts']==0 else 0
     points=(100 if s['attempts']==0 else 50)+(round(50*left/s['config']['seconds']) if left is not None else 0)+min(50,max(0,s['streak']-1)*10)
   else:
    if action=='answer' and not expired:s['attempts']+=1
    s['streak']=0;advance=expired or action in ('skip','timeout') or s['attempts']>=2
    feedback={'status':'wrong','selected':selected,'message':'Süre doldu.' if expired else 'Soru geçildi.' if action=='skip' else 'Tekrar dene.' if not advance else 'İkinci deneme bitti.'}
   if advance:
    s['score']+=points;s['events'].append({'questionId':q['id'],'prompt':q['prompt'],'correct':correct,'points':points,'attempts':s['attempts'],'selected':s['selected'][:]})
    feedback.update({'points':points,'answers':q['targetIds']})
    s['index']+=1;s['selected']=[];s['attempts']=0;s['round_start']=now;s['paused_total']=0
   s['feedback']=feedback
  else:raise GameError('Geçersiz işlem.')
  s['revision']+=1;save(c,s);c.commit();return public(s)
 except Exception:
  c.rollback();raise
