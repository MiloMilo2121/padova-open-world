using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Padova.Gameplay;
using Padova.Geography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

public static class UpgradePadovaPresentation
{
    const string Folder="Assets/Architecture/PalazzoDellaRagione";
    const string ScenePath="Assets/Scenes/PadovaPlayable.unity";
    [Serializable] class GroundData { public float[] plane; public GroundPart[] parts; }
    [Serializable] class GroundPart { public string id; public Vector3[] vertices; public int[] triangles; }
    static SurveyMeshLibrary library;
    static Transform landmark;
    // Frame from the long edge of source unit UN_VOL:50321's minimum rotated rectangle.
    static readonly Vector3 Centre=new Vector3(68.63295f,0,-47.52084f);
    static readonly Vector3 Along=new Vector3(0.991859f,0,0.127337f);
    static readonly Vector3 North=new Vector3(-0.127337f,0,0.991859f);
    static Vector3 Point(float u,float y,float n)=>Centre+Along*u+North*n+Vector3.up*y;

    static void Ensure(string path)
    {
        if(AssetDatabase.IsValidFolder(path))return;
        Ensure(Path.GetDirectoryName(path).Replace('\\','/'));
        AssetDatabase.CreateFolder(Path.GetDirectoryName(path).Replace('\\','/'),Path.GetFileName(path));
    }
    static Mesh Mesh(string name,Vector3[] vertices,int[] triangles,Vector2[] uv=null)
    {
        var mesh=new Mesh{name=name,indexFormat=IndexFormat.UInt32};
        mesh.vertices=vertices;mesh.triangles=triangles;
        mesh.uv=uv??vertices.Select(v=>new Vector2(v.x,v.z)*0.5f).ToArray();
        mesh.RecalculateNormals();mesh.RecalculateTangents();mesh.RecalculateBounds();
        AssetDatabase.AddObjectToAsset(mesh,library);
        return mesh;
    }
    static GameObject Surface(string name,Mesh mesh,Material material,Transform parent,bool collider=false)
    {
        var go=new GameObject(name);go.transform.SetParent(parent,false);
        go.AddComponent<MeshFilter>().sharedMesh=mesh;
        go.AddComponent<MeshRenderer>().sharedMaterial=material;
        if(collider)go.AddComponent<MeshCollider>().sharedMesh=mesh;
        return go;
    }
    static void Band(string name,float bottom,float top,float setback,float left,float right,float photoTop,float photoBottom,Material material,float width=87)
    {
        // Photo is seen looking south: east is at image left. Retain original image pixels.
        var v=new[]{Point(width/2,bottom,setback),Point(-width/2,bottom,setback),Point(-width/2,top,setback),Point(width/2,top,setback)};
        var uv=new[]{new Vector2(left,1-photoBottom),new Vector2(right,1-photoBottom),new Vector2(right,1-photoTop),new Vector2(left,1-photoTop)};
        Surface(name,Mesh(name,v,new[]{0,2,1,0,3,2},uv),material,landmark);
    }
    static Material PhotoMaterial(string name,string path)
    {
        var material=AssetDatabase.LoadAssetAtPath<Material>(Folder+"/"+name+".mat");
        if(!material){material=new Material(Shader.Find("Universal Render Pipeline/Unlit"));AssetDatabase.CreateAsset(material,Folder+"/"+name+".mat");}
        material.SetTexture("_BaseMap",AssetDatabase.LoadAssetAtPath<Texture2D>(path));
        material.SetColor("_BaseColor",Color.white);material.SetFloat("_Cull",0);
        EditorUtility.SetDirty(material);return material;
    }
    static void ImportPhoto()
    {
        var target=Folder+"/RagioneNorth-Descouens-CCBYSA4.jpg";
        if(!File.Exists(target))File.Copy(".context/architecture/Exterior of Palazzo della Ragione (Padua).jpg",target);
        AssetDatabase.ImportAsset(target,ImportAssetOptions.ForceSynchronousImport);
        var importer=(TextureImporter)AssetImporter.GetAtPath(target);
        importer.maxTextureSize=4096;importer.wrapMode=TextureWrapMode.Clamp;importer.anisoLevel=8;
        importer.textureCompression=TextureImporterCompression.CompressedHQ;importer.SaveAndReimport();
    }
    public static object Build()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Stop Play Mode first.");
        if(UnityEngine.SceneManagement.SceneManager.GetActiveScene().isDirty)throw new InvalidOperationException("Save unsaved scene work first.");
        var scene=EditorSceneManager.OpenScene(ScenePath,OpenSceneMode.Single);
        Ensure(Folder);ImportPhoto();
        var path=Folder+"/ReferenceGeometry.asset";
        library=AssetDatabase.LoadAssetAtPath<SurveyMeshLibrary>(path);
        if(!library){library=ScriptableObject.CreateInstance<SurveyMeshLibrary>();AssetDatabase.CreateAsset(library,path);}
        foreach(var name in new[]{"Continuous mapped paving","Palazzo della Ragione | photographic elevations"})
        {
            var old=GameObject.Find(name);if(old)UnityEngine.Object.DestroyImmediate(old);
        }
        foreach(var old in AssetDatabase.LoadAllAssetsAtPath(path).OfType<Mesh>())UnityEngine.Object.DestroyImmediate(old,true);
        var ground=JsonConvert.DeserializeObject<GroundData>(File.ReadAllText("Data/PadovaCentro/derived/walk-surface.json"));
        var parent=new GameObject("Continuous mapped paving").transform;
        var paving=AssetDatabase.LoadAssetAtPath<Material>("Assets/Gameplay/PavingPreview.mat");
        foreach(var feature in UnityEngine.Object.FindObjectsByType<SurveyFeature>(FindObjectsSortMode.None))
        {
            if(feature.Layer=="UN_VOL" && feature.HasWalls)continue;
            // Unresolved portico caps are inspection aids, not floating architecture for the game.
            feature.GetComponent<Renderer>().enabled=false;
            feature.GetComponent<Collider>().enabled=false;
        }
        foreach(var part in ground.parts)
        {
            var go=Surface(part.id,Mesh(part.id,part.vertices,part.triangles),paving,parent,true);go.layer=8;
        }

