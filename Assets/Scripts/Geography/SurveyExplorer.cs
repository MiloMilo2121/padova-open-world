using UnityEngine;
using UnityEngine.InputSystem;

namespace Padova.Geography
{
    [RequireComponent(typeof(Camera))]
    public sealed class SurveyExplorer : MonoBehaviour
    {
        public DistrictSurvey District;
        public SurveyFeature Selected;
        public bool PlanView;
        public float TravelledMetres;
        public int SelectionCount;
        public int ViewChanges;
        public Vector3 HomePosition = new Vector3(245, 290, -365);
        public Vector3 HomeTarget = new Vector3(10, 0, 10);
        Camera view;
        GUIStyle title, subtitle, small, body, badge;
        readonly Color ink = new Color(0.89f, 0.91f, 0.93f);
        readonly Color muted = new Color(0.58f, 0.66f, 0.70f);
        readonly Color accent = new Color(0.92f, 0.68f, 0.34f);
        MaterialPropertyBlock highlight;

        void Awake()
        {
            view = GetComponent<Camera>();
            highlight = new MaterialPropertyBlock();
            Application.targetFrameRate = 60;
            ResetView();
        }

        public void ResetView()
        {
            if (!view) view = GetComponent<Camera>();
            PlanView = false;
            view.orthographic = false;
            transform.position = HomePosition;
            transform.LookAt(HomeTarget);
            ViewChanges++;
        }

        public void TogglePlan()
        {
            PlanView = !PlanView;
            view.orthographic = PlanView;
            if (PlanView)
            {
                transform.SetPositionAndRotation(new Vector3(0, 450, 0), Quaternion.Euler(90, 0, 0));
                view.orthographicSize = 255;
            }
            else ResetView();
            ViewChanges++;
        }

        public void FocusAnchor(int index)
        {
            if (District == null || index < 0 || index >= District.Anchors.Length) return;
            PlanView = false;
            view.orthographic = false;
            var at = District.Anchors[index].Position;
            transform.position = at + new Vector3(68, 105, -120);
            transform.LookAt(at);
            ViewChanges++;
        }

        void Update()
        {
            var keys = Keyboard.current;
            if (keys != null)
            {
                if (keys.rKey.wasPressedThisFrame) ResetView();
                if (keys.fKey.wasPressedThisFrame) TogglePlan();
                if (keys.digit1Key.wasPressedThisFrame) FocusAnchor(0);
                if (keys.digit2Key.wasPressedThisFrame) FocusAnchor(1);
                if (keys.digit3Key.wasPressedThisFrame) FocusAnchor(2);
                var forward = PlanView ? Vector3.forward : Vector3.ProjectOnPlane(transform.forward, Vector3.up).normalized;
                var right = PlanView ? Vector3.right : Vector3.ProjectOnPlane(transform.right, Vector3.up).normalized;
                var delta = forward * ((keys.wKey.isPressed ? 1 : 0) - (keys.sKey.isPressed ? 1 : 0))
                          + right * ((keys.dKey.isPressed ? 1 : 0) - (keys.aKey.isPressed ? 1 : 0))
                          + Vector3.up * ((keys.eKey.isPressed ? 1 : 0) - (keys.qKey.isPressed ? 1 : 0));
                var before = transform.position;
                var next = before + Vector3.ClampMagnitude(delta, 1) * (keys.leftShiftKey.isPressed ? 100 : 40) * Time.unscaledDeltaTime;
                next.x = Mathf.Clamp(next.x, -450, 450);
                next.z = Mathf.Clamp(next.z, -450, 450);
                next.y = Mathf.Clamp(next.y, 12, 650);
                transform.position = next;
                TravelledMetres += Vector3.Distance(before, next);
            }
            var mouse = Mouse.current;
            if (mouse == null) return;
            if (mouse.rightButton.isPressed && !PlanView)
            {
                var angles = transform.eulerAngles;
                float pitch = angles.x > 180 ? angles.x - 360 : angles.x;
                var delta = mouse.delta.ReadValue() * 0.14f;
                transform.rotation = Quaternion.Euler(Mathf.Clamp(pitch - delta.y, 5, 89), angles.y + delta.x, 0);
            }
            float scroll = mouse.scroll.ReadValue().y;
            if (PlanView) view.orthographicSize = Mathf.Clamp(view.orthographicSize - scroll * 0.10f, 35, 330);
            else if (Mathf.Abs(scroll) > 0.01f)
            {
                var next = transform.position + transform.forward * scroll * 0.08f;
                transform.position = new Vector3(Mathf.Clamp(next.x, -450, 450), Mathf.Clamp(next.y, 12, 650), Mathf.Clamp(next.z, -450, 450));
            }
            if (mouse.leftButton.wasPressedThisFrame)
            {
                var screen = mouse.position.ReadValue();
                var ui = new Vector2(screen.x * 1600 / Screen.width, (Screen.height-screen.y) * 1000 / Screen.height);
                if (ui.y < 175 || ui.y > 800) return;
                if (Physics.Raycast(view.ScreenPointToRay(screen), out var hit, 2000)) Select(hit.collider.GetComponent<SurveyFeature>());
            }
        }

