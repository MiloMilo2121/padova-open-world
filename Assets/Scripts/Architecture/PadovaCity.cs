using System.Collections.Generic;
using System.Diagnostics;
using UnityEngine;

namespace Padova.Architecture
{
    /// <summary>
    /// Builds central Padova from CityPlan.json at load time (and in the Editor for preview).
    /// Generated objects are never saved into the scene; only the compact plan is versioned.
    /// </summary>
    [ExecuteAlways, DefaultExecutionOrder(-500)]
    public sealed class PadovaCity : MonoBehaviour
    {
        public TextAsset Plan;
        public Material[] Materials = new Material[(int)Slot.Count];
        public float ChunkSize = 90;
        public bool PreviewInEditor = true;
        public int GroundLayer = 8, BuildingLayer = 9;
        public bool IncludeHorizon = true;

        [Header("Last build")]
        public int Units;
        public int Vertices;
        public int Triangles;
        public int Chunks;
        public float BuildMilliseconds;

        Transform root;
        public CityPlan Data { get; private set; }

        void OnEnable()
        {
            if (Application.isPlaying || PreviewInEditor) Build();
        }

        void OnDisable() => Clear();

        public void Clear()
        {
            if (root)
            {
                foreach (var mf in root.GetComponentsInChildren<MeshFilter>(true)) DestroyAsset(mf.sharedMesh);
                foreach (var mc in root.GetComponentsInChildren<MeshCollider>(true)) if (mc.sharedMesh) DestroyAsset(mc.sharedMesh);
                DestroyAsset(root.gameObject);
            }
            root = null;
            var stale = transform.Find("Generated city");
            if (stale) DestroyAsset(stale.gameObject);
        }

        static void DestroyAsset(Object o)
        {
            if (!o) return;
            if (Application.isPlaying) Destroy(o); else DestroyImmediate(o);
        }

        sealed class Chunk { public MeshSink Render = new MeshSink(); public MeshSink Low = new MeshSink(); public MeshSink Collide = new MeshSink(); }

        public void Build()
        {
            Clear();
            if (!Plan) return;
            var clock = Stopwatch.StartNew();
            Data = JsonUtility.FromJson<CityPlan>(Plan.text);
            var go = new GameObject("Generated city") { hideFlags = HideFlags.DontSave };
            root = go.transform;
            root.SetParent(transform, false);
            var chunks = new Dictionary<Vector2Int, Chunk>();
            Chunk At(float x, float z)
            {
                var key = new Vector2Int(Mathf.FloorToInt(x / ChunkSize), Mathf.FloorToInt(z / ChunkSize));
                if (!chunks.TryGetValue(key, out var c)) chunks[key] = c = new Chunk();
                return c;
            }

            Units = 0;
            var columnBoxes = new List<Bounds>();
            foreach (var unit in Data.units)
            {
                var chunk = At(unit.cx, unit.cz);
                if(!LandmarkBuilder.Replaces(unit))
                {
                    var style=LandmarkBuilder.Style(unit);
                    var fb = new FacadeBuilder(chunk.Render);
                    fb.Unit(unit, style);
                    columnBoxes.AddRange(fb.Columns);
                    CollisionWalls(chunk.Collide, unit);
                    SimpleUnit(chunk.Low,unit,style.Wall);
                }
                Units++;
            }
            foreach (var roof in Data.roofs)
            {
                if(LandmarkBuilder.Replaces(roof))continue;
                var c=At(roof.cx,roof.cz);Roof(c.Render,roof);Roof(c.Low,roof);
            }

            var ragioneSink = new MeshSink();
            var ragione = new RagioneBuilder(ragioneSink, Data.ragione);
            ragione.Build();
            var landmarkSink=new MeshSink();
            var landmarks=new LandmarkBuilder(landmarkSink,Data);landmarks.Build();

            Vertices = Triangles = 0;
            Chunks = 0;
            foreach (var pair in chunks)
            {
                var hi=Emit($"Block {pair.Key.x},{pair.Key.y}", pair.Value.Render, BuildingLayer, false);
                var lo=Emit($"Distant block {pair.Key.x},{pair.Key.y}",pair.Value.Low,BuildingLayer,false);
                if(hi && lo)
                {
                    var group=new GameObject($"Detail {pair.Key.x},{pair.Key.y}"){hideFlags=HideFlags.DontSave};group.transform.SetParent(root,false);
                    hi.transform.SetParent(group.transform,true);lo.transform.SetParent(group.transform,true);
                    var lod=group.AddComponent<LODGroup>();
                    lod.SetLODs(new[]{new LOD(.23f,new[]{hi.GetComponent<Renderer>()}),new LOD(.008f,new[]{lo.GetComponent<Renderer>()})});
                    lod.localReferencePoint=hi.GetComponent<Renderer>().bounds.center;lod.size=40;
                    lo.GetComponent<MeshRenderer>().shadowCastingMode=UnityEngine.Rendering.ShadowCastingMode.Off;
                }
                if (pair.Value.Collide.VertexCount > 0)
                {
                    var col = new GameObject($"Walls {pair.Key.x},{pair.Key.y}") { hideFlags = HideFlags.DontSave, layer = BuildingLayer };
                    col.transform.SetParent(root, false);
                    col.AddComponent<MeshCollider>().sharedMesh = pair.Value.Collide.ToMesh(col.name, null, out _, false);
                }
                Chunks++;
            }
            Emit("Palazzo della Ragione", ragioneSink, BuildingLayer, false);
            Emit("Clock, Capitanio, Duomo and Bo",landmarkSink,BuildingLayer,false);
            Emit("Clock passage floor",landmarks.Ground,GroundLayer,true);
            var colliders = new GameObject("Architecture colliders") { hideFlags = HideFlags.DontSave, layer = BuildingLayer };
            colliders.transform.SetParent(root, false);
            foreach (var (centre, size, rotation) in ragione.Colliders) Box(colliders.transform, centre, size, rotation);
            foreach (var (centre, size, rotation) in landmarks.Colliders) Box(colliders.transform, centre, size, rotation);
            foreach (var b in columnBoxes) Box(colliders.transform, b.center, b.size, Quaternion.identity);

            var ground = new MeshSink();
            Ground(ground);
            Emit("Streets and piazzas", ground, GroundLayer, true);
            if(IncludeHorizon)Horizon();
            BuildMilliseconds = (float)clock.Elapsed.TotalMilliseconds;
        }

