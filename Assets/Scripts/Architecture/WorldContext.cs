using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace Padova.Architecture
{
    [Serializable] public sealed class WorldPlan
    {
        public int version;public float[] extent,plane,coreExtent,terrain;public int terrainNX,terrainNZ;public float terrainStep;public WorldUnit[] units;public WorldPatch[] patches;
        public WorldTree[] trees;public WorldRoad[] roads;public WorldPlace[] landmarks;public string attribution,detailStatus;
        public float GroundAt(float x,float z)
        {
            float original=plane[0]*x+plane[1]*z+plane[2];if(terrain==null||terrain.Length==0)return original;
            float fx=Mathf.Clamp((x-extent[0])/terrainStep,0,terrainNX-1.001f),fz=Mathf.Clamp((z-extent[1])/terrainStep,0,terrainNZ-1.001f);
            int i=(int)fx,j=(int)fz;float a=fx-i,b=fz-j;
            float h=Mathf.Lerp(Mathf.Lerp(terrain[j*terrainNX+i],terrain[j*terrainNX+i+1],a),Mathf.Lerp(terrain[(j+1)*terrainNX+i],terrain[(j+1)*terrainNX+i+1],a),b);
            float dx=Mathf.Max(coreExtent[0]-x,0,x-coreExtent[2]),dz=Mathf.Max(coreExtent[1]-z,0,z-coreExtent[3]);float blend=Mathf.Clamp01(Mathf.Sqrt(dx*dx+dz*dz)/120);blend=blend*blend*(3-2*blend);
            return Mathf.Lerp(original,h,blend);
        }
    }
    [Serializable] public sealed class WorldUnit
    {
        public string id;public float ground,top,under,cx,cz,area,surveyHeight,surveyBase,surveyClearance;public bool suspended;
        public float[] outline,cap,roof;public int[] ringSizes,capTris,roofTris;
    }
    [Serializable] public sealed class WorldPatch {public string id,kind;public float[] v;public int[] t;}
    [Serializable] public sealed class WorldTree {public float x,z,height;public string source;}
    [Serializable] public sealed class WorldRoad {public string id,name;public float[] points;}
    [Serializable] public sealed class WorldPlace {public string name,source;public float x,z;}
    /// <summary>Survey records superseded by Blender landmark models (Assets/Art/Landmarks/Landmarks.json).</summary>
    [Serializable] public sealed class LandmarkManifest
    {
        public string[] replacedUnits=new string[0],replacedPatches=new string[0];public float[] ownGround=new float[0];public WorldPlace[] places=new WorldPlace[0];public LandmarkModel[] models=new LandmarkModel[0];
        public bool OwnsGround(float x0,float z0,float x1,float z1)
        {
            for(int i=0;i+3<ownGround.Length;i+=4)if(x0>=ownGround[i]-.01f&&z0>=ownGround[i+1]-.01f&&x1<=ownGround[i+2]+.01f&&z1<=ownGround[i+3]+.01f)return true;
            return false;
        }
    }
    [Serializable] public sealed class LandmarkModel {public string name,asset;public float[] anchor;}

    [ExecuteAlways,DefaultExecutionOrder(-450)]
    public sealed class WorldContext:MonoBehaviour
    {
        public TextAsset Plan,Landmarks;public PadovaCity City;public float ViewDistance=1200;public float CollisionDistance=330;
        public int Buildings,Chunks;public float BuildMilliseconds;
        public WorldPlan Data{get;private set;}
        Transform root;readonly List<(Vector3 point,GameObject visual,Collider collider)> chunks=new();
        float nextUpdate;
        void OnEnable(){if(Plan)Build();}
        void OnDisable(){Clear();}
        static void Dispose(UnityEngine.Object obj){if(!obj)return;if(Application.isPlaying)Destroy(obj);else DestroyImmediate(obj);}
        void Clear()
        {
            if(root){foreach(var f in root.GetComponentsInChildren<MeshFilter>(true))Dispose(f.sharedMesh);Dispose(root.gameObject);}
            root=null;chunks.Clear();
        }
        sealed class Block {public MeshSink Mesh=new();public Vector2 Centre;}
        public void Build()
        {
            Clear();if(!Plan)return;
            if(!City)City=UnityEngine.Object.FindFirstObjectByType<PadovaCity>();
            if(!City || City.Materials.Length<(int)Slot.Count)return;
            var watch=System.Diagnostics.Stopwatch.StartNew();Data=JsonUtility.FromJson<WorldPlan>(Plan.text);
            var manifest=Landmarks?JsonUtility.FromJson<LandmarkManifest>(Landmarks.text):new LandmarkManifest();
            var replacedUnits=new HashSet<string>(manifest.replacedUnits);var replacedPatches=new HashSet<string>(manifest.replacedPatches);
            if(manifest.places.Length>0){var places=new List<WorldPlace>(Data.landmarks);places.AddRange(manifest.places);Data.landmarks=places.ToArray();}
            root=new GameObject("Generated surrounding Padova"){hideFlags=HideFlags.DontSave}.transform;root.SetParent(transform,false);
            var blocks=new Dictionary<Vector2Int,Block>();
            Block At(float x,float z)
            {
                var key=new Vector2Int(Mathf.FloorToInt(x/150),Mathf.FloorToInt(z/150));
                if(!blocks.TryGetValue(key,out var b))blocks[key]=b=new Block{Centre=new Vector2((key.x+.5f)*150,(key.y+.5f)*150)};
                return b;
            }
            Buildings=0;
            foreach(var unit in Data.units)
            {
                if(replacedUnits.Contains(unit.id))continue;
                Unit(At(unit.cx,unit.cz).Mesh,unit);Buildings++;
            }
            foreach(var pair in blocks)
            {
                var b=pair.Value;var go=Emit("Surrounding block "+pair.Key,b.Mesh,9,true);
                chunks.Add((new Vector3(b.Centre.x,0,b.Centre.y),go,go.GetComponent<Collider>()));
            }
            Chunks=blocks.Count;
            var patches=new Dictionary<string,MeshSink>();
            foreach(var p in Data.patches)
            {
                if(replacedPatches.Contains(p.id))continue;
                if(!patches.TryGetValue(p.kind,out var sink))patches[p.kind]=sink=new MeshSink();
                var slot=p.kind=="road"?Slot.Asphalt:p.kind=="water"?Slot.ClockBlue:Slot.Foliage;
                var v=new Vector3[p.v.Length/2];var uv=new Vector2[v.Length];
                float offset=p.kind=="road"?.015f:p.kind=="water"?-.06f:.02f;
                for(int i=0;i<v.Length;i++){v[i]=new Vector3(p.v[i*2],Data.GroundAt(p.v[i*2],p.v[i*2+1])+offset,p.v[i*2+1]);uv[i]=new Vector2(v[i].x,v[i].z);}
                sink.Indexed(slot,v,uv,p.t,1);
            }
            foreach(var p in patches)Emit("Mapped "+p.Key,p.Value,8,false);
            var baseGround=new MeshSink();float x0=Data.extent[0],z0=Data.extent[1],x1=Data.extent[2],z1=Data.extent[3];
            Vector3 P(float x,float z)=>new Vector3(x,Data.GroundAt(x,z)-.025f,z);
            // Surrounding ground is a fitted-level context surface; original road/green/water plans overlay it.
            void GroundRect(float a,float b,float c,float d){if(c<=a||d<=b||manifest.OwnsGround(a,b,c,d))return;baseGround.Quad(Slot.Courtyard,P(a,b),P(c,b),P(c,d),P(a,d),Vector3.up,new Vector2(a,b),new Vector2(c,b),new Vector2(c,d),new Vector2(a,d));}
            var core=City.Data.extent;
            for(float x=x0;x<x1;x+=25)for(float z=z0;z<z1;z+=25)
            {
                float right=Mathf.Min(x+25,x1),top=Mathf.Min(z+25,z1);
                GroundRect(x,z,Mathf.Min(right,core[0]),top);GroundRect(Mathf.Max(x,core[2]),z,right,top);
                float a=Mathf.Max(x,core[0]),b=Mathf.Min(right,core[2]);
                GroundRect(a,z,b,Mathf.Min(top,core[1]));GroundRect(a,Mathf.Max(z,core[3]),b,top);
            }
            Emit("Surrounding ground",baseGround,8,true);
            var treeBlocks=new Dictionary<Vector2Int,MeshSink>();
            foreach(var tree in Data.trees)
            {
                var key=new Vector2Int(Mathf.FloorToInt(tree.x/150),Mathf.FloorToInt(tree.z/150));
                if(!treeBlocks.TryGetValue(key,out var sink))treeBlocks[key]=sink=new MeshSink();
                WorldShapes.Tree(sink,new Vector3(tree.x,Data.GroundAt(tree.x,tree.z)+.03f,tree.z),tree.height);
            }
            foreach(var b in treeBlocks)
            {
                var go=Emit("Mapped green area trees "+b.Key,b.Value,0,false);
                chunks.Add((new Vector3((b.Key.x+.5f)*150,0,(b.Key.y+.5f)*150),go,null));
            }
            if(Camera.main)RefreshVisibility(Camera.main.transform.position);
            BuildMilliseconds=(float)watch.Elapsed.TotalMilliseconds;
        }
        void Unit(MeshSink s,WorldUnit u)
        {
            var slot=new[]{Slot.Plaster0,Slot.Plaster3,Slot.Plaster9}[(int)(UnitStyle.Hash(u.id)%3)];
            float bottom=u.suspended?u.under:u.surveyBase;
            bool windows=Mathf.Abs(u.cx)<750 && Mathf.Abs(u.cz)<650;
            int start=0;
            foreach(int n in u.ringSizes)
            {
                for(int k=0;k<n;k++)
                {
                    int a=start+k,b=start+(k+1)%n;var f=new Frame(new Vector2(u.outline[2*a],u.outline[2*a+1]),new Vector2(u.outline[2*b],u.outline[2*b+1]));
                    s.Quad(slot,f.P(0,bottom,0),f.P(f.L,bottom,0),f.P(f.L,u.top,0),f.P(0,u.top,0),f.N,Vector2.zero,new Vector2(f.L,0),new Vector2(f.L,u.top-bottom),new Vector2(0,u.top-bottom));
                    if(windows && f.L>2.4f)
                        for(float x=1.2f;x<f.L-.5f;x+=3.4f)for(float y=bottom+2;y<u.top-2;y+=3.3f)
                            s.Quad(Slot.Glass,f.P(x-.45f,y,.015f),f.P(x+.45f,y,.015f),f.P(x+.45f,y+1.4f,.015f),f.P(x-.45f,y+1.4f,.015f),f.N,Vector2.zero,Vector2.right,Vector2.one,Vector2.up);
                }
                start+=n;
            }
            if(u.roof!=null && u.roof.Length>0)
            {
                var v=new Vector3[u.roof.Length/5];var uv=new Vector2[v.Length];
                for(int i=0;i<v.Length;i++){v[i]=new Vector3(u.roof[i*5],u.roof[i*5+1],u.roof[i*5+2]);uv[i]=new Vector2(u.roof[i*5+3],u.roof[i*5+4]);}
                s.Indexed(Slot.Roof,v,uv,u.roofTris,1);
            }
            if(u.suspended)
            {
                var v=new Vector3[u.cap.Length/2];var uv=new Vector2[v.Length];
                for(int i=0;i<v.Length;i++){v[i]=new Vector3(u.cap[2*i],u.under,u.cap[2*i+1]);uv[i]=new Vector2(v[i].x,v[i].z);}
                s.Indexed(Slot.Ceiling,v,uv,u.capTris,-1);
            }
        }
        GameObject Emit(string name,MeshSink sink,int layer,bool collider)
        {
            var go=new GameObject(name){hideFlags=HideFlags.DontSave,layer=layer};go.transform.SetParent(root,false);
            var mesh=sink.ToMesh(name,City.Materials,out var mats);mesh.hideFlags=HideFlags.DontSave;
            go.AddComponent<MeshFilter>().sharedMesh=mesh;var renderer=go.AddComponent<MeshRenderer>();renderer.sharedMaterials=mats;
            renderer.shadowCastingMode=ShadowCastingMode.Off;renderer.receiveShadows=false;
            if(collider)go.AddComponent<MeshCollider>().sharedMesh=mesh;
            return go;
        }
        public void RefreshVisibility(Vector3 eye)
        {
            eye.y=0;
            foreach(var c in chunks)
            {
                float d=Vector3.Distance(eye,c.point);
                if(c.visual)c.visual.GetComponent<Renderer>().enabled=d<ViewDistance;
                if(c.collider)c.collider.enabled=d<CollisionDistance;
            }
        }
        void Update()
        {
            if(Time.realtimeSinceStartup<nextUpdate)return;nextUpdate=Time.realtimeSinceStartup+.35f;
            if(Camera.main)RefreshVisibility(Camera.main.transform.position);
        }
    }
}
