#!/usr/bin/env python3
"""Bake transforms into USD meshes to handle negative scales.

Genesis doesn't support negative scale (mirroring) transforms.
This script bakes all transforms into the mesh vertices.

Usage:
    python bake_usd_transforms.py <input.usd> <output.usd>
"""

import sys
from pathlib import Path
from pxr import Usd, UsdGeom, Gf
import numpy as np


def bake_mesh_transform(mesh_prim):
    """Bake the transform matrix into mesh vertices."""
    mesh = UsdGeom.Mesh(mesh_prim)

    # Get transform matrix
    xformable = UsdGeom.Xformable(mesh_prim)
    transform_matrix = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())

    # Get current points
    points_attr = mesh.GetPointsAttr()
    if not points_attr:
        return False

    points = points_attr.Get()
    if not points:
        return False

    # Transform points
    transformed_points = []
    for point in points:
        # Convert to Gf.Vec4f for matrix multiplication (homogeneous coordinates)
        vec4 = transform_matrix * Gf.Vec4f(point[0], point[1], point[2], 1.0)
        transformed_points.append(Gf.Vec3f(vec4[0], vec4[1], vec4[2]))

    # Set transformed points
    points_attr.Set(transformed_points)

    # Reset transform to identity
    xformable.ClearXformOpOrder()

    return True


def bake_usd_file(input_path: str, output_path: str, verbose: bool = True):
    """Bake all mesh transforms in USD file."""
    # Open stage
    stage = Usd.Stage.Open(input_path)
    if not stage:
        raise RuntimeError(f"Failed to open USD file: {input_path}")

    # Flatten to resolve all references/layers
    if verbose:
        print("Flattening USD stage...")
    stage = stage.Flatten()

    # Export to output file
    stage.Export(output_path)

    # Reopen to modify
    output_stage = Usd.Stage.Open(output_path)

    # Find all meshes and bake transforms
    mesh_count = 0
    baked_count = 0

    if verbose:
        print(f"Baking transforms into mesh vertices...")

    for prim in Usd.PrimRange(output_stage.GetPseudoRoot()):
        if prim.IsA(UsdGeom.Mesh):
            mesh_count += 1

            # Check if mesh has non-identity transform
            xformable = UsdGeom.Xformable(prim)
            transform = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())

            # Check for negative determinant (mirroring)
            matrix = np.array(transform).reshape(4, 4)
            det = np.linalg.det(matrix[:3, :3])

            if abs(det + 1.0) < 0.01:  # Negative determinant (mirroring)
                if verbose and baked_count < 10:
                    print(f"  Baking (mirrored): {prim.GetPath()}")
                bake_mesh_transform(prim)
                baked_count += 1
            elif not transform.IsIdentity():
                if verbose and baked_count < 10:
                    print(f"  Baking: {prim.GetPath()}")
                bake_mesh_transform(prim)
                baked_count += 1

            if verbose and baked_count == 11:
                print(f"  ... (continuing for remaining meshes)")

    # Save
    output_stage.Save()

    if verbose:
        print(f"\n✅ Processed {mesh_count} meshes")
        print(f"✅ Baked {baked_count} transforms")
        print(f"✅ Output saved to: {output_path}")

    return mesh_count, baked_count


def main():
    if len(sys.argv) < 3:
        print("Usage: python bake_usd_transforms.py <input.usd> <output.usd>")
        print("\nExample:")
        print("  python bake_usd_transforms.py scene.usd scene_baked.usd")
        return 1

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if not Path(input_path).exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return 1

    print(f"Baking transforms in USD file...")
    print(f"  Input:  {input_path}")
    print(f"  Output: {output_path}")
    print()

    try:
        bake_usd_file(input_path, output_path)
        print(f"\n✅ Success! Use '{output_path}' with Genesis.")
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
