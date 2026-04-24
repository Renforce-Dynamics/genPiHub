#!/usr/bin/env python3
"""Demo AMO policy capabilities with automatic sequence.

This script demonstrates all AMO capabilities in an automatic sequence:
- Forward/backward locomotion
- Lateral movement (left/right)
- Turning (yaw control)
- Height adjustment (up/down)
- Torso orientation (pitch, roll, yaw)

Usage:
    # With viewer (interactive watching)
    python scripts/amo/genesislab/demo_amo_capabilities.py --viewer

    # Record video (headless)
    python scripts/amo/genesislab/demo_amo_capabilities.py --record-video --video-path output/amo_demo.mp4

    # Custom mesh terrain
    python scripts/amo/genesislab/demo_amo_capabilities.py --viewer --mesh-path data/assets/Barracks.glb
"""

from __future__ import annotations

import argparse
import os
import time
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
import torch
from pathlib import Path

# Import from Policy Hub
from genPiHub import load_policy
from genPiHub.configs import (
    AMOPolicyConfig,
    GenesisEnvConfig,
)
from genPiHub.tools import DOFConfig, CommandState
from genPiHub.environments import GenesisEnv

# Import GenesisLab terrain config
from genesislab.components.terrains import TerrainCfg
from genesislab.engine.scene import CameraCfg, RecordingCfg


@dataclass
class DemoSegment:
    """A segment of the demo sequence."""
    name: str
    duration: float  # seconds
    vx: float = 0.0
    vy: float = 0.0
    yaw_rate: float = 0.0
    height: float = 0.0
    torso_yaw: float = 0.0
    torso_pitch: float = 0.0
    torso_roll: float = 0.0

    def __str__(self):
        parts = []
        if self.vx != 0.0:
            parts.append(f"vx={self.vx:+.2f}")
        if self.vy != 0.0:
            parts.append(f"vy={self.vy:+.2f}")
        if self.yaw_rate != 0.0:
            parts.append(f"yaw={self.yaw_rate:+.2f}")
        if self.height != 0.0:
            parts.append(f"h={self.height:+.2f}")
        if self.torso_yaw != 0.0:
            parts.append(f"t_yaw={self.torso_yaw:+.2f}")
        if self.torso_pitch != 0.0:
            parts.append(f"t_pitch={self.torso_pitch:+.2f}")
        if self.torso_roll != 0.0:
            parts.append(f"t_roll={self.torso_roll:+.2f}")

        param_str = ", ".join(parts) if parts else "idle"
        return f"{self.name:30s} ({self.duration:4.1f}s): {param_str}"


