"""BeyondMimic environment configuration.

BeyondMimic is a whole-body tracking policy that uses ONNX Runtime for inference.
It supports motions with internal reference data embedded in the ONNX model.

Reference: whole_body_tracking project
"""

# Only export robot configuration constants to avoid circular imports
# Full environment configuration should be imported directly when needed
from .genesislab import *