        landmark=new GameObject("Palazzo della Ragione | photographic elevations").transform;
        var photo=PhotoMaterial("North elevation",Folder+"/RagioneNorth-Descouens-CCBYSA4.jpg");
        // Heights anchor to DBT eave/portico levels; plane depths are reference-derived, not a scan.
        Band("North shops - original photograph",1.4f,8.3f,22.8f,.020f,.918f,.714f,.842f,photo,92);
        Band("North loggia - original photograph",8.3f,18.7f,19.4f,.012f,.920f,.463f,.641f,photo,92);
        Band("North hall - original photograph",18.7f,24.0f,14.1f,.086f,.891f,.374f,.465f,photo,83);
        Band("North eave ornaments",23.95f,26.2f,14.15f,.086f,.891f,.318f,.374f,photo,83);
        var vertices=new List<Vector3>();var uvs=new List<Vector2>();var indices=new List<int>();
        const int cross=32,along=40;
        for(int i=0;i<=along;i++)
        {
            float u=-41.5f+83f*i/along;
            for(int j=0;j<=cross;j++)
            {
                float t=-Mathf.PI/2+Mathf.PI*j/cross;
                float n=13.8f*Mathf.Sin(t);float y=24+7.7f*Mathf.Cos(t);
                vertices.Add(Point(u,y,n));
                uvs.Add(new Vector2(Mathf.Lerp(.865f,.137f,i/(float)along),1-Mathf.Lerp(.262f,.340f,Mathf.Abs(Mathf.Sin(t)))));
                if(i<along&&j<cross)
                {
                    int k=i*(cross+1)+j;
                    indices.AddRange(new[]{k,k+cross+1,k+1,k+1,k+cross+1,k+cross+2});
                }
            }
        }
        Surface("Ship-hull roof envelope - photograph reference",Mesh("Roof envelope",vertices.ToArray(),indices.ToArray(),uvs.ToArray()),photo,landmark);
        var backing=new Material(Shader.Find("Universal Render Pipeline/Lit"));
        backing.SetColor("_BaseColor",new Color(.52f,.38f,.27f));backing.SetFloat("_Smoothness",.15f);
        var backingPath=Folder+"/Unresolved side elevations.mat";
        var existingBacking=AssetDatabase.LoadAssetAtPath<Material>(backingPath);
        if(existingBacking){UnityEngine.Object.DestroyImmediate(backing);backing=existingBacking;}else AssetDatabase.CreateAsset(backing,backingPath);
        backing.SetFloat("_Cull",0);EditorUtility.SetDirty(backing);
        // Close the reference volume in 3D; unobserved elevations remain plain, without invented windows.
        var bodyVerts=new List<Vector3>();var bodyTriangles=new List<int>();
        void Quad(Vector3 a,Vector3 b,Vector3 c,Vector3 d)
        {
            int k=bodyVerts.Count;bodyVerts.AddRange(new[]{a,b,c,d});
            bodyTriangles.AddRange(new[]{k,k+2,k+1,k,k+3,k+2});
        }
        Quad(Point(-41.5f,8.3f,-13.8f),Point(41.5f,8.3f,-13.8f),Point(41.5f,24,-13.8f),Point(-41.5f,24,-13.8f));
        Quad(Point(-41.5f,8.3f,13.8f),Point(-41.5f,8.3f,-13.8f),Point(-41.5f,24,-13.8f),Point(-41.5f,24,13.8f));
        Quad(Point(41.5f,8.3f,-13.8f),Point(41.5f,8.3f,13.8f),Point(41.5f,24,13.8f),Point(41.5f,24,-13.8f));
        Quad(Point(-41.5f,8.3f,13.8f),Point(41.5f,8.3f,13.8f),Point(41.5f,8.3f,-13.8f),Point(-41.5f,8.3f,-13.8f));
        Surface("Hall reference envelope",Mesh("Hall reference envelope",bodyVerts.ToArray(),bodyTriangles.ToArray()),backing,landmark);
        bodyVerts.Clear();bodyTriangles.Clear();
        foreach(float end in new[]{-41.5f,41.5f})
            for(int j=0;j<cross;j++)
            {
                float a=-Mathf.PI/2+Mathf.PI*j/cross,b=-Mathf.PI/2+Mathf.PI*(j+1)/cross;
                Quad(Point(end,24,13.8f*Mathf.Sin(a)),Point(end,24,13.8f*Mathf.Sin(b)),Point(end,24+7.7f*Mathf.Cos(b),13.8f*Mathf.Sin(b)),Point(end,24+7.7f*Mathf.Cos(a),13.8f*Mathf.Sin(a)));
            }
        Surface("Roof end envelopes",Mesh("Roof end envelopes",bodyVerts.ToArray(),bodyTriangles.ToArray()),backing,landmark);
        // Source-derived bodies stay as collision/registration evidence; covered renderers are hidden.
        string[] replaced={"43684","47695","47699","47702","45907","45910","45915","47642","50047","50054","50055","50310","50321","50331","50351"};
        foreach(var f in UnityEngine.Object.FindObjectsByType<SurveyFeature>(FindObjectsSortMode.None))
            if(replaced.Contains(f.SourceId.Replace("UN_VOL:","")))f.GetComponent<Renderer>().enabled=false;

