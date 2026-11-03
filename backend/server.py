"""Standalone local preview and reusable Dijital Okul router."""
import json
import os
import secrets
import sqlite3
from pathlib import Path
from fastapi import FastAPI,APIRouter,Depends,HTTPException,Request
from fastapi.responses import FileResponse,RedirectResponse
from fastapi.staticfiles import StaticFiles
from . import atlas

def make_router(identity,connect,classes,demo=False,independent=False):
 router=APIRouter(prefix='/api/atlas')
 async def connection():
  c=connect()
  try:yield c
  finally:c.close()
 async def form(request):
  f=await request.form()
  expected=getattr(request.state,'csrf','')
  if not expected or not secrets.compare_digest(str(f.get('csrf','')),expected):raise HTTPException(400,'Oturum doğrulaması başarısız; sayfayı yenileyin.')
  return f
 def checked(c,id,k):
  try:return atlas.load(c,id,k['id'])
  except KeyError:raise HTTPException(404,'Oturum bulunamadı.')
 @router.get('/context')
 async def context(request:Request,k=Depends(identity),c=Depends(connection)):
  return {'teacher':k['ad_soyad'],'classes':classes(c,k),'csrf':request.state.csrf,'demo':demo,'independent':independent}
 @router.post('/sessions')
 async def start(request:Request,k=Depends(identity),c=Depends(connection)):
  f=await form(request)
  try:
   config=json.loads(str(f.get('config','{}')));class_name=str(f.get('className',''))
   if class_name not in classes(c,k):raise HTTPException(404,'Sınıf yetkisi bulunamadı.')
   return atlas.start(c,k['id'],class_name,config)
  except (ValueError,TypeError) as e:raise HTTPException(400,str(e))
 @router.get('/sessions')
 async def history(k=Depends(identity),c=Depends(connection)):
  return [dict(zip(('id','className','created','finished','score'),r)) for r in c.execute('SELECT id,class_name,created,finished,score FROM atlas_session WHERE teacher_id=? ORDER BY created DESC LIMIT 30',(k['id'],))]
 @router.get('/sessions/{id}')
 async def get(id:str,k=Depends(identity),c=Depends(connection)):return atlas.public(checked(c,id,k))
 @router.post('/sessions/{id}/action')
 async def action(id:str,request:Request,k=Depends(identity),c=Depends(connection)):
  f=await form(request);checked(c,id,k)
  try:return atlas.act(c,id,k['id'],str(f.get('action')),int(str(f.get('revision','-1'))),f.get('selected'))
  except (ValueError,TypeError) as e:raise HTTPException(400,str(e))
 return router

def standalone():
 independent=os.environ.get('ATLAS_STANDALONE')=='1'
 app=FastAPI(title='Farabi Atlas' if independent else 'Farabi Atlas — yerel geliştirme')
 db=Path(os.environ.get('ATLAS_DB',str(atlas.ROOT/'var/preview.db')));db.parent.mkdir(parents=True,exist_ok=True)
 def connect():return sqlite3.connect(db,timeout=10)
 with connect() as c:atlas.initialize(c)
 token=secrets.token_urlsafe(32)
 def identity(request:Request):
  request.state.csrf=token
  return {'id':1,'ad_soyad':'Tahta modu' if independent else 'Yerel geliştirme','rol':'ogretmen'}
 app.include_router(make_router(identity,connect,lambda c,k:['Sınıf etkinliği' if independent else 'Demo sınıfı'],demo=not independent,independent=independent))
 app.mount('/kure',StaticFiles(directory=str(atlas.ROOT/'dist'),html=True),name='atlas')
 @app.get('/')
 def root():return RedirectResponse('/kure/')
 return app

def install(app):
 """Called by okul/app.py; reuses its authentication, CSRF, DB and class permissions."""
 import db
 import yetki
 from deps import rol
 from deps import TEMPLATES
 TEMPLATES.env.globals['ATLAS_ETKIN']=True
 teacher=rol('ogretmen','yonetici')
 def classes(c,k):
  return [r[0] for r in c.execute('SELECT DISTINCT sinif FROM ogrenci ORDER BY sinif')] if k['rol']=='yonetici' else yetki.ogretmen_siniflari(c,k['id'])
 app.include_router(make_router(teacher,db.baglanti,classes))
 @app.get('/kure/',include_in_schema=False)
 def index(k=Depends(teacher)):return FileResponse(atlas.ROOT/'dist/index.html',headers={'Cache-Control':'no-store'})
 @app.get('/kure',include_in_schema=False)
 def slash():return RedirectResponse('/kure/')
 app.mount('/kure/assets',StaticFiles(directory=str(atlas.ROOT/'dist/assets')),name='atlas-assets')
 app.mount('/kure/data',StaticFiles(directory=str(atlas.ROOT/'dist/data')),name='atlas-data')
