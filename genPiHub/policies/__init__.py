"""Policy implementations and registry."""

from genPiHub.utils.registry import Registry
from .base_policy import Policy

# Create policy registry
policy_registry = Registry(package="genPiHub.policies", base_class=Policy)

__all__ = [
    "Policy",
    "policy_registry",
]


def __getattr__(name: str):
    """Dynamic import of registered policies."""
    try:
        policy_class = policy_registry.get(name)
    except Exception as e:
        raise AttributeError(f"module {__name__} has no attribute {name}") from e
    print(f"[genPiHub] Loading policy: {name}")
    globals()[name] = policy_class
    return policy_class


# ===== Register policies here =====
policy_registry.add("AMOPolicy", ".amo_policy")
policy_registry.add("CLOTPolicy", ".clot_policy")
# policy_registry.add("ProtoMotionsPolicy", ".protomotions_policy")  # TODO
