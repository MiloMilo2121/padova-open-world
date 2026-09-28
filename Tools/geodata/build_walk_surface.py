"""Dissolve overlapping road classes and fit a continuous navigation surface to source heights.

This repairs the *rendering interpretation*, not the original DBT. It preserves the mapped
plan boundary; fitted elevations are an explicit approximation until a ground survey exists.
"""
import json
import numpy as np
from shapely.geometry import shape, box
from shapely.ops import transform, unary_union
import padova

regions=[]
heights=[]
clip=transform(padova.local,box(*padova.BOUNDS))
for layer in ['AR_STR','AC_PED','AR_MARC']:
    source=json.loads((padova.DATA/'source'/f'{layer}.geojson').read_text())
    for feature in source['features']:
        geom=transform(padova.local,shape(feature['geometry']))
        if not geom.is_valid:continue
        regions.append(geom.intersection(clip))
        if layer=='AR_MARC':
            for poly in padova.polygons(geom):
                for ring in [poly.exterior,*poly.interiors]:
                    heights.extend(ring.coords)
p=np.unique(np.array(heights),axis=0)
p=p[(np.abs(p[:,0])<350)&(np.abs(p[:,1])<250)&(p[:,2]>12)&(p[:,2]<21)]
A=np.c_[p[:,0],p[:,1],np.ones(len(p))]
b=p[:,2]-padova.VERTICAL_ORIGIN
coeff=np.linalg.lstsq(A,b,rcond=None)[0]
for _ in range(4):
    residual=np.abs(np.sum(A*coeff,axis=1)-b)
    mask=residual<max(.25,float(np.median(residual))*2.5)
    coeff=np.linalg.lstsq(A[mask],b[mask],rcond=None)[0]
merged=unary_union(regions)
parts=[]
area=0
for i,poly in enumerate(padova.polygons(merged)):
    rings,indices=padova.triangulate(poly)
    verts=[]
    for ring in rings:
        for x,z,*_ in ring:
            verts.append({'x':round(x,4),'y':round(float(coeff[0]*x+coeff[1]*z+coeff[2]),4),'z':round(z,4)})
    parts.append({'id':f'walk-{i}','vertices':verts,'triangles':indices})
    area+=poly.area
out={'method':'Dissolved source plan geometry; robust plane fitted to sidewalk elevation samples',
     'heightIsApproximation':True,'plane':coeff.tolist(),'fitSamples':int(mask.sum()),
     'fitRmseMetres':float(np.sqrt(np.mean((np.sum(A[mask]*coeff,axis=1)-b[mask])**2))),
     'sourceArea':merged.area,'triangulatedArea':area,'parts':parts}
assert abs(area-merged.area)<.001
padova.write_json(padova.DATA/'derived/walk-surface.json',out)
print({k:v for k,v in out.items() if k!='parts'},'parts',len(parts))
