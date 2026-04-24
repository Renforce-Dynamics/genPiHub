"""Atomic observation terms for HoloMotion (G1 29DoF).

Each ``_get_obs_<name>`` function is a direct port of the matching method in
``HoloMotion/deployment/unitree_g1_ros2_29dof/src/humanoid_policy/policy_node_29dof.py``.
The returned vector is always in ONNX joint order (when dof-valued).

The evaluator protocol follows :class:`PolicyObsBuilder` — look up
``_get_obs_<term_name>`` on the evaluator object. The evaluator in our case is
:class:`HoloMotionPolicy` itself; it owns the env/ctrl state buffers that these
functions read.
"""

from __future__ import annotations

import numpy as np


def gravity_orientation_from_quat_wxyz(q_wxyz: np.ndarray) -> np.ndarray:
    """Project gravity into the body frame given a base quaternion [w,x,y,z].

    Ported verbatim from HoloMotion/deployment obs_builder.get_gravity_orientation.
    """
    qw = float(q_wxyz[0])
    qx = float(q_wxyz[1])
    qy = float(q_wxyz[2])
    qz = float(q_wxyz[3])
    out = np.empty(3, dtype=np.float32)
    out[0] = 2.0 * (-qz * qx + qw * qy)
    out[1] = -2.0 * (qz * qy + qw * qx)
    out[2] = 1.0 - 2.0 * (qw * qw + qz * qz)
    return out
