import json
from pathlib import Path
from unittest.mock import patch
import pytest

from ballbreaker.core.config import load_config, save_config, DEFAULT_CONFIG

def test_load_config_no_file(tmp_path):
    """
    If the configuration file doesn't exist, load_config should return DEFAULT_CONFIG.
    """
    mock_file = tmp_path / "config.json"
    mock_dir = tmp_path
    
    with patch("ballbreaker.core.config.CONFIG_FILE", mock_file), \
         patch("ballbreaker.core.config.CONFIG_DIR", mock_dir):
        config = load_config()
        assert config == DEFAULT_CONFIG


def test_save_and_load_config(tmp_path):
    """
    Verify that saving a custom config and subsequently loading it works correctly.
    """
    mock_file = tmp_path / "config.json"
    mock_dir = tmp_path
    
    custom_config = {
        "install_dir": "/custom/opt",
        "bin_dir": "/custom/bin",
        "desktop_dir": "/custom/desktop",
        "elevate": False
    }
    
    with patch("ballbreaker.core.config.CONFIG_FILE", mock_file), \
         patch("ballbreaker.core.config.CONFIG_DIR", mock_dir):
        
        # Save custom config
        assert save_config(custom_config) is True
        assert mock_file.exists()
        
        # Verify JSON content
        with open(mock_file, "r") as f:
            saved_data = json.load(f)
            assert saved_data["install_dir"] == "/custom/opt"
            assert saved_data["elevate"] is False
            
        # Load and verify merge
        loaded = load_config()
        assert loaded["install_dir"] == "/custom/opt"
        assert loaded["bin_dir"] == "/custom/bin"
        assert loaded["desktop_dir"] == "/custom/desktop"
        assert loaded["elevate"] is False


def test_load_corrupted_config(tmp_path):
    """
    If the configuration file contains invalid JSON, load_config should recover
    by falling back to DEFAULT_CONFIG instead of raising an error.
    """
    mock_file = tmp_path / "config.json"
    mock_dir = tmp_path
    
    mock_file.write_text("invalid json content")
    
    with patch("ballbreaker.core.config.CONFIG_FILE", mock_file), \
         patch("ballbreaker.core.config.CONFIG_DIR", mock_dir):
        config = load_config()
        assert config == DEFAULT_CONFIG
