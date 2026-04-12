#!/usr/bin/env python3
"""Debug BeyondMimic observations."""

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

print("Testing observation construction...")
policy.reset()

# Create fake environment data
env_data = {
    "dof_pos": G1_BEYONDMIMIC_DEFAULT_POS.copy(),
    "dof_vel": np.zeros(29, dtype=np.float32),
    "base_quat": np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),  # Identity [w,x,y,z]
    "base_ang_vel": np.zeros(3, dtype=np.float32),
    "base_lin_vel": np.zeros(3, dtype=np.float32),
}

# First call - should initialize
obs1, extras1 = policy.get_observation(env_data, {})
print(f"\nFirst obs shape: {obs1.shape}")
print(f"First obs (all zeros expected): min={obs1.min():.4f}, max={obs1.max():.4f}, mean={obs1.mean():.4f}")

# Get action to populate command
action1 = policy.get_action(obs1)
print(f"\nFirst action: min={action1.min():.4f}, max={action1.max():.4f}")
print(f"Command populated: {policy.command is not None}")

if policy.command:
    print(f"  ref_joint_pos shape: {policy.command['joint_pos'].shape}")
    print(f"  ref_joint_pos (first 5): {policy.command['joint_pos'][:5]}")
    print(f"  body_quat_w shape: {policy.command['body_quat_w'].shape}")
    print(f"  body_quat_w[7] (anchor): {policy.command['body_quat_w'][7]}")

# Second call - should build real observation
obs2, extras2 = policy.get_observation(env_data, {})
print(f"\nSecond obs shape: {obs2.shape}")
print(f"Expected shape: 154 (WOSE mode)")

# Break down observation
print(f"\nObservation breakdown:")
idx = 0
print(f"  [{idx}:{idx+29}] ref_joint_pos: {obs2[idx:idx+5]}")
idx += 29
print(f"  [{idx}:{idx+29}] ref_joint_vel: {obs2[idx:idx+5]}")
idx += 29
print(f"  [{idx}:{idx+6}] motion_anchor_ori_b: {obs2[idx:idx+6]}")
idx += 6
print(f"  [{idx}:{idx+3}] ang_vel: {obs2[idx:idx+3]}")
idx += 3
print(f"  [{idx}:{idx+29}] joint_pos_rel: {obs2[idx:idx+5]}")
idx += 29
print(f"  [{idx}:{idx+29}] joint_vel: {obs2[idx:idx+5]}")
idx += 29
print(f"  [{idx}:{idx+29}] last_action: {obs2[idx:idx+5]}")
idx += 29
print(f"  Total: {idx} dims")

print(f"\nInit to world matrix:")
print(policy.init_to_world)
