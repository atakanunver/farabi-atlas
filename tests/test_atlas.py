import json
import sqlite3
import time
import pytest
from fastapi.testclient import TestClient
from backend import atlas
from backend.server import standalone,make_router

@pytest.fixture
def db():
 c=sqlite3.connect(':memory:');atlas.initialize(c);yield c;c.close()

def config(game='turkiye',**kw):return dict(game=game,category='country',count=5,seconds=30,difficulty='easy',**kw)

def test_catalog():
 features=list(atlas.FEATURES.values())
 assert len([p for p in features if p['type']=='province'])==81
 assert len([p for p in features if p['type']=='district'])==973
 assert len(atlas.FEATURES)==len(atlas.CATALOG)
 assert all(p['name_tr'] and p['scope'] in ('turkey','world') for p in features)
 assert set(atlas.FEATURES['TR-18']['neighbors'])=={'TR-06','TR-14','TR-19','TR-37','TR-71','TR-78'}
 for p in features:
  for n in p.get('neighbors',[]):assert p['id'] in atlas.FEATURES[n]['neighbors']
  if p['type']=='district':assert atlas.FEATURES[p['parentId']]['type']=='province'
 for q in atlas.QUESTIONS:assert all(id in atlas.FEATURES for id in q['targetIds'])

@pytest.mark.parametrize('game',sorted(atlas.GAMES))
def test_full_game_and_idempotency(db,game):
 s=atlas.start(db,7,'9-A',config(game))
 while not s['done']:
  private=atlas.load(db,s['id'],7);q=private['questions'][private['index']]
  for target in q['targetIds'][:q.get('required',1)]:
   before=s
   s=atlas.act(db,s['id'],7,'answer',s['revision'],target)
   duplicate=atlas.act(db,s['id'],7,'answer',before['revision'],target)
   assert duplicate['revision']==s['revision'] and duplicate['score']==s['score']
 assert s['score']>=500
 assert len(s['events'])==s['total']
 assert atlas.act(db,s['id'],7,'finish',s['revision'])['score']==s['score']
 with pytest.raises(KeyError):atlas.load(db,s['id'],8)

def test_second_attempt_timeout_pause(db):
 s=atlas.start(db,7,'9-A',config());private=atlas.load(db,s['id'],7);target=private['questions'][0]['targetIds'][0]
 wrong=next(k for k in atlas.FEATURES if k.startswith('TR-') and k!=target)
 s=atlas.act(db,s['id'],7,'answer',s['revision'],wrong);assert s['index']==0 and s['attempts']==1
 s=atlas.act(db,s['id'],7,'answer',s['revision'],target);assert 50<=s['score']<=100
 s=atlas.act(db,s['id'],7,'pause',s['revision']);assert s['paused']
 with pytest.raises(atlas.GameError):atlas.act(db,s['id'],7,'answer',s['revision'],target)
 s=atlas.act(db,s['id'],7,'resume',s['revision']);assert not s['paused']
 with pytest.raises(atlas.GameError):atlas.act(db,s['id'],7,'timeout',s['revision'])
 private=atlas.load(db,s['id'],7);private['round_start']=time.time()-35
 atlas.save(db,private);db.commit();s=atlas.act(db,s['id'],7,'timeout',s['revision']);assert s['index']==2

@pytest.mark.parametrize('category',['country','capital','river','mountain','lake','strait','desert','sea'])
def test_world_categories(category):
 qs=atlas.make_questions({**config('dunya'),'category':category})
 assert len(qs)==5
 assert all(atlas.FEATURES[q['targetIds'][0]]['type']==category for q in qs)

def test_http_csrf_and_range(tmp_path,monkeypatch):
 monkeypatch.setenv('ATLAS_DB',str(tmp_path/'test.db'))
 with TestClient(standalone()) as c:
  context=c.get('/api/atlas/context').json();assert context['demo']
  assert c.post('/api/atlas/sessions',data={'config':json.dumps(config()),'className':'Demo sınıfı'}).status_code==400
  body={'csrf':context['csrf'],'config':json.dumps(config()),'className':'9-A'}
  assert c.post('/api/atlas/sessions',data=body).status_code==404
  body['className']='Demo sınıfı';s=c.post('/api/atlas/sessions',data=body).json()
  assert 'targetIds' not in s['question']
  assert c.get('/api/atlas/sessions/not-found').status_code==404
  assert c.get('/kure/').status_code==200

def test_production_permissions(tmp_path):
 from fastapi import FastAPI,Request,HTTPException
 database=tmp_path/'okul.db'
 def connect():return sqlite3.connect(database)
 with connect() as c:atlas.initialize(c)
 def identity(request:Request):
  role=request.headers.get('test-role')
  if role not in ('ogretmen','yonetici'):raise HTTPException(404)
  request.state.csrf='test-csrf';return {'id':int(request.headers.get('test-user','1')),'ad_soyad':'Test öğretmeni'}
 app=FastAPI();app.include_router(make_router(identity,connect,lambda c,k:['9-A']))
 with TestClient(app) as c:
  assert c.get('/api/atlas/context').status_code==404
  headers={'test-role':'ogretmen'}
  body={'csrf':'test-csrf','config':json.dumps(config()),'className':'9-A'}
  s=c.post('/api/atlas/sessions',headers=headers,data=body).json()
  assert c.get('/api/atlas/sessions/'+s['id'],headers={**headers,'test-user':'2'}).status_code==404
  assert c.get('/api/atlas/sessions',headers={**headers,'test-user':'2'}).json()==[]

def test_independent_service_without_portal(tmp_path,monkeypatch):
 monkeypatch.setenv('ATLAS_STANDALONE','1')
 monkeypatch.setenv('ATLAS_DB',str(tmp_path/'independent.db'))
 with TestClient(standalone()) as c:
  response=c.get('/kure/',follow_redirects=False)
  assert response.status_code==200 and 'location' not in response.headers
  ctx=c.get('/api/atlas/context').json()
  assert ctx['independent'] and not ctx['demo'] and ctx['classes']==['Sınıf etkinliği']
  s=c.post('/api/atlas/sessions',data={'csrf':ctx['csrf'],'className':'Sınıf etkinliği','config':json.dumps(config())})
  assert s.status_code==200 and s.json()['score']==0
