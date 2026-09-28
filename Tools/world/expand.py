"""Create a surrounding Padova context from the existing, licensed municipal survey.
Core CityPlan is untouched. Outer detail is deliberately lower; coordinates, heights and
portico clearances remain source values. CGAL roof pitch and facade detailing are typology.
"""
import sys,json,hashlib,math
from pathlib import Path
import numpy as np
import shapefile
from shapely.geometry import shape,box,Point
from shapely.geometry.polygon import orient
from shapely.ops import transform,unary_union
ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/'Tools/geodata'),str(ROOT/'Tools/architecture')]
import padova
import plan_city as pc

SURVEY=ROOT/'.context/geodata/padova-dbt'
OUT=ROOT/'Data/World'
OUT.mkdir(parents=True,exist_ok=True)
EXTENT=(-1500,-1300,1500,1300)
REGION=box(*EXTENT)
core=json.loads((ROOT/'Assets/Geography/PadovaCentro/CityPlan.json').read_text())
core_ids={u['id'] for u in core['units']}|set(sum(pc.RAGIONE.values(),[]))
core_rect=box(*core['extent'])
# Query shapefiles in their native RDN2008 longitude/latitude CRS.
from pyproj import Transformer
back=Transformer.from_crs(7791,6706,always_xy=True)
lon0,lat0=back.transform(padova.E0+EXTENT[0]-100,padova.N0+EXTENT[1]-100)
lon1,lat1=back.transform(padova.E0+EXTENT[2]+100,padova.N0+EXTENT[3]+100)
records=[]
rejected=[]
def read(layer):
    reader=shapefile.Reader(str(SURVEY/(layer+'.shp')),encoding='latin1')
    for record in reader.iterShapeRecords(bbox=(lon0,lat0,lon1,lat1)):
        g=transform(lambda x,y,z=None:padova.local(x,y),shape(record.shape.__geo_interface__))
        if g.is_valid and g.intersects(REGION):yield record,g

survey=list(read('UN_VOL'))
# The central fitted plane must not be extrapolated for kilometres. Use a smooth
# local interpolation of DBT base elevations (QGR - AV), joined to the existing core.
samples=[]
for rec,geom in survey:
    p=rec.record.as_dict();base=p['UN_VOL_QGR']-p['UN_VOL_AV']-15
    if p['UN_VOL_POR']=='01' and 3<p['UN_VOL_AV']<80 and -9<base<9:
        c=geom.representative_point();samples.append((c.x,c.y,base))
samples=np.array(samples);step=50;nx=61;nz=53;terrain=[]
for j in range(nz):
    z=EXTENT[1]+j*step
    for i in range(nx):
        x=EXTENT[0]+i*step;d=(samples[:,0]-x)**2+(samples[:,1]-z)**2
        nearest=np.argpartition(d,23)[:24];terrain.append(round(float(np.median(samples[nearest,2])),3))
def ground(x,z):
    fx=np.clip((x-EXTENT[0])/step,0,nx-1.001);fz=np.clip((z-EXTENT[1])/step,0,nz-1.001)
    i,j=int(fx),int(fz);a,b=fx-i,fz-j
    height=(terrain[j*nx+i]*(1-a)+terrain[j*nx+i+1]*a)*(1-b)+(terrain[(j+1)*nx+i]*(1-a)+terrain[(j+1)*nx+i+1]*a)*b
    c=core['extent'];distance=math.hypot(max(c[0]-x,0,x-c[2]),max(c[1]-z,0,z-c[3]))
    mix=min(1,distance/120);mix=mix*mix*(3-2*mix)
    return pc.ground(x,z)*(1-mix)+height*mix
units=[]; shapes=[]; poly_by_id={}
for rec,geom in survey:
    p=rec.record.as_dict();fid='UN_VOL:'+str(p['OBJECTID'])
    if fid in core_ids:continue
    top=p['UN_VOL_QGR']-15
    if not(0<p['UN_VOL_AV']<150 and top>0):continue
    for i,poly in enumerate(padova.polygons(geom)):
        if poly.area<3:continue
        c=poly.representative_point()
        if not REGION.contains(c):continue
        fidpart=fid+('' if i==0 else '#'+str(i))
        poly=orient(poly,1)
        rings=pc.rings(poly);g=ground(c.x,c.y)
        base=top-p['UN_VOL_AV'];inh=p['UN_VOL_INH'];suspended=p['UN_VOL_POR'] in ['02','03'] and 2<inh<p['UN_VOL_AV']-1.5
        coords,idx=pc.earcut(poly)
        unit={'id':fidpart,'ground':round(g,3),'top':round(top,3),'under':round(base+inh,3) if suspended else 0,'suspended':bool(suspended),
              'surveyHeight':p['UN_VOL_AV'],'surveyBase':round(base,3),'surveyClearance':inh,
              'cx':round(c.x,3),'cz':round(c.y,3),'area':round(poly.area,3),
              'outline':[round(float(v),3) for ring in rings for xy in ring for v in xy[:2]],'ringSizes':[len(r) for r in rings],
              'cap':[round(float(v),3) for xy in coords for v in xy], 'capTris':idx}
        units.append(unit);poly_by_id[fidpart]=poly
        # Keep distant roofs cheap and retain original footprint corners. No fabricated heights.
        simplified=orient(poly.simplify(.10,preserve_topology=True),1)
        if simplified.is_valid:shapes.append((str(len(units)-1),simplified))
