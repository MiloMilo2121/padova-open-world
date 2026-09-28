"""Check shipped expansion coordinates and elevations against original DBT records."""
import json,sys
from pathlib import Path
import shapefile
from shapely.geometry import shape
from shapely.geometry.polygon import orient
from shapely.ops import transform
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'Tools/geodata'))
import padova
plan=json.loads((ROOT/'Data/World/WorldPlan.json').read_text())
reader=shapefile.Reader(str(ROOT/'.context/geodata/padova-dbt/UN_VOL.shp'),encoding='latin1')
index={str(r.OBJECTID):(i,r.as_dict()) for i,r in enumerate(reader.iterRecords())}
vertices=0;ports=0
for unit in plan['units']:
    identifier=unit['id'].split(':')[1];base,_,part=identifier.partition('#');i,record=index[base]
    assert abs(unit['top']-(record['UN_VOL_QGR']-15))<.0011,identifier
    assert abs(unit['surveyHeight']-record['UN_VOL_AV'])<.0011,identifier
    if unit['suspended']:
        ports+=1;assert abs(unit['under']-unit['surveyBase']-record['UN_VOL_INH'])<.0021,identifier
    geometry=transform(lambda x,y,z=None:padova.local(x,y),shape(reader.shape(i).__geo_interface__))
    polygon=orient(list(padova.polygons(geometry))[int(part or 0)],1)
    rings=[list(polygon.exterior.coords)[:-1]]+[list(r.coords)[:-1] for r in polygon.interiors]
    assert [len(r) for r in rings]==unit['ringSizes'],identifier
    values=[value for ring in rings for xy in ring for value in xy[:2]]
    assert len(values)==len(unit['outline']),identifier
    assert max(abs(a-b) for a,b in zip(values,unit['outline']))<.00051,identifier
    vertices+=len(values)//2
report={'passed':True,'units':len(plan['units']),'vertices':vertices,'suspendedUnits':ports,'coordinateToleranceMetres':.00051,'source':'Original municipal UN_VOL shapefile'}
(ROOT/'.context/world/source-validation.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report))
