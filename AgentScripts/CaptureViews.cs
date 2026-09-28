using System.Collections.Generic;
using System.IO;
using Padova.Architecture;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

/// <summary>Offscreen captures of named viewpoints through the scene's own camera settings.</summary>
public static class CaptureViews
{
    static readonly (string name, Vector3 eye, Vector3 target)[] Views =
    {
        ("frutta-spawn", new Vector3(80, 3.0f, 17.8f), new Vector3(78, 9, -25)),
        ("aerial-core", new Vector3(175, 80, 95), new Vector3(40, 0, -45)),
        ("erbe-south", new Vector3(20, 2.2f, -118), new Vector3(75, 12, -60)),
        ("erbe-ragione", new Vector3(95, 2.4f, -100), new Vector3(55, 14, -62)),
        ("signori", new Vector3(-60, 2.2f, 2), new Vector3(-133, 14, 8)),
        ("aerial-ragione", new Vector3(120, 45, 20), new Vector3(60, 18, -45)),
        ("duomo", new Vector3(-145, 28, -60), new Vector3(-244, 24, -141)),
        ("bo-courtyard", new Vector3(229, 2.5f, -78), new Vector3(237, 9, -72)),
        ("expanded-city", new Vector3(450, 240, 480), new Vector3(0, 5, 0)),
    };

    public static object Capture(string outDir, string only = "")
    {
        Directory.CreateDirectory(outDir);
        var main = Camera.main;
        var go = new GameObject("Capture camera") { hideFlags = HideFlags.DontSave };
        var cam = go.AddComponent<Camera>();
        cam.CopyFrom(main);
        cam.fieldOfView = 60;
        var data = go.AddComponent<UniversalAdditionalCameraData>();
        data.renderPostProcessing = true;
        data.antialiasing = AntialiasingMode.SubpixelMorphologicalAntiAliasing;
        DynamicGI.UpdateEnvironment();
        var rt = new RenderTexture(1600, 900, 24, RenderTextureFormat.ARGB32) { antiAliasing = 1 };
        var written = new List<string>();
        foreach (var (name, eye, target) in Views)
        {
            if (only.Length > 0 && !only.Contains(name)) continue;
            go.transform.SetPositionAndRotation(eye, Quaternion.LookRotation(target - eye));
            Object.FindFirstObjectByType<WorldContext>()?.RefreshVisibility(eye);
            cam.targetTexture = rt;
            RenderPipeline.SubmitRenderRequest(cam,new UniversalRenderPipeline.SingleCameraRequest {destination=rt});
            RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, rt.height, TextureFormat.RGB24, false);
            tex.ReadPixels(new Rect(0, 0, rt.width, rt.height), 0, 0);
            tex.Apply();
            var path = Path.Combine(outDir, name + ".png");
            File.WriteAllBytes(path, tex.EncodeToPNG());
            Object.DestroyImmediate(tex);
            written.Add(path);
        }
        RenderTexture.active = null;
        cam.targetTexture = null;
        Object.DestroyImmediate(rt);
        Object.DestroyImmediate(go);
        return written;
    }

    public static object All() => Capture(Path.GetFullPath(".context/views"));
}
