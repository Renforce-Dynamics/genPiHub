"""BeyondMimic environment configuration.

BeyondMimic is a whole-body tracking policy that uses ONNX Runtime for inference.
It supports motions with internal reference data embedded in the ONNX model.

Reference: whole_body_tracking project
"""

# Only export robot configuration constants to avoid circular imports
# Full environment configuration should be imported directly when needed
from .robot_cfg import (
    G1_29DOF_BEYONDMIMIC_NAMES,
    G1_BEYONDMIMIC_DEFAULT_POS,
    G1_BEYONDMIMIC_ACTION_SCALES,
    G1_BEYONDMIMIC_STIFFNESS,
    G1_BEYONDMIMIC_DAMPING,
    G1_BEYONDMIMIC_EFFORT_LIMITS,
    G1_BEYONDMIMIC_VELOCITY_LIMIT,
    G1_BEYONDMIMIC_INITIAL_BASE_POS,
    G1_BEYONDMIMIC_INITIAL_BASE_QUAT,
)

__all__ = [
    "G1_29DOF_BEYONDMIMIC_NAMES",
    "G1_BEYONDMIMIC_DEFAULT_POS",
    "G1_BEYONDMIMIC_ACTION_SCALES",
    "G1_BEYONDMIMIC_STIFFNESS",
    "G1_BEYONDMIMIC_DAMPING",
    "G1_BEYONDMIMIC_EFFORT_LIMITS",
    "G1_BEYONDMIMIC_VELOCITY_LIMIT",
    "G1_BEYONDMIMIC_INITIAL_BASE_POS",
    "G1_BEYONDMIMIC_INITIAL_BASE_QUAT",
]