def create_demo_sequence() -> List[DemoSegment]:
    """Create the complete demo sequence showcasing all AMO capabilities.

    Optimized flow:
    1. Static posture demonstrations (at origin)
       - Height adjustments
       - Torso bending (pitch, roll, yaw)
    2. Locomotion demonstrations
       - Forward/backward
       - Lateral movement
       - Turning
    3. Combined movements
    4. Return to origin

    Reference from play_amo.py keyboard controls:
    - W/S: vx ±0.05 (forward/backward)
    - A/D: yaw ±0.1 (turn left/right)
    - Z/X: height ±0.05
    - J/U: torso_yaw ±0.1
    - K/I: torso_pitch ±0.05
    - L/O: torso_roll ±0.05

    Returns:
        List of demo segments
    """

    segments = [
        # ========================================
        # PHASE 1: STATIC POSTURE CONTROL (at origin)
        # ========================================
        DemoSegment(
            name="[1/22] 🧍 Initial Standing",
            duration=2.0,
        ),

        # --- Height Control ---
        DemoSegment(
            name="[2/22] ⬇️  Crouch Down (standing)",
            duration=3.0,
            height=-0.15,
        ),
        DemoSegment(
            name="[3/22] ⬆️  Stand Tall (standing)",
            duration=3.0,
            height=0.15,
        ),
        DemoSegment(
            name="[4/22] ↕️  Return to Normal Height",
            duration=2.0,
            height=0.0,
        ),

        # --- Torso Pitch (Bowing) ---
        DemoSegment(
            name="[5/22] 🙇 Bow Forward (pitch)",
            duration=3.0,
            torso_pitch=0.3,
        ),
        DemoSegment(
            name="[6/22] 🙆 Lean Backward (pitch)",
            duration=3.0,
            torso_pitch=-0.2,
        ),
        DemoSegment(
            name="[7/22] ↕️  Torso Neutral",
            duration=2.0,
            torso_pitch=0.0,
        ),

        # --- Torso Roll (Side Tilt) ---
        DemoSegment(
            name="[8/22] ◀️  Tilt Left (roll)",
            duration=3.0,
            torso_roll=0.25,
        ),
        DemoSegment(
            name="[9/22] ▶️  Tilt Right (roll)",
            duration=3.0,
            torso_roll=-0.25,
        ),
        DemoSegment(
            name="[10/22] ↔️  Torso Upright",
            duration=2.0,
            torso_roll=0.0,
        ),

        # --- Torso Yaw (Twist) ---
        DemoSegment(
            name="[11/22] ↶ Twist Left (yaw)",
            duration=3.0,
            torso_yaw=0.3,
        ),
        DemoSegment(
            name="[12/22] ↷ Twist Right (yaw)",
            duration=3.0,
            torso_yaw=-0.3,
        ),
        DemoSegment(
            name="[13/22] 🧍 Reset to Neutral",
            duration=2.0,
            torso_yaw=0.0,
        ),

        # ========================================
        # PHASE 2: LOCOMOTION (symmetric paths)
        # ========================================

        # --- Forward and Back (net displacement = 0) ---
        DemoSegment(
            name="[14/22] 🚶 Forward Walk",
            duration=4.0,
            vx=0.5,
        ),
        DemoSegment(
            name="[15/22] 🔙 Backward Walk (return)",
            duration=4.0,
            vx=-0.5,  # Same magnitude, opposite direction
        ),

        # --- Lateral Movement (net displacement = 0) ---
        DemoSegment(
            name="[16/22] ⬅️  Lateral Left",
            duration=3.0,
            vy=0.3,
        ),
        DemoSegment(
            name="[17/22] ➡️  Lateral Right (return)",
            duration=3.0,
            vy=-0.3,  # Same magnitude, opposite direction
        ),

        # --- Complete 360° Circle (net displacement ≈ 0) ---
        DemoSegment(
            name="[18/22] 🔄 Circle Motion (360°)",
            duration=10.0,  # 2π/0.628 ≈ 10s for full circle
            vx=0.4,
            yaw_rate=0.628,  # ≈ π/5 rad/s → 360° in 10s
        ),

        # ========================================
        # PHASE 3: COMBINED MOVEMENTS
        # ========================================
        DemoSegment(
            name="[19/22] 🎭 Forward + Crouch + Turn",
            duration=5.0,
            vx=0.4,
            yaw_rate=0.4,
            height=-0.1,
        ),
        DemoSegment(
            name="[20/22] 🔄 Reverse Turn (compensate)",
            duration=5.0,
            vx=0.4,
            yaw_rate=-0.4,  # Opposite turn to cancel rotation
            height=0.0,
        ),

        # ========================================
        # PHASE 4: FINALE - RETURN TO ORIGIN
        # ========================================
        DemoSegment(
            name="[21/22] 🏁 Final Approach",
            duration=2.0,
            vx=0.2,  # Slow forward
        ),
        DemoSegment(
            name="[22/22] ✅ Arrive at Origin",
            duration=3.0,
            vx=0.0,
            vy=0.0,
            yaw_rate=0.0,
            height=0.0,
            torso_yaw=0.0,
            torso_pitch=0.0,
            torso_roll=0.0,
        ),
    ]

    return segments


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Demo AMO capabilities with automatic sequence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Environment
    parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda"])
    parser.add_argument("--num-envs", type=int, default=1, help="Number of environments")
    parser.add_argument("--viewer", action="store_true", help="Enable viewer")
    parser.add_argument("--headless", action="store_true", help="Disable viewer (headless mode)")

    # Mesh Terrain
    parser.add_argument(
        "--mesh-path",
        type=str,
        default="data/assets/test_plane.obj",
        help="Path to mesh file (.obj, .stl, .glb, .gltf)",
    )
    parser.add_argument(
        "--env-spacing",
        type=float,
        default=4.0,
        help="Spacing between environments (meters)",
    )
    parser.add_argument(
        "--decompose-threshold",
        type=float,
        default=float("inf"),
        help="Convex decomposition error threshold",
    )
    parser.add_argument(
        "--sdf-cell-size",
        type=float,
        default=0.1,
        help="SDF cell size for collision detection",
    )

    # Demo Control
    parser.add_argument("--print-every", type=int, default=50, help="Print stats every N steps")
    parser.add_argument("--speed-multiplier", type=float, default=1.0, help="Speed up/slow down demo (1.0=normal)")

    # Camera and Recording
    parser.add_argument("--record-video", action="store_true", help="Enable video recording")
    parser.add_argument("--video-path", type=str, default="output/amo_capabilities_demo.mp4", help="Video output path")
    parser.add_argument("--video-fps", type=int, default=60, help="Video frame rate")
    parser.add_argument("--camera-res", type=int, nargs=2, default=[1920, 1080], help="Camera resolution")
    parser.add_argument("--camera-pos", type=float, nargs=3, default=[7.0, 0.0, 3], help="Camera position")
    parser.add_argument("--camera-lookat", type=float, nargs=3, default=[0.0, 0.0, 0.75], help="Camera look-at")
    parser.add_argument("--camera-fov", type=float, default=50.0, help="Camera field of view")

    # Policy
    parser.add_argument("--model-dir", type=str, default="data/AMO", help="AMO model directory")
    parser.add_argument("--action-scale", type=float, default=0.25, help="Action scaling factor")

    return parser.parse_args()


