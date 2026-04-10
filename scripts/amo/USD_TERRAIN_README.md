# USD Terrain Loading for Genesis

## Problem Summary

When loading USD files as terrain in Genesis, you may encounter two common issues:

### 1. "No entities found in USD stage"
**Cause**: The USD file contains only visual geometry without physics metadata. Genesis requires `UsdPhysics.CollisionAPI` or `UsdPhysics.RigidBodyAPI` to identify entities.

**Solution**: Add physics schemas to all mesh prims.

### 2. "Negative determinant of rotation matrix detected"
**Cause**: Some meshes in the USD file have negative scale transforms (mirroring/reflection), which Genesis doesn't support.

**Solution**: Bake all transforms into mesh vertices to eliminate transform matrices.

## Quick Fix

Use the all-in-one preparation script:

```bash
python scripts/amo/prepare_usd_for_genesis.py <input.usd> <output.usd>
```

This script:
1. Flattens the USD file to resolve all references
2. Adds `CollisionAPI` to all meshes
3. Bakes transforms into mesh vertices
4. Exports a Genesis-ready USD file

## Example Usage

```bash
# Prepare a USD file for Genesis
python scripts/amo/prepare_usd_for_genesis.py \
    data/assets/psi0/107734119_175999932.usd \
    data/assets/psi0/107734119_genesis_ready.usd

# Use it in your script
python scripts/amo/play_amo_with_terrain_usd.py
```

## Individual Fix Scripts

If you need to apply fixes separately:

### Add Physics Schemas Only
```bash
python scripts/amo/fix_usd_physics_v2.py <input.usd> <output.usd>
```
- Adds `CollisionAPI` to all meshes
- Uses layer override (keeps original file)

### Bake Transforms Only
```bash
python scripts/amo/bake_usd_transforms.py <input.usd> <output.usd>
```
- Flattens the stage
- Bakes transform matrices into mesh vertices
- Fixes negative scale issues

## Configuration

After preparing your USD file, configure the terrain in your script:

```python
from genPiHub.configs import create_amo_genesis_env_config_with_usd_scene

env_cfg = create_amo_genesis_env_config_with_usd_scene(
    usd_scene_path="data/assets/psi0/107734119_genesis_ready.usd",
    num_envs=1,
    backend="cuda",
    viewer=True,
    increase_collision_limits=True,  # For complex scenes with many meshes
)
```

## Performance Tips

For complex USD files (many meshes):
- Set `increase_collision_limits=True` to handle more collision pairs
- Consider reducing mesh complexity if loading is slow
- Use headless mode for faster iteration during development

## Troubleshooting

### Still getting "No entities found"?
- Verify physics schemas were added:
  ```python
  from pxr import Usd, UsdPhysics, UsdGeom
  stage = Usd.Stage.Open("your_file.usd")
  meshes = [p for p in Usd.PrimRange(stage.GetPseudoRoot()) if p.IsA(UsdGeom.Mesh)]
  collision_prims = [p for p in meshes if p.HasAPI(UsdPhysics.CollisionAPI)]
  print(f"Meshes: {len(meshes)}, With collision: {len(collision_prims)}")
  ```

### Still getting negative determinant errors?
- Check if transforms were properly baked:
  ```python
  from pxr import Usd, UsdGeom
  import numpy as np
  
  stage = Usd.Stage.Open("your_file.usd")
  for prim in Usd.PrimRange(stage.GetPseudoRoot()):
      if prim.IsA(UsdGeom.Mesh):
          xform = UsdGeom.Xformable(prim)
          matrix = xform.ComputeLocalToWorldTransform(Usd.TimeCode.Default())
          det = np.linalg.det(np.array(matrix).reshape(4,4)[:3,:3])
          if abs(det + 1.0) < 0.1:
              print(f"Mirrored mesh found: {prim.GetPath()}")
  ```

### Missing shader warnings?
- These are safe to ignore - they're about missing material files
- Genesis will use default materials for rendering
- Collisions are based on geometry, not materials

## Notes

- The preparation process flattens the USD file, so the output is standalone
- Keep both original and prepared files - the original is useful for iteration
- Large USD files may take several minutes to process
- Prepared files are typically larger due to baked geometry
