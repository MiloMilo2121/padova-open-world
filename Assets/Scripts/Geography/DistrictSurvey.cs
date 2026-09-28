using System;
using UnityEngine;

namespace Padova.Geography
{
    public sealed class DistrictSurvey : MonoBehaviour
    {
        public double OriginEasting;
        public double OriginNorthing;
        public float VerticalOrigin;
        public int VolumeCount;
        public int SurfaceCount;
        public int OpenPorticoCount;
        public string SourceHash;
        public SurveyAnchor[] Anchors;
    }

    [Serializable]
    public class SurveyAnchor
    {
        public string Name;
        public string SourceId;
        public Vector3 Position;
    }
}
