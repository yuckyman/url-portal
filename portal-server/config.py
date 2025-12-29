"""
Configuration for the Wintermute Portal Router.
"""

import os
from pathlib import Path

from dotenv import load_dotenv


_ENV_PATH = Path(__file__).resolve().parents[1] / '.env'
load_dotenv(_ENV_PATH)


class Config:
    """Application configuration."""
    
    # Server settings
    HOST = os.getenv('WM_PORTAL_HOST', '0.0.0.0')
    PORT = int(os.getenv('WM_PORTAL_PORT', '8090'))
    DEBUG = os.getenv('WM_PORTAL_DEBUG', 'False').lower() == 'true'
    
    # Wintermute repo path on yuckbox
    WINTERMUTE_REPO_PATH = os.getenv(
        'WINTERMUTE_REPO_PATH',
        '/home/ian/WINTERMUTE'
    )
    
    # Git configuration
    GIT_USER_NAME = os.getenv('GIT_USER_NAME', 'Wintermute Portal')
    GIT_USER_EMAIL = os.getenv('GIT_USER_EMAIL', 'portal@wintermute.local')

    # Working Copy (iOS) URL template for opening files.
    # Repo is static for the primary vault: http://yuckbox:3000/ian/wintermute
    WORKING_COPY_REPO = 'wintermute'
    WORKING_COPY_URL_KEY = os.getenv('WC_URL_KEY', '')
    WORKING_COPY_URL_TEMPLATE = (
        'working-copy://x-callback-url/read?repo={repo}&path={path}{key_param}'
        '&type=auto&clipboard=no'
    )

    # Gitea web URL for opening files in the browser.
    GITEA_BASE_URL = os.getenv('GITEA_BASE_URL', 'http://yuckbox:3000/ian/wintermute')
    GITEA_BRANCH = os.getenv('GITEA_BRANCH', 'main')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

    # Webhook settings
    PORTAL_WEBHOOK_SECRET = os.getenv('PORTAL_WEBHOOK_SECRET', '')
    PORTAL_WEBHOOK_TTL_SECONDS = int(os.getenv('PORTAL_WEBHOOK_TTL_SECONDS', '300'))
    PORTAL_WORKERS = int(os.getenv('PORTAL_WORKERS', '1'))
    PORTAL_DEDUP_WINDOW_SECONDS = int(os.getenv('PORTAL_DEDUP_WINDOW_SECONDS', '60'))
