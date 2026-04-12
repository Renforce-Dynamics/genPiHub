#!/usr/bin/env python3
"""Debug MuJoCo BeyondMimic actions."""

import mujoco
import numpy as np
from pathlib import Path

from genPiHub import load_policy
from genPiHub.configs import BeyondMimicPolicyConfig
from genPiHub.tools import DOFConfig
from genPiHub.envs.beyondmimic.genesislab.robot_cfg import (
    G1_29DOF_BEYONDMIMIC_NAMES,
    G1_BEYONDMIMIC_DEFAULT_POS,
    G1_BEYONDMIMIC_ACTION_SCALES,
)

# Load policy
model_file = Path(".reference/RoboJuDo/assets/models/g1/beyondmimic/Dance_wose.onnx")
dof_cfg = DOFConfig(
    joint_names=G1_29DOF_BEYONDMIMIC_NAMES,
    num_dofs=29,
    default_pos=G1_BEYONDMIMIC_DEFAULT_POS,
)

policy_config = BeyondMimicPolicyConfig(
    name="BeyondMimicPolicy",
    policy_file=model_file,
    device="cpu",
    obs_dof=dof_cfg,
    action_dof=dof_cfg,
    action_scales=G1_BEYONDMIMIC_ACTION_SCALES,
    freq=50.0,
    without_state_estimator=True,
    use_motion_from_model=True,
)

policy_kwargs = {k: v for k, v in policy_config.__dict__.items() if k != 'name'}
policy = load_policy("BeyondMimicPolicy", **policy_kwargs)
policy.reset()

# Create MuJoCo environment
model = mujoco.MjModel.from_xml_path("data/beyondmimic/g1_29dof_rev_1_0.xml")
data = mujoco.MjData(model)

# Set initial positions
for i, name in enumerate(G1_29DOF_BEYONDMIMIC_NAMES):
    jnt_id = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, name)
    if jnt_id >= 0:
        dof_adr = model.jnt_dofadr[jnt_id]
        data.qpos[dof_adr] = G1_BEYONDMIMIC_DEFAULT_POS[i]

mujoco.mj_forward(model, data)

# Get state
env_data = {
    "dof_pos": G1_BEYONDMIMIC_DEFAULT_POS.copy(),
    "dof_vel": np.zeros(29, dtype=np.float32),
    "base_quat": np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
    "base_ang_vel": np.zeros(3, dtype=np.float32),
    "base_lin_vel": np.zeros(3, dtype=np.float32),
}

# First pass to initialize
obs1, extras1 = policy.get_observation(env_data, {})
action1 = policy.get_action(obs1)

print("First pass (initialization):")
print(f"  Action shape: {action1.shape}")
print(f"  Action (first 5): {action1[:5]}")

# Second pass with real data
obs2, extras2 = policy.get_observation(env_data, {})
action2 = policy.get_action(obs2)

print("\nSecond pass (with reference motion):")
print(f"  Action (first 5): {action2[:5]}")
print(f"  Ref joint pos (first 5): {policy.command['joint_pos'][:5]}")
print(f"  Default pos (first 5): {G1_BEYONDMIMIC_DEFAULT_POS[:5]}")

# Compute PD target
pd_target = G1_BEYONDMIMIC_DEFAULT_POS + action2
print(f"\nPD target (first 5): {pd_target[:5]}")
print(f"  Should match ref? {np.allclose(pd_target[:5], policy.command['joint_pos'][:5], atol=0.5)}")

# Compare with reference
diff = pd_target - policy.command['joint_pos']
print(f"\nDifference (PD target - ref):")
print(f"  Mean abs diff: {np.abs(diff).mean():.4f}")
print(f"  Max abs diff: {np.abs(diff).max():.4f}")
print(f"  First 5: {diff[:5]}")