        Physics.SyncTransforms();
        var motor=UnityEngine.Object.FindFirstObjectByType<ThirdPersonMotor>();
        float Height(float x,float z)=>ground.plane[0]*x+ground.plane[1]*z+ground.plane[2];
        motor.Spawn=new Vector3(80,Height(80,12)+.06f,12);
        motor.Goal=new Vector3(80,Height(80,-8),-8);
        motor.SpawnYaw=180;
        motor.Respawn();
        var marker=GameObject.Find("Piazza walk destination");marker.transform.position=motor.Goal+Vector3.up*.08f;
        // Give the saved Game/Scene preview an idle pose, so a stopped Editor does not show a T-pose.
        var idle=AssetDatabase.LoadAssetAtPath<AnimationClip>("Assets/Gameplay/idle.anim");
        idle.SampleAnimation(motor.Animator.gameObject,0.2f);
        var skin=motor.GetComponentInChildren<SkinnedMeshRenderer>();
        var pose=new Mesh();skin.BakeMesh(pose);
        float sole=pose.vertices.Min(v=>skin.transform.TransformPoint(v).y);
        motor.Animator.transform.position+=Vector3.up*(motor.Spawn.y-.025f-sole);
        UnityEngine.Object.DestroyImmediate(pose);
        var sunlight=RenderSettings.sun;
        if(sunlight){sunlight.shadowBias=.005f;sunlight.shadowNormalBias=.08f;}
        Camera.main.fieldOfView=65;
        Camera.main.transform.SetPositionAndRotation(motor.Spawn+new Vector3(0,1.0f,5.8f),Quaternion.Euler(-4,180,0));
        AssetDatabase.SaveAssets();EditorSceneManager.SaveScene(scene,ScenePath);
        return new{groundParts=ground.parts.Length,photographicLandmark=landmark.name,spawn=motor.Spawn.ToString(),note="Reference-derived facade layers and roof envelope; not a laser-scanned reconstruction."};
    }
}
