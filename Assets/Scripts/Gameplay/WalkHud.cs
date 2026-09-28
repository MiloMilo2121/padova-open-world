using UnityEngine;

namespace Padova.Gameplay
{
    public sealed class WalkHud : MonoBehaviour
    {
        public ThirdPersonMotor Player;
        public Transform GoalMarker;
        public string LocationName = "Piazza della Frutta";
        GUIStyle title, body, small;
        readonly Color white = new Color(0.96f, 0.96f, 0.92f);

        void Update()
        {
            if (GoalMarker) GoalMarker.gameObject.SetActive(!Player.ReachedGoal);
        }

        GUIStyle Style(int size, FontStyle weight)
        {
            var s = new GUIStyle(GUI.skin.label) { fontSize = size, fontStyle = weight };
            s.normal.textColor = white;
            return s;
        }
        static void Panel(Rect r)
        {
            var c = GUI.color;
            GUI.color = new Color(0.045f, 0.06f, 0.075f, 0.84f);
            GUI.DrawTexture(r, Texture2D.whiteTexture);
            GUI.color = c;
        }
        void OnGUI()
        {
            if (!Player) return;
            if (title == null) { title = Style(24, FontStyle.Bold); body = Style(16, FontStyle.Normal); small = Style(12, FontStyle.Normal); }
            var matrix = GUI.matrix;
            GUI.matrix = Matrix4x4.Scale(new Vector3(Screen.width/1600f, Screen.height/1000f, 1));
            Panel(new Rect(28, 26, 490, 86));
            GUI.Label(new Rect(47, 39, 450, 35), "PADOVA  /  " + LocationName.ToUpperInvariant(), title);
            GUI.Label(new Rect(47, 78, 450, 25), "Surveyed footprints, heights and porticoes · DBT 2007", small);
            var distance = Vector3.ProjectOnPlane(Player.Goal-Player.transform.position, Vector3.up).magnitude;
            Panel(new Rect(28, 133, 330, 66));
            GUI.Label(new Rect(46, 145, 298, 28), Player.ReachedGoal ? "Piazza crossed. Keep exploring." : "Reach the piazza marker", body);
            GUI.Label(new Rect(46, 174, 298, 22), Player.ReachedGoal ? "First walk complete" : Mathf.CeilToInt(distance) + " m away", small);
            if (!Player.ReachedGoal)
            {
                var p = Camera.main.WorldToScreenPoint(Player.Goal+Vector3.up*2.7f);
                if (p.z > 0)
                    GUI.Label(new Rect(p.x*1600/Screen.width-28, (Screen.height-p.y)*1000/Screen.height, 110, 28), Mathf.CeilToInt(distance)+" m", body);
            }
            Panel(new Rect(28, 904, 900, 64));
            GUI.Label(new Rect(46, 914, 865, 26), "Arrow keys move   ·   Space jump   ·   Shift run   ·   Tab toggle run", body);
            GUI.Label(new Rect(46, 943, 865, 22), "Q / E orbit   ·   C centre camera   ·   Click-drag look   ·   Scroll zoom   ·   R return to start", small);
            Panel(new Rect(0, 979, 1600, 21));
            GUI.Label(new Rect(28, 980, 1470, 21), "Survey: Comune di Padova / Regione Veneto, IODL 2.0 · Names: © OpenStreetMap contributors, ODbL · Textures & sky: Poly Haven CC0 · Character: Kenney CC0", small);
            GUI.matrix = matrix;
        }
    }
}
