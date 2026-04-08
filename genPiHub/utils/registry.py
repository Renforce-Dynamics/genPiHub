"""Registry system for dynamic policy and environment loading.

Inspired by RoboJuDo's module registry system.
"""

from typing import Any, Type, TypeVar, Generic
import importlib
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class Registry(Generic[T]):
    """Registry for dynamic class loading.

    Example:
        >>> from genPiHub.policies import Policy
        >>> policy_registry = Registry(package="genPiHub.policies", base_class=Policy)
        >>> policy_registry.add("AMOPolicy", ".amo_policy")
        >>>
        >>> # Later, dynamically load
        >>> policy_class = policy_registry.get("AMOPolicy")
        >>> policy = policy_class(config, device="cuda")
    """

    def __init__(self, package: str = "", base_class: Type[T] | None = None):
        """Initialize registry.

        Args:
            package: Base package name for relative imports
            base_class: Base class for type checking
        """
        self.package = package
        self.base_class = base_class
        self._registry: dict[str, str] = {}
        self._loaded: dict[str, Type[T]] = {}

    def add(self, name: str, module_path: str):
        """Register a class for lazy loading.

        Args:
            name: Class name to register
            module_path: Module path (absolute or relative to package)
        """
        if name in self._registry:
            logger.warning(f"Overwriting existing registration for '{name}'")
        self._registry[name] = module_path

    def get(self, name: str) -> Type[T]:
        """Get registered class (loads on first access).

        Args:
            name: Registered class name

        Returns:
            Class type

        Raises:
            KeyError: If name not registered
            ImportError: If module cannot be imported
            AttributeError: If class not found in module
        """
        # Check if already loaded
        if name in self._loaded:
            return self._loaded[name]

        # Check if registered
        if name not in self._registry:
            available = ", ".join(self._registry.keys())
            raise KeyError(
                f"'{name}' not registered. Available: {available}"
            )

        # Load module
        module_path = self._registry[name]
        if module_path.startswith("."):
            # Relative import
            full_path = self.package + module_path
        else:
            # Absolute import
            full_path = module_path

        try:
            module = importlib.import_module(full_path)
        except ImportError as e:
            raise ImportError(
                f"Failed to import module '{full_path}' for '{name}': {e}"
            ) from e

        # Get class from module
        if not hasattr(module, name):
            raise AttributeError(
                f"Module '{full_path}' has no attribute '{name}'"
            )

        cls = getattr(module, name)

        # Type check
        if self.base_class is not None:
            if not issubclass(cls, self.base_class):
                raise TypeError(
                    f"'{name}' must be subclass of {self.base_class.__name__}"
                )

        # Cache and return
        self._loaded[name] = cls
        logger.debug(f"Loaded '{name}' from '{full_path}'")
        return cls

    def list_registered(self) -> list[str]:
        """List all registered names."""
        return list(self._registry.keys())

    def is_registered(self, name: str) -> bool:
        """Check if name is registered."""
        return name in self._registry
