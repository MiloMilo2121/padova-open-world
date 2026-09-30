using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using Padova.Architecture;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

/// <summary>Imports the Blender landmark FBX files (Tools/blender/build_landmarks.py), remaps their
/// materials onto the game's existing Padova materials and places them at their survey anchors.</summary>
public static class BuildLandmarks
{
    const string Folder="Assets/Art/Landmarks";
    const string Manifest=Folder+"/Landmarks.json";
    static readonly string[] MaterialFolders={"Assets/Art/Padova/Materials",Folder+"/Materials"};

    static Material Ensure(string name,Func<Material> make)
    {
        string path=Folder+"/Materials/"+name+".mat";
        var mat=AssetDatabase.LoadAssetAtPath<Material>(path);
        if(mat)return mat;
        if(!AssetDatabase.IsValidFolder(Folder+"/Materials"))AssetDatabase.CreateFolder(Folder,"Materials");
        mat=make();mat.name=name;AssetDatabase.CreateAsset(mat,path);return mat;
    }
    static void ExtraMaterials()
    {
        var lit=Shader.Find("Universal Render Pipeline/Lit");
        Ensure("Canal water",()=>{var m=new Material(lit);m.SetColor("_BaseColor",new Color(.13f,.2f,.19f));m.SetFloat("_Smoothness",.9f);m.SetFloat("_Metallic",0);return m;});
        Ensure("Bronze",()=>{var m=new Material(lit);m.SetColor("_BaseColor",new Color(.25f,.2f,.14f));m.SetFloat("_Smoothness",.5f);m.SetFloat("_Metallic",.8f);return m;});
        string tex=Folder+"/Textures/RingBalustrade.png";
        var ti=(TextureImporter)AssetImporter.GetAtPath(tex);
        if(ti&&(!ti.alphaIsTransparency||ti.wrapMode!=TextureWrapMode.Repeat)){ti.alphaIsTransparency=true;ti.wrapMode=TextureWrapMode.Repeat;ti.SaveAndReimport();}
        Ensure("Ring balustrade",()=>{var m=new Material(AssetDatabase.LoadAssetAtPath<Material>("Assets/Art/Padova/Materials/Balustrade.mat"));m.mainTexture=AssetDatabase.LoadAssetAtPath<Texture2D>(tex);m.SetTexture("_BaseMap",m.mainTexture);return m;});
    }
    static Material Find(string name)
    {
        string clean=name.Split('.')[0];
        foreach(var folder in MaterialFolders){var m=AssetDatabase.LoadAssetAtPath<Material>(folder+"/"+clean+".mat");if(m)return m;}
        return null;
    }

    public static object Import()
    {
        ExtraMaterials();
        var report=new List<object>();
        foreach(var fbx in Directory.GetFiles(Folder,"*.fbx"))
        {
            string path=fbx.Replace('\\','/');
            AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceSynchronousImport);
            var mi=(ModelImporter)AssetImporter.GetAtPath(path);
            mi.bakeAxisConversion=true;mi.globalScale=1;mi.useFileScale=true;mi.addCollider=false;mi.isReadable=true;
            mi.meshCompression=ModelImporterMeshCompression.Off;mi.indexFormat=ModelImporterIndexFormat.Auto;
            mi.importNormals=ModelImporterNormals.Import;mi.importAnimation=false;mi.importCameras=false;mi.importLights=false;
            mi.materialImportMode=ModelImporterMaterialImportMode.ImportStandard;mi.materialLocation=ModelImporterMaterialLocation.InPrefab;
            var missing=new List<string>();
            // Names from both the current remaps and embedded materials: re-running must stay idempotent
            // (remapped materials are no longer sub-assets, so reading only sub-assets would drop them).
            var names=mi.GetExternalObjectMap().Keys.Where(k=>k.type==typeof(Material)).Select(k=>k.name)
                .Concat(AssetDatabase.LoadAllAssetsAtPath(path).OfType<Material>().Select(m=>m.name)).Distinct().ToList();
            foreach(var id in mi.GetExternalObjectMap().Keys.ToList())mi.RemoveRemap(id);
            foreach(var name in names)
            {
                var target=Find(name);
                if(target)mi.AddRemap(new AssetImporter.SourceAssetIdentifier(typeof(Material),name),target);else missing.Add(name);
            }
            mi.SaveAndReimport();
            report.Add(new{path,missing,mapped=names.Count-missing.Count});
        }
        return report;
    }

    public static object Place()
    {
        if(EditorApplication.isPlaying)throw new InvalidOperationException("Stop Play Mode first.");
        var scene=EditorSceneManager.OpenScene("Assets/Scenes/PadovaPlayable.unity",OpenSceneMode.Single);
        var manifestAsset=AssetDatabase.LoadAssetAtPath<TextAsset>(Manifest);
        var manifest=JsonUtility.FromJson<LandmarkManifest>(manifestAsset.text);
        var world=UnityEngine.Object.FindFirstObjectByType<WorldContext>();
        world.Landmarks=manifestAsset;world.Build();
        var old=GameObject.Find("Landmark models");if(old)UnityEngine.Object.DestroyImmediate(old);
        var root=new GameObject("Landmark models");
        var placed=new List<object>();
        foreach(var model in manifest.models)
        {
            var prefab=AssetDatabase.LoadAssetAtPath<GameObject>(model.asset);
            var go=(GameObject)PrefabUtility.InstantiatePrefab(prefab,root.transform);
            // Blender (east, north, up) imports as Unity (east, north, -up); +90 degrees about X gives (east, up, north).
            go.transform.SetPositionAndRotation(new Vector3(model.anchor[0],model.anchor[1],model.anchor[2]),Quaternion.Euler(90,0,0));
            foreach(var t in go.GetComponentsInChildren<Transform>(true))t.gameObject.layer=9;
            foreach(var r in go.GetComponentsInChildren<MeshRenderer>(true))
            {
                string n=r.gameObject.name;var mesh=r.GetComponent<MeshFilter>().sharedMesh;
                if(n.EndsWith("_Collision")){r.enabled=false;r.gameObject.AddComponent<MeshCollider>().sharedMesh=mesh;continue;}
                if(n.EndsWith("_Ground")){r.gameObject.layer=8;r.gameObject.AddComponent<MeshCollider>().sharedMesh=mesh;r.shadowCastingMode=ShadowCastingMode.Off;continue;}
                if(n.EndsWith("_Water")){r.shadowCastingMode=ShadowCastingMode.Off;continue;}
                r.shadowCastingMode=ShadowCastingMode.On;
            }
            var bounds=go.GetComponentsInChildren<Renderer>().Where(r=>r.enabled).Select(r=>r.bounds).Aggregate((a,b)=>{a.Encapsulate(b);return a;});
            placed.Add(new{model.name,position=go.transform.position,min=bounds.min,max=bounds.max});
        }
        EditorUtility.SetDirty(world);EditorSceneManager.MarkSceneDirty(scene);EditorSceneManager.SaveScene(scene);
        return new{placed,world.Buildings,world.Chunks,places=world.Data.landmarks.Length};
    }

    public static object Build(){var imported=Import();var placed=Place();return new{imported,placed};}
}
