"""Environment implementations and registry."""

from genPiHub.utils.registry import Registry
from .base_env import Environment

# Create environment registry
environment_registry = Registry(package="genPiHub.environments", base_class=Environment)

__all__ = [
    "Environment",
    "environment_registry",
]


def __getattr__(name: str):
    """Dynamic import of registered environments."""
    try:
        env_class = environment_registry.get(name)
    except Exception as e:
        raise AttributeError(f"module {__name__} has no attribute {name}") from e
    print(f"[genPiHub] Loading environment: {name}")
    globals()[name] = env_class
    return env_class


# ===== Register environments here =====
environment_registry.add("GenesisEnv", ".genesis_env")  # ✅ Implemented
# environment_registry.add("MuJoCoEnv", ".mujoco_env")  # TODO
# environment_registry.add("IsaacEnv", ".isaac_env")  # TODO
