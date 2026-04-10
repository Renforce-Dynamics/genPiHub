#!/usr/bin/env python3
"""Prepare a USD file for use with Genesis.

This script performs two operations:
1. Adds physics schemas (CollisionAPI) to all meshes so Genesis can recognize them as entities
2. Bakes transforms into mesh vertices to handle negative scales (mirroring)

Usage:
    python prepare_usd_for_genesis.py <input.usd> <output.usd>

Example:
    python prepare_usd_for_genesis.py scene.usd scene_genesis_ready.usd
"""

import sys
from pathlib import Path
from pxr import Usd, UsdGeom, UsdPhysics, Gf
import numpy as np


def add_physics_schemas(stage):
    """Add CollisionAPI to all meshes."""
    mesh_count = 0
    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if prim.IsA(UsdGeom.Mesh):
            if not prim.HasAPI(UsdPhysics.CollisionAPI):
                UsdPhysics.CollisionAPI.Apply(prim)
            mesh_count += 1
    return mesh_count


def bake_mesh_transform(mesh_prim):
    """Bake the transform matrix into mesh vertices and fix winding order if mirrored."""
    mesh = UsdGeom.Mesh(mesh_prim)
    xformable = UsdGeom.Xformable(mesh_prim)

    # Get transform matrix
    transform_matrix = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())

    # Check for negative determinant (mirroring)
    matrix = np.array(transform_matrix).reshape(4, 4)
    det = np.linalg.det(matrix[:3, :3])
    is_mirrored = det < 0

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
        vec4 = transform_matrix * Gf.Vec4f(point[0], point[1], point[2], 1.0)
        transformed_points.append(Gf.Vec3f(vec4[0], vec4[1], vec4[2]))

    # Set transformed points
    points_attr.Set(transformed_points)

    # If mirrored, flip face winding order to maintain correct normals
    if is_mirrored:
        face_vertex_indices_attr = mesh.GetFaceVertexIndicesAttr()
        face_vertex_counts_attr = mesh.GetFaceVertexCountsAttr()

        if face_vertex_indices_attr and face_vertex_counts_attr:
            indices = list(face_vertex_indices_attr.Get())
            counts = list(face_vertex_counts_attr.Get())

            # Reverse winding order for each face
            flipped_indices = []
            idx = 0
            for count in counts:
                face_indices = indices[idx:idx+count]
                flipped_indices.extend(reversed(face_indices))
                idx += count

            face_vertex_indices_attr.Set(flipped_indices)

    # Reset ALL transforms in the prim's xform stack
    xformable.ClearXformOpOrder()

    # Also clear parent transforms to ensure no inherited transforms
    parent = mesh_prim.GetParent()
    while parent and parent.IsValid():
        parent_xform = UsdGeom.Xformable(parent)
        if parent_xform:
            parent_xform.ClearXformOpOrder()
        parent = parent.GetParent()

    return True


def bake_transforms(stage, verbose=True):
    """Bake all mesh transforms that have negative determinants (mirroring)."""
    mesh_count = 0
    baked_count = 0

    for prim in Usd.PrimRange(stage.GetPseudoRoot()):
        if prim.IsA(UsdGeom.Mesh):
            mesh_count += 1

            xformable = UsdGeom.Xformable(prim)
            transform = xformable.ComputeLocalToWorldTransform(Usd.TimeCode.Default())

            # Check for negative determinant (mirroring) or non-identity transform
            matrix = np.array(transform).reshape(4, 4)
            det = np.linalg.det(matrix[:3, :3])

            # Check if transform is identity
            is_identity = np.allclose(matrix, np.eye(4))

            if abs(det + 1.0) < 0.01 or not is_identity:
                if verbose and baked_count < 5:
                    print(f"  Baking transform: {prim.GetPath()}")
                bake_mesh_transform(prim)
                baked_count += 1

            if verbose and baked_count == 6:
                print(f"  ... (continuing for remaining meshes)")

    return mesh_count, baked_count


def prepare_usd_for_genesis(input_path: str, output_path: str, verbose: bool = True):
    """Prepare USD file for Genesis by adding physics and baking transforms."""

    if verbose:
        print(f"Step 1: Opening and flattening USD file...")

    # Open and flatten stage to resolve all references
    stage = Usd.Stage.Open(input_path)
    if not stage:
        raise RuntimeError(f"Failed to open USD file: {input_path}")

    flattened_layer = stage.Flatten()
    stage = Usd.Stage.Open(flattened_layer)

    if verbose:
        print(f"Step 2: Adding physics schemas...")

    mesh_count = add_physics_schemas(stage)

    if verbose:
        print(f"  ✅ Added CollisionAPI to {mesh_count} meshes")
        print(f"\nStep 3: Baking transforms...")

    _, baked_count = bake_transforms(stage, verbose=verbose)

    if verbose:
        print(f"  ✅ Baked {baked_count} mesh transforms")
        print(f"\nStep 4: Saving output file...")

    stage.Export(output_path)

    if verbose:
        print(f"  ✅ Saved to: {output_path}")

    return mesh_count, baked_count


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    if not Path(input_path).exists():
        print(f"❌ Error: Input file not found: {input_path}")
        return 1

    print("=" * 80)
    print("Preparing USD file for Genesis")
    print("=" * 80)
    print(f"Input:  {input_path}")
    print(f"Output: {output_path}")
    print()

    try:
        mesh_count, baked_count = prepare_usd_for_genesis(input_path, output_path)
        print()
        print("=" * 80)
        print(f"✅ Success!")
        print(f"   Processed {mesh_count} meshes")
        print(f"   Baked {baked_count} transforms")
        print(f"\n   Use '{output_path}' with Genesis.")
        print("=" * 80)
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
