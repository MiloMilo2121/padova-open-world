using UnityEngine;
using UnityEngine.InputSystem;

namespace Padova.World
{
    [RequireComponent(typeof(Rigidbody))]
    public sealed class CityCar:MonoBehaviour
    {
        public WheelCollider[] Wheels;public Transform[] WheelVisuals;public bool Driven,Paused;
        public Vector3 Home;public Quaternion HomeRotation;public float DistanceTravelled;
        public float Speed=>Body?Body.linearVelocity.magnitude:0;
        public Rigidbody Body{get;private set;}
        Vector3 lastPosition;
        void Awake(){Body=GetComponent<Rigidbody>();Body.centerOfMass=new Vector3(0,.28f,0);Home=transform.position;HomeRotation=transform.rotation;lastPosition=Home;}
        void FixedUpdate()
        {
            var k=Keyboard.current;float throttle=0,steer=0;bool brake=true;
            if(Driven && !Paused && k!=null)
            {
                throttle=(k.upArrowKey.isPressed||k.wKey.isPressed?1:0)-(k.downArrowKey.isPressed||k.sKey.isPressed?1:0);
                steer=(k.rightArrowKey.isPressed||k.dKey.isPressed?1:0)-(k.leftArrowKey.isPressed||k.aKey.isPressed?1:0);
                brake=k.spaceKey.isPressed;
            }
            float forward=Vector3.Dot(Body.linearVelocity,transform.forward);
            foreach(var w in Wheels)
            {
                w.motorTorque=brake?0:(forward>22 && throttle>0 || forward< -7 && throttle<0?0:throttle*650);
                w.brakeTorque=brake?2400:Mathf.Abs(throttle)<.1f?80:0;
                if(w.transform.localPosition.z>0)w.steerAngle=steer*Mathf.Lerp(32,12,Speed/22);
            }
            Body.AddForce(-transform.up*Speed*12);
            DistanceTravelled+=Vector3.Distance(lastPosition,transform.position);lastPosition=transform.position;
            if(transform.position.y< -5 || Mathf.Abs(transform.position.x)>1380 || Mathf.Abs(transform.position.z)>1180)ResetCar();
        }
        void LateUpdate(){for(int i=0;i<Wheels.Length;i++){Wheels[i].GetWorldPose(out var p,out var q);WheelVisuals[i].SetPositionAndRotation(p,q);}}
        public void ResetCar(){Body.linearVelocity=Vector3.zero;Body.angularVelocity=Vector3.zero;transform.SetPositionAndRotation(Home,HomeRotation);lastPosition=Home;}
    }
}
