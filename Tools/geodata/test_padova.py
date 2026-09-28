import json
import unittest

import numpy as np
from pyproj import Geod
from shapely.geometry import Polygon, Point

import padova


class SurveyImportTests(unittest.TestCase):
    def test_courtyard_remains_empty(self):
        polygon = Polygon([(0, 0), (20, 0), (20, 20), (0, 20)],
                          holes=[[(5, 5), (5, 15), (15, 15), (15, 5)]])
        rings, indices = padova.triangulate(polygon)
        vertices = [v for r in rings for v in r]
        triangles = [Polygon([vertices[indices[i+j]] for j in range(3)]) for i in range(0, len(indices), 3)]
        self.assertAlmostEqual(sum(t.area for t in triangles), 300)
        self.assertTrue(all(polygon.covers(t.representative_point()) for t in triangles))
        self.assertTrue(all(t.intersection(Polygon(polygon.interiors[0])).area < 1e-9 for t in triangles))

    def test_concave_outline_has_upward_triangles(self):
        polygon = Polygon([(0, 0), (8, 0), (8, 2), (2, 2), (2, 8), (0, 8)])
        rings, indices = padova.triangulate(polygon)
        points = np.array([v for r in rings for v in r])
        for i in range(0, len(indices), 3):
            a, b, c = points[indices[i:i+3]]
            u, v = b-a, c-a
            self.assertLess(u[0]*v[1]-u[1]*v[0], 0)  # +Y in Unity X/Z plane

    def test_metric_projection_is_not_degrees_or_web_mercator(self):
        x, z = padova.local(*padova.ORIGIN)
        self.assertAlmostEqual(x, 0)
        self.assertAlmostEqual(z, 0)
        a = (11.872, 45.407)
        b = (11.876, 45.407)
        exact = Geod(ellps="GRS80").inv(*a, *b)[2]
        projected = np.linalg.norm(np.array(padova.local(*b))-padova.local(*a))
        self.assertLess(abs(exact-projected), 0.2)
        self.assertGreater(padova.local(*b)[0], padova.local(*a)[0])

    def test_source_snapshots_and_heights_are_preserved(self):
        manifest = json.loads((padova.DATA / "manifest.json").read_text())
        for layer in manifest['layers']:
            source = padova.DATA / 'source' / (layer['name'] + '.geojson')
            self.assertEqual(padova.digest(source.read_bytes()), layer['subsetSha256'])
        records = {r['id']: r['properties'] for r in json.loads((padova.DATA / 'source/UN_VOL.geojson').read_text())['features']}
        derived = json.loads((padova.DATA / 'derived/district.json').read_text())
        for m in derived['meshes']:
            self.assertTrue(all(np.isfinite([v['x'], v['y'], v['z']]).all() for v in m['vertices']))
            if m['layer'] != 'UN_VOL':
                continue
            source = records[m['sourceId']]
            self.assertEqual(m['eave'], source['UN_VOL_QGR'])
            self.assertEqual(m['height'], source['UN_VOL_AV'])
            self.assertEqual(m['walls'], source['UN_VOL_POR'] == '01')
            self.assertAlmostEqual(max(v['y'] for v in m['vertices']), source['UN_VOL_QGR']-padova.VERTICAL_ORIGIN, places=3)
            if source['UN_VOL_POR'] != '01':
                self.assertEqual(len(set(v['y'] for v in m['vertices'])), 1, 'Unsupported portico clearance must not be fabricated')


if __name__ == '__main__':
    unittest.main()
