"""Tablet Controller - Controls the tablet via Accessibility Services.

Handles all communication with the tablet through shell commands and accessibility services.
This version works when running Tucker directly on your tablet via Termux.
"""

import subprocess
import shutil
import time
from typing import Optional, Tuple
from loguru import logger
from config import Config


class TabletController:
    """Controls tablet via shell commands (works on Termux)."""

    def __init__(self, host: str = None, port: int = None):
        """Initialize tablet controller.

        Args:
            host: Not used in Termux mode
            port: Not used in Termux mode
        """
        self.host = host or "localhost"
        self.port = port or 5037

        # Find tools: am (activity manager), input (simulate taps/keys), screencap, wm
        self.am_path = self._find_tool("am")
        self.input_path = self._find_tool("input")
        self.screencap_path = self._find_tool("screencap")
        # 'wm' is usually available as a shell builtin; use plain 'wm' if not found
        self.wm_path = self._find_tool("wm") or "wm"

        logger.info(
            f"TabletController initialized (Termux mode) - am: {self.am_path}, input: {self.input_path}, screencap: {self.screencap_path}"
        )

    def _find_tool(self, name: str) -> str:
        """Locate a tool binary via shutil.which or return the tool name as fallback."""
        path = shutil.which(name)
        if path:
            logger.debug(f"Found {name} at: {path}")
            return path
        logger.debug(f"{name} not found in PATH, will attempt to call '{name}' directly")
        return name

    def _run_shell(self, *args, check_output=False) -> str:
        """Run a shell command directly.

        Args:
            *args: Command arguments
            check_output: If True, return output

        Returns:
            Command output as string
        """
        cmd = list(args)
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
            if result.returncode != 0:
                if check_output:
                    logger.error(f"Shell error ({' '.join(cmd)}): {result.stderr.strip()}")
                    return ""
                logger.debug(f"Shell non-zero exit ({result.returncode}) for: {' '.join(cmd)}")
            return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {' '.join(cmd)}")
            return ""
        except Exception as e:
            logger.error(f"Failed to run shell command {' '.join(cmd)}: {e}")
            return ""

    def check_connection(self) -> bool:
        """Check if we can access the tablet (always true in Termux mode).

        Returns:
            True (always connected when running on tablet)
        """
        logger.info("✓ Tablet connected! (Running on Termux)")
        return True

    def shell(self, command: str) -> str:
        """Execute shell command directly on tablet.

        Args:
            command: Shell command to execute

        Returns:
            Command output
        """
        try:
            result = subprocess.run(["sh", "-c", command], capture_output=True, text=True, timeout=15)
            return result.stdout.strip()
        except Exception as e:
            logger.error(f"Shell command failed: {e}")
            return ""

    def tap(self, x: int, y: int) -> bool:
        """Tap at coordinates on tablet screen using input command.

        Args:
            x: X coordinate
            y: Y coordinate

        Returns:
            True if successful
        """
        try:
            cmd = [self.input_path, "tap", str(x), str(y)]
            self._run_shell(*cmd)
            logger.debug(f"Tapped at ({x}, {y})")
            return True
        except Exception as e:
            logger.error(f"Failed to tap: {e}")
            return False

    def type_text(self, text: str) -> bool:
        """Type text on tablet.

        Args:
            text: Text to type

        Returns:
            True if successful
        """
        try:
            # Escape quotes for shell-safe use
            safe_text = text.replace('"', '\\"').replace("'", "\\'")
            cmd = [self.input_path, "text", safe_text]
            self._run_shell(*cmd)
            logger.debug(f"Typed text: {text}")
            return True
        except Exception as e:
            logger.error(f"Failed to type: {e}")
            return False

    def press_key(self, key: str) -> bool:
        """Press a key on the tablet.

        Args:
            key: Key name (BACK, HOME, POWER, ENTER, etc.)

        Returns:
            True if successful
        """
        key_codes = {
            "BACK": 4,
            "HOME": 3,
            "POWER": 26,
            "ENTER": 66,
            "SPACE": 62,
            "DEL": 67,
        }

        code = key_codes.get(key.upper())
        if code is None:
            logger.warning(f"Unknown key: {key}")
            return False

        try:
            cmd = [self.input_path, "keyevent", str(code)]
            self._run_shell(*cmd)
            logger.debug(f"Pressed key: {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to press key: {e}")
            return False

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration: int = 500) -> bool:
        """Swipe on tablet screen.

        Args:
            x1, y1: Start coordinates
            x2, y2: End coordinates
            duration: Swipe duration in ms

        Returns:
            True if successful
        """
        try:
            cmd = [self.input_path, "swipe", str(x1), str(y1), str(x2), str(y2), str(duration)]
            self._run_shell(*cmd)
            logger.debug(f"Swiped from ({x1}, {y1}) to ({x2}, {y2})")
            return True
        except Exception as e:
            logger.error(f"Failed to swipe: {e}")
            return False

    def take_screenshot(self, filename: str) -> bool:
        """Take a screenshot on the tablet (Termux mode).

        Args:
            filename: Where to save the screenshot

        Returns:
            True if successful
        """
        try:
            cmd = [self.screencap_path, "-p", filename]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                logger.info(f"Screenshot saved to {filename}")
                return True
            else:
                logger.error(f"Screenshot failed: {result.stderr.strip()}")
                return False
        except FileNotFoundError:
            logger.error(
                "screencap not found. On Termux install the termux-api package or ensure 'screencap' and 'input' are available."
            )
            return False
        except Exception as e:
            logger.error(f"Failed to take screenshot: {e}")
            return False

    def get_screen_info(self) -> dict:
        """Get information about tablet screen.

        Returns:
            Dict with screen dimensions and info
        """
        try:
            output = self.shell("wm size")
            # Output format: "Physical size: 1920x1080"
            if output and "x" in output:
                size = output.split(":")[-1].strip()
                parts = size.split("x")
                if len(parts) == 2:
                    width, height = map(int, parts)
                    return {"width": width, "height": height, "size": size}
        except Exception as e:
            logger.error(f"Failed to get screen info: {e}")

        return {"width": 1080, "height": 1920}  # Default


if __name__ == "__main__":
    # Test the tablet controller
    try:
        controller = TabletController()
        print("Checking tablet connection...")
        if controller.check_connection():
            print("✓ Ready to control tablet!")
        else:
            print("✗ Tablet not connected")
    except Exception as e:
        print(f"Error: {e}")
