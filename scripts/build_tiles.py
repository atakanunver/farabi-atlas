"""Generate small PMTiles archives locally. Dependencies are build-time only."""
import gzip
import json
import math
from pathlib import Path
from shapely.geometry import shape,box,mapping
from shapely.ops import transform
import mapbox_vector_tile
from pmtiles.writer import Writer
from pmtiles.tile import zxy_to_tileid,TileType,Compression

ROOT=Path(__file__).resolve().parents[1]
R=20037508.342789244
def project(x,y,z=None):
 return x*R/180,math.log(math.tan((90+max(-85.05112878,min(85.05112878,y)))*math.pi/360))*R/math.pi

def build(name,features,minzoom,maxzoom,bounds):
 prepared=[(f,transform(project,shape(f['geometry']))) for f in features]
 entries=[]
 for z in range(minzoom,maxzoom+1):
  n=2**z;size=2*R/n
  x1,y1=project(bounds[0],bounds[1]);x2,y2=project(bounds[2],bounds[3])
  for x in range(max(0,int((x1+R)/size)),min(n-1,int((x2+R)/size))+1):
   for y in range(max(0,int((R-y2)/size)),min(n-1,int((R-y1)/size))+1):
    rect=box(-R+x*size,R-(y+1)*size,-R+(x+1)*size,R-y*size);fs=[]
    for i,(f,g) in enumerate(prepared):
     if not g.intersects(rect):continue
     clipped=g.intersection(rect).simplify(size/4096*.5,preserve_topology=True)
     if clipped.is_empty or clipped.geom_type=='GeometryCollection':continue
     fs.append({'geometry':mapping(clipped),'properties':{'id':f['properties']['id'],'type':f['properties']['type']},'id':i})
    if fs:
     data=mapbox_vector_tile.encode({'name':'atlas','features':fs},default_options={'quantize_bounds':rect.bounds,'extents':4096})
     entries.append((zxy_to_tileid(z,x,y),gzip.compress(data,mtime=0)))
 with (ROOT/'public/data'/name).open('wb') as out:
  writer=Writer(out)
  for id,data in sorted(entries):writer.write_tile(id,data)
  writer.finalize({'tile_type':TileType.MVT,'tile_compression':Compression.GZIP,'min_zoom':minzoom,'max_zoom':maxzoom,'min_lon_e7':int(bounds[0]*1e7),'min_lat_e7':int(bounds[1]*1e7),'max_lon_e7':int(bounds[2]*1e7),'max_lat_e7':int(bounds[3]*1e7),'center_zoom':minzoom,'center_lon_e7':int((bounds[0]+bounds[2])/2*1e7),'center_lat_e7':int((bounds[1]+bounds[3])/2*1e7)}, {'name':name,'format':'pbf','vector_layers':[{'id':'atlas','fields':{'id':'String','type':'String'},'minzoom':minzoom,'maxzoom':maxzoom}]})
 print(name,len(entries),'tiles')

if __name__=='__main__':
 features=json.loads((ROOT/'public/data/catalog.json').read_text())['features']
 build('world-lite.pmtiles',[f for f in features if f['properties']['type']=='country'],0,3,[-180,-85,180,85])
 build('game-world.pmtiles',[f for f in features if f['properties']['scope']=='world' and f['properties']['type']!='country'],0,3,[-180,-85,180,85])
 build('turkey.pmtiles',[f for f in features if f['properties']['type']=='province'],4,6,[25,35,45,43])
 build('game-turkey.pmtiles',[f for f in features if f['properties']['type']=='district'],4,6,[25,35,45,43])
