"""
Notification system for human oversight.

Implements:
- Console/CLI notifications with rich formatting
- Log-based notifications
- Configurable notification levels
- Notification history
"""

import logging
from typing import Optional, List
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

# Try to import rich for fancy console output
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
    _console = Console()
except ImportError:
    HAS_RICH = False
    _console = None


class NotificationLevel(str, Enum):
    """Notification importance level."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class NotificationChannel(str, Enum):
    """Notification delivery channel."""

    CONSOLE = "console"
    LOG = "log"
    BOTH = "both"


class Notification:
    """A notification message."""

    def __init__(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        title: Optional[str] = None,
        details: Optional[str] = None,
        timestamp: Optional[datetime] = None
    ):
        self.message = message
        self.level = level
        self.title = title or self._default_title()
        self.details = details
        self.timestamp = timestamp or datetime.now()

    def _default_title(self) -> str:
        """Get default title based on level."""
        titles = {
            NotificationLevel.DEBUG: "Debug",
            NotificationLevel.INFO: "Information",
            NotificationLevel.WARNING: "Warning",
            NotificationLevel.ERROR: "Error",
            NotificationLevel.CRITICAL: "Critical Alert"
        }
        return titles.get(self.level, "Notification")

    def to_dict(self):
        """Convert to dictionary."""
        return {
            "message": self.message,
            "level": self.level.value,
            "title": self.title,
            "details": self.details,
            "timestamp": self.timestamp.isoformat()
        }


class NotificationManager:
    """
    Manages notifications for human oversight.

    Supports console and log-based notifications.
    """

    def __init__(
        self,
        default_channel: NotificationChannel = NotificationChannel.BOTH,
        min_level: NotificationLevel = NotificationLevel.INFO,
        use_rich_formatting: bool = True
    ):
        """
        Initialize notification manager.

        Args:
            default_channel: Default notification channel
            min_level: Minimum level to display
            use_rich_formatting: Use rich formatting for console (if available)
        """
        self.default_channel = default_channel
        self.min_level = min_level
        self.use_rich = use_rich_formatting and HAS_RICH

        # Notification history
        self.history: List[Notification] = []

        # Level order for filtering
        self.level_order = {
            NotificationLevel.DEBUG: 0,
            NotificationLevel.INFO: 1,
            NotificationLevel.WARNING: 2,
            NotificationLevel.ERROR: 3,
            NotificationLevel.CRITICAL: 4
        }

        logger.info(
            f"NotificationManager initialized (channel={default_channel.value}, "
            f"min_level={min_level.value}, rich={self.use_rich})"
        )

    def notify(
        self,
        message: str,
        level: NotificationLevel = NotificationLevel.INFO,
        title: Optional[str] = None,
        details: Optional[str] = None,
        channel: Optional[NotificationChannel] = None
    ):
        """
        Send a notification.

        Args:
            message: Notification message
            level: Importance level
            title: Optional title
            details: Optional detailed information
            channel: Optional channel (uses default if None)
        """
        # Check if level meets minimum
        if self.level_order[level] < self.level_order[self.min_level]:
            return

        # Create notification
        notification = Notification(
            message=message,
            level=level,
            title=title,
            details=details
        )

        # Add to history
        self.history.append(notification)

        # Determine channel
        channel = channel or self.default_channel

        # Send to appropriate channels
        if channel in [NotificationChannel.CONSOLE, NotificationChannel.BOTH]:
            self._send_console(notification)

        if channel in [NotificationChannel.LOG, NotificationChannel.BOTH]:
            self._send_log(notification)

    def _send_console(self, notification: Notification):
        """Send notification to console."""
        if self.use_rich and _console:
            self._send_rich_console(notification)
        else:
            self._send_plain_console(notification)

    def _send_rich_console(self, notification: Notification):
        """Send formatted notification using rich."""
        # Determine style based on level
        styles = {
            NotificationLevel.DEBUG: "dim",
            NotificationLevel.INFO: "cyan",
            NotificationLevel.WARNING: "yellow",
            NotificationLevel.ERROR: "red",
            NotificationLevel.CRITICAL: "bold red on white"
        }
        style = styles.get(notification.level, "white")

        # Create panel content
        content = Text(notification.message, style=style)
        if notification.details:
            content.append("\n\n" + notification.details)

        # Create and print panel
        panel = Panel(
            content,
            title=notification.title,
            border_style=style
        )

        _console.print(panel)

    def _send_plain_console(self, notification: Notification):
        """Send plain text notification to console."""
        # Create prefix based on level
        prefixes = {
            NotificationLevel.DEBUG: "[DEBUG]",
            NotificationLevel.INFO: "[INFO]",
            NotificationLevel.WARNING: "[WARNING]",
            NotificationLevel.ERROR: "[ERROR]",
            NotificationLevel.CRITICAL: "[CRITICAL]"
        }
        prefix = prefixes.get(notification.level, "[NOTICE]")

        # Print notification
        print(f"\n{prefix} {notification.title}")
        print("-" * 70)
        print(notification.message)
        if notification.details:
            print(f"\nDetails: {notification.details}")
        print("-" * 70)

    def _send_log(self, notification: Notification):
        """Send notification to logger."""
        # Map notification level to log level
        log_methods = {
            NotificationLevel.DEBUG: logger.debug,
            NotificationLevel.INFO: logger.info,
            NotificationLevel.WARNING: logger.warning,
            NotificationLevel.ERROR: logger.error,
            NotificationLevel.CRITICAL: logger.critical
        }

        log_method = log_methods.get(notification.level, logger.info)

        # Build log message
        msg = f"{notification.title}: {notification.message}"
        if notification.details:
            msg += f" | {notification.details}"

        log_method(msg)

    def debug(self, message: str, **kwargs):
        """Send debug notification."""
        self.notify(message, level=NotificationLevel.DEBUG, **kwargs)

    def info(self, message: str, **kwargs):
        """Send info notification."""
        self.notify(message, level=NotificationLevel.INFO, **kwargs)

    def warning(self, message: str, **kwargs):
        """Send warning notification."""
        self.notify(message, level=NotificationLevel.WARNING, **kwargs)

    def error(self, message: str, **kwargs):
        """Send error notification."""
        self.notify(message, level=NotificationLevel.ERROR, **kwargs)

    def critical(self, message: str, **kwargs):
        """Send critical notification."""
        self.notify(message, level=NotificationLevel.CRITICAL, **kwargs)

    def get_history(
        self,
        level: Optional[NotificationLevel] = None,
        limit: int = 100
    ) -> List[Notification]:
        """
        Get notification history.

        Args:
            level: Optional filter by level
            limit: Maximum notifications to return

        Returns:
            List of notifications
        """
        notifications = self.history

        if level:
            notifications = [n for n in notifications if n.level == level]

        return notifications[-limit:]

    def clear_history(self):
        """Clear notification history."""
        self.history.clear()
        logger.debug("Notification history cleared")

    def get_stats(self) -> dict:
        """
        Get notification statistics.

        Returns:
            Dictionary with stats
        """
        total = len(self.history)

        by_level = {}
        for level in NotificationLevel:
            count = sum(1 for n in self.history if n.level == level)
            by_level[level.value] = count

        return {
            "total_notifications": total,
            "by_level": by_level,
            "use_rich_formatting": self.use_rich
        }

    def set_min_level(self, level: NotificationLevel):
        """
        Set minimum notification level to display.

        Args:
            level: New minimum level
        """
        self.min_level = level
        logger.info(f"Notification minimum level set to {level.value}")

    def set_channel(self, channel: NotificationChannel):
        """
        Set default notification channel.

        Args:
            channel: New default channel
        """
        self.default_channel = channel
        logger.info(f"Notification channel set to {channel.value}")
