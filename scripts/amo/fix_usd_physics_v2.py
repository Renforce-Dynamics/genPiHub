#!/usr/bin/env python3
"""Add physics schemas to USD file so Genesis can parse it.

This script creates a new USD file that references the original and adds
UsdPhysics.CollisionAPI to all mesh prims, allowing Genesis to recognize them.

Usage:
    python fix_usd_physics_v2.py <input.usd> <output.usd>
"""

import sys
from pathlib import Path
from pxr import Usd, UsdGeom, UsdPhysics, Sdf


def add_physics_to_meshes_layered(input_path: str, output_path: str, verbose: bool = True):
    """Create a new USD file with collision APIs added via layer override.

    Args:
        input_path: Input USD file path
        output_path: Output USD file path (will be created/overwritten)
        verbose: Print progress information
    """
    # Create a new stage
    stage = Usd.Stage.CreateNew(output_path)

    # Add the input file as a sublayer reference
    root_layer = stage.GetRootLayer()
    root_layer.subLayerPaths.append(input_path)

    # Open the original stage to find meshes
    orig_stage = Usd.Stage.Open(input_path)

    # Find all mesh prims and add collision API as overrides in new layer
    mesh_count = 0
    collision_count = 0

    if verbose:
        print(f"Scanning for meshes in {input_path}...")

    for prim in Usd.PrimRange(orig_stage.GetPseudoRoot()):
        if prim.IsA(UsdGeom.Mesh):
            mesh_count += 1
            prim_path = prim.GetPath()

            # Get or create the prim in output stage as an override
            out_prim = stage.OverridePrim(prim_path)

            # Add CollisionAPI
            UsdPhysics.CollisionAPI.Apply(out_prim)
            collision_count += 1

            if verbose and collision_count <= 10:
                print(f"  Adding CollisionAPI to: {prim_path}")
            elif verbose and collision_count == 11:
                print(f"  ... (continuing for remaining meshes)")

    # Save the stage
    stage.Save()

    if verbose:
        print(f"\n✅ Found {mesh_count} meshes")
        print(f"✅ Added CollisionAPI overrides for {collision_count} meshes")
        print(f"✅ Output saved to: {output_path}")
        print(f"\nThe output file references the original, so keep both files.")

    return mesh_count, collision_count


def main():
    if len(sys.argv) < 3:
        print("Usage: python fix_usd_physics_v2.py <input.usd> <output.usd>")
        print("\nExample:")
        print("  python fix_usd_physics_v2.py scene.usd scene_with_physics.usd")
        return 1

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    # Validate input
    if not Path(input_path).exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return 1

    # Convert to absolute paths for sublayer reference
    input_path = str(Path(input_path).resolve())
    output_path = str(Path(output_path).resolve())

    print(f"Creating USD file with physics schemas...")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print()

    try:
        # Suppress USD warnings
        import warnings
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            add_physics_to_meshes_layered(input_path, output_path)

        print(f"\n✅ Success! Use '{output_path}' with Genesis.")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
