"""genPiHub: Unified framework for humanoid robot policies.

A plug-and-play framework for deploying humanoid robot policies across
multiple simulation backends (Genesis, MuJoCo, Isaac Sim) and real robots.

Example:
    >>> from genPiHub import load_policy
    >>> policy = load_policy("AMOPolicy", model_dir=".reference/AMO", device="cuda")
    >>> policy.reset()
"""

from genPiHub.policies import Policy, policy_registry
from genPiHub.environments import Environment, environment_registry
from genPiHub.configs import (
    PolicyConfig,
    EnvConfig,
    AMOPolicyConfig,
    GenesisEnvConfig,
)
from genPiHub.tools import DOFConfig


def load_policy(name: str, **kwargs) -> Policy:
    """Load a policy by name.

    Args:
        name: Policy name (e.g., "AMOPolicy")
        **kwargs: Policy-specific arguments

    Returns:
        Policy instance

    Example:
        >>> policy = load_policy("AMOPolicy", model_dir=".reference/AMO")
    """
    policy_class = policy_registry.get(name)

    # If kwargs provided, try to construct config
    if kwargs:
        # Get config class
        config_name = name.replace("Policy", "PolicyConfig")
        try:
            from genPiHub import configs
            config_class = getattr(configs, config_name)
            config = config_class(**kwargs)
        except AttributeError:
            # Fallback to PolicyConfig
            config = PolicyConfig(**kwargs)

        device = kwargs.get("device", "cpu")
        return policy_class(config, device)

    # No kwargs, need config object
    raise ValueError("Must provide either config or kwargs")


def load_environment(name: str, **kwargs) -> Environment:
    """Load an environment by name.

    Args:
        name: Environment name (e.g., "GenesisEnv")
        **kwargs: Environment-specific arguments

    Returns:
        Environment instance

    Example:
        >>> env = load_environment("GenesisEnv", robot="G1")
    """
    env_class = environment_registry.get(name)

    # If kwargs provided, try to construct config
    if kwargs:
        # Get config class
        config_name = name.replace("Env", "EnvConfig")
        try:
            from genPiHub import configs
            config_class = getattr(configs, config_name)
            config = config_class(**kwargs)
        except AttributeError:
            # Fallback to EnvConfig
            config = EnvConfig(**kwargs)

        device = kwargs.get("device", "cpu")
        return env_class(config, device)

    # No kwargs, need config object
    raise ValueError("Must provide either config or kwargs")


__all__ = [
    # Core classes
    "Policy",
    "Environment",
    # Registries
    "policy_registry",
    "environment_registry",
    # Configs
    "PolicyConfig",
    "EnvConfig",
    "AMOPolicyConfig",
    "GenesisEnvConfig",
    "DOFConfig",
    # Loaders
    "load_policy",
    "load_environment",
]

__version__ = "0.1.0"
