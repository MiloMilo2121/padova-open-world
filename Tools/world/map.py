"""Bake a north-up game map from the same survey polygons as the 3D city."""
import json,sys
from pathlib import Path
from PIL import Image, ImageDraw
from shapely.geometry import shape
from shapely.ops import transform
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Tools/geodata'))
import padova
world=json.loads((ROOT/'Data/World/WorldPlan.json').read_text())
core=json.loads((ROOT/'Assets/Geography/PadovaCentro/CityPlan.json').read_text())
size=(2400,2080)
im=Image.new('RGB',size,'#ece5d6');draw=ImageDraw.Draw(im)
def point(x,z):return ((x+1500)*.8,(1300-z)*.8)
for p in world['patches']:
    v=p['v'];tris=p['t'];pts=[point(*v[i:i+2]) for i in range(0,len(v),2)]
    color={'road':'#fff9e8','green':'#b1c5a1','water':'#89babe'}[p['kind']]
    for i in range(0,len(tris),3):draw.polygon([pts[k] for k in tris[i:i+3]],fill=color)
for road in world['roads']:
    v=road['points'];draw.line([point(*v[i:i+2]) for i in range(0,len(v),2)],fill='#fff9e8',width=3)
for unit in world['units']+core['units']:
    v=unit['outline'];start=0
    for ring,n in enumerate(unit['ringSizes']):
        pts=[point(*v[i*2:i*2+2]) for i in range(start,start+n)];start+=n
        draw.polygon(pts,fill='#bd9980' if ring==0 else '#ece5d6',outline='#aa8974' if ring==0 else '#ece5d6')
# Ragione is excluded from generic CityPlan units because it has its own model.
# Draw its original source units so the map retains its exact outline as well.
ragione_ids={50321,43684,47642,47695,47699,45910,45915,47702,45907}
for f in json.loads((ROOT/'Data/PadovaCentro/source/UN_VOL.geojson').read_text())['features']:
    if f['properties']['OBJECTID'] not in ragione_ids:continue
    geometry=transform(padova.local,shape(f['geometry']))
    for poly in padova.polygons(geometry):draw.polygon([point(*p[:2]) for p in poly.exterior.coords],fill='#aa8974')
im.save(ROOT/'Data/World/Map.png',optimize=True)
print('Map.png',size)
