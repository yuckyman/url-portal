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
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
