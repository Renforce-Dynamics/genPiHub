#!/usr/bin/env python3
"""Run BeyondMimic policy using Policy Hub framework with Genesis backend.

This script demonstrates using BeyondMimic through the Policy Hub unified interface.
BeyondMimic is a whole-body motion tracking policy that uses ONNX Runtime for inference.

✅ 100% Policy Hub Integration:
   - BeyondMimicPolicy via load_policy()
   - GenesisEnv via genPiHub.environments
   - BeyondMimic environment config via create_beyondmimic_genesis_env_config()
   - Unified state access via env.get_data()
   - Automatic joint mapping

🎭 Motion Playback:
   - Uses ONNX model with embedded motion data
   - Timestep-based playback control
   - Play speed adjustment
   - Automatic reset when motion completes

Usage examples:
    # Headless mode (default)
    python scripts/beyondmimic/genesislab/play_beyondmimic.py \
        --model-file path/to/beyondmimic_dance.onnx

    # With viewer
    python scripts/beyondmimic/genesislab/play_beyondmimic.py \
        --model-file path/to/beyondmimic_dance.onnx \
        --viewer

    # Adjust playback speed
    python scripts/beyondmimic/genesislab/play_beyondmimic.py \
        --model-file path/to/model.onnx \
        --play-speed 0.5  # Slower
        --max-timestep 1000  # Limit duration

    # Multiple parallel environments
    python scripts/beyondmimic/genesislab/play_beyondmimic.py \
        --model-file path/to/model.onnx \
        --num-envs 4
"""

from __future__ import annotations

import sys
from pathlib import Path
import argparse
import time
import numpy as np
import torch

# Import from Policy Hub
from genPiHub import load_policy
from genPiHub.configs import (
    BeyondMimicPolicyConfig,
    GenesisEnvConfig,
    create_beyondmimic_genesis_env_config,
)
from genPiHub.tools import DOFConfig
from genPiHub.environments import GenesisEnv
from genPiHub.envs.beyondmimic.genesislab.robot_cfg import (
    G1_29DOF_BEYONDMIMIC_NAMES,
    G1_BEYONDMIMIC_DEFAULT_POS,
    G1_BEYONDMIMIC_ACTION_SCALES,
)


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Play BeyondMimic policy via Policy Hub (Genesis backend)"
    )

    # Environment
    parser.add_argument("--device", type=str, default=None, choices=["cpu", "cuda"])
    parser.add_argument("--num-envs", type=int, default=1)
    parser.add_argument("--viewer", action="store_true", help="Enable viewer (default: headless)")
    parser.add_argument("--headless", action="store_true", help="Disable viewer (explicit headless mode)")

    # Control
    parser.add_argument("--max-steps", type=int, default=3000)
    parser.add_argument("--print-every", type=int, default=100)

    # Policy & Model
    parser.add_argument(
        "--model-file", type=str, required=True,
        help="Path to BeyondMimic ONNX model file (required)"
    )
    parser.add_argument(
        "--use-model-meta", action="store_true",
        help="Load config from ONNX model metadata"
    )
    parser.add_argument(
        "--without-state-estimator", action="store_true",
        help="Disable state estimator (WOSE mode)"
    )

    # Motion playback
    parser.add_argument(
        "--start-timestep", type=int, default=0,
        help="Starting timestep for motion playback"
    )
    parser.add_argument(
        "--max-timestep", type=int, default=0,
        help="Maximum timestep (0 = infinite)"
    )
    parser.add_argument(
        "--play-speed", type=float, default=1.0,
        help="Playback speed multiplier"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Loop motion when it completes"
    )

    # Advanced
    parser.add_argument(
        "--onnx-provider", type=str, default=None,
        choices=["cpu", "cuda", "tensorrt"],
        help="ONNX Runtime execution provider (default: auto-detect)"
    )

    return parser.parse_args()


