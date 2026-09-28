using System;
using System.IO;
using System.Linq;
using Newtonsoft.Json;
using Padova.Geography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;

public static class BuildPadovaSurvey
{
    const string Folder = "Assets/Geography/PadovaCentro";
    const string ScenePath = "Assets/Scenes/PadovaCentroSurvey.unity";
    [Serializable] public class Data
    {
        public int schemaVersion, sourceYear;
        public double originEasting, originNorthing;
        public float verticalOrigin;
        public Part[] meshes;
        public Label[] labels;
    }
    [Serializable] public class Part
    {
        public string id, sourceId, layer, portion;
        public float area, eave, height, x, z;
        public bool walls;
        public Vector3[] vertices;
        public int[] triangles;
    }
    [Serializable] public class Label { public string id, name; public float x, z; }
    [Serializable] public class Validation { public string districtSha256; }

    static void EnsureFolder(string path)
    {
        if (AssetDatabase.IsValidFolder(path)) return;
        var parent = Path.GetDirectoryName(path).Replace('\\', '/');
        EnsureFolder(parent);
        AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
    }

    static Material Material(string name, Color color)
    {
        var path = Folder + "/" + name + ".mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (!material)
        {
            material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            AssetDatabase.CreateAsset(material, path);
        }
        material.SetColor("_BaseColor", color);
        material.SetFloat("_Smoothness", 0.08f);
        material.SetFloat("_Cull", 0);
        EditorUtility.SetDirty(material);
        return material;
    }

