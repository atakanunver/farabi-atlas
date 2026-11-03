import {geoMercator,geoOrthographic,geoPath,geoGraticule10,geoDistance} from 'd3-geo';
import type {GeoProjection} from 'd3-geo';
import {MapBase,type FarabiMap,type Catalog,type Kind,type MapFeature} from './api';
const NS='http://www.w3.org/2000/svg';
const el=(name:string,attrs:Record<string,string>={})=>{const e=document.createElementNS(NS,name);for(const[k,v]of Object.entries(attrs))e.setAttribute(k,v);return e;};
export class SvgAdapter extends MapBase implements FarabiMap{
 private svg=el('svg',{'role':'img','aria-label':'Etkileşimli coğrafya haritası'});
 private projection!:GeoProjection;private observer:ResizeObserver;private globe=false;private minScale=.6;private scaleFactor=1;private offset=[0,0];private rotation:[number,number,number]=[-25,-20,0];private last:MapFeature|null=null;
 private down:{x:number;y:number;ox:number;oy:number;rot:[number,number,number];moved:boolean}|null=null;
 constructor(private host:HTMLElement,catalog:Catalog){super(catalog);host.replaceChildren(this.svg);this.svg.classList.add('safe-map');this.observer=new ResizeObserver(()=>this.draw());this.observer.observe(host);
  this.svg.addEventListener('pointerdown',e=>{this.down={x:e.clientX,y:e.clientY,ox:this.offset[0],oy:this.offset[1],rot:[...this.rotation],moved:false};});
  this.svg.addEventListener('pointermove',e=>{if(!this.down)return;const dx=e.clientX-this.down.x,dy=e.clientY-this.down.y;if(Math.hypot(dx,dy)>10)this.down.moved=true;if(!this.down.moved)return;this.svg.setPointerCapture(e.pointerId);if(this.globe)this.rotation=[this.down.rot[0]+dx*.25,this.down.rot[1]-dy*.25,0];else this.offset=[this.down.ox+dx,this.down.oy+dy];this.draw();});
  this.svg.addEventListener('pointerup',e=>{const d=this.down;this.down=null;if(!d||d.moved)return;const node=(e.target as Element).closest('[data-id]');if(node){const f=this.getFeature(node.getAttribute('data-id')!);if(f){this.last=f;this.emit(f);}}});
  this.svg.addEventListener('wheel',e=>{
   e.preventDefault();if(!e.deltaY)return;
   const rect=this.svg.getBoundingClientRect();
   const delta=e.deltaY*(e.deltaMode===1?16:e.deltaMode===2?rect.height:1);
   this.zoomAt(Math.exp(-Math.max(-240,Math.min(240,delta))*.0025),e.clientX-rect.left,e.clientY-rect.top);
  },{passive:false});this.draw();
 }
 async ready(){}getRenderMode(){return 'SAFE' as const;}
 featureAt(x:number,y:number){const node=document.elementFromPoint(x,y)?.closest('[data-id]');return node?this.getFeature(node.getAttribute('data-id')!):null;}
 async focus(id:string){const f=this.getFeature(id);if(!f)return;const c=f.properties.center;if(this.globe)this.rotation=[-c[0],-c[1],0];else{this.scaleFactor=Math.max(this.scaleFactor,2);this.draw();const p=this.projection(c);if(p){this.offset[0]+=this.host.clientWidth/2-p[0];this.offset[1]+=this.host.clientHeight/2-p[1];}}this.draw();}
 highlight(id:string,color='#b9df7c'){this.highlights.set(id,color);this.draw();}clearHighlights(){this.highlights.clear();this.draw();}
 setLayers(l:Kind[]){this.layers=l;this.draw();}showLabels(v:boolean){this.labels=v;this.draw();}
 resetView(){this.scaleFactor=1;this.offset=[0,0];this.rotation=[-25,-20,0];this.draw();}
 setScope(s:'turkey'|'world'){this.scope=s;this.resetView();}setGlobe(v:boolean){this.globe=v;this.resetView();}zoom(d:number){if(d)this.zoomAt(d>0?1.35:1/1.35,this.host.clientWidth/2,this.host.clientHeight/2);}
 private zoomAt(multiplier:number,x:number,y:number){
  const next=Math.max(this.minScale,Math.min(16,this.scaleFactor*multiplier)),ratio=next/this.scaleFactor;
  if(!this.globe){
   const cx=this.host.clientWidth/2,cy=this.host.clientHeight/2;
   this.offset=[(this.offset[0]+cx-x)*ratio+x-cx,(this.offset[1]+cy-y)*ratio+y-cy];
  }
  this.scaleFactor=next;this.draw();
 }
 destroy(){this.observer.disconnect();this.svg.remove();this.handlers.clear();}
 private draw(){const w=this.host.clientWidth||900,h=this.host.clientHeight||600;this.svg.setAttribute('viewBox',`0 0 ${w} ${h}`);this.svg.replaceChildren();
  const provinces=this.catalog.features.filter(f=>f.properties.type==='province');
  if(this.globe){this.minScale=.6;this.projection=geoOrthographic().translate([w/2,h/2]).scale(Math.min(w,h)*.43*this.scaleFactor).rotate(this.rotation).clipAngle(90);const sea=el('path',{d:geoPath(this.projection)({type:'Sphere'})||'',class:'ocean-sphere'});this.svg.append(sea);}
  else{this.projection=geoMercator();if(this.scope==='turkey')this.projection.fitExtent([[w*.05,h*.15],[w*.95,h*.85]],{type:'FeatureCollection',features:provinces});else this.projection.scale(Math.min(w/6.4,h/3.5)).translate([w/2,h*.54]);const s=this.projection.scale(),t=this.projection.translate();this.minScale=this.scope==='turkey'?Math.min(w/6.4,h/3.5)/s*.6:.6;this.projection.scale(s*this.scaleFactor).translate([w/2+(t[0]-w/2)*this.scaleFactor+this.offset[0],h/2+(t[1]-h/2)*this.scaleFactor+this.offset[1]]).clipExtent([[0,0],[w,h]]);}
  const path=geoPath(this.projection);if(this.globe)this.svg.append(el('path',{d:path(geoGraticule10())||'',class:'graticule'}));const base=this.catalog.features.filter(f=>f.properties.type==='country');const labelBoxes:{x:number;y:number;w:number}[]=[];
  const active=this.catalog.features.filter(f=>this.layers.includes(f.properties.type)&&(this.scope==='world'?f.properties.scope==='world':f.properties.scope==='turkey'||(f.properties.center[0]>24&&f.properties.center[0]<46&&f.properties.center[1]>34&&f.properties.center[1]<43)));
  const drawFeature=(f:MapFeature,interactive:boolean)=>{const p=f.properties;const isPoint=f.geometry.type==='Point';const isLine=f.geometry.type.includes('Line');let display=f;
   if(!this.globe&&p.id==='COUNTRY-ATA'){
    const clamp=(c:any):any=>typeof c[0]==='number'?[c[0],Math.max(-85,c[1])]:c.map(clamp);
    display={...f,geometry:{...f.geometry,coordinates:clamp((f.geometry as GeoJSON.MultiPolygon).coordinates)} as MapFeature['geometry']};
   }
   const attrs:Record<string,string>={d:path(display)||'',class:`geo ${interactive?'target':'land'} kind-${p.type}`,'data-feature':p.id};if(interactive)attrs['data-id']=p.id;
   const n=el('path',attrs);const color=this.highlights.get(p.id);if(color){n.setAttribute('style',`${isLine?'stroke':'fill'}:${color}`);n.classList.add('highlighted');}
   if(interactive){const title=el('title');title.textContent=this.labels?p.name_tr:'Coğrafi hedef';n.append(title);}this.svg.append(n);
   if(interactive&&isLine){const hit=el('path',{d:attrs.d,class:'line-hit','data-id':p.id});this.svg.append(hit);}
   const center=(isPoint?(f.geometry as GeoJSON.Point).coordinates:p.center) as [number,number];
   if(interactive&&this.labels&&(this.globe?geoDistance(center,[-this.rotation[0],-this.rotation[1]])<1.5:true)){
    const xy=this.projection(center);if(xy&&xy[0]>0&&xy[0]<w&&xy[1]>0&&xy[1]<h&&(active.length<100||this.scaleFactor>2||p.type==='province')){const box={x:xy[0],y:xy[1]+(isPoint?-12:3),w:p.name_tr.length*6.5};if(!labelBoxes.some(b=>Math.abs(b.x-box.x)<(b.w+box.w)/2+5&&Math.abs(b.y-box.y)<17)){labelBoxes.push(box);const t=el('text',{x:String(box.x),y:String(box.y),class:'map-label','data-id':p.id});t.textContent=p.name_tr;this.svg.append(t);}}
   }
  };
  path.pointRadius(7);base.forEach(f=>drawFeature(f as MapFeature,false));
  active.sort((a,b)=>Number(a.geometry.type==='Point')-Number(b.geometry.type==='Point')).forEach(f=>drawFeature(f as MapFeature,true));
 }
}
