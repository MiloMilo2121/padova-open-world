using UnityEngine;
using UnityEngine.InputSystem;

namespace Padova.Gameplay
{
    [DefaultExecutionOrder(100)]
    public sealed class ThirdPersonCamera : MonoBehaviour
    {
        public ThirdPersonMotor Player;
        public float Yaw = 270;
        public float Pitch = 14;
        public float Distance = 4.4f;
        public float ActualDistance;
        public bool Obstructed;
        public bool CursorCaptured;
        Vector3 velocity;
        bool snap;
        float lastManualLook;
        InputAction centerAction, releaseAction;

        void Awake()
        {
            centerAction = new InputAction("Center camera", InputActionType.Button, "<Keyboard>/c");
            releaseAction = new InputAction("Release cursor", InputActionType.Button, "<Keyboard>/escape");
            centerAction.performed += _ => { if(Player && Player.Visual) Yaw=Player.Visual.eulerAngles.y; Pitch=-4; lastManualLook=Time.unscaledTime; };
            releaseAction.performed += _ => ReleaseCursor();
        }
        void OnEnable() { centerAction?.Enable(); releaseAction?.Enable(); }
        void Start() { ResetCamera(); }

        public void ResetCamera()
        {
            Yaw = Player ? Player.SpawnYaw : 180;
            Pitch = -4;
            Distance = 5.8f;
            lastManualLook = Time.unscaledTime;
            snap = true;
        }

        public void ReleaseCursor()
        {
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
            CursorCaptured = false;
        }

        void OnDisable() { centerAction?.Disable(); releaseAction?.Disable(); ReleaseCursor(); }
        void OnDestroy() { centerAction?.Dispose(); releaseAction?.Dispose(); }

#if UNITY_EDITOR || DEVELOPMENT_BUILD
        public void SetTestHeading(float yaw)
        {
            Yaw = yaw;
            lastManualLook = Time.unscaledTime + 30;
            snap = true;
        }
#endif

        void LateUpdate()
        {
            if (!Player || Player.ControlsPaused) return;
            var mouse = Mouse.current;
            var keyboard = Keyboard.current;
            if (keyboard != null)
            {
                float orbit = (keyboard.eKey.isPressed ? 1 : 0) - (keyboard.qKey.isPressed ? 1 : 0);
                if (Mathf.Abs(orbit) > 0)
                {
                    Yaw += orbit * 90 * Time.unscaledDeltaTime;
                    lastManualLook = Time.unscaledTime;
                }
            }
            if (mouse != null)
            {
                if (mouse.leftButton.isPressed || mouse.rightButton.isPressed)
                {
                    var delta = mouse.delta.ReadValue();
                    Yaw += delta.x * 0.12f;
                    Pitch = Mathf.Clamp(Pitch-delta.y*0.10f, -12, 65);
                    lastManualLook = Time.unscaledTime;
                }
                Distance = Mathf.Clamp(Distance-mouse.scroll.ReadValue().y*0.006f, 2, 7);
            }
            // Recenter after steering has stopped, avoiding a camera-relative strafe feedback loop.
            if (Time.unscaledTime-lastManualLook > 1.8f && Player.CurrentSpeed < 0.1f && Player.Visual)
                Yaw = Mathf.LerpAngle(Yaw, Player.Visual.eulerAngles.y, 1-Mathf.Exp(-2.5f*Time.unscaledDeltaTime));
            var pivot = Player.transform.position + Vector3.up * 1.4f;
            var rotation = Quaternion.Euler(Pitch, Yaw, 0);
            var back = rotation * Vector3.back;
            float length = Distance;
            Obstructed = Physics.SphereCast(pivot, 0.20f, back, out var hit, Distance, ThirdPersonMotor.WorldMask, QueryTriggerInteraction.Ignore);
            if (Obstructed) length = Mathf.Max(0.25f, hit.distance-0.12f);
            var goal = pivot + back * length;
            // Resolve obstruction immediately; smoothing through the wall would reintroduce clipping.
            transform.position = snap || Obstructed ? goal : Vector3.SmoothDamp(transform.position, goal, ref velocity, 0.07f);
            transform.rotation = rotation;
            ActualDistance = Vector3.Distance(pivot, transform.position);
            snap = false;
        }
    }
}
