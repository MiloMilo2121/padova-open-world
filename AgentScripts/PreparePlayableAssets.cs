using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class PreparePlayableAssets
{
    public static void Folder(string path)
    {
        if (AssetDatabase.IsValidFolder(path)) return;
        var parent = Path.GetDirectoryName(path).Replace('\\', '/');
        Folder(parent);
        AssetDatabase.CreateFolder(parent, Path.GetFileName(path));
    }
    static void Import(string source, string destination)
    {
        Folder(Path.GetDirectoryName(destination).Replace('\\', '/'));
        if (!File.Exists(destination)) File.Copy(source, destination);
        AssetDatabase.ImportAsset(destination, ImportAssetOptions.ForceSynchronousImport);
    }
    public static object Prepare()
    {
        string art = "Assets/Art/Kenney/";
        Import(".context/playable/Kenney/Model/characterMedium.fbx", art + "characterMedium.fbx");
        Import(".context/playable/Kenney/Skins/skaterMaleA.png", art + "skaterMaleA.png");
        Import(".context/playable/Kenney/License.txt", art + "License.txt");
        var rig = (ModelImporter)AssetImporter.GetAtPath(art + "characterMedium.fbx");
        rig.animationType = ModelImporterAnimationType.Generic;
        rig.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
        rig.materialImportMode = ModelImporterMaterialImportMode.None;
        rig.SaveAndReimport();
        var avatar = AssetDatabase.LoadAllAssetsAtPath(art + "characterMedium.fbx").OfType<Avatar>().FirstOrDefault();
        foreach (string name in new[] { "idle", "run", "jump" })
        {
            Import(".context/playable/Kenney/Animations/" + name + ".fbx", art + name + ".fbx");
            var importer = (ModelImporter)AssetImporter.GetAtPath(art + name + ".fbx");
            importer.animationType = ModelImporterAnimationType.Generic;
            importer.avatarSetup = ModelImporterAvatarSetup.CopyFromOther;
            importer.sourceAvatar = avatar;
            importer.materialImportMode = ModelImporterMaterialImportMode.None;
            importer.importAnimation = true;
            var clips = importer.defaultClipAnimations;
            foreach (var clip in clips)
            {
                clip.name = name;
                clip.loopTime = name != "jump";
                clip.lockRootRotation = true;
                clip.lockRootHeightY = true;
                clip.lockRootPositionXZ = true;
            }
            importer.clipAnimations = clips;
            importer.SaveAndReimport();
        }
        foreach (string texture in new[] { "paving_diff", "paving_nor_gl", "plaster_diff" })
        {
            var path = "Assets/Art/Surfaces/" + texture + ".jpg";
            Import(".context/playable/" + texture + ".jpg", path);
            var importer = (TextureImporter)AssetImporter.GetAtPath(path);
            importer.maxTextureSize = 1024;
            importer.anisoLevel = 8;
            importer.wrapMode = TextureWrapMode.Repeat;
            importer.textureType = texture.Contains("nor") ? TextureImporterType.NormalMap : TextureImporterType.Default;
            importer.SaveAndReimport();
        }
        var model = AssetDatabase.LoadAssetAtPath<GameObject>(art + "characterMedium.fbx");
        return new { avatar = avatar ? avatar.name : "missing", model = model.name,
            renderers = model.GetComponentsInChildren<SkinnedMeshRenderer>().Select(r => new { r.name, size = r.localBounds.size.ToString() }).ToArray(),
            clips = new[] {"idle", "run", "jump"}.Select(n => AssetDatabase.LoadAllAssetsAtPath(art+n+".fbx").OfType<AnimationClip>().Where(c=>!c.name.StartsWith("__preview")).Select(c=>c.name+":"+c.length).ToArray()).ToArray() };
    }
}
