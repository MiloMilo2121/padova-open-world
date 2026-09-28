using System;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace Padova.Architecture
{
    /// <summary>Reference-modelled details anchored to DBT outlines and vertical limits.
    /// Sources and approximations are listed in Data/World/landmarks.md. No photo projection.</summary>
    public sealed class LandmarkBuilder
    {
        readonly MeshSink s;
        readonly FacadeBuilder fb;
        readonly CityPlan plan;
        public readonly List<(Vector3 centre,Vector3 size,Quaternion rotation)> Colliders=new();
        public readonly MeshSink Ground=new();
        static readonly HashSet<string> Custom=new(){"UN_VOL:42143","UN_VOL:42159","UN_VOL:41276","UN_VOL:36949","UN_VOL:40598","UN_VOL:33889"};
        public static bool Replaces(PlanUnit u)=>Custom.Contains(u.id);
        public static bool Replaces(PlanRoof r)=>r.units!=null && r.units.Any(Custom.Contains);
        public LandmarkBuilder(MeshSink sink,CityPlan data){s=sink;fb=new FacadeBuilder(sink);plan=data;}

        public static UnitStyle Style(PlanUnit u)
        {
            var st=UnitStyle.For(u);
            if(u.name=="Palazzo del Bo")
            {
                st.Wall=Slot.Plaster6;st.Shutters=false;st.Surround=true;st.StringCourse=true;
                st.RoundColumns=true;st.ArcadeArch=Arch.None;st.ColumnSpacing=3.0f;
                st.GroundArch=Arch.Round;st.UpperArch=Arch.None;st.Balcony=false;
            }
            if(u.id=="UN_VOL:44273"||u.id=="UN_VOL:44720")
            {
                st.Wall=Slot.Plaster2;st.Surround=true;st.Shutters=false;st.Bay=3.8f;st.FloorH=5.1f;st.StringCourse=true;
            }
            if(u.name=="Duomo di Padova")st.Wall=Slot.Brick;
            return st;
        }

        static IEnumerable<Frame> Edges(PlanUnit u,bool holes=false)
        {
            int start=0;
            for(int r=0;r<u.ringSizes.Length;r++)
            {
                int n=u.ringSizes[r];
                if((holes && r>0)||(!holes && r==0))
                    for(int i=0;i<n;i++)
                    {
                        int a=start+i,b=start+(i+1)%n;
                        yield return new Frame(new Vector2(u.outline[2*a],u.outline[2*a+1]),new Vector2(u.outline[2*b],u.outline[2*b+1]));
                    }
                start+=n;
            }
        }
        static Frame Front(PlanUnit u,Vector3 direction)=>Edges(u).Where(f=>Vector3.Dot(f.N,direction)>.65f).OrderByDescending(f=>f.L).First();
        UnitStyle Plain(Slot slot)=>new UnitStyle{Wall=slot,RoundColumns=true,ColumnSpacing=3,ArcadeArch=Arch.Round,Rng=new System.Random(1532)};

        public void Build()
        {
            var by=plan.units.ToDictionary(u=>u.id);
            Clock(by["UN_VOL:42159"],by["UN_VOL:42143"]);
            Dome(by["UN_VOL:41276"],34.43f,Slot.Lead);
            Lantern(by["UN_VOL:36949"],by["UN_VOL:41276"].top);
            Dome(by["UN_VOL:40598"],34.43f,Slot.Lead);
            Baptistery(by["UN_VOL:33889"]);
            foreach(var u in plan.units)
            {
                if(u.id=="UN_VOL:44273"||u.id=="UN_VOL:44720")Capitanio(u);
                if(u.id=="UN_VOL:45916")Bo(u);
                if(u.id=="UN_VOL:43028"||u.id=="UN_VOL:31217"||u.id=="UN_VOL:43091")CathedralFront(u);
            }
        }

        void Disc(Slot slot,in Frame f,float u,float y,float radius,float depth,int segments=64)
        {
            for(int i=0;i<segments;i++)
            {
                float a=i*Mathf.PI*2/segments,b=(i+1)*Mathf.PI*2/segments;
                s.Tri(slot,f.P(u,y,depth),f.P(u+Mathf.Cos(a)*radius,y+Mathf.Sin(a)*radius,depth),f.P(u+Mathf.Cos(b)*radius,y+Mathf.Sin(b)*radius,depth),f.N,Vector2.zero,Vector2.zero,Vector2.zero);
            }
        }
        void Ring(Slot slot,Frame f,float u,float y,float radius,float width,float depth)
        {
            for(int i=0;i<64;i++)
            {
                float a=i*Mathf.PI/32,b=(i+1)*Mathf.PI/32;
                Vector3 P(float angle,float r)=>f.P(u+Mathf.Cos(angle)*r,y+Mathf.Sin(angle)*r,depth);
                s.Quad(slot,P(a,radius),P(b,radius),P(b,radius+width),P(a,radius+width),f.N,Vector2.zero,Vector2.right,Vector2.one,Vector2.up);
            }
        }
        void Stroke(in Frame f,Vector2 a,Vector2 b,float width,float depth,Slot slot=Slot.Gold)
        {
            var d=(b-a).normalized;var n=new Vector2(-d.y,d.x)*width/2;
            s.Quad(slot,f.P(a.x+n.x,a.y+n.y,depth),f.P(b.x+n.x,b.y+n.y,depth),f.P(b.x-n.x,b.y-n.y,depth),f.P(a.x-n.x,a.y-n.y,depth),f.N,Vector2.zero,Vector2.right,Vector2.one,Vector2.up);
        }
        static string Roman(int value)
        {
            string result="";
            foreach(var pair in new[]{(10,"X"),(9,"IX"),(5,"V"),(4,"IV"),(1,"I")})while(value>=pair.Item1){result+=pair.Item2;value-=pair.Item1;}
            return result;
        }
        void Clock(PlanUnit body,PlanUnit cap)
        {
            var front=Front(body,Vector3.right);float g=body.ground,top=body.top,w=front.L;
            fb.Style=Plain(Slot.Plaster9);
            foreach(var f in Edges(body))
            {
                bool gate=Mathf.Abs(f.N.x)>.7f;
                var rows=new List<FacadeBuilder.Row>();
                var portal=new Opening{U0=f.L*.22f,U1=f.L*.78f,Yb=g,Ys=g+5.1f,Yt=g+5.1f+f.L*.28f,Arch=Arch.Round};
                if(gate)rows.Add(new FacadeBuilder.Row{Yb=g,Yt=portal.Yt,Ops=new List<Opening>{portal}});
                fb.WallWithRowsLocal(Slot.Plaster9,f,g-.1f,top-1.05f,rows);
                for(float x=.1f;x<f.L-.2f;x+=1.6f)fb.Block(Slot.Stone,f,x,Mathf.Min(x+.7f,f.L),top-1.05f,top,-.25f,.05f);
                if(gate)
                {
                    fb.Reveal(Slot.Stone,f,portal,0,-.5f);fb.Surround(Slot.Stone,f,portal,.38f,.05f);
                    var rot=Quaternion.LookRotation(f.N);
                    Colliders.Add((f.P(portal.U0/2,(g+portal.Yt)/2,-.2f),new Vector3(portal.U0,portal.Yt-g,.4f),rot));
                    Colliders.Add((f.P((portal.U1+f.L)/2,(g+portal.Yt)/2,-.2f),new Vector3(f.L-portal.U1,portal.Yt-g,.4f),rot));
                    Colliders.Add((f.P(f.L/2,(portal.Yt+top)/2,-.2f),new Vector3(f.L,top-portal.Yt,.4f),rot));
                }
                else Colliders.Add((f.P(f.L/2,(g+top)/2,-.2f),new Vector3(f.L,top-g,.4f),Quaternion.LookRotation(f.N)));
                fb.Block(Slot.Stone,f,-.15f,f.L+.15f,g+8.2f,g+8.6f,-.1f,.35f);
                fb.Block(Slot.Stone,f,-.15f,f.L+.15f,top-1.4f,top-1.05f,-.1f,.3f);
                for(float y=g+10;y<top-7;y+=.5f)
                {
                    fb.Block(Slot.Stone,f,0,.43f,y,y+.25f,0,.08f);fb.Block(Slot.Stone,f,f.L-.43f,f.L,y,y+.25f,0,.08f);
                }
            }
            float cy=g+(top-g)*.55f,r=Mathf.Min(2.7f,w*.35f),cx=w/2;
            Disc(Slot.ClockBlue,front,cx,cy,r,.055f);
            Ring(Slot.Stone,front,cx,cy,r,.22f,.1f);Ring(Slot.Gold,front,cx,cy,r*.70f,.045f,.13f);
            Ring(Slot.Gold,front,cx,cy,r*.40f,.045f,.13f);Disc(Slot.Gold,front,cx,cy,.19f,.15f);
            for(int hour=1;hour<=24;hour++)
            {
                float angle=Mathf.PI*.5f-hour*Mathf.PI/12;
                var c=new Vector2(cx+Mathf.Cos(angle)*r*.85f,cy+Mathf.Sin(angle)*r*.85f);
                string label=Roman(hour);float size=.14f;
                for(int j=0;j<label.Length;j++)
                {
                    float x=c.x+(j-label.Length/2f)*size,y=c.y;
                    if(label[j]=='I')Stroke(front,new Vector2(x,y-.14f),new Vector2(x,y+.14f),.028f,.16f);
                    else if(label[j]=='V'){Stroke(front,new Vector2(x-.045f,y+.14f),new Vector2(x,y-.14f),.028f,.16f);Stroke(front,new Vector2(x,y-.14f),new Vector2(x+.055f,y+.14f),.028f,.16f);}
                    else {Stroke(front,new Vector2(x-.05f,y-.14f),new Vector2(x+.05f,y+.14f),.028f,.16f);Stroke(front,new Vector2(x+.05f,y-.14f),new Vector2(x-.05f,y+.14f),.028f,.16f);}
                }
            }
            for(int i=0;i<11;i++)
            {
                float a=i*Mathf.PI*2/11;var c=new Vector2(cx+Mathf.Cos(a)*r*.55f,cy+Mathf.Sin(a)*r*.55f);
                Stroke(front,c-Vector2.up*.12f,c+Vector2.up*.12f,.035f,.16f);Stroke(front,c-Vector2.right*.1f,c+Vector2.right*.1f,.035f,.16f);
            }
            Stroke(front,new Vector2(cx,cy),new Vector2(cx+r*.52f,cy+r*.32f),.09f,.19f);
            Stroke(front,new Vector2(cx,cy),new Vector2(cx-r*.20f,cy+r*.62f),.045f,.20f);
            foreach(float x in new[]{.85f,1.45f,w-1.45f,w-.85f})
            {
                s.Cylinder(Slot.Stone,front.P(x,g+.3f,.26f),.18f,6.8f,12,.9f);
                fb.Block(Slot.Stone,front,x-.28f,x+.28f,g,g+.3f,0,.6f);
                fb.Block(Slot.Stone,front,x-.28f,x+.28f,g+7.0f,g+7.25f,0,.6f);
            }
            fb.Block(Slot.Stone,front,-.2f,w+.2f,g+7.25f,g+8.2f,0,.75f);
            foreach(float x in new[]{cx-r*.95f,cx+r*.95f})foreach(float y in new[]{cy-r*.95f,cy+r*.95f})
            {Disc(Slot.Dark,front,x,y,.23f,.07f);Ring(Slot.Stone,front,x,y,.23f,.08f,.12f);}
            // Lantern openings, bounded by the surveyed rectangular top and circular cap top.
            foreach(var f in Edges(body))for(int k=0;k<2;k++)
            {
                float c=f.L*(k+1)/3;var o=new Opening{U0=c-.5f,U1=c+.5f,Yb=top-4.2f,Ys=top-2.2f,Yt=top-1.7f,Arch=Arch.Round};
                fb.Panel(Slot.Dark,f,o,.025f);fb.Surround(Slot.Stone,f,o,.15f,.09f);
            }
            Dome(cap,body.top,Slot.Lead);
            var centre=new Vector3(body.cx,g+.06f,body.cz);
            Ground.Box(Slot.Trachyte,centre,front.E*(w*.28f),Vector3.up*.04f,front.N*4.1f);
        }

        void Dome(PlanUnit u,float baseY,Slot material)
        {
            var points=u.outline.Take(u.ringSizes[0]*2).ToArray();
            float minx=float.MaxValue,maxx=float.MinValue,minz=float.MaxValue,maxz=float.MinValue;
            for(int i=0;i<points.Length;i+=2){minx=Mathf.Min(minx,points[i]);maxx=Mathf.Max(maxx,points[i]);minz=Mathf.Min(minz,points[i+1]);maxz=Mathf.Max(maxz,points[i+1]);}
            var c=new Vector3((minx+maxx)/2,0,(minz+maxz)/2);float rx=(maxx-minx)/2,rz=(maxz-minz)/2;
            float bottom=Mathf.Min(baseY,u.top-.3f),height=u.top-bottom;
            var vertices=new Vector3[49,17];var uv=new Vector2[49,17];
            for(int a=0;a<=48;a++)for(int b=0;b<=16;b++)
            {
                float angle=a*Mathf.PI/24,phi=b*Mathf.PI/32;
                vertices[a,b]=c+new Vector3(Mathf.Cos(angle)*rx*Mathf.Cos(phi),bottom+height*Mathf.Sin(phi),Mathf.Sin(angle)*rz*Mathf.Cos(phi));
                uv[a,b]=new Vector2(a*rx*Mathf.PI/24,b*height/16);
            }
            s.Grid(material,vertices,uv,true);
        }
        void Lantern(PlanUnit u,float bottom)
        {
            var edges=Edges(u).ToArray();float radius=edges.Max(f=>Vector2.Distance(new Vector2(f.A.x,f.A.z),new Vector2(u.cx,u.cz)));
            float top=u.top,roof=top-1.5f;
            s.Cylinder(Slot.Stone,new Vector3(u.cx,bottom,u.cz),radius,roof-bottom,24);
            for(int i=0;i<8;i++)
            {
                float a=i*Mathf.PI/4;var n=new Vector3(Mathf.Cos(a),0,Mathf.Sin(a));var e=new Vector3(-n.z,0,n.x);
                var f=new Frame(new Vector2(u.cx+n.x*radius-e.x*.7f,u.cz+n.z*radius-e.z*.7f),new Vector2(u.cx+n.x*radius+e.x*.7f,u.cz+n.z*radius+e.z*.7f));
                if(Vector3.Dot(f.N,n)<0)f=new Frame(new Vector2(f.P(f.L,0,0).x,f.P(f.L,0,0).z),new Vector2(f.A.x,f.A.z));
                var o=new Opening{U0=.25f,U1=f.L-.25f,Yb=bottom+1,Ys=roof-1.4f,Yt=roof-.9f,Arch=Arch.Round};fb.Panel(Slot.Dark,f,o,.02f);fb.Surround(Slot.Stone,f,o,.14f,.08f);
            }
            Dome(u,roof,Slot.Lead);
        }
        void Baptistery(PlanUnit u)
        {
            float radius=Mathf.Sqrt(u.area/Mathf.PI),g=u.ground,drum=u.top-3.5f;
            var c=new Vector3(u.cx,g,u.cz);s.Cylinder(Slot.Brick,c,radius,drum-g,32);
            for(int i=0;i<16;i++)
            {
                float a=i*Mathf.PI/8;var n=new Vector3(Mathf.Cos(a),0,Mathf.Sin(a));
                s.Box(Slot.Brick,new Vector3(u.cx,0,u.cz)+n*(radius+.06f)+Vector3.up*((g+drum)/2),new Vector3(-n.z,0,n.x)*.12f,Vector3.up*((drum-g)/2),n*.12f);
            }
            Dome(u,drum,Slot.Roof);
        }
        void Capitanio(PlanUnit u)
        {
            foreach(var f in Edges(u).Where(f=>f.N.x>.7f && f.L>3))
            {
                for(float x=.15f;x<f.L;x+=3.8f)fb.Block(Slot.Stone,f,x,x+.22f,u.ground+4.8f,u.top-.55f,0,.12f);
                fb.Block(Slot.Stone,f,0,f.L,u.ground+5.0f,u.ground+5.3f,0,.22f);
                fb.Block(Slot.Stone,f,0,f.L,u.top-.6f,u.top-.25f,0,.35f);
            }
        }
        void CathedralFront(PlanUnit u)
        {
            foreach(var f in Edges(u).Where(f=>f.N.x>.8f && f.L>7))
            {
                fb.Rect(Slot.Brick,f,0,u.ground,f.L,u.top,.035f);
                int count=u.id=="UN_VOL:43028"?3:1;
                for(int i=0;i<count;i++)
                {
                    float c=f.L*(i+1)/(count+1);float w=Mathf.Min(2.4f,f.L/(count+1)*.6f);
                    var o=new Opening{U0=c-w/2,U1=c+w/2,Yb=u.ground,Ys=u.ground+4.1f,Yt=u.ground+4.1f,Arch=Arch.None};
                    fb.Panel(Slot.Door,f,o,.045f);fb.Surround(Slot.Stone,f,o,.25f,.17f);
                }
                if(count==3)
                    foreach(float x in new[]{f.L*.24f,f.L*.76f}){Disc(Slot.Glass,f,x,u.ground+14,1.35f,.055f);Ring(Slot.Stone,f,x,u.ground+14,1.35f,.22f,.12f);}
            }
        }
        void Bo(PlanUnit u)
        {
            foreach(var f in Edges(u,true))
            {
                if(f.L<3)continue;
                float g=u.ground,mid=g+(u.top-g)*.48f;
                fb.Rect(Slot.Plaster6,f,-1.5f,g,f.L+1.5f,u.top,-1.4f);
                foreach(var level in new[]{(g,mid),(mid,u.top)})
                {
                    float height=level.Item2-level.Item1-.55f;
                    for(float x=.35f;x<f.L-.2f;x+=3.1f)
                    {
                        s.Cylinder(Slot.Stone,f.P(x,level.Item1+.2f,0),.19f,height-.1f,10,.86f);
                        fb.Block(Slot.Stone,f,x-.3f,x+.3f,level.Item2-.8f,level.Item2-.55f,-.45f,0);
                        fb.Block(Slot.Stone,f,x-.26f,x+.26f,level.Item1,level.Item1+.2f,-.42f,0);
                    }
                    fb.Block(Slot.Stone,f,0,f.L,level.Item2-.55f,level.Item2-.15f,-.45f,.02f);
                    fb.Block(Slot.Stone,f,0,f.L,level.Item2-.15f,level.Item2,-1.45f,.2f);
                }
                for(float x=1.2f;x<f.L-.5f;x+=2.2f)
                {
                    var p=f.P(x,mid-.6f,.06f);s.Tri(Slot.Stone,p-f.E*.23f,p+f.E*.23f,p-Vector3.up*.45f,f.N,Vector2.zero,Vector2.right,Vector2.up);
                    fb.Block(Slot.Stone,f,x-.25f,x+.25f,mid-.6f,mid-.2f,.02f,.09f);
                }
            }
        }
    }
}