    public static object Build()
    {
        if (EditorApplication.isPlaying) throw new InvalidOperationException("Stop Play Mode before rebuilding the survey.");
        for (int i = 0; i < SceneManager.sceneCount; i++)
            if (SceneManager.GetSceneAt(i).isDirty) throw new InvalidOperationException("An open scene has unsaved work. Save it before rebuilding.");
        var data = JsonConvert.DeserializeObject<Data>(File.ReadAllText("Data/PadovaCentro/derived/district.json"));
        if (data.schemaVersion != 1 || data.meshes.Length < 100) throw new InvalidDataException("Unexpected survey schema or empty district.");
        var hash = JsonConvert.DeserializeObject<Validation>(File.ReadAllText("Data/PadovaCentro/validation.json")).districtSha256;
        using (var sha = System.Security.Cryptography.SHA256.Create())
        {
            var actual = BitConverter.ToString(sha.ComputeHash(File.ReadAllBytes("Data/PadovaCentro/derived/district.json"))).Replace("-", "").ToLowerInvariant();
            if (actual != hash) throw new InvalidDataException("Derived mesh data does not match validation hash.");
        }
        EnsureFolder(Folder);
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var libraryPath = Folder + "/SurveyMeshes.asset";
        var library = AssetDatabase.LoadAssetAtPath<SurveyMeshLibrary>(libraryPath);
        if (!library)
        {
            library = ScriptableObject.CreateInstance<SurveyMeshLibrary>();
            AssetDatabase.CreateAsset(library, libraryPath);
        }
        foreach (var old in AssetDatabase.LoadAllAssetsAtPath(libraryPath).OfType<Mesh>())
            UnityEngine.Object.DestroyImmediate(old, true);
        library.SourceHash = hash;
        EditorUtility.SetDirty(library);
        var walls = Material("SurveyVolumes", new Color(0.68f, 0.70f, 0.67f));
        var portico = Material("UnresolvedPorticoes", new Color(0.60f, 0.40f, 0.19f));
        var streets = Material("StreetSurfaces", new Color(0.26f, 0.33f, 0.37f));
        var pedestrian = Material("PedestrianSurfaces", new Color(0.44f, 0.49f, 0.48f));
        var root = new GameObject("Padova Centro | DBT 2007");
        var district = root.AddComponent<DistrictSurvey>();
        district.OriginEasting = data.originEasting;
        district.OriginNorthing = data.originNorthing;
        district.VerticalOrigin = data.verticalOrigin;
        district.SourceHash = hash;
        var volumes = new GameObject("Building volumes").transform;
        var surfaces = new GameObject("Mapped street and pedestrian surfaces").transform;
        volumes.SetParent(root.transform);
        surfaces.SetParent(root.transform);
        foreach (var part in data.meshes)
        {
            var building = part.layer == "UN_VOL";
            var go = new GameObject(part.id);
            go.transform.SetParent(building ? volumes : surfaces);
            var mesh = new Mesh { name = part.id, indexFormat = IndexFormat.UInt32 };
            mesh.vertices = part.vertices;
            mesh.triangles = part.triangles;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
            AssetDatabase.AddObjectToAsset(mesh, library);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var renderer = go.AddComponent<MeshRenderer>();
            renderer.sharedMaterial = building ? (part.walls ? walls : portico) : (part.layer == "AR_STR" ? streets : pedestrian);
            renderer.shadowCastingMode = building ? ShadowCastingMode.TwoSided : ShadowCastingMode.Off;
            go.AddComponent<MeshCollider>().sharedMesh = mesh;
            var evidence = go.AddComponent<SurveyFeature>();
            evidence.SourceId = part.sourceId;
            evidence.Layer = part.layer;
            evidence.Portion = part.portion;
            evidence.FootprintArea = part.area;
            evidence.EaveElevation = part.eave;
            evidence.VolumeHeight = part.height;
            evidence.HasWalls = part.walls;
            if (building)
            {
                district.VolumeCount++;
                if (!part.walls) district.OpenPorticoCount++;
            }
            else district.SurfaceCount++;
            GameObjectUtility.SetStaticEditorFlags(go, StaticEditorFlags.BatchingStatic);
        }
        string[] ids = { "TP_STR:107", "TP_STR:109", "TP_STR:122" };
        string[] names = { "PIAZZA DELLE ERBE", "PIAZZA DELLA FRUTTA", "PIAZZA DEI SIGNORI" };
        district.Anchors = ids.Select((id, i) =>
        {
            var label = data.labels.Single(l => l.id == id);
            return new SurveyAnchor { Name = names[i], SourceId = id, Position = new Vector3(label.x, 2, label.z) };
        }).ToArray();
        var light = new GameObject("Survey lighting").AddComponent<Light>();
        light.type = LightType.Directional;
        light.intensity = 1.3f;
        light.color = new Color(1.0f, 0.94f, 0.84f);
        light.shadows = LightShadows.Soft;
        light.transform.rotation = Quaternion.Euler(48, -32, 0);
        RenderSettings.sun = light;
        RenderSettings.ambientMode = AmbientMode.Flat;
        RenderSettings.ambientLight = new Color(0.62f, 0.67f, 0.72f);
        RenderSettings.fog = false;
        var camera = new GameObject("Survey Camera").AddComponent<Camera>();
        camera.tag = "MainCamera";
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(0.065f, 0.095f, 0.125f);
        camera.nearClipPlane = 0.3f;
        camera.farClipPlane = 2500;
        camera.fieldOfView = 48;
        camera.gameObject.AddComponent<UniversalAdditionalCameraData>();
        camera.gameObject.AddComponent<AudioListener>();
        var explorer = camera.gameObject.AddComponent<SurveyExplorer>();
        explorer.District = district;
        explorer.ResetView();
        // This is a navigable survey viewer. No fictional walking ground or collision walls under porticoes.
        QualitySettings.vSyncCount = 1;
        PlayerSettings.defaultScreenWidth = 1600;
        PlayerSettings.defaultScreenHeight = 1000;
        PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
        PlayerSettings.runInBackground = true;
        AssetDatabase.SaveAssets();
        EditorSceneManager.SaveScene(scene, ScenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        AssetDatabase.SaveAssets();
        Selection.activeGameObject = root;
        if (SceneView.lastActiveSceneView)
            SceneView.lastActiveSceneView.LookAt(new Vector3(0, 0, 0), Quaternion.Euler(50, -25, 0), 450);
        return new { scene = ScenePath, volumes = district.VolumeCount, surfaces = district.SurfaceCount,
                     openPorticoes = district.OpenPorticoCount, sourceHash = hash };
    }
}
