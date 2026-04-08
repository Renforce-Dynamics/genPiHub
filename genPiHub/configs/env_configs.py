"""Environment configuration definitions."""

from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path

from genPiHub.tools import DOFConfig


@dataclass
class EnvConfig:
    """Base configuration for all environments.

    Attributes:
        name: Environment name
        backend: Backend type ("genesis", "mujoco", "isaac", etc.)
        device: Device for computation

        # Robot configuration
        robot_type: Robot type ("G1", "H1", etc.)
        dof: DOF configuration

        # Assets
        asset_path: Path to robot asset file

        # Physics
        physics_dt: Physics simulation timestep
        control_dt: Control timestep
    """

    # Basic info
    name: str = "BaseEnv"
    backend: str = "genesis"
    device: str = "cpu"

    # Robot
    robot_type: str = "G1"
    dof: DOFConfig = field(default_factory=DOFConfig)

    # Assets
    asset_path: Optional[Path | str] = None

    # Physics
    physics_dt: float = 0.005  # 200 Hz
    control_dt: float = 0.02   # 50 Hz

    # Visualization
    viewer: bool = False

    def __post_init__(self):
        """Post-initialization validation."""
        # Convert path
        if self.asset_path is not None and not isinstance(self.asset_path, Path):
            self.asset_path = Path(self.asset_path)

        # Validate timesteps
        assert self.physics_dt > 0, "physics_dt must be positive"
        assert self.control_dt > 0, "control_dt must be positive"
        assert self.control_dt >= self.physics_dt, "control_dt must be >= physics_dt"


# ===== Environment-specific configs =====

@dataclass
class GenesisEnvConfig(EnvConfig):
    """Configuration for Genesis environment."""

    name: str = "GenesisEnv"
    backend: str = "genesis"

    # Genesis-specific
    num_envs: int = 1
    backend_type: str = "gpu"  # "cpu" or "gpu"


@dataclass
class MuJoCoEnvConfig(EnvConfig):
    """Configuration for MuJoCo environment (placeholder)."""

    name: str = "MuJoCoEnv"
    backend: str = "mujoco"

    # MuJoCo-specific
    # TODO: Add MuJoCo-specific parameters


@dataclass
class IsaacEnvConfig(EnvConfig):
    """Configuration for Isaac Sim environment (placeholder)."""

    name: str = "IsaacEnv"
    backend: str = "isaac"

    # Isaac-specific
    # TODO: Add Isaac-specific parameters
