using System.Linq;
using NUnit.Framework;
using Padova.Geography;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace PadovaOpenWorld.Tests
{
    public class SurveySceneTests
    {
        const string Path = "Assets/Scenes/PadovaCentroSurvey.unity";
        Scene scene;
        bool opened;

        [SetUp]
        public void LoadSurvey()
        {
            scene = SceneManager.GetSceneByPath(Path);
            opened = !scene.isLoaded;
            if (opened) scene = EditorSceneManager.OpenScene(Path, OpenSceneMode.Additive);
        }

        [TearDown]
        public void CloseSurvey()
        {
            if (opened) EditorSceneManager.CloseScene(scene, true);
        }

        T[] Find<T>() where T : Component => scene.GetRootGameObjects().SelectMany(o => o.GetComponentsInChildren<T>()).ToArray();

        [Test]
        public void SavedScenePreservesAllAcceptedSourceParts()
        {
            var district = Find<DistrictSurvey>().Single();
            var parts = Find<SurveyFeature>();
            Assert.That(district.VolumeCount, Is.EqualTo(1374));
            Assert.That(district.SurfaceCount, Is.EqualTo(519));
            Assert.That(parts.Length, Is.EqualTo(1893));
            Assert.That(parts.Select(p => p.name).Distinct().Count(), Is.EqualTo(parts.Length));
            Assert.That(district.OriginEasting, Is.EqualTo(724933.0767774055).Within(0.001));
            Assert.That(district.OriginNorthing, Is.EqualTo(5032261.930084035).Within(0.001));
        }

        [Test]
        public void EveryBuildingKeepsItsElevationAndPorticoSemantics()
        {
            foreach (var part in Find<SurveyFeature>().Where(p => p.Layer == "UN_VOL"))
            {
                var mesh = part.GetComponent<MeshFilter>().sharedMesh;
                Assert.That(mesh, Is.Not.Null, part.SourceId);
                Assert.That(part.SourceId, Does.StartWith("UN_VOL:"));
                Assert.That(mesh.bounds.max.y, Is.EqualTo(part.EaveElevation - 15).Within(0.002), part.SourceId);
                if (part.Portion != "01")
                {
                    Assert.That(part.HasWalls, Is.False);
                    Assert.That(mesh.bounds.size.y, Is.LessThan(0.002), "No invented portico clearance: " + part.SourceId);
                }
                else
                    Assert.That(mesh.bounds.size.y, Is.EqualTo(part.VolumeHeight).Within(0.002), part.SourceId);
                Assert.That(part.GetComponent<MeshCollider>().sharedMesh, Is.SameAs(mesh));
            }
        }

        [Test]
        public void ViewHasMetricAnchorsAndPackagedMeshes()
        {
            var district = Find<DistrictSurvey>().Single();
            Assert.That(district.Anchors.Select(a => a.SourceId), Is.EquivalentTo(new[] { "TP_STR:107", "TP_STR:109", "TP_STR:122" }));
            Assert.That(Vector3.Distance(district.Anchors[0].Position, district.Anchors[1].Position), Is.InRange(65, 75));
            Assert.That(Find<SurveyExplorer>().Single().District, Is.SameAs(district));
            Assert.That(AssetDatabase.LoadAllAssetsAtPath("Assets/Geography/PadovaCentro/SurveyMeshes.asset").OfType<Mesh>().Count(), Is.EqualTo(1893));
        }
    }
}