def create_amo_policy_config(args) -> AMOPolicyConfig:
    """Create AMO policy configuration."""
    model_dir = Path(args.model_dir)

    # AMO DOF configuration (23 DOF G1)
    amo_dof_names = [
        "left_hip_pitch_joint", "left_hip_roll_joint", "left_hip_yaw_joint",
        "left_knee_joint", "left_ankle_pitch_joint", "left_ankle_roll_joint",
        "right_hip_pitch_joint", "right_hip_roll_joint", "right_hip_yaw_joint",
        "right_knee_joint", "right_ankle_pitch_joint", "right_ankle_roll_joint",
        "waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint",
        "left_shoulder_pitch_joint", "left_shoulder_roll_joint", "left_shoulder_yaw_joint", "left_elbow_joint",
        "right_shoulder_pitch_joint", "right_shoulder_roll_joint", "right_shoulder_yaw_joint", "right_elbow_joint",
    ]

    amo_default_pos = [
        -0.1, 0., 0., 0.3, -0.2, 0.,  # left leg
        -0.1, 0., 0., 0.3, -0.2, 0.,  # right leg
        0., 0., 0.,                    # waist
        0.5, 0., 0.2, 0.3,            # left arm
        0.5, 0., -0.2, 0.3,           # right arm
    ]

    dof_cfg = DOFConfig(
        joint_names=amo_dof_names,
        num_dofs=23,
        default_pos=amo_default_pos,
    )

    return AMOPolicyConfig(
        name="AMOPolicy",
        policy_file=model_dir / "amo_jit.pt",
        adapter_file=model_dir / "adapter_jit.pt",
        norm_stats_file=model_dir / "adapter_norm_stats.pt",
        device=args.device or ("cuda" if torch.cuda.is_available() else "cpu"),
        obs_dof=dof_cfg,
        action_dof=dof_cfg,
        action_scale=args.action_scale,
        freq=50.0,  # 50 Hz control
    )


