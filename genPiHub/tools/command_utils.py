"""Command utilities for interactive control and command state management."""

from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import threading
import sys
import termios
import tty
from typing import Optional


@dataclass
class CommandState:
    """Command state for velocity control.

    Stores velocity commands and body pose commands for humanoid control.
    """
    vx: float = 0.0          # Forward velocity (m/s)
    vy: float = 0.0          # Lateral velocity (m/s)
    yaw_rate: float = 0.0    # Yaw rate (rad/s)
    height: float = 0.0      # Height adjustment
    torso_yaw: float = 0.0   # Torso yaw
    torso_pitch: float = 0.0 # Torso pitch
    torso_roll: float = 0.0  # Torso roll
    arm_enable: float = 0.0  # Arm enable flag

    def as_array(self) -> np.ndarray:
        """Convert to numpy array for policy input.

        Returns:
            Array of shape (8,): [vx, yaw_rate, vy, height, torso_yaw, torso_pitch, torso_roll, arm_enable]
        """
        return np.array([
            self.vx,
            self.yaw_rate,
            self.vy,
            self.height,
            self.torso_yaw,
            self.torso_pitch,
            self.torso_roll,
            self.arm_enable,
        ], dtype=np.float32)


class TerminalController:
    """Interactive keyboard controller for humanoid commands.

    Controls:
        w/s - Increase/decrease forward velocity (vx)
        a/d - Rotate left/right (yaw_rate)
        e/c - Strafe right/left (vy)
        z/x - Lower/raise height
        q   - Quit
    """

    def __init__(self, state: CommandState, vx_step: float = 0.05, vy_step: float = 0.05,
                 yaw_step: float = 0.1, height_step: float = 0.02):
        """Initialize terminal controller.

        Args:
            state: CommandState to modify
            vx_step: Forward velocity step size
            vy_step: Lateral velocity step size
            yaw_step: Yaw rate step size
            height_step: Height adjustment step size
        """
        self.state = state
        self.vx_step = vx_step
        self.vy_step = vy_step
        self.yaw_step = yaw_step
        self.height_step = height_step

        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._quit = False

        # Terminal settings
        self._old_settings = None

    def start(self):
        """Start keyboard listener thread."""
        self._running = True
        self._quit = False
        self._thread = threading.Thread(target=self._keyboard_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """Stop keyboard listener thread."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=1.0)
        self._restore_terminal()

    def poll(self) -> bool:
        """Poll for quit signal.

        Returns:
            True if user pressed 'q' to quit
        """
        return self._quit

    def _setup_terminal(self):
        """Setup terminal for raw input."""
        if sys.stdin.isatty():
            self._old_settings = termios.tcgetattr(sys.stdin)
            tty.setcbreak(sys.stdin.fileno())

    def _restore_terminal(self):
        """Restore terminal settings."""
        if self._old_settings is not None:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, self._old_settings)

    def _get_key(self) -> Optional[str]:
        """Get a single keypress without blocking.

        Returns:
            Key character or None if no key pressed
        """
        if sys.stdin.isatty():
            import select
            if select.select([sys.stdin], [], [], 0.0)[0]:
                return sys.stdin.read(1)
        return None

    def _keyboard_loop(self):
        """Main keyboard listener loop."""
        self._setup_terminal()

        try:
            while self._running:
                key = self._get_key()
                if key is None:
                    continue

                # Process key
                if key == 'w':
                    self.state.vx += self.vx_step
                    print(f"\r[CMD] vx={self.state.vx:.2f}  ", end='', flush=True)
                elif key == 's':
                    self.state.vx -= self.vx_step
                    print(f"\r[CMD] vx={self.state.vx:.2f}  ", end='', flush=True)
                elif key == 'a':
                    self.state.yaw_rate += self.yaw_step
                    print(f"\r[CMD] yaw={self.state.yaw_rate:.2f}  ", end='', flush=True)
                elif key == 'd':
                    self.state.yaw_rate -= self.yaw_step
                    print(f"\r[CMD] yaw={self.state.yaw_rate:.2f}  ", end='', flush=True)
                elif key == 'e':
                    self.state.vy += self.vy_step
                    print(f"\r[CMD] vy={self.state.vy:.2f}  ", end='', flush=True)
                elif key == 'c':
                    self.state.vy -= self.vy_step
                    print(f"\r[CMD] vy={self.state.vy:.2f}  ", end='', flush=True)
                elif key == 'z':
                    self.state.height -= self.height_step
                    print(f"\r[CMD] height={self.state.height:.2f}  ", end='', flush=True)
                elif key == 'x':
                    self.state.height += self.height_step
                    print(f"\r[CMD] height={self.state.height:.2f}  ", end='', flush=True)
                elif key == 'q':
                    print(f"\r[CMD] Quit requested  ", flush=True)
                    self._quit = True
                    self._running = False
                    break

        finally:
            self._restore_terminal()