def create_beyondmimic_policy_config(args) -> BeyondMimicPolicyConfig:
    """Create BeyondMimic policy configuration.

    Args:
        args: Command line arguments

    Returns:
        BeyondMimicPolicyConfig instance
    """
    model_file = Path(args.model_file)
    if not model_file.exists():
        raise FileNotFoundError(f"Model file not found: {model_file}")

    # Create DOF config (29 DOF G1 with hands)
    dof_cfg = DOFConfig(
        joint_names=G1_29DOF_BEYONDMIMIC_NAMES,
        num_dofs=29,
        default_pos=G1_BEYONDMIMIC_DEFAULT_POS,
    )

    # Determine device for ONNX Runtime
    onnx_device = args.onnx_provider or args.device
    if onnx_device is None:
        onnx_device = "cuda" if torch.cuda.is_available() else "cpu"

    # Auto-detect WOSE mode from filename
    without_se = args.without_state_estimator
    if "wose" in model_file.stem.lower():
        without_se = True
        print(f"   Auto-detected WOSE mode from filename")

    return BeyondMimicPolicyConfig(
        name="BeyondMimicPolicy",
        policy_file=model_file,
        device=onnx_device,
        obs_dof=dof_cfg,
        action_dof=dof_cfg,
        action_scales=G1_BEYONDMIMIC_ACTION_SCALES,
        freq=50.0,  # 50 Hz control
        use_model_meta_config=args.use_model_meta,
        without_state_estimator=without_se,
        use_motion_from_model=True,  # BeyondMimic embeds motion in model
        start_timestep=args.start_timestep,
        max_timestep=args.max_timestep,
    )


