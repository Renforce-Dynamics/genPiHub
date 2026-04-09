"""BeyondMimic environment configuration.

BeyondMimic is a whole-body tracking policy that uses ONNX Runtime for inference.
It supports motions with internal reference data embedded in the ONNX model.

Reference: whole_body_tracking project
"""

from .env_cfg import BeyondMimicGenesisEnvCfg, build_beyondmimic_env_config

__all__ = ["BeyondMimicGenesisEnvCfg", "build_beyondmimic_env_config"]
