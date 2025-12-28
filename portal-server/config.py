"""
Configuration for the Wintermute Portal Router.
"""

import os
from pathlib import Path


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
    WORKING_COPY_REPO = 'ian/wintermute'
    WORKING_COPY_URL_TEMPLATE = 'working-copy://x-callback-url/open?repo={repo}&path={path}'
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