        static void SimpleUnit(MeshSink sink,PlanUnit u,Slot wall)
        {
            int start=0;float lo=u.suspended?u.under:u.ground-.25f;
            foreach(int n in u.ringSizes)
            {
                for(int k=0;k<n;k++)
                {
                    int a=start+k,b=start+(k+1)%n;
                    var f=new Frame(new Vector2(u.outline[2*a],u.outline[2*a+1]),new Vector2(u.outline[2*b],u.outline[2*b+1]));
                    sink.Quad(wall,f.P(0,lo,0),f.P(f.L,lo,0),f.P(f.L,u.top,0),f.P(0,u.top,0),f.N,Vector2.zero,new Vector2(f.L,0),new Vector2(f.L,u.top-lo),new Vector2(0,u.top-lo));
                }
                start+=n;
            }
        }

        void Box(Transform parent, Vector3 centre, Vector3 size, Quaternion rotation)
        {
            var go = new GameObject("Support") { hideFlags = HideFlags.DontSave, layer = BuildingLayer };
            go.transform.SetParent(parent, false);
            go.transform.SetPositionAndRotation(centre, rotation);
            go.AddComponent<BoxCollider>().size = size;
        }

        GameObject Emit(string name, MeshSink sink, int layer, bool collider)
        {
            if (sink.VertexCount == 0) return null;
            var go = new GameObject(name) { hideFlags = HideFlags.DontSave, layer = layer };
            go.transform.SetParent(root, false);
            var mesh = sink.ToMesh(name, Materials, out var mats);
            mesh.hideFlags = HideFlags.DontSave;
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            mr.sharedMaterials = mats;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.On;
            if (collider) go.AddComponent<MeshCollider>().sharedMesh = mesh;
            Vertices += mesh.vertexCount;
            for (int i = 0; i < mesh.subMeshCount; i++) Triangles += (int)mesh.GetIndexCount(i) / 3;
            return go;
        }

        void CollisionWalls(MeshSink sink, PlanUnit u)
        {
            float lo = u.suspended ? u.under - 0.05f : u.ground - 1.5f;
            float hi = u.suspended ? u.under + 3.0f : Mathf.Min(u.top, u.ground + 12);
            int start = 0;
            foreach (int n in u.ringSizes)
            {
                for (int k = 0; k < n; k++)
                {
                    int a = start + k, b = start + (k + 1) % n;
                    var f = new Frame(new Vector2(u.outline[2 * a], u.outline[2 * a + 1]), new Vector2(u.outline[2 * b], u.outline[2 * b + 1]));
                    if (f.L < 0.01f) continue;
                    sink.Quad(Slot.Stone, f.P(0, lo, 0), f.P(f.L, lo, 0), f.P(f.L, hi, 0), f.P(0, hi, 0), f.N,
                        Vector2.zero, Vector2.zero, Vector2.zero, Vector2.zero);
                }
                start += n;
            }
            if (u.suspended && u.ceilingTris != null && u.ceilingTris.Length > 0)
            {
                var pts = new Vector3[u.ceiling.Length / 2];
                var uvs = new Vector2[pts.Length];
                for (int k = 0; k < pts.Length; k++) pts[k] = new Vector3(u.ceiling[2 * k], u.under, u.ceiling[2 * k + 1]);
                sink.Indexed(Slot.Stone, pts, uvs, u.ceilingTris, -1);
            }
        }