print('surrounding units',len(units),flush=True)
skels=pc.run_skeletons(shapes)
for key,poly in shapes:
    u=units[int(key)];faces=skels.get(key)
    if not faces:rejected.append(u['id']);continue
    v,t,_,_=pc.roof_mesh(poly,faces,u['top'],pc.ROOF_SLOPE,lambda a,b:False)
    u['roof']=[round(float(x),3) for x in v];u['roofTris']=t

patches=[];trees=[]
def add_patch(kind,fid,geom):
    for poly in padova.polygons(geom.intersection(REGION).difference(core_rect)):
        if poly.area<3:continue
        coords,idx=pc.earcut(orient(poly,1))
        patches.append({'id':fid,'kind':kind,'v':[round(float(x),3) for xy in coords for x in xy], 't':idx})

for layer,kind in [('AR_STR','road'),('AR_VRD','green'),('AB_CDA','water')]:
    for rec,geom in read(layer):
        # These area shapefiles lack unique OBJECTID values; stable source row
        # identities are tied to the exact shapefile hashes in the manifest.
        fid=layer+':'+str(rec.record.oid)
        add_patch(kind,fid,geom)
        if kind=='green' and geom.area>45:
            poly=max(padova.polygons(geom),key=lambda p:p.area)
            seed=int(hashlib.sha256((layer+':'+str(rec.record.oid)).encode()).hexdigest()[:8],16)
            rng=np.random.default_rng(seed)
            inside=poly.buffer(-2)
            if inside.is_empty:continue
            minx,minz,maxx,maxz=inside.bounds
            count=min(14,max(1,int(poly.area/160)))
            for _ in range(count*4):
                x,z=rng.uniform(minx,maxx),rng.uniform(minz,maxz)
                if inside.contains(Point(x,z)) and REGION.contains(Point(x,z)):
                    if all((x-t['x'])**2+(z-t['z'])**2>36 for t in trees[-100:]):
                        trees.append({'x':round(x,2),'z':round(z,2),'source':fid,'height':round(float(rng.uniform(4,8)),2)})
                        count-=1
                if count<=0:break

network=json.loads((ROOT/'.context/world/street-network.json').read_text())
roads=[]
for f in network['features']:
    geom=transform(lambda x,y,z=None:padova.local(x,y),shape(f['geometry']))
    for line in getattr(geom,'geoms',[geom]):
        if not line.intersects(REGION):continue
        coords=list(line.coords)
        roads.append({'id':f['id'],'name':f['properties'].get('nome',''),
                      'points':[round(float(v),3) for p in coords for v in p[:2]]})

landmarks=[]
names=['Palazzo della Ragione',"Torre dell' orologio",'Duomo di Padova','Battistero','Palazzo del Bo','Palazzo delle Debite','Loggia della Gran Guardia']
for name in names:
    group=[u for u in core['units'] if u['name']==name]
    if name=='Palazzo della Ragione':x,z=core['ragione']['cx'],core['ragione']['cz']
    elif name=="Torre dell' orologio":
        tower=next(u for u in core['units'] if u['id']=='UN_VOL:42159');x,z=tower['cx'],tower['cz']
    else:
        if not group:continue
        biggest=max(group,key=lambda u:u['area']);x,z=biggest['cx'],biggest['cz']
    landmarks.append({'name':name,'x':x,'z':z,'source':'DBT/OSM'})
capitanio=next(u for u in core['units'] if u['id']=='UN_VOL:44273')
landmarks.append({'name':'Palazzo del Capitanio','x':capitanio['cx'],'z':capitanio['cz'],'source':'Municipal reference; DBT UN_VOL:44273'})
plan={'version':2,'extent':EXTENT,'plane':core['plane'],'coreExtent':core['extent'],'terrain':terrain,'terrainStep':step,'terrainNX':nx,'terrainNZ':nz,'units':units,'patches':patches,'trees':trees,'roads':roads,'landmarks':landmarks,
      'attribution':'Comune di Padova / Regione del Veneto DBT 2007, IODL 2.0. Road network: Regione Veneto, IODL 2.0. Names: OSM contributors, ODbL.',
      'detailStatus':'Survey footprints, eave and clearance values. Roofs and tree placement within mapped green areas are typology.'}
(OUT/'WorldPlan.json').write_text(json.dumps(plan,separators=(',',':'),ensure_ascii=False)+'\n')
report={'units':len(units),'patches':len(patches),'trees':len(trees),'roadSegments':len(roads),'roofFailures':rejected,'extent':EXTENT,
        'sourceFiles':{f:hashlib.sha256((SURVEY/(f+'.shp')).read_bytes()).hexdigest() for f in ['UN_VOL','AR_STR','AR_VRD','AB_CDA']}}
(OUT/'manifest.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:v for k,v in report.items() if k not in ['sourceFiles','roofFailures']},'roof failures',len(rejected),flush=True)
