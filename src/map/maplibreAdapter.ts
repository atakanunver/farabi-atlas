import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {Protocol} from 'pmtiles';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import {MapBase,type FarabiMap,type Catalog,type Kind,type RenderMode,type MapFeature} from './api';
export class MapLibreAdapter extends MapBase implements FarabiMap{
 private map:maplibregl.Map;private loaded:Promise<void>;private globe=false;private markers:maplibregl.Marker[]=[];
 constructor(host:HTMLElement,catalog:Catalog,private mode:RenderMode,onFailure:()=>void){super(catalog);
  maplibregl.setWorkerUrl(workerUrl);maplibregl.setWorkerCount(mode==='LITE'?1:2);
  const protocol=new Protocol();maplibregl.addProtocol('pmtiles',protocol.tile);
  this.map=new maplibregl.Map({container:host,style:{version:8,sources:{'local-world':{type:'vector',url:'pmtiles://'+new URL(import.meta.env.BASE_URL+'data/world-lite.pmtiles',location.origin).href}},layers:[{id:'ocean',type:'background',paint:{'background-color':'#16262d'}},{id:'local-land',type:'fill',source:'local-world','source-layer':'atlas',paint:{'fill-color':'#344541','fill-outline-color':'#64716b'}}]},center:[35,39],zoom:4.5,pitch:0,bearing:0,canvasContextAttributes:{antialias:mode==='FULL'},pixelRatio:mode==='LITE'?1:Math.min(devicePixelRatio,1.5),attributionControl:false,renderWorldCopies:false});
  this.loaded=new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(new Error('Harita başlatma zaman aşımı')),6000);this.map.once('load',()=>{clearTimeout(t);this.map.addSource('atlas',{type:'geojson',data:catalog,promoteId:'id'});this.map.addLayer({id:'base',type:'fill',source:'atlas',filter:['==',['get','type'],'country'],paint:{'fill-color':'#344541','fill-outline-color':'#64716b'}});this.map.addLayer({id:'areas',type:'fill',source:'atlas',filter:['literal',false],paint:{'fill-color':['coalesce',['feature-state','color'],'#526556'],'fill-outline-color':'#9aa99a','fill-opacity':.9}});this.map.addLayer({id:'lines',type:'line',source:'atlas',filter:['literal',false],paint:{'line-color':['coalesce',['feature-state','color'],'#69b1d0'],'line-width':3}});this.map.addLayer({id:'hits',type:'line',source:'atlas',filter:['literal',false],paint:{'line-color':'#69b1d0','line-width':22,'line-opacity':0}});this.map.addLayer({id:'points',type:'circle',source:'atlas',filter:['literal',false],paint:{'circle-color':['coalesce',['feature-state','color'],'#e6c784'],'circle-radius':9,'circle-stroke-width':2,'circle-stroke-color':'#202323'}});this.update();resolve();});this.map.once('error',e=>{clearTimeout(t);reject(e.error);});});
  this.map.on('click',e=>{const f=this.featureAt(e.point.x,e.point.y);if(f)this.emit(f);});this.map.getCanvas().addEventListener('webglcontextlost',e=>{e.preventDefault();onFailure();});
 }
 ready(){return this.loaded;}getRenderMode(){return this.mode;}
 featureAt(x:number,y:number){const hit=this.map.queryRenderedFeatures([x,y],{layers:['points','areas','hits']});hit.sort((a,b)=>Number(b.geometry.type==='Point')-Number(a.geometry.type==='Point'));return hit.length?this.getFeature(String(hit[0].properties.id)):null;}
 async focus(id:string){const f=this.getFeature(id);if(f)this.map.easeTo({center:f.properties.center,zoom:Math.max(this.map.getZoom(),f.properties.type==='province'?6:3),duration:this.mode==='FULL'?400:0});}
 highlight(id:string,color='#b9df7c'){this.highlights.set(id,color);this.map.setFeatureState({source:'atlas',id},{color});}
 clearHighlights(){this.highlights.forEach((_,id)=>this.map.removeFeatureState({source:'atlas',id}));this.highlights.clear();}
 setLayers(l:Kind[]){this.layers=l;this.update();this.updateLabels();}showLabels(v:boolean){this.labels=v;this.updateLabels();}
 resetView(){this.map.jumpTo({center:this.scope==='turkey'?[35,39]:[25,20],zoom:this.scope==='turkey'?4.5:1.4});}
 setScope(s:'turkey'|'world'){this.scope=s;this.update();this.resetView();this.updateLabels();}
 setGlobe(v:boolean){this.globe=v;this.map.setProjection({type:v?'globe':'mercator'});this.resetView();}
 zoom(d:number){this.map.zoomTo(this.map.getZoom()+d*.6,{duration:this.mode==='FULL'?200:0});}
 destroy(){this.markers.forEach(m=>m.remove());this.map.remove();this.handlers.clear();}
 private updateLabels(){this.markers.forEach(m=>m.remove());this.markers=[];if(!this.labels)return;const active=this.catalog.features.filter(f=>this.layers.includes(f.properties.type)&&f.properties.scope===this.scope);if(active.length>100)return;active.forEach(f=>{const node=document.createElement('span');node.className='gl-label';node.textContent=f.properties.name_tr;node.style.pointerEvents='none';this.markers.push(new maplibregl.Marker({element:node}).setLngLat(f.properties.center).addTo(this.map));});}
 private update(){if(!this.map.getSource('atlas'))return;const active:maplibregl.FilterSpecification=['all',['in',['get','type'],['literal',this.layers]],this.scope==='turkey'?['any',['==',['get','scope'],'turkey'],['all',['>=',['at',0,['get','center']],24],['<=',['at',0,['get','center']],46],['>=',['at',1,['get','center']],34],['<=',['at',1,['get','center']],43]]]:['==',['get','scope'],'world']];this.map.setFilter('areas',['all',active,['in',['geometry-type'],['literal',['Polygon','MultiPolygon']]]]);this.map.setFilter('lines',['all',active,['in',['geometry-type'],['literal',['LineString','MultiLineString']]]]);this.map.setFilter('hits',['all',active,['in',['geometry-type'],['literal',['LineString','MultiLineString']]]]);this.map.setFilter('points',['all',active,['==',['geometry-type'],'Point']]);}
}