def create_amo_mesh_terrain_env_config(args, mesh_path: str, num_envs: int, env_spacing: float, backend: str, viewer: bool):
    """Create AMO environment configuration with mesh terrain."""
    from genPiHub.envs.amo import AmoGenesisEnvCfg

    cfg = AmoGenesisEnvCfg()

    # Reduce timestep for stability
    cfg.scene.dt = 0.001
    cfg.scene.substeps = 5

    # Configure scene
    cfg.scene.num_envs = num_envs
    cfg.scene.backend = backend
    cfg.scene.viewer = viewer

    # # Replace plane terrain with mesh terrain
    # cfg.scene.terrain = TerrainCfg(
    #     terrain_type="mesh",
    #     mesh_path=mesh_path,
    #     env_spacing=env_spacing,
    #     mesh_decompose_error_threshold=args.decompose_threshold,
    #     mesh_sdf_cell_size=args.sdf_cell_size,
    # )

    # Disable observation corruption for demo
    cfg.observations.policy.enable_corruption = False

    # Static commands (will be controlled by demo sequence)
    cfg.commands.base_velocity.resampling_time_range = (1e9, 1e9)

    # Configure camera
    cfg.scene.camera = CameraCfg(
        res=tuple(args.camera_res),
        pos=tuple(args.camera_pos),
        lookat=tuple(args.camera_lookat),
        fov=args.camera_fov,
        backend="rasterizer",
        show_in_gui=False,
    )

    # Configure recording
    if args.record_video:
        cfg.scene.recording = RecordingCfg(
            enabled=True,
            save_path=args.video_path,
            fps=args.video_fps,
            codec="libx264",
            codec_preset="medium",
            codec_tune="film",
            render_rgb=True,
            render_depth=False,
            render_segmentation=False,
            render_normal=False,
        )
        print(f"\n🎥 Video recording enabled:")
        print(f"   Output: {args.video_path}")
        print(f"   Resolution: {args.camera_res[0]}x{args.camera_res[1]}")
        print(f"   FPS: {args.video_fps}")
    else:
        cfg.scene.recording = None

    return cfg


class DemoSequenceController:
    """Controller for executing the demo sequence."""

    def __init__(self, segments: List[DemoSegment], speed_multiplier: float = 1.0, control_freq: float = 50.0):
        self.segments = segments
        self.speed_multiplier = speed_multiplier
        self.control_freq = control_freq
        self.control_dt = 1.0 / control_freq

        # Compute step ranges for each segment
        self.segment_step_ranges = []
        current_step = 0
        for seg in segments:
            duration_adjusted = seg.duration / speed_multiplier
            num_steps = int(duration_adjusted * control_freq)
            self.segment_step_ranges.append((current_step, current_step + num_steps))
            current_step += num_steps

        self.total_steps = current_step
        self.current_segment_idx = 0

    def get_command(self, step: int) -> Tuple[CommandState, str, int]:
        """Get command for current step.

        Returns:
            (command_state, segment_name, segment_idx)
        """
        # Find current segment
        seg_idx = 0
        for idx, (start, end) in enumerate(self.segment_step_ranges):
            if start <= step < end:
                seg_idx = idx
                break

        if seg_idx != self.current_segment_idx:
            self.current_segment_idx = seg_idx

        seg = self.segments[seg_idx]

        # Create command state
        # Note: AMO adapter expects height, torso_yaw, torso_pitch, torso_roll in adapter input
        # For now, we only control base velocity commands (vx, vy, yaw_rate, height)
        cmd = CommandState(
            vx=seg.vx,
            vy=seg.vy,
            yaw_rate=seg.yaw_rate,
            height=seg.height,
        )

        return cmd, seg.name, seg_idx


