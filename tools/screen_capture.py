"""tools/screen_capture.py - small improvements to use controller's screenshot properly
"""

from pathlib import Path
from loguru import logger
from config import Config
from agents.tablet_controller import TabletController


class ScreenCapture:
    """Captures screenshots from the tablet."""

    def __init__(self, controller: TabletController = None):
        self.controller = controller or TabletController()
        self.screenshots_dir = Config.SCREENSHOTS_DIR

    def take_screenshot(self, filename: str = None) -> str:
        """Take a screenshot and save it.

        Returns the path to saved screenshot or None on failure.
        """
        if not filename:
            import datetime
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"screenshot_{timestamp}.png"

        filepath = self.screenshots_dir / filename

        ok = self.controller.take_screenshot(str(filepath))

        if ok and filepath.exists():
            logger.info(f"✓ Screenshot saved: {filepath}")
            return str(filepath)
        else:
            logger.error(f"✗ Failed to save screenshot: {filepath}")
            return None

    def get_recent_screenshot(self) -> str:
        screenshots = sorted(self.screenshots_dir.glob('screenshot_*.png'), key=lambda p: p.stat().st_mtime, reverse=True)
        if screenshots:
            return str(screenshots[0])
        return None

    def clear_old_screenshots(self, keep_count: int = 10):
        screenshots = sorted(self.screenshots_dir.glob('screenshot_*.png'), key=lambda p: p.stat().st_mtime, reverse=True)
        to_delete = screenshots[keep_count:]
        for f in to_delete:
            try:
                f.unlink()
                logger.debug(f"Deleted old screenshot: {f.name}")
            except Exception as e:
                logger.error(f"Failed to delete {f}: {e}")
