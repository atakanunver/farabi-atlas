import type { Feature, Geometry, FeatureCollection } from 'geojson';
export type RenderMode = 'FULL'|'LITE'|'SAFE';
export type Kind='province'|'district'|'country'|'capital'|'river'|'mountain'|'lake'|'strait'|'desert'|'sea'|'island'|'peninsula';
export type MapFeature=Feature<Geometry,{id:string;name_tr:string;name_en?:string;type:Kind;scope:'turkey'|'world';center:[number,number];region?:string;neighbors?:string[];countryId?:string;parentId?:string;aliases?:string[]}>;
export type Catalog=FeatureCollection<Geometry,MapFeature['properties']>;
export interface FarabiMap {
 ready():Promise<void>;getRenderMode():RenderMode;
 focus(id:string):Promise<void>;highlight(id:string,color?:string):void;clearHighlights():void;
 enableSelection():void;disableSelection():void;onFeatureClick(cb:(feature:MapFeature)=>void):()=>void;
 getFeature(id:string):MapFeature|null;featureAt(x:number,y:number):MapFeature|null;
 setLayers(layers:Kind[]):void;showLabels(enabled:boolean):void;resetView():void;
 setScope(scope:'turkey'|'world'):void;setGlobe(enabled:boolean):void;zoom(delta:number):void;destroy():void;
}
export abstract class MapBase {
 protected handlers=new Set<(f:MapFeature)=>void>();protected selection=true;
 protected layers:Kind[]=['province'];protected scope:'turkey'|'world'='turkey';protected labels=true;
 protected highlights=new Map<string,string>();
 constructor(protected catalog:Catalog){}
 getFeature(id:string){return this.catalog.features.find(f=>f.properties.id===id) as MapFeature??null;}
 onFeatureClick(cb:(f:MapFeature)=>void){this.handlers.add(cb);return()=>this.handlers.delete(cb);}
 enableSelection(){this.selection=true;} disableSelection(){this.selection=false;}
 protected emit(f:MapFeature){if(this.selection)this.handlers.forEach(cb=>cb(f));}
}
