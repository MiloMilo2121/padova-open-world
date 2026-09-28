using UnityEngine;

namespace Padova.Architecture
{
    /// <summary>Authored market-day dressing. Placements are gameplay context, not surveyed street objects.</summary>
    [ExecuteAlways,DefaultExecutionOrder(-400)]
    public sealed class Streetscape:MonoBehaviour
    {
        public PadovaCity City; public int Stalls,Lamps,Benches;
        Transform root;
        public static readonly Vector2[] MarketPositions={new(43,6),new(49,6),new(55,6),new(101,-4),new(107,-4),new(113,-4),new(42,-92),new(48,-92),new(54,-92),new(106,-84),new(112,-84),new(118,-84)};
        void OnEnable(){if(City && City.Data!=null)Build();}
        void OnDisable(){Clear();}
        void Clear(){if(!root)return;foreach(var f in root.GetComponentsInChildren<MeshFilter>())Dispose(f.sharedMesh);Dispose(root.gameObject);root=null;}
        static void Dispose(Object o){if(Application.isPlaying)Destroy(o);else DestroyImmediate(o);}
        public void Build()
        {
            Clear();if(!City || City.Data==null)return;
            root=new GameObject("Market day and street furniture"){hideFlags=HideFlags.DontSave}.transform;root.SetParent(transform,false);
            var sink=new MeshSink();Stalls=Lamps=Benches=0;
            Vector3 P(Vector2 v)=>new Vector3(v.x,City.Data.GroundAt(v.x,v.y)+.035f,v.y);
            foreach(var v in MarketPositions)
            {
                var p=P(v);WorldShapes.Stall(sink,p,Quaternion.identity,Stalls++);
                Box("Market table",p+Vector3.up*.52f,new Vector3(2.85f,1.04f,1.5f));
            }
            foreach(var v in new Vector2[]{new(25,14),new(125,10),new(22,-99),new(129,-95),new(-99,-11),new(-99,25),new(-53,29),new(-170,-117),new(195,-97),new(183,-55),new(-191,35)})
            {
                var p=P(v);WorldShapes.Lamp(sink,p);Box("Lamp",p+Vector3.up*1.9f,new Vector3(.3f,3.8f,.3f));Lamps++;
            }
            foreach(var v in new Vector2[]{new(28,14),new(122,10),new(-97,29),new(-52,26),new(-188,35),new(25,-99)})
            {var p=P(v);WorldShapes.Bench(sink,p,Quaternion.identity);Box("Bench",p+Vector3.up*.5f,new Vector3(1.8f,1,.65f));Benches++;}
            var go=new GameObject("Stalls, lamps and benches"){hideFlags=HideFlags.DontSave};go.transform.SetParent(root,false);
            go.AddComponent<MeshFilter>().sharedMesh=sink.ToMesh(go.name,City.Materials,out var materials);
            go.AddComponent<MeshRenderer>().sharedMaterials=materials;
        }
        void Box(string name,Vector3 p,Vector3 size){var go=new GameObject(name){hideFlags=HideFlags.DontSave,layer=9};go.transform.SetParent(root,false);go.transform.position=p;go.AddComponent<BoxCollider>().size=size;}
    }
}
