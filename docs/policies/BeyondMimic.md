# BeyondMimic Policy

**Whole-body motion tracking** via ONNX, with the reference motion embedded in
the model itself.

BeyondMimic is a deployment-oriented tracker: one `.onnx` file carries both the
actor weights *and* the retargeted motion clip as `metadata_props`. The wrapper
loads the model with `onnxruntime`, reads DOF config + action scales from the
metadata, and rolls the embedded motion forward each step.

**Origin:** [BeyondMimic / whole_body_tracking](https://github.com/HybridRobotics/whole_body_tracking).
The wrapper in this repo talks to the exported ONNX surface only — no
dependency on the upstream training stack.

---

## Install

```bash
pip install onnxruntime          # CPU
pip install onnxruntime-gpu      # CUDA / TensorRT
```

Then drop the checkpoint somewhere visible:

```
models/beyondmimic_<motion>.onnx
```

---

## Quick start

```python
from genPiHub import load_policy

policy = load_policy(
    name="BeyondMimicPolicy",
    policy_file="models/beyondmimic_dance.onnx",
    device="cuda",        # "cpu" | "cuda" | "tensorrt"
)

policy.reset()
obs, _ = policy.get_observation(env_data, {})
action = policy.get_action(obs)
policy.post_step_callback()
```

See [`scripts/beyondmimic/genesislab/play_beyondmimic.py`](../../scripts/beyondmimic/genesislab/play_beyondmimic.py)
for an end-to-end Genesis run (records to `output/beyondmimic.mp4`).

---

## Interface

### `env_data`

| Key            | Shape  | Notes                                     |
|----------------|--------|-------------------------------------------|
| `dof_pos`      | `(29,)`| URDF order, radians                       |
| `dof_vel`      | `(29,)`| URDF order, rad/s                         |
| `base_quat`    | `(4,)` | `[w, x, y, z]`                            |
| `base_ang_vel` | `(3,)` | Body frame                                |
| `base_lin_vel` | `(3,)` | World frame (only used when `without_state_estimator=False`) |

### `ctrl_data`

Usually empty — motion comes from the ONNX metadata. If you want to drive the
reference externally, set `use_motion_from_model=False` in the config and pass
a `(num_actions*2,)` joint-pos+vel command via `ctrl_data["motion_command"]`.

### Observation layout

```
wose mode (without_state_estimator=True, default):
  command(2·N) + ori(6) + ang_vel(3) + joint_pos_rel(N) + joint_vel(N) + last_action(N)
  = 154 dims for 29-DoF G1

with state estimator:
  + base_lin_vel(3) + anchor_pos(3) = 160 dims
```

`ori` is the 6D orientation representation (first two columns of the rotation
matrix), not Euler angles.

---

## Configuration

```python
from genPiHub.configs import BeyondMimicPolicyConfig

cfg = BeyondMimicPolicyConfig(
    policy_file="models/beyondmimic_dance.onnx",

    # Load joint names, defaults, stiffness/damping, action scales from ONNX
    # metadata. Strongly recommended — these must match the training setup.
    use_model_meta_config=True,

    # Motion source. Default = use the clip embedded in the ONNX model.
    use_motion_from_model=True,
    max_timestep=-1,      # -1 = auto-detect from model
    start_timestep=0,

    # No separate state estimator (most checkpoints were trained in this mode)
    without_state_estimator=True,

    # Per-joint action scales. Ignored when use_model_meta_config=True.
    action_scales=[],
    action_beta=1.0,      # EMA smoothing (1.0 = off)

    device="cuda",
    freq=50.0,
)
```

For common robot setups (G1 29 DoF), pre-baked constants live in
[`genPiHub/envs/beyondmimic/genesislab/robot_cfg.py`](../../genPiHub/envs/beyondmimic/genesislab/robot_cfg.py):
`G1_BEYONDMIMIC_DEFAULT_POS`, `G1_BEYONDMIMIC_STIFFNESS`, `G1_BEYONDMIMIC_DAMPING`,
`G1_BEYONDMIMIC_INITIAL_BASE_QUAT` (wxyz identity), etc.

---

## Motion lifecycle

1. On `reset()`, the wrapper resets `timestep = start_timestep`, clears the
   yaw-alignment transform, and fires a zero-input warm-up forward pass.
2. Each `get_observation` call advances the embedded motion cursor via
   `play_speed` and pulls the next `(joint_pos, joint_vel)` reference.
3. `post_step_callback()` advances `step_count`. When the cursor passes the end
   of the clip, `flag_motion_done` is set — callers can choose to reset or
   wrap.

The yaw of the first-frame reference is captured on the first call and used to
rotate incoming base orientation into the motion's frame, so the robot's
starting heading does not matter.

---

## Robot support

- **Unitree G1 29 DoF** — the shipping configuration; constants in
  `envs/beyondmimic/genesislab/robot_cfg.py`.
- **Other humanoids** — in principle supported: the wrapper reads the joint
  list from ONNX metadata and adapts. In practice the checkpoint must have
  been trained for that robot.

---

## Troubleshooting

**`onnxruntime not available` warning.** The wrapper does not hard-fail at
import; it only fails when you actually try to run inference. Install
`onnxruntime-gpu` for CUDA or `onnxruntime` for CPU-only.

**`Observation shape mismatch` at first step.** Usually the `without_state_estimator`
flag does not match the checkpoint. Try toggling it; the obs dim jumps from 154
to 160 when the state estimator is enabled.

**Robot lurches sideways on reset.** The yaw-alignment transform is captured on
the *first* observation, not in `reset()`. Make sure you call
`policy.get_observation()` before the first `env.step()`.

**Motion loops too fast / too slow.** `play_speed` defaults to 1.0; the motion
is sampled at the same frequency as `cfg.freq` (50 Hz by default). If the clip
was recorded at 30 Hz you'll want `freq=30.0` to match, not faster playback.
