"""Math utilities for genPiHub.

Provides common mathematical operations for robotics applications,
particularly quaternion operations.
"""

import torch
from typing import Union
import numpy as np


def quat_rotate_inverse(quat: torch.Tensor, vec: torch.Tensor) -> torch.Tensor:
    """Rotate a vector by the inverse of a quaternion.

    Args:
        quat: The quaternion in (w, x, y, z). Shape is (..., 4).
        vec: The vector in (x, y, z). Shape is (..., 3).

    Returns:
        The rotated vector in (x, y, z). Shape is (..., 3).
    """
    return quat_apply_inverse(quat, vec)


def quat_apply_inverse(quat: torch.Tensor, vec: torch.Tensor) -> torch.Tensor:
    """Apply an inverse quaternion rotation to a vector.

    This is more efficient than quat_rotate_inverse.

    Args:
        quat: The quaternion in (w, x, y, z). Shape is (..., 4).
        vec: The vector in (x, y, z). Shape is (..., 3).

    Returns:
        The rotated vector in (x, y, z). Shape is (..., 3).
    """
    # Store shape
    shape = vec.shape
    # Reshape to (N, 3) for multiplication
    quat = quat.reshape(-1, 4)
    vec = vec.reshape(-1, 3)
    # Extract components from quaternions
    xyz = quat[:, 1:]
    t = xyz.cross(vec, dim=-1) * 2
    return (vec - quat[:, 0:1] * t + xyz.cross(t, dim=-1)).view(shape)


def quat_rotate(quat: torch.Tensor, vec: torch.Tensor) -> torch.Tensor:
    """Rotate a vector by a quaternion.

    Args:
        quat: The quaternion in (w, x, y, z). Shape is (..., 4).
        vec: The vector in (x, y, z). Shape is (..., 3).

    Returns:
        The rotated vector in (x, y, z). Shape is (..., 3).
    """
    return quat_apply(quat, vec)


def quat_apply(quat: torch.Tensor, vec: torch.Tensor) -> torch.Tensor:
    """Apply a quaternion rotation to a vector.

    Args:
        quat: The quaternion in (w, x, y, z). Shape is (..., 4).
        vec: The vector in (x, y, z). Shape is (..., 3).

    Returns:
        The rotated vector in (x, y, z). Shape is (..., 3).
    """
    # Store shape
    shape = vec.shape
    # Reshape to (N, 3) for multiplication
    quat = quat.reshape(-1, 4)
    vec = vec.reshape(-1, 3)
    # Extract components from quaternions
    xyz = quat[:, 1:]
    t = xyz.cross(vec, dim=-1) * 2
    return (vec + quat[:, 0:1] * t + xyz.cross(t, dim=-1)).view(shape)


def quat_conjugate(quat: torch.Tensor) -> torch.Tensor:
    """Compute the conjugate of a quaternion.

    Args:
        quat: The quaternion in (w, x, y, z). Shape is (..., 4).

    Returns:
        The conjugate quaternion in (w, x, y, z). Shape is (..., 4).
    """
    shape = quat.shape
    quat = quat.reshape(-1, 4)
    return torch.cat([quat[:, 0:1], -quat[:, 1:]], dim=-1).view(shape)


def quat_mul(quat1: torch.Tensor, quat2: torch.Tensor) -> torch.Tensor:
    """Multiply two quaternions.

    Args:
        quat1: First quaternion in (w, x, y, z). Shape is (..., 4).
        quat2: Second quaternion in (w, x, y, z). Shape is (..., 4).

    Returns:
        The product quaternion in (w, x, y, z). Shape is (..., 4).
    """
    shape = quat1.shape
    quat1 = quat1.reshape(-1, 4)
    quat2 = quat2.reshape(-1, 4)

    w1, x1, y1, z1 = quat1[:, 0], quat1[:, 1], quat1[:, 2], quat1[:, 3]
    w2, x2, y2, z2 = quat2[:, 0], quat2[:, 1], quat2[:, 2], quat2[:, 3]

    w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
    x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
    y = w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2
    z = w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2

    return torch.stack([w, x, y, z], dim=-1).view(shape)


def normalize(vec: torch.Tensor, eps: float = 1e-9) -> torch.Tensor:
    """Normalize a vector.

    Args:
        vec: The vector. Shape is (..., N).
        eps: Small value to avoid division by zero.

    Returns:
        The normalized vector. Shape is (..., N).
    """
    return vec / (torch.norm(vec, dim=-1, keepdim=True) + eps)