def main():
    args = parse_args()

    # Handle viewer/headless logic
    use_viewer = args.viewer and not args.headless

    # Check mesh file exists
    if not os.path.exists(args.mesh_path):
        print(f"\n❌ ERROR: Mesh file not found: {args.mesh_path}")
        return 1

    print(f"\n{'='*80}")
    print(f"  AMO CAPABILITY DEMO")
    print(f"{'='*80}")
    print(f"✅ Mesh file: {os.path.basename(args.mesh_path)}")

    # Determine device
    backend = args.device or ("cuda" if torch.cuda.is_available() else "cpu")
    print(f"✅ Backend: {backend}")

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Create demo sequence
    print(f"\n[1/5] Creating demo sequence...")
    demo_segments = create_demo_sequence()
    print(f"✅ Demo sequence: {len(demo_segments)} segments")
    for seg in demo_segments:
        print(f"   {seg}")

    # Load AMO policy configuration
    print(f"\n[2/5] Creating AMO policy configuration...")
    policy_config = create_amo_policy_config(args)
    print(f"✅ Policy config: {policy_config.obs_dof.num_dofs} DOFs, {policy_config.freq}Hz")

    # Create environment with mesh terrain
    print(f"\n[3/5] Creating environment with mesh terrain...")
    amo_env_cfg = create_amo_mesh_terrain_env_config(
        args=args,
        mesh_path=args.mesh_path,
        num_envs=args.num_envs,
        env_spacing=args.env_spacing,
        backend=backend,
        viewer=use_viewer,
    )

    genesis_cfg = GenesisEnvConfig(
        dof=policy_config.obs_dof,
        num_envs=args.num_envs,
    )

    env = GenesisEnv(cfg=genesis_cfg, device=backend, env_cfg=amo_env_cfg)
    print(f"✅ Environment: {env.num_envs} envs, {env.num_dofs} DOFs")
    print(f"   Terrain: Mesh ({args.env_spacing}m spacing)")

    # Load AMO policy
    print(f"\n[4/5] Loading AMO policy...")
    policy_kwargs = {k: v for k, v in policy_config.__dict__.items() if k != 'name'}
    policy = load_policy("AMOPolicy", **policy_kwargs)
    print(f"✅ Policy loaded: {policy.cfg.name}")

    # Setup demo controller
    print(f"\n[5/5] Setting up demo controller...")
    demo_controller = DemoSequenceController(
        segments=demo_segments,
        speed_multiplier=args.speed_multiplier,
        control_freq=policy_config.freq,
    )
    print(f"✅ Demo controller: {demo_controller.total_steps} total steps")
    total_duration = sum(seg.duration for seg in demo_segments) / args.speed_multiplier
    print(f"   Total duration: {total_duration:.1f}s (speed={args.speed_multiplier}x)")

    # Reset environment and policy
    env.reset()
    policy.reset()

    print(f"\n{'='*80}")
    print(f"▶️  STARTING DEMO")
    print(f"{'='*80}\n")

    # Main loop
    start_time = time.time()
    last_segment_idx = -1

    try:
        for step in range(demo_controller.total_steps):
            # Get command from demo sequence
            cmd_state, seg_name, seg_idx = demo_controller.get_command(step)

            # Print segment transition
            if seg_idx != last_segment_idx:
                print(f"\n{'─'*80}")
                print(f"  {seg_name}")
                print(f"{'─'*80}")
                last_segment_idx = seg_idx

            # Get environment data
            env_data = env.get_data()

            # Set commands in env_data
            env_data["commands"] = cmd_state.as_array()

            # Get observation and action from policy
            obs, extras = policy.get_observation(env_data, {})
            action = policy.get_action(obs)

            # Step environment
            step_result = env.step(action)

            # Handle episode termination
            if step_result.get("terminated", False).any() or step_result.get("truncated", False).any():
                policy.reset()
                print(f"   ⚠️  Episode terminated/truncated at step {step}, resetting policy")

            # Print stats
            if step % args.print_every == 0:
                base_pos = env.base_pos
                elapsed = time.time() - start_time
                fps = (step + 1) / max(1e-6, elapsed)
                progress = (step + 1) / demo_controller.total_steps * 100
                print(
                    f"   step={step:06d}/{demo_controller.total_steps} ({progress:5.1f}%) "
                    f"fps={fps:6.1f} pos=[{base_pos[0]:6.2f}, {base_pos[1]:6.2f}, {base_pos[2]:5.3f}] "
                    f"cmd: vx={cmd_state.vx:+.2f} vy={cmd_state.vy:+.2f} yaw={cmd_state.yaw_rate:+.2f} h={cmd_state.height:+.2f}"
                )

            # Policy post-step callback
            policy.post_step_callback()

    except KeyboardInterrupt:
        print(f"\n\n⏹️  Demo stopped by user at step {step}/{demo_controller.total_steps}")

    elapsed = time.time() - start_time
    print(f"\n{'='*80}")
    print(f"✅ DEMO COMPLETE!")
    print(f"{'='*80}")
    print(f"   Total steps: {demo_controller.total_steps}")
    print(f"   Total time: {elapsed:.1f}s")
    print(f"   Average FPS: {demo_controller.total_steps / elapsed:.1f}")
    if args.record_video:
        print(f"   Video saved: {args.video_path}")
    print()

    return 0


if __name__ == "__main__":
    main()
