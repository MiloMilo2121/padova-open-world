using System;

namespace Padova.Architecture
{
    /// <summary>Compact architecture plan written by Tools/architecture/plan_city.py from the DBT survey.</summary>
    [Serializable]
    public sealed class CityPlan
    {
        public int version;
        public float[] plane;
        public float roofSlope;
        public float[] extent;
        public PlanUnit[] units;
        public PlanRoof[] roofs;
        public PlanGround[] ground;
        public float[] curbs;
        public RagioneFrame ragione;
        public string attribution;

        public float GroundAt(float x, float z) => plane[0] * x + plane[1] * z + plane[2];
    }

    [Serializable]
    public sealed class PlanUnit
    {
        public string id, name, use;
        public bool suspended;
        public float ground, top, surveyTop, under, area, cx, cz;
        public float[] outline;
        public int[] ringSizes;
        /// <summary>Eight values per wall segment: x0, z0, x1, z1, y0, y1, kind, flags.</summary>
        public float[] segs;
        public float[] ceiling;
        public int[] ceilingTris;
    }

    [Serializable]
    public sealed class PlanRoof
    {
        public string[] units;
        public string key, use;
        public float cx, cz, @base;
        public float[] v;
        public int[] t;
        public float[] wv;
        public int[] wt;
    }

    [Serializable]
    public sealed class PlanGround
    {
        public string mat;
        public float level;
        public float[] v;
        public int[] t;
    }

    [Serializable]
    public sealed class RagioneFrame
    {
        public float cx, cz, ax, az, ground;
        public float[] hall, northLoggia, southLoggia, northShops, southShops;
        public float northGap, southGap, hallEave, loggiaEave, shopEave, ridge;
        public string sources;
    }

    public enum SegmentKind { Street = 0, Upper = 1, PorticoBack = 2, Blank = 3, Arcade = 4 }

    [Flags]
    public enum SegmentFlags { None = 0, TopExposed = 1, Courtyard = 2, OverPortico = 4 }
}
