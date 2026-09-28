using UnityEngine;

namespace Padova.Architecture
{
    /// <summary>Original geometry for contextual street furniture and fictional vehicles.</summary>
    public static class WorldShapes
    {
        public static void Ellipsoid(MeshSink s,Slot slot,Vector3 c,Vector3 size,int sides=12,int rings=8)
        {
            var p=new Vector3[sides+1,rings+1];var uv=new Vector2[sides+1,rings+1];
            for(int i=0;i<=sides;i++)for(int j=0;j<=rings;j++)
            {
                float a=i*Mathf.PI*2/sides,b=-Mathf.PI/2+j*Mathf.PI/rings;
                p[i,j]=c+Vector3.Scale(new Vector3(Mathf.Cos(a)*Mathf.Cos(b),Mathf.Sin(b),Mathf.Sin(a)*Mathf.Cos(b)),size);
                uv[i,j]=new Vector2(i/(float)sides,j/(float)rings);
            }
            s.Grid(slot,p,uv,true);
        }
        public static void Tree(MeshSink s,Vector3 p,float height)
        {
            s.Cylinder(Slot.Bark,p,.12f+height*.012f,height*.66f,7,.55f);
            Ellipsoid(s,Slot.Foliage,p+Vector3.up*(height*.72f),new Vector3(height*.25f,height*.28f,height*.23f),8,5);
            Ellipsoid(s,Slot.Foliage,p+new Vector3(height*.15f,height*.59f,height*.09f),new Vector3(height*.2f,height*.20f,height*.22f),7,4);
        }
        public static void Lamp(MeshSink s,Vector3 p)
        {
            s.Cylinder(Slot.Iron,p,.23f,.25f,10,.85f);s.Cylinder(Slot.Iron,p+Vector3.up*.25f,.095f,3.55f,10,.6f);
            s.Cylinder(Slot.Iron,p+Vector3.up*.65f,.14f,.1f,10);s.Cylinder(Slot.Iron,p+Vector3.up*3.55f,.19f,.12f,8);
            s.Cylinder(Slot.LampGlow,p+Vector3.up*3.7f,.19f,.57f,6,1.35f);
            for(int k=0;k<6;k++)
            {
                float a=k*Mathf.PI/3;var d=new Vector3(Mathf.Cos(a),0,Mathf.Sin(a));
                s.Cylinder(Slot.Iron,p+d*.22f+Vector3.up*3.7f,.021f,.6f,5);
            }
            s.Cylinder(Slot.Iron,p+Vector3.up*4.27f,.30f,.23f,6,.05f);
            Ellipsoid(s,Slot.Gold,p+Vector3.up*4.55f,Vector3.one*.07f,7,4);
        }
        public static void Bench(MeshSink s,Vector3 p,Quaternion rotation)
        {
            var x=rotation*Vector3.right;var z=rotation*Vector3.forward;
            for(int k=0;k<4;k++)s.Box(Slot.Wood,p+Vector3.up*.47f+z*(k*.12f-.18f),x*.85f,Vector3.up*.035f,z*.048f);
            for(int k=0;k<3;k++)s.Box(Slot.Wood,p+Vector3.up*(.74f+k*.14f)-z*.27f,x*.85f,Vector3.up*.05f,z*.035f);
            foreach(float side in new[]{-.6f,.6f})
            {
                s.Box(Slot.Iron,p+x*side+Vector3.up*.24f,x*.04f,Vector3.up*.24f,z*.25f);
                s.Box(Slot.Iron,p+x*side+Vector3.up*.73f-z*.25f,x*.035f,Vector3.up*.3f,z*.035f);
            }
        }
        public static void Stall(MeshSink s,Vector3 p,Quaternion rotation,int variant)
        {
            var x=rotation*Vector3.right;var z=rotation*Vector3.forward;Vector3 P(float a,float y,float b)=>p+x*a+z*b+Vector3.up*y;
            foreach(float a in new[]{-1.4f,1.4f})foreach(float b in new[]{-1f,1f})s.Cylinder(Slot.Wood,P(a,0,b),.04f,2.3f,6);
            s.Box(Slot.Wood,P(0,.85f,0),x*1.4f,Vector3.up*.075f,z*.7f);
            foreach(float a in new[]{-1.2f,1.2f})s.Box(Slot.Wood,P(a,.42f,0),x*.08f,Vector3.up*.42f,z*.55f);
            for(int k=0;k<8;k++)
            {
                float a=-1.65f+k*.4125f,b=a+.4125f;var slot=k%2==0?Slot.White:variant%2==0?Slot.AwningGreen:Slot.AwningRed;
                foreach(int side in new[]{-1,1})
                {
                    var p0=P(a,2.65f,0);var p1=P(b,2.65f,0);var p2=P(b,2.25f,side*1.3f);var p3=P(a,2.25f,side*1.3f);
                    var normal=(Vector3.up+z*side*.3f).normalized;
                    s.Quad(slot,p0,p1,p2,p3,normal,Vector2.zero,Vector2.right,Vector2.one,Vector2.up);
                    if(slot==Slot.White)s.Quad(slot,p0,p1,p2,p3,-normal,Vector2.zero,Vector2.right,Vector2.one,Vector2.up);
                    s.Quad(slot,p3,p2,P(b,2.0f,side*1.3f),P(a,2.0f,side*1.3f),z*side,Vector2.zero,Vector2.right,Vector2.one,Vector2.up);
                }
            }
            for(int crate=0;crate<4;crate++)
            {
                float a=-1.05f+crate*.7f;
                s.Box(Slot.Door,P(a,.98f,0),x*.29f,Vector3.up*.07f,z*.5f);
                for(int i=0;i<4;i++)for(int j=0;j<4;j++)
                    Ellipsoid(s,(crate+variant)%3==0?Slot.VehicleRed:(crate+variant)%3==1?Slot.Plaster4:Slot.AwningGreen,P(a-.2f+i*.13f,1.1f,-.32f+j*.2f),Vector3.one*.085f,6,4);
            }
        }
        public static void CarBody(MeshSink s,Slot paint)
        {
            s.Box(paint,new Vector3(0,.62f,0),Vector3.right*.86f,Vector3.up*.28f,Vector3.forward*2.05f,true);
            // Sloping cabin with clear windscreen, window frames and bumpers.
            var a=new Vector3(-.77f,.90f,-1.05f);var b=new Vector3(.77f,.90f,-1.05f);
            var c=new Vector3(.63f,1.55f,-.65f);var d=new Vector3(-.63f,1.55f,-.65f);
            s.Quad(Slot.Glass,a,b,c,d,Vector3.back,Vector2.zero,Vector2.right,Vector2.one,Vector2.up);
            a.z=.92f;b.z=.92f;c.z=.53f;d.z=.53f;
            s.Quad(Slot.Glass,b,a,d,c,Vector3.forward,Vector2.zero,Vector2.right,Vector2.one,Vector2.up);
            foreach(float side in new[]{-1f,1f})
            {
                s.Quad(Slot.Glass,new Vector3(side*.77f,.90f,-1.05f),new Vector3(side*.77f,.90f,.92f),new Vector3(side*.63f,1.55f,.53f),new Vector3(side*.63f,1.55f,-.65f),Vector3.right*side,Vector2.zero,Vector2.right,Vector2.one,Vector2.up);
                s.Box(paint,new Vector3(side*.71f,1.22f,-.04f),Vector3.right*.04f,Vector3.up*.34f,Vector3.forward*.055f);
                s.Box(Slot.Iron,new Vector3(side*.87f,.80f,-.3f),Vector3.right*.02f,Vector3.up*.025f,Vector3.forward*.12f);
            }
            s.Box(paint,new Vector3(0,1.56f,-.06f),Vector3.right*.65f,Vector3.up*.045f,Vector3.forward*.61f);
            foreach(float z in new[]{-2.06f,2.06f})s.Box(Slot.Iron,new Vector3(0,.47f,z),Vector3.right*.84f,Vector3.up*.09f,Vector3.forward*.07f);
            foreach(float x in new[]{-.58f,.58f})
            {
                s.Box(Slot.LampGlow,new Vector3(x,.76f,2.066f),Vector3.right*.21f,Vector3.up*.11f,Vector3.forward*.025f);
                s.Box(Slot.VehicleRed,new Vector3(x,.78f,-2.067f),Vector3.right*.19f,Vector3.up*.08f,Vector3.forward*.025f);
            }
            s.Box(Slot.White,new Vector3(0,.57f,-2.14f),Vector3.right*.23f,Vector3.up*.065f,Vector3.forward*.008f);
        }
        public static void Wheel(MeshSink s)
        {
            const int count=20;var p=new Vector3[count+1,2];var uv=new Vector2[count+1,2];
            for(int i=0;i<=count;i++)for(int j=0;j<2;j++)
            {float a=i*Mathf.PI*2/count;p[i,j]=new Vector3(j==0?-.10f:.10f,Mathf.Cos(a)*.31f,Mathf.Sin(a)*.31f);uv[i,j]=new Vector2(i/(float)count,j);}
            s.Grid(Slot.Dark,p,uv,false);
            foreach(float side in new[]{-.105f,.105f})for(int i=0;i<count;i++)
            {float a=i*Mathf.PI*2/count,b=(i+1)*Mathf.PI*2/count;s.Tri(Slot.GreyStone,new Vector3(side,0,0),new Vector3(side,Mathf.Cos(a)*.22f,Mathf.Sin(a)*.22f),new Vector3(side,Mathf.Cos(b)*.22f,Mathf.Sin(b)*.22f),Vector3.right*Mathf.Sign(side),Vector2.zero,Vector2.right,Vector2.one);}
        }
        public static void Plane(MeshSink s)
        {
            Ellipsoid(s,Slot.White,new Vector3(0,0,0),new Vector3(.55f,.58f,3),20,10);
            Ellipsoid(s,Slot.Glass,new Vector3(0,.39f,.65f),new Vector3(.45f,.4f,.92f),16,8);
            s.Box(Slot.VehicleRed,new Vector3(0,-.1f,.10f),Vector3.right*4.6f,Vector3.up*.075f,Vector3.forward*.67f);
            s.Box(Slot.VehicleRed,new Vector3(0,.2f,-2.25f),Vector3.right*1.9f,Vector3.up*.05f,Vector3.forward*.45f);
            s.Box(Slot.VehicleRed,new Vector3(0,.65f,-2.28f),Vector3.right*.055f,Vector3.up*.6f,Vector3.forward*.45f);
        }
    }
}
