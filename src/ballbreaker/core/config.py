import json
from pathlib import Path
from typing import Any, Dict

CONFIG_DIR = Path.home() / ".config" / "ballbreaker"
CONFIG_FILE = CONFIG_DIR / "config.json"

DEFAULT_CONFIG = {
    "install_dir": "/opt",
    "bin_dir": str(Path.home() / ".local" / "bin"),
    "desktop_dir": str(Path.home() / ".local" / "share" / "applications"),
    "elevate": True
}

def load_config() -> Dict[str, Any]:
    """
    Load configuration overrides from ~/.config/ballbreaker/config.json.
    Falls back to default config if file does not exist or fails to parse.
    """
    if not CONFIG_FILE.exists():
        return DEFAULT_CONFIG.copy()
    
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Merge to ensure all keys exist
            config = DEFAULT_CONFIG.copy()
            config.update(data)
            return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config: Dict[str, Any]) -> bool:
    """
    Save configuration overrides to ~/.config/ballbreaker/config.json.
    Returns True if successful, False otherwise.
    """
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # Ensure we only save relevant config keys
        cleaned_config = {}
        for key in DEFAULT_CONFIG:
            if key in config:
                val = config[key]
                if isinstance(val, Path):
                    cleaned_config[key] = str(val)
                else:
                    cleaned_config[key] = val
            else:
                cleaned_config[key] = DEFAULT_CONFIG[key]
                
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cleaned_config, f, indent=4)
        return True
    except Exception:
        return False
