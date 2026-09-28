using NUnit.Framework;
using UnityEditor;
using UnityEngine.Rendering;

namespace PadovaOpenWorld.Tests
{
    public class ProjectSetupTests
    {
        [Test]
        public void ProjectHasSceneAndUniversalRenderPipeline()
        {
            Assert.That(AssetDatabase.LoadAssetAtPath<SceneAsset>("Assets/Scenes/SampleScene.unity"), Is.Not.Null);
            Assert.That(GraphicsSettings.defaultRenderPipeline, Is.Not.Null);
            Assert.That(GraphicsSettings.defaultRenderPipeline.GetType().Name, Does.Contain("Universal"));
        }
    }
}
