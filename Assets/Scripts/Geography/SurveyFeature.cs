using UnityEngine;

namespace Padova.Geography
{
    // Every rendered part retains the upstream DBT record identity.
    public sealed class SurveyFeature : MonoBehaviour
    {
        public string SourceId;
        public string Layer;
        public string Portion;
        public float FootprintArea;
        public float EaveElevation;
        public float VolumeHeight;
        public bool HasWalls;
        public const int SurveyYear = 2007;
    }
}
