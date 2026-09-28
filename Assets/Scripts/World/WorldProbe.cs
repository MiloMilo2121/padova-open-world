#if UNITY_EDITOR || DEVELOPMENT_BUILD
using System;
using Unity.Pipeline.Commands;
using UnityEngine;
using UnityEngine.AI;

namespace Padova.World
{
    public static class WorldProbe
    {
        static OpenWorld Game=>UnityEngine.Object.FindFirstObjectByType<OpenWorld>();
        static float[] XYZ(Vector3 p)=>new[]{p.x,p.y,p.z};
        [CliCommand("world_state","Read exploration mode, map, cars, flight and pedestrian navigation state.")]
        public static object Read()
        {
            var g=Game;if(!g)return new{ready=false};
            int invalid=0;foreach(var a in g.Crowd.GetComponentsInChildren<NavMeshAgent>())if(!a.isOnNavMesh)invalid++;
            return new{ready=true,mode=g.Mode,mapOpen=g.MapOpen,position=XYZ(g.Position),player=XYZ(g.Player.transform.position),frame=Time.frameCount,focused=Application.isFocused,
                g.HasWaypoint,waypoint=XYZ(g.Waypoint),mapCentre=new[]{g.MapCentre.x,g.MapCentre.y},mapSpan=g.MapSpan,screenWidth=Screen.width,screenHeight=Screen.height,
                cars=g.Cars.Length,nearby=g.Nearby?g.Nearby.name:"",carPosition=XYZ(g.Cars[0].transform.position),carSpeed=g.Driving?g.Driving.Speed:0,
                carTravel=g.Cars[0].DistanceTravelled,carHeading=g.Cars[0].transform.eulerAngles.y,planeSpeed=g.Plane.Speed,altitude=g.Plane.Altitude,planeHeading=g.Plane.transform.eulerAngles.y,
                planeTravel=g.Plane.DistanceTravelled,npcs=g.Crowd.ActiveCount,npcsMoved=g.Crowd.MovedCount,npcTravel=g.Crowd.TotalTravel,invalidNav=invalid,
                worldBuildings=g.City.Buildings,g.Discoveries,playerEnabled=g.Player.enabled,colliderEnabled=g.Player.GetComponent<CharacterController>().enabled};
        }
        [CliCommand("world_fixture","Place the walking character beside a car or reset the exploration state for repeatable input tests.")]
        public static object Fixture([CliArg("name","car | reset",Required=true)]string name)
        {
            var g=Game;g.SetMap(false);
            if(g.Mode=="fly")g.EndFlight();if(g.Mode=="drive"){g.Driving.ResetCar();g.ExitCar();}
            if(name=="reset"){g.Player.Respawn();g.HasWaypoint=false;}
            else if(name=="car")
            {
                var car=g.Cars[0];car.ResetCar();var p=car.transform.position+car.transform.right*2.2f;
                if(Physics.Raycast(p+Vector3.up*3,Vector3.down,out var hit,8,1<<8))p=hit.point+Vector3.up*.04f;
                var controller=g.Player.GetComponent<CharacterController>();controller.enabled=false;g.Player.transform.position=p;controller.enabled=true;
                g.Player.VerticalSpeed=-2;g.Player.FollowCamera.SetTestHeading(car.transform.eulerAngles.y);
            }
            else throw new ArgumentException(name);
            return Read();
        }
    }
}
#endif
