# AMO Policy

**Adaptive Motion Optimization** for humanoid whole-body control.

AMO is an online RL policy that maps a small command vector (locomotion velocity
+ torso pose + height) to joint PD targets. Trained with procedural command
sampling on Unitree G1 (23 DoF), it handles locomotion, turning, crouching, and
torso orientation without reference motions.

**Paper:** AMO: Adaptive Motion Optimization for Hyper-Dexterous Humanoid Whole-Body Control (RSS 2025)
**Origin:** Renforce Dynamics research, ported verbatim into genPiHub as the `amo_policy_impl` module.

---

## Install

AMO is bundled with genPiHub — no extra deps. You only need the two TorchScript
checkpoints:

```
<model_dir>/
├── amo_jit.pt               # main actor (23-dim action)
├── adapter_jit.pt           # proprioceptive adapter
└── adapter_norm_stats.pt    # normalization statistics
```

Default search path is `.reference/AMO/` at the project root; override via
`policy_file` / `adapter_file` / `norm_stats_file` in the config.

---

## Quick start

```python
from genPiHub import load_policy

policy = load_policy(
    name="AMOPolicy",
    model_dir=".reference/AMO",
    device="cuda",
)

policy.reset()
obs, _    = policy.get_observation(env_data, {"commands": commands})
action    = policy.get_action(obs)
```

See [`genPiHub/examples/amo_example.py`](../../genPiHub/examples/amo_example.py) for a
standalone load test with dummy data and
[`scripts/amo/genesislab/`](../../scripts/amo/genesislab/) for runnable Genesis
integration:

- `play_amo.py` — keyboard teleop
- `demo_amo_capabilities.py` — scripted 22-segment capability showcase
- `play_amo_with_terrain_usd.py` — USD terrain playback
- `play_amo_mesh_terrain.py` — mesh terrain playback

---

## Interface

### `env_data`

| Key            | Shape  | Notes                                          |
|----------------|--------|------------------------------------------------|
| `dof_pos`      | `(23,)`| URDF order, radians                            |
| `dof_vel`      | `(23,)`| URDF order, rad/s                              |
| `base_quat`    | `(4,)` | `[w, x, y, z]`                                 |
| `base_ang_vel` | `(3,)` | Body frame                                     |

### `ctrl_data["commands"]`

An 8-vector driving the policy's task interface:

| Index | Field         | Range (typical)  | Meaning                         |
|-------|---------------|------------------|---------------------------------|
| 0     | `vx`          | `[-0.8, 0.8]`    | Forward velocity (m/s)          |
| 1     | `vy`          | `[-0.4, 0.4]`    | Lateral velocity (m/s)          |
| 2     | `yaw_rate`    | `[-1.0, 1.0]`    | Turn rate (rad/s)               |
| 3     | `height`      | `[-0.2, 0.2]`    | Δ-height offset (m)             |
| 4     | `torso_yaw`   | `[-0.5, 0.5]`    | Torso yaw offset (rad)          |
| 5     | `torso_pitch` | `[-0.3, 0.3]`    | Torso pitch offset (rad)        |
| 6     | `torso_roll`  | `[-0.3, 0.3]`    | Torso roll offset (rad)         |
| 7     | `gait_phase`  | auto             | Managed by the policy clock     |

Unused axes should be zero. See `demo_amo_capabilities.py` for a worked
sequence that exercises every axis.

### Actions

`get_action` returns a 23-vector of joint-position offsets (already scaled by
`action_scale=0.25`); add to default pose to get PD setpoints. The internal
`amo_policy_impl` handles normalization, adapter forward pass, and action
scaling — the wrapper just routes state in and actions out.

---

## Configuration

```python
from genPiHub.configs import AMOPolicyConfig
from pathlib import Path

cfg = AMOPolicyConfig(
    policy_file=Path(".reference/AMO/amo_jit.pt"),
    adapter_file=Path(".reference/AMO/adapter_jit.pt"),
    norm_stats_file=Path(".reference/AMO/adapter_norm_stats.pt"),

    # Scaling (match the checkpoint's training setup)
    action_scale=0.25,
    scales_ang_vel=0.25,
    scales_dof_vel=0.05,
    gait_freq=1.3,          # Hz; drives the phase clock

    # History (fixed at train time — don't change unless you re-trained)
    history_length=35,
    history_obs_size=93,

    device="cuda",
)
```

---

## Robot support

**Unitree G1 (23 DoF)** — the checkpoint's native target. Joint layout:

```
left_{hip_pitch, hip_roll, hip_yaw, knee, ankle_pitch, ankle_roll}
right_{hip_pitch, hip_roll, hip_yaw, knee, ankle_pitch, ankle_roll}
waist_{yaw, roll, pitch}
left_{shoulder_pitch, shoulder_roll, shoulder_yaw, elbow, wrist_roll}
right_{shoulder_pitch, shoulder_roll, shoulder_yaw, elbow, wrist_roll}
```

Retargeting to other humanoids requires re-training; the wrapper is DOF-count
agnostic via `DOFConfig` but the checkpoint is not.

---

## Troubleshooting

**Missing checkpoints.** The loader falls back to `.reference/AMO` if no
`policy_file` is given. Point `model_dir` to wherever your `amo_jit.pt` lives.

**"Action is too large / the robot explodes."** You likely sent an action in the
wrong order, or forgot to add the default pose. The wrapper returns offsets,
not absolute joint targets — the environment is responsible for adding
`policy.get_init_dof_pos()` (or the equivalent default pose) before applying PD.

**Policy output stuck at zero.** Check that `commands` is being passed through
`ctrl_data` and is an 8-vector, not the 3-vector used by HoloMotion.
