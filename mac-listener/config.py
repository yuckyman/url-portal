"""
Configuration for the Mac listener service.
"""

import os
from pathlib import Path
from typing import List


class Config:
    """Application configuration."""

    # Server settings
    HOST = os.getenv('WM_MAC_HOST', '0.0.0.0')
    PORT = int(os.getenv('WM_MAC_PORT', '8091'))
    DEBUG = os.getenv('WM_MAC_DEBUG', 'False').lower() == 'true'

    # Security: allowlist + HMAC
    SHARED_SECRET = os.getenv('WM_MAC_SHARED_SECRET', '')
    ALLOWLIST_REQUIRED = os.getenv('WM_MAC_ALLOWLIST_REQUIRED', 'true').lower() == 'true'
    ALLOWED_IPS = [
        ip.strip() for ip in os.getenv('WM_MAC_ALLOWED_IPS', '').split(',')
        if ip.strip()
    ]
    SIGNATURE_REQUIRED = os.getenv('WM_MAC_SIGNATURE_REQUIRED', 'true').lower() == 'true'
    MAX_SKEW_SECONDS = int(os.getenv('WM_MAC_MAX_SKEW_SECONDS', '300'))

    # Safe path constraints
    ALLOWED_ROOTS: List[Path] = [
        Path(p.strip()).expanduser().resolve()
        for p in os.getenv('WM_MAC_ALLOWED_ROOTS', '').split(':')
        if p.strip()
    ]

    # Obsidian configuration
    OBSIDIAN_VAULTS = [
        v.strip() for v in os.getenv('WM_MAC_OBSIDIAN_VAULTS', 'WINTERMUTE').split(',')
        if v.strip()
    ]

    # URL handling
    ALLOWED_URL_SCHEMES = [
        s.strip() for s in os.getenv('WM_MAC_ALLOWED_URL_SCHEMES', 'http,https').split(',')
        if s.strip()
    ]
    ALLOWED_URL_APPS = [
        a.strip() for a in os.getenv('WM_MAC_ALLOWED_URL_APPS', '').split(',')
        if a.strip()
    ]

    # Agent presets
    PRESETS_PATH = Path(os.getenv('WM_MAC_PRESETS_PATH', 'presets.json'))

    # Terminal app for tmux attach (Terminal by default)
    TERMINAL_APP = os.getenv('WM_MAC_TERMINAL_APP', 'Terminal')
