# HoloMotion policy (Horizon Robotics, Unitree G1 29DoF)

genPiHub wrapper for [HorizonRobotics/HoloMotion v1.2](https://huggingface.co/HorizonRobotics/HoloMotion_v1.2)
ONNX checkpoints. Runs in-simulation inference inside genesislab without
touching the original HoloMotion training stack.

## What HoloMotion ships

Two independent policies are released under the same HF repo:

| Task type           | Architecture                    | ONNX size | Obs dim | Action dim |
|---------------------|---------------------------------|-----------|---------|------------|
| `velocity_tracking` | MLP actor, no KV cache          | 3.7 MB    | 776     | 29         |
| `motion_tracking`   | Transformer-MoE w/ KV cache     | 246 MB    | 522     | 29         |

Both are exported with per-joint action scale, stiffness, damping and default
pose embedded as ONNX `metadata_props` — the wrapper reads them at load time.

> **Status.** `velocity_tracking` is fully wired. `motion_tracking` is stubbed:
> the wrapper raises `NotImplementedError` at construction because it needs the
> retargeted-motion loader and reference-FK path which have not been ported yet.

## 1. Download the checkpoints

```bash
# Velocity only (3.7 MB)
bash scripts/download/download_holomotion_ckpt.sh velocity

# Motion only (246 MB)
bash scripts/download/download_holomotion_ckpt.sh motion

# Both
bash scripts/download/download_holomotion_ckpt.sh all
```

Destination defaults to `$HOME/.cache/genesis/holomotion/`. Override via
`HOLOMOTION_CACHE_DIR=/custom/path`. The script expects `hf` (new Hugging Face
CLI) or the legacy `huggingface-cli` to be installed.

Resulting layout:

```
$HOME/.cache/genesis/holomotion/
├── holomotion_v1.2_velocity_tracking_model/
│   ├── config.yaml
│   └── exported/model_29500.onnx
└── holomotion_v1.2_motion_tracking_model/
    ├── config.yaml
    └── exported/model.onnx
```

## 2. Load via genPiHub

```python
from genPiHub import load_policy

policy = load_policy(
    "HoloMotionPolicy",
    model_dir="/home/you/.cache/genesis/holomotion/holomotion_v1.2_velocity_tracking_model",
    task_type="velocity_tracking",          # or "auto"
    device="cuda",                           # "cpu" | "cuda" | "tensorrt"
)
policy.reset()
```

`load_policy` builds a `HoloMotionPolicyConfig` — relevant fields:

| Field                          | Default     | Notes                                             |
|--------------------------------|-------------|---------------------------------------------------|
| `model_dir`                    | `None`      | Preferred entry point. Overrides `policy_file`.   |
| `policy_file`, `config_file`   | `None`      | Only needed if you don't use `model_dir`.         |
| `task_type`                    | `"auto"`    | Inferred from `obs_groups` when `auto`.           |
| `device`                       | `"cuda"`    | onnxruntime EP.                                    |
| `freq`                         | `50.0`      | Control rate matching HoloMotion deployment.      |
| `action_scale`                 | `1.0`       | Scalar. Per-joint scale is read from ONNX.        |
| `action_clip`                  | `100.0`     | Matches `env.config.normalization.clip_actions`.  |
| `vel_cmd_is_moving_threshold`  | `0.1`       | Flag toggled when `‖[vx,vy,vyaw]‖ > threshold`.   |
| `obs_group_name`               | `"unified"` | HoloMotion's config uses a unified obs group.     |
| `actor_term_prefix`            | `"actor_"`  | Actor obs terms have this prefix.                 |

## 3. Calling the wrapper

The wrapper follows the standard genPiHub `Policy` protocol:

```python
obs, extras = policy.get_observation(env_data, ctrl_data)
action      = policy.get_action(obs)
policy.post_step_callback()
```

### env_data keys

| Key            | Shape                            | Frame / order                                     |
|----------------|----------------------------------|---------------------------------------------------|
| `dof_pos`      | `(29,)`                          | URDF order (see note below), radians              |
| `dof_vel`      | `(29,)`                          | URDF order, rad/s                                 |
| `base_quat`    | `(4,)` as `[w, x, y, z]`         | base -> world                                     |
| `base_ang_vel` | `(3,)`                           | **body frame** (already rotated into base)        |

### ctrl_data keys (velocity_tracking)

| Key        | Shape  | Meaning                                    |
|------------|--------|--------------------------------------------|
| `commands` | `(3,)` | `[vx, vy, vyaw]` m/s, m/s, rad/s           |

The 4th obs component (`is_moving` flag) is derived by the wrapper from the
command magnitude.

### DOF order — URDF vs ONNX

HoloMotion exports an **interleaved** joint order
(`left_hip_pitch, right_hip_pitch, waist_yaw, left_hip_roll, right_hip_roll,
waist_roll, ...`) that differs from typical URDF ordering. The wrapper
maintains two permutations:

* `policy.urdf_to_onnx[i]` — index into URDF arrays placed at ONNX position
  `i`. Applied to `dof_pos`, `dof_vel` inside `get_observation`.
* `policy.onnx_to_urdf[i]` — index into the ONNX action placed at URDF
  position `i`. Applied to the scaled action before it leaves `get_action`.

URDF names come from `cfg.action_dof.joint_names`. **If you pass an empty DOF
config, the wrapper falls back to identity** (the env is assumed to already be
in ONNX order) — do this only for sanity tests.

### dof_pos is encoded as a delta

The `actor_dof_pos` obs term is `q - q_default`, not raw `q`. The default pose
is the one embedded in ONNX metadata; you do not need to do this subtraction
yourself — just pass raw `q`.

## 4. Example

See `src/genPiHub/genPiHub/examples/holomotion_example.py`. Run it stand-alone
after downloading the velocity checkpoint:

```bash
python src/genPiHub/genPiHub/examples/holomotion_example.py
```

You should see `obs_dim=776`, `action_dim=29`, and a non-zero action vector
each step.

## 5. Motion tracking — TODO

`task_type="motion_tracking"` currently raises at construction. To finish this
path the wrapper needs:

1. **Motion loader** — read the retargeted `.npz` motion (`dof_pos`,
   `root_pos`, `root_rot`, keybody positions, …) at 30 Hz and resample to
   50 Hz.
2. **Reference FK** — compute `ref_base_linvel`, `ref_base_angvel`,
   `ref_gravity_projection`, `ref_keybody_rel_pos` for the current frame and
   the next 10 future frames (indexes 1, 5, 10, 15, 20).
3. **`_get_obs_actor_ref_*` methods** — replace the current
   `NotImplementedError` stubs in `holomotion_policy.py` with real
   implementations that consume the above loader.
4. **KV cache wiring** — already stubbed; `_zero_kv_cache()` allocates the
   right shape from the ONNX `past_key_values` input, we pass `step_idx`
   through as `int64`, and re-feed `present_key_values`.

Until that work lands, users who want motion tracking should run
HoloMotion's upstream deployment scripts outside genesislab.
