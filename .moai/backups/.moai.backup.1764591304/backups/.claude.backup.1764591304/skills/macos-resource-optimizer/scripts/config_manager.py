#!/usr/bin/env python3
"""
Configuration Manager - Centralized Configuration Handling

Manages optimizer configuration with:
- JSON-based configuration
- Environment variable overrides
- Runtime configuration updates
- Validation and defaults

Author: MoAI-ADK
Version: 3.0.0 (Phase 3 - Production)
Date: 2025-12-01
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigManager:
    """
    Centralized configuration management.

    Loads configuration from JSON with environment variable overrides.
    """

    DEFAULT_CONFIG_PATH = Path(__file__).parent.parent / "config/optimizer_config.json"

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize configuration manager.

        Args:
            config_path: Path to configuration file (optional)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()
        self._apply_env_overrides()

    def _load_config(self) -> Dict:
        """Load configuration from file."""
        if self.config_path.exists():
            try:
                with open(self.config_path) as f:
                    return json.load(f)
            except Exception as e:
                print(f"⚠️  Config load error: {e}, using defaults")
                return self._get_default_config()
        else:
            print(f"⚠️  Config not found at {self.config_path}, using defaults")
            return self._get_default_config()

    def _get_default_config(self) -> Dict:
        """Get default configuration."""
        return {
            "tab_suspension": {
                "enabled": True,
                "auto_suspend": False,
                "protect_pinned": True,
                "protect_active": True,
                "protect_audible": True
            },
            "memory_optimization": {
                "enabled": True,
                "auto_purge": False
            },
            "process_management": {
                "enabled": True,
                "never_terminate": ["Ghostty", "Visual Studio Code", "Chrome", "Firefox", "Safari"]
            },
            "monitoring": {
                "enabled": True
            },
            "learning": {
                "enabled": True
            },
            "notifications": {
                "enabled": True,
                "use_osascript_popups": True
            },
            "error_handling": {
                "enabled": True,
                "auto_recovery": True
            }
        }

    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        # Tab suspension
        if os.getenv("TAB_SUSPENSION_ENABLED"):
            self.config["tab_suspension"]["enabled"] = os.getenv("TAB_SUSPENSION_ENABLED").lower() == "true"

        # Auto suspend
        if os.getenv("TAB_AUTO_SUSPEND"):
            self.config["tab_suspension"]["auto_suspend"] = os.getenv("TAB_AUTO_SUSPEND").lower() == "true"

        # Notifications
        if os.getenv("NOTIFICATIONS_ENABLED"):
            self.config["notifications"]["enabled"] = os.getenv("NOTIFICATIONS_ENABLED").lower() == "true"

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """
        Get configuration value.

        Args:
            section: Configuration section
            key: Configuration key
            default: Default value if not found

        Returns:
            Configuration value
        """
        return self.config.get(section, {}).get(key, default)

    def set(self, section: str, key: str, value: Any):
        """
        Set configuration value (runtime only, not persisted).

        Args:
            section: Configuration section
            key: Configuration key
            value: Value to set
        """
        if section not in self.config:
            self.config[section] = {}

        self.config[section][key] = value

    def is_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.

        Args:
            feature: Feature name (section name)

        Returns:
            True if enabled
        """
        return self.config.get(feature, {}).get("enabled", False)

    def get_blacklist(self) -> list:
        """Get process blacklist."""
        return self.config.get("process_management", {}).get("never_terminate", [])

    def get_alert_thresholds(self) -> Dict:
        """Get alert thresholds."""
        return self.config.get("monitoring", {}).get("alert_thresholds", {
            "memory_percent": 85,
            "swap_percent": 80,
            "disk_percent": 90
        })

    def save(self):
        """Save configuration to file."""
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"✅ Configuration saved to {self.config_path}")
        except Exception as e:
            print(f"❌ Config save error: {e}")


# Global config instance
_config_instance: Optional[ConfigManager] = None


def get_config() -> ConfigManager:
    """Get global configuration instance."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


if __name__ == "__main__":
    # Test config manager
    config = ConfigManager()

    print("📋 Configuration Test")
    print("=" * 60)
    print(f"Tab suspension enabled: {config.is_enabled('tab_suspension')}")
    print(f"Learning enabled: {config.is_enabled('learning')}")
    print(f"Blacklist: {config.get_blacklist()}")
    print(f"Alert thresholds: {config.get_alert_thresholds()}")
    print()
    print("✅ Configuration loaded successfully")
