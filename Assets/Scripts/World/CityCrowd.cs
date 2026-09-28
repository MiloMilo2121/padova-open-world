using System.Collections.Generic;
using UnityEngine;
using UnityEngine.AI;

namespace Padova.World
{
    public sealed class CityCrowd:MonoBehaviour
    {
        public NavMeshData Navigation;public GameObject Character;public Material[] Skins;public int Count=32;
        public Vector3[] Destinations;public int ActiveCount,MovedCount;public float TotalTravel;
        NavMeshDataInstance navigation;readonly List<Walker> walkers=new();System.Random random=new(854);
        sealed class Walker{public NavMeshAgent Agent;public Animator Animator;public Vector3 Last;public float Distance,Next;}
        void Start()
        {
            if(!Navigation || !Character)return;navigation=NavMesh.AddNavMeshData(Navigation);
            for(int i=0;i<Count;i++)
            {
                var seed=Destinations[i%Destinations.Length]+new Vector3((i%4)*1.5f,0,(i/4%4)*1.5f);
                if(!NavMesh.SamplePosition(seed,out var sample,12,NavMesh.AllAreas))continue;
                var go=new GameObject("Pedestrian "+(i+1));go.transform.SetParent(transform);go.transform.position=sample.position;
                var model=Instantiate(Character,go.transform);model.SetActive(true);model.transform.localPosition=Vector3.zero;model.transform.localRotation=Quaternion.identity;
                if(Skins!=null && Skins.Length>0)foreach(var renderer in model.GetComponentsInChildren<SkinnedMeshRenderer>())renderer.sharedMaterial=Skins[i%Skins.Length];
                float scale=.94f+(i%7)*.018f;model.transform.localScale=Vector3.one*scale;
                var agent=go.AddComponent<NavMeshAgent>();agent.radius=.27f;agent.height=1.8f;agent.speed=.85f+(i%5)*.18f;agent.acceleration=3;agent.angularSpeed=180;agent.stoppingDistance=.35f;agent.avoidancePriority=20+i;
                var animator=model.GetComponentInChildren<Animator>();if(animator){animator.SetBool("Grounded",true);animator.cullingMode=AnimatorCullingMode.CullUpdateTransforms;}
                var walker=new Walker{Agent=agent,Animator=animator,Last=sample.position};walkers.Add(walker);Destination(walker);
            }
            ActiveCount=walkers.Count;
        }
        void Destination(Walker w)
        {
            for(int tries=0;tries<8;tries++)
            {
                var p=Destinations[random.Next(Destinations.Length)]+new Vector3((float)random.NextDouble()*6-3,0,(float)random.NextDouble()*6-3);
                if(!NavMesh.SamplePosition(p,out var hit,8,NavMesh.AllAreas))continue;
                var path=new NavMeshPath();if(!w.Agent.CalculatePath(hit.position,path)||path.status!=NavMeshPathStatus.PathComplete)continue;
                w.Agent.SetPath(path);break;
            }
            w.Next=Time.time+25+(float)random.NextDouble()*35;
        }
        void Update()
        {
            MovedCount=0;float total=0;
            foreach(var w in walkers)
            {
                w.Distance+=Vector3.Distance(w.Last,w.Agent.transform.position);w.Last=w.Agent.transform.position;total+=w.Distance;
                if(w.Distance>2)MovedCount++;
                if(w.Animator)w.Animator.SetFloat("Speed",w.Agent.velocity.magnitude,.15f,Time.deltaTime);
                if(!w.Agent.pathPending && (Time.time>w.Next || w.Agent.remainingDistance<.6f))Destination(w);
            }
            TotalTravel=total;
        }
        void OnDestroy(){if(navigation.valid)navigation.Remove();}
    }
}