        public void Select(SurveyFeature feature)
        {
            if (Selected) Selected.GetComponent<Renderer>().SetPropertyBlock(null);
            Selected = feature;
            if (!Selected) return;
            highlight.SetColor("_BaseColor", accent);
            Selected.GetComponent<Renderer>().SetPropertyBlock(highlight);
            SelectionCount++;
        }

        void InitStyles()
        {
            if (title != null) return;
            title = Style(36, FontStyle.Bold, ink);
            subtitle = Style(13, FontStyle.Bold, accent);
            small = Style(13, FontStyle.Normal, muted);
            body = Style(16, FontStyle.Normal, ink);
            badge = Style(12, FontStyle.Bold, ink);
        }

        static GUIStyle Style(int size, FontStyle weight, Color color)
        {
            var style = new GUIStyle(GUI.skin.label) { fontSize = size, fontStyle = weight, wordWrap = true };
            style.normal.textColor = color;
            return style;
        }

        static void Panel(Rect rect)
        {
            var previous = GUI.color;
            GUI.color = new Color(0.055f, 0.080f, 0.105f, 0.94f);
            GUI.DrawTexture(rect, Texture2D.whiteTexture);
            GUI.color = previous;
        }

        void OnGUI()
        {
            InitStyles();
            var previousMatrix = GUI.matrix;
            GUI.matrix = Matrix4x4.Scale(new Vector3(Screen.width / 1600f, Screen.height / 1000f, 1));
            Panel(new Rect(24, 24, 505, 137));
            GUI.Label(new Rect(44, 39, 460, 25), "PADOVA OPEN WORLD   /   GEOGRAPHIC FOUNDATION", subtitle);
            GUI.Label(new Rect(42, 66, 470, 55), "Centro storico", title);
            GUI.Label(new Rect(44, 119, 460, 28), "Palazzo della Ragione · Erbe · Frutta · Signori", small);
            Panel(new Rect(1115, 24, 461, 120));
            GUI.Label(new Rect(1135, 40, 420, 24), "2007 MUNICIPAL TOPOGRAPHIC SURVEY", subtitle);
            GUI.Label(new Rect(1135, 71, 420, 58), "Source footprints and elevation attributes.\nFaçades and roof forms are not reconstructed yet.", body);

            // Labels are anchored inside the source street polygons, not hand-positioned in the city.
            if (District && District.Anchors != null)
                foreach (var anchor in District.Anchors)
                {
                    var p = view.WorldToScreenPoint(anchor.Position + Vector3.up * 6);
                    if (p.z <= 0) continue;
                    var x = p.x * 1600 / Screen.width;
                    var y = (Screen.height-p.y) * 1000 / Screen.height;
                    if (x < 15 || x > 1390 || y < 175 || y > 775) continue;
                    Panel(new Rect(x-5, y-3, 188, 28));
                    GUI.Label(new Rect(x+3, y, 180, 23), anchor.Name, badge);
                }

            Panel(new Rect(24, 820, 590, 156));
            if (Selected)
            {
                GUI.Label(new Rect(44, 835, 550, 24), "SELECTED  /  " + Selected.SourceId, subtitle);
                string detail = Selected.Layer == "UN_VOL"
                    ? $"Volume height {Selected.VolumeHeight:F2} m · eave elevation {Selected.EaveElevation:F2} m\nFootprint {Selected.FootprintArea:F1} m² · " + (Selected.HasWalls ? "ground-based volume" : "portico / overhang: clearance unresolved")
                    : $"{Selected.Layer} · mapped surface {Selected.FootprintArea:F1} m²";
                GUI.Label(new Rect(44, 868, 550, 76), detail, body);
            }
            else
            {
                GUI.Label(new Rect(44, 835, 550, 24), "A CITY BUILT FROM ITS RECORDS", subtitle);
                GUI.Label(new Rect(44, 868, 550, 75), $"{District.VolumeCount:N0} building volumes · {District.SurfaceCount:N0} street / pedestrian parts\nClick geometry to inspect its source and dimensions.", body);
            }
            GUI.Label(new Rect(44, 944, 550, 25), "Cartographic colours · amber caps mark unresolved porticoes", small);

            Panel(new Rect(900, 848, 676, 128));
            GUI.Label(new Rect(922, 861, 632, 24), "EXPLORE   /   " + (PlanView ? "NORTH-UP PLAN" : "3D SURVEY"), subtitle);
            GUI.Label(new Rect(922, 892, 632, 28), "WASD move   ·   Q / E altitude   ·   right-drag look   ·   scroll zoom", body);
            GUI.Label(new Rect(922, 922, 632, 27), "F plan / 3D   ·   R reset   ·   1 Erbe   ·   2 Frutta   ·   3 Signori", small);
            Panel(new Rect(0, 978, 1600, 22));
            GUI.Label(new Rect(24, 979, 1390, 21), "Comune di Padova / Regione del Veneto · DBT 2007 · IODL 2.0 · EPSG:7791 · 1 unit = 1 metre", small);
            GUI.matrix = previousMatrix;
        }
    }
}
