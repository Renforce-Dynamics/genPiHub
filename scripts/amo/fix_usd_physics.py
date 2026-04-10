#!/usr/bin/env python3
"""Add physics schemas to USD file so Genesis can parse it.

This script adds UsdPhysics.CollisionAPI to all mesh prims in a USD file,
allowing Genesis to recognize them as rigid entities.

Usage:
    python fix_usd_physics.py <input.usd> <output.usd>

Example:
    python fix_usd_physics.py data/assets/psi0/107734119_175999932.usd data/assets/psi0/107734119_with_physics.usd
"""

import sys
from pathlib import Path
from pxr import Usd, UsdGeom, UsdPhysics


def add_physics_to_meshes(input_path: str, output_path: str, verbose: bool = True):
    """Add collision API to all mesh prims in USD file.

    Args:
        input_path: Input USD file path
        output_path: Output USD file path (will be created/overwritten)
        verbose: Print progress information
    """
    # Open input stage
    stage = Usd.Stage.Open(input_path)
    if not stage:
        raise RuntimeError(f"Failed to open USD file: {input_path}")

    # Create output stage
    output_stage = Usd.Stage.CreateNew(output_path)

    # Copy all prims
    output_stage.GetRootLayer().subLayerPaths.append(input_path)

    # Flatten the stage to embed all references
    output_stage = Usd.Stage.Open(output_path)
    output_stage.Flatten()

    # Find all mesh prims and add collision API
    mesh_count = 0
    collision_count = 0

    for prim in Usd.PrimRange(output_stage.GetPseudoRoot()):
        if prim.IsA(UsdGeom.Mesh):
            mesh_count += 1

            # Add CollisionAPI if not already present
            if not prim.HasAPI(UsdPhysics.CollisionAPI):
                UsdPhysics.CollisionAPI.Apply(prim)
                collision_count += 1

                if verbose and collision_count <= 10:
                    print(f"  Added CollisionAPI to: {prim.GetPath()}")

    # Save output
    output_stage.GetRootLayer().Save()

    if verbose:
        print(f"\n✅ Processed {mesh_count} meshes")
        print(f"✅ Added CollisionAPI to {collision_count} meshes")
        print(f"✅ Output saved to: {output_path}")

    return mesh_count, collision_count


def main():
    if len(sys.argv) < 3:
        print("Usage: python fix_usd_physics.py <input.usd> <output.usd>")
        print("\nExample:")
        print("  python fix_usd_physics.py scene.usd scene_with_physics.usd")
        return 1

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    # Validate input
    if not Path(input_path).exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return 1

    print(f"Processing USD file: {input_path}")
    print(f"Output will be saved to: {output_path}")
    print()

    try:
        add_physics_to_meshes(input_path, output_path)
        print(f"\n✅ Success! Use '{output_path}' with Genesis.")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
