using System.Linq;
using NUnit.Framework;
using Padova.Architecture;
using Padova.Gameplay;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace PadovaOpenWorld.Tests
{
    public class PlayableSceneTests
    {
        Scene scene;
        bool opened;
        [SetUp] public void Load()
        {
            scene=SceneManager.GetSceneByPath("Assets/Scenes/PadovaPlayable.unity");
            opened=!scene.isLoaded;
            if(opened) scene=EditorSceneManager.OpenScene("Assets/Scenes/PadovaPlayable.unity",OpenSceneMode.Additive);
        }
        [TearDown] public void Close() { if(opened) EditorSceneManager.CloseScene(scene,true); }
        T[] Find<T>() where T:Component => scene.GetRootGameObjects().SelectMany(o=>o.GetComponentsInChildren<T>(true)).ToArray();

        PadovaCity City()
        {
            var city=Find<PadovaCity>().Single();
            city.Build();
            Physics.SyncTransforms();
            return city;
        }

        [Test] public void CharacterHasAnimatedSkinAndThirdPersonRig()
        {
            var player=Find<ThirdPersonMotor>().Single();
            Assert.That(player.Animator,Is.Not.Null);
            Assert.That(player.Animator.avatar,Is.Not.Null);
            Assert.That(player.Animator.avatar.isValid,Is.True);
            Assert.That(player.Animator.runtimeAnimatorController.animationClips.Select(c=>c.name),Does.Contain("run"));
            Assert.That(player.GetComponentInChildren<SkinnedMeshRenderer>(),Is.Not.Null);
            Assert.That(player.GetComponent<CharacterController>().height,Is.InRange(1.6f,1.9f));
            Assert.That(Find<ThirdPersonCamera>().Single().Player,Is.SameAs(player));
            Assert.That(Vector3.Distance(player.Spawn,player.Goal),Is.InRange(19,22));
        }

        [Test] public void CityIsGeneratedFromTheSurveyPlanWithoutSavingMeshesIntoTheScene()
        {
            var city=City();
            Assert.That(city.Data.units.Length,Is.GreaterThan(1300));
            Assert.That(city.Data.units.Count(u=>u.suspended),Is.GreaterThan(300),"DBT suspended units become porticoes");
            Assert.That(city.Data.roofs.Length,Is.GreaterThan(1000));
            Assert.That(city.Units,Is.EqualTo(city.Data.units.Length));
            Assert.That(city.Triangles,Is.InRange(500000,4000000));
            var generated=city.transform.Find("Generated city");
            Assert.That(generated,Is.Not.Null);
            Assert.That((generated.gameObject.hideFlags&HideFlags.DontSave)!=0,Is.True,"Generated meshes must stay out of the scene file");
            Assert.That(generated.Find("Palazzo della Ragione"),Is.Not.Null);
            Assert.That(city.Materials.Length,Is.EqualTo((int)Slot.Count));
            Assert.That(city.Materials.All(m=>m!=null),Is.True);
        }

        [Test] public void SurveyedHeightsArePreservedForEveryUnitAndPortico()
        {
            var city=City();
            foreach(var u in city.Data.units)
            {
                Assert.That(u.top,Is.GreaterThanOrEqualTo(u.surveyTop-0.001f),u.id);
                Assert.That(u.top-u.surveyTop,Is.LessThan(0.36f),"Roof merge tolerance exceeded: "+u.id);
                if(u.suspended) Assert.That(u.under,Is.InRange(u.ground+2f,u.top),u.id);
            }
            var r=city.Data.ragione;
            Assert.That(r.ridge-r.ground,Is.EqualTo(35f).Within(0.01f),"OSM Palazzo della Ragione height");
            Assert.That(r.hall[1]-r.hall[0],Is.InRange(80f,90f));
        }

        [Test] public void NavigationUsesOneContinuousSurfaceAtTheStartingRoute()
        {
            City();
            var player=Find<ThirdPersonMotor>().Single();
            float previous=0;
            for(int i=0;i<=8;i++)
            {
                var point=Vector3.Lerp(player.Spawn,player.Goal,i/8f);
                var hits=Physics.RaycastAll(new Vector3(point.x,80,point.z),Vector3.down,160,ThirdPersonMotor.GroundMask);
                Assert.That(hits.Length,Is.EqualTo(1),"Stacked or missing ground at route sample "+i);
                if(i>0)Assert.That(Mathf.Abs(hits[0].point.y-previous),Is.LessThan(.05f),"Raised seam across route");
                previous=hits[0].point.y;
            }
        }

        [Test] public void BuildingsCollideAndPorticoesAreWalkable()
        {
            var city=City();
            var portico=city.Data.units.First(u=>u.suspended&&u.under-u.ground>3.5f&&u.area>40);
            var inside=new Vector3(portico.cx,portico.ground+1.0f,portico.cz);
            Assert.That(Physics.CheckSphere(inside,0.3f,1<<9),Is.False,"A person must fit under a surveyed portico: "+portico.id);
            var player=Find<ThirdPersonMotor>().Single();
            bool wall=false;
            foreach(var d in new[]{Vector3.forward,Vector3.back,Vector3.left,Vector3.right})
                wall|=Physics.Raycast(player.Spawn+Vector3.up,d,120,1<<9);
            Assert.That(wall,Is.True,"Architecture colliders near the start");
        }

        [Test] public void AttributionIsRecorded()
        {
            var plan=AssetDatabase.LoadAssetAtPath<TextAsset>("Assets/Geography/PadovaCentro/CityPlan.json");
            Assert.That(plan.text,Does.Contain("IODL 2.0"));
            Assert.That(plan.text,Does.Contain("OpenStreetMap"));
            Assert.That(System.IO.File.ReadAllText("Data/PadovaCentro/osm/landmarks.json"),Does.Contain("ODbL"));
        }
    }
}