        void Roof(MeshSink sink, PlanRoof roof)
        {
            int n = roof.v.Length / 5;
            var pts = new Vector3[n];
            var uvs = new Vector2[n];
            for (int k = 0; k < n; k++)
            {
                pts[k] = new Vector3(roof.v[5 * k], roof.v[5 * k + 1], roof.v[5 * k + 2]);
                uvs[k] = new Vector2(roof.v[5 * k + 3], roof.v[5 * k + 4]);
            }
            var slot = roof.use == "church" || roof.use == "tower" ? Slot.Roof : Slot.Roof;
            sink.Indexed(slot, pts, uvs, roof.t, +1);
            n = roof.wv.Length / 5;
            if (n == 0) return;
            pts = new Vector3[n];
            uvs = new Vector2[n];
            for (int k = 0; k < n; k++)
            {
                pts[k] = new Vector3(roof.wv[5 * k], roof.wv[5 * k + 1], roof.wv[5 * k + 2]);
                uvs[k] = new Vector2(roof.wv[5 * k + 3], roof.wv[5 * k + 4]);
            }
            sink.Indexed(Slot.Wood, pts, uvs, roof.wt, 0);
        }

        void Ground(MeshSink sink)
        {
            foreach (var patch in Data.ground)
            {
                var slot = patch.mat switch
                {
                    "sidewalk" => Slot.Sidewalk,
                    "portico" => Slot.PorticoFloor,
                    "courtyard" => Slot.Courtyard,
                    _ => Slot.Trachyte
                };
                int n = patch.v.Length / 2;
                var pts = new Vector3[n];
                var uvs = new Vector2[n];
                for (int k = 0; k < n; k++)
                {
                    float x = patch.v[2 * k], z = patch.v[2 * k + 1];
                    pts[k] = new Vector3(x, Data.GroundAt(x, z) + patch.level, z);
                    uvs[k] = new Vector2(x, z);
                }
                // Tessellate long collision triangles without moving any source boundary.
                // Unity/PhysX warns above 500 m; 200 m also keeps queries well conditioned.
                void Triangle(Vector3 a,Vector3 b,Vector3 c,Vector2 ta,Vector2 tb,Vector2 tc)
                {
                    float ab=(a-b).sqrMagnitude,bc=(b-c).sqrMagnitude,ca=(c-a).sqrMagnitude;
                    if(Mathf.Max(ab,bc,ca)>40000)
                    {
                        if(bc>ab && bc>=ca){Triangle(b,c,a,tb,tc,ta);return;}
                        if(ca>ab && ca>bc){Triangle(c,a,b,tc,ta,tb);return;}
                        var m=(a+b)*.5f;var uv=(ta+tb)*.5f;
                        Triangle(a,m,c,ta,uv,tc);Triangle(m,b,c,uv,tb,tc);return;
                    }
                    sink.Tri(slot,a,b,c,Vector3.up,ta,tb,tc);
                }
                for(int i=0;i<patch.t.Length;i+=3){int a=patch.t[i],b=patch.t[i+1],ic=patch.t[i+2];Triangle(pts[a],pts[b],pts[ic],uvs[a],uvs[b],uvs[ic]);}
            }
            var c = Data.curbs;
            for (int k = 0; k + 5 < c.Length; k += 6)
            {
                var f = new Frame(new Vector2(c[k], c[k + 1]), new Vector2(c[k + 2], c[k + 3]));
                float g0 = Data.GroundAt(c[k], c[k + 1]), g1 = Data.GroundAt(c[k + 2], c[k + 3]);
                var p0 = new Vector3(c[k], g0 + c[k + 4], c[k + 1]);
                var p1 = new Vector3(c[k + 2], g1 + c[k + 4], c[k + 3]);
                var p2 = new Vector3(c[k + 2], g1 + c[k + 5], c[k + 3]);
                var p3 = new Vector3(c[k], g0 + c[k + 5], c[k + 1]);
                sink.Quad(Slot.Stone, p0, p1, p2, p3, f.N, new Vector2(0, 0), new Vector2(f.L, 0), new Vector2(f.L, 0.15f), new Vector2(0, 0.15f));
            }
        }

        void Horizon()
        {
            // A wide, non-colliding apron so views past the surveyed district do not end in a void.
            var sink = new MeshSink();
            float r = 2500, y = Data.GroundAt(0, 0) - 0.06f;
            sink.Quad(Slot.Trachyte, new Vector3(-r, y, -r), new Vector3(r, y, -r), new Vector3(r, y, r), new Vector3(-r, y, r), Vector3.up,
                new Vector2(-r, -r), new Vector2(r, -r), new Vector2(r, r), new Vector2(-r, r));
            var go = Emit("Horizon apron", sink, 0, false);
            if (go) go.GetComponent<MeshRenderer>().shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
        }
    }
}