def main() -> int:
    """Main entry point."""
    args = parse_args()

    # Handle viewer/headless flags
    use_viewer = args.viewer and not args.headless

    print("=" * 60)
    print("BeyondMimic Policy via Policy Hub (Genesis)")
    print(f"Mode: {'Viewer' if use_viewer else 'Headless'}")
    print("=" * 60)

    # Check ONNX Runtime availability
    try:
        import onnxruntime as ort
        print(f"✅ ONNX Runtime: {ort.__version__}")
        print(f"   Available providers: {ort.get_available_providers()}")
    except ImportError:
        print("❌ ONNX Runtime not available!")
        print("   Install: pip install onnxruntime-gpu")
        return 1

    # Determine device
    backend = args.device or ("cuda" if torch.cuda.is_available() else "cpu")

    if torch.cuda.is_available():
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True

    # Load BeyondMimic policy configuration
    print("\n[1] Creating BeyondMimic policy configuration...")
    try:
        policy_config = create_beyondmimic_policy_config(args)
        print(f"✅ Policy config created: {policy_config.obs_dof.num_dofs} DOFs")
        print(f"   - Model file: {policy_config.policy_file}")
        print(f"   - ONNX device: {policy_config.device}")
        print(f"   - Use model metadata: {policy_config.use_model_meta_config}")
        print(f"   - Without SE: {policy_config.without_state_estimator}")
    except Exception as e:
        print(f"❌ Failed to create policy config: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Create environment via Policy Hub GenesisEnv
    print("\n[2] Creating environment via Policy Hub...")

    # Create BeyondMimic environment config
    bm_env_cfg = create_beyondmimic_genesis_env_config(
        num_envs=args.num_envs,
        backend=backend,
        viewer=use_viewer,
        enable_corruption=False,
        episode_length_s=20.0,
    )

    from genesislab.components.terrains import TerrainCfg
    # bm_env_cfg.scene.terrain = TerrainCfg(
    #     terrain_type="mesh",
    #     mesh_path="/home/ununtu/code/glab/genesislab/data/assets/test_plane.obj",
    #     mesh_decompose_error_threshold=0.0,
    #     env_spacing=0,
    #     mesh_sdf_cell_size=0.02,
    # )
    # Use USD as terrain (terrain system approach)
    bm_env_cfg.scene.terrain = TerrainCfg(
        terrain_type="usd",
        usd_path="/home/ununtu/code/glab/genesislab/data/assets/isaacsim_assets/Assets/Isaac/4.5/Isaac/Environments/Simple_Warehouse/warehouse.usd",
        env_spacing=0,
    )

    from genesislab.engine.scene import CameraCfg, RecordingCfg
    bm_env_cfg.scene.camera = CameraCfg(
        res=tuple([1920, 1080]),
        pos=tuple([3.0, 0.0, 3.0]),
        lookat=tuple([0.0, 0.0, 0.5]),
        fov=45.0,
        backend="rasterizer",  # Fast rendering for headless
        show_in_gui=False,     # Don't show in viewer
    )

    # Recording configuration (only if --record-video is set)
    bm_env_cfg.scene.recording = RecordingCfg(
        enabled=True,
        save_path="output/beyondmimic.mp4",
        fps=50,
        codec="libx264",
        codec_preset="veryfast",
        codec_tune="zerolatency",
        render_rgb=True,
        render_depth=False,
        render_segmentation=False,
        render_normal=False,
    )
    print(f"\n🎥 Video recording enabled:")

    # Create GenesisEnv wrapper
    genesis_cfg = GenesisEnvConfig(
        dof=policy_config.obs_dof,
        num_envs=args.num_envs,
    )

    try:
        env = GenesisEnv(cfg=genesis_cfg, device=backend, env_cfg=bm_env_cfg)
        print(f"✅ Environment created: {env.num_envs} envs, {env.num_dofs} DOFs")
    except Exception as e:
        print(f"❌ Failed to create environment: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Load BeyondMimic policy through Policy Hub
    print("\n[3] Loading BeyondMimic policy via Policy Hub...")

    try:
        # Extract kwargs for load_policy (exclude 'name' to avoid conflict)
        policy_kwargs = {k: v for k, v in policy_config.__dict__.items() if k != 'name'}
        policy = load_policy("BeyondMimicPolicy", **policy_kwargs)
        print(f"✅ Policy loaded: {policy.cfg.name}")
        print(f"   - Device: {policy.device}")
        print(f"   - Control frequency: {policy.freq} Hz")
        print(f"   - Num observations: {policy.num_obs}")
        print(f"   - Num actions: {policy.num_actions}")
        print(f"   - Has ONNX model: {policy.session is not None}")
    except Exception as e:
        print(f"❌ Failed to load policy: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Override play speed if specified
    if args.play_speed != 1.0:
        policy.play_speed = args.play_speed
        print(f"   - Play speed: {policy.play_speed}x")

    # Reset
    print("\n[4] Resetting...")
    env.reset()
    policy.reset()
    print("✅ Ready to run")

    # Main loop
    print(f"\n[5] Running for {args.max_steps} steps...")
    if args.max_timestep > 0:
        print(f"   Motion will stop at timestep {args.max_timestep}")
    if args.loop:
        print("   Loop mode enabled - motion will restart when complete")
    print()

    try:
        t0 = time.time()
        motion_resets = 0

        for step in range(args.max_steps):
            # Get environment state via Policy Hub interface
            env_data = env.get_data()

            # Get observation and action through Policy Hub interface
            obs, extras = policy.get_observation(env_data, {})
            action = policy.get_action(obs)

            # Step environment (GenesisEnv.step handles action mapping)
            step_result = env.step(action)

            # Post-step callback (updates timestep)
            policy.post_step_callback()

            # Check if motion is done
            if args.loop and extras.get("motion_done", False):
                policy.reset()
                motion_resets += 1
                print(f"\n🔄 Motion completed, restarting (loop {motion_resets})...\n")

            # Handle environment resets
            if step_result.get("terminated", False).any() or step_result.get("truncated", False).any():
                policy.reset()

            # Print status
            if step % args.print_every == 0:
                base_pos = env.base_pos
                fps = (step + 1) / max(1e-6, time.time() - t0)
                timestep = extras.get("timestep", policy.timestep)
                motion_done = extras.get("motion_done", False)
                status = "DONE" if motion_done else f"t={timestep:.0f}"

                print(
                    f"step={step:06d} fps={fps:6.1f} "
                    f"pos=[{base_pos[0]:6.2f}, {base_pos[1]:6.2f}, {base_pos[2]:5.3f}] "
                    f"motion={status}"
                )

            # Stop if motion is done and not looping
            if not args.loop and extras.get("motion_done", False):
                print(f"\n✅ Motion playback completed at step {step}")
                break

    except KeyboardInterrupt:
        print("\n✅ Interrupted by user")
    finally:
        del env

    print("\n" + "=" * 60)
    print("✅ Done!")
    if args.loop and motion_resets > 0:
        print(f"   Total loops: {motion_resets}")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
