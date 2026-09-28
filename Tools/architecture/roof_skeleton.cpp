// Straight-skeleton hip roofs for surveyed footprints (offline data tool, not shipped).
// Input (stdin):  count, then per polygon: id ringCount, then per ring: n x0 y0 ... (outer CCW, holes CW).
// Output (stdout): per polygon "id faceCount" (or "id FAIL"), then per face: n x y t ... where t is the
// offset distance of the skeleton vertex (0 on the footprint outline). Roof height = t * tan(pitch).
// Build: clang++ -std=c++17 -O2 -I/opt/homebrew/include roof_skeleton.cpp -L/opt/homebrew/lib -lgmp -lmpfr
#include <CGAL/Exact_predicates_inexact_constructions_kernel.h>
#include <CGAL/Polygon_with_holes_2.h>
#include <CGAL/create_straight_skeleton_from_polygon_with_holes_2.h>
#include <iostream>
#include <iomanip>
#include <string>

typedef CGAL::Exact_predicates_inexact_constructions_kernel K;
typedef K::Point_2 Point;
typedef CGAL::Polygon_2<K> Polygon;
typedef CGAL::Polygon_with_holes_2<K> PolygonWithHoles;

int main()
{
    std::ios::sync_with_stdio(false);
    std::cout << std::setprecision(9);
    int count;
    std::cin >> count;
    for (int p = 0; p < count; ++p)
    {
        std::string id;
        int rings;
        std::cin >> id >> rings;
        PolygonWithHoles shape;
        for (int r = 0; r < rings; ++r)
        {
            int n;
            std::cin >> n;
            Polygon ring;
            for (int i = 0; i < n; ++i) { double x, y; std::cin >> x >> y; ring.push_back(Point(x, y)); }
            if (r == 0) shape = PolygonWithHoles(ring); else shape.add_hole(ring);
        }
        try
        {
            auto skeleton = CGAL::create_interior_straight_skeleton_2(shape);
            if (!skeleton) { std::cout << id << " FAIL\n"; continue; }
            std::cout << id << " " << skeleton->size_of_faces() << "\n";
            for (auto face = skeleton->faces_begin(); face != skeleton->faces_end(); ++face)
            {
                int n = 0;
                auto start = face->halfedge(), h = start;
                do { ++n; h = h->next(); } while (h != start);
                std::cout << n;
                h = start;
                do
                {
                    auto v = h->vertex();
                    std::cout << " " << v->point().x() << " " << v->point().y() << " " << v->time();
                    h = h->next();
                } while (h != start);
                std::cout << "\n";
            }
        }
        catch (...) { std::cout << id << " FAIL\n"; }
    }
    return 0;
}
