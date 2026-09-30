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
        [CliCommand("world_fixture","Place the walking character beside a car, at a mapped point, or reset the exploration state for repeatable input tests.")]
        public static object Fixture([CliArg("name","car | reset | at",Required=true)]string name,
            [CliArg("x","Grid east for 'at'")]float x=0,[CliArg("z","Grid north for 'at'")]float z=0,[CliArg("yaw","Heading in degrees for 'at'")]float yaw=0)
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
            else if(name=="at")
            {
                var p=new Vector3(x,200,z);
                if(!Physics.Raycast(p,Vector3.down,out var hit,400,(1<<8)|(1<<9)))throw new InvalidOperationException("No ground at "+x+","+z);
                var controller=g.Player.GetComponent<CharacterController>();controller.enabled=false;g.Player.transform.position=hit.point+Vector3.up*.04f;controller.enabled=true;
                g.Player.VerticalSpeed=-2;g.Player.FollowCamera.SetTestHeading(yaw);g.Player.Visual.rotation=Quaternion.Euler(0,yaw,0);
            }
            else throw new ArgumentException(name);
            return Read();
        }
    }
}
#endif
