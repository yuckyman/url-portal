"""
Quart application for Wintermute Portal Router
Handles QR code portal requests and executes actions on the vault.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

from quart import Quart, request, jsonify, redirect, url_for

from config import Config
from actions import ActionRegistry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Quart(__name__)
app.config.from_object(Config)

# Initialize action registry
action_registry = ActionRegistry(Config.WINTERMUTE_REPO_PATH)


def validate_portal_id(portal_id: str) -> bool:
    """
    Validate portal ID format: 2-24 chars, lowercase alphanumeric.
    
    Args:
        portal_id: The portal ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not portal_id:
        return False
    if len(portal_id) < 2 or len(portal_id) > 24:
        return False
    valid_chars = set('abcdefghijklmnopqrstuvwxyz0123456789')
    return all(c in valid_chars for c in portal_id.lower())


def load_portals_config() -> Dict[str, Any]:
    """
    Load portals.json from the wintermute repo.
    
    Returns:
        Dictionary of portal configurations
        
    Raises:
        FileNotFoundError: If portals.json doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    portals_path = Path(Config.WINTERMUTE_REPO_PATH) / '0_admin' / '00_index' / 'portals.json'
    
    if not portals_path.exists():
        logger.error(f"Portals config not found at {portals_path}")
        raise FileNotFoundError(f"Portals config not found: {portals_path}")
    
    with open(portals_path, 'r', encoding='utf-8') as f:
        return json.load(f)


@app.route('/wm/p/<portal_id>', methods=['GET'])
async def portal_handler(portal_id: str):
    """
    Handle portal ID requests from QR codes.
    
    For now, returns a simple JSON response with action info.
    In the future, could redirect to shortcuts:// or show a button page.
    """
    try:
        # Validate portal ID format
        if not validate_portal_id(portal_id):
            logger.warning(f"Invalid portal ID format: {portal_id}")
            return jsonify({
                'error': 'Invalid portal ID format',
                'message': 'Portal ID must be 2-24 lowercase alphanumeric characters'
            }), 400
        
        # Load portals config
        portals = load_portals_config()
        
        if portal_id not in portals:
            logger.warning(f"Portal ID not found: {portal_id}")
            return jsonify({
                'error': 'Portal not found',
                'message': f'No configuration found for portal ID: {portal_id}'
            }), 404
        
        portal_config = portals[portal_id]
        action = portal_config.get('action')
        
        if not action:
            logger.error(f"Portal {portal_id} missing action")
            return jsonify({
                'error': 'Invalid portal configuration',
                'message': 'Portal configuration missing action'
            }), 500
        
        logger.info(f"Portal {portal_id} requested, action: {action}")
        
        # Return portal info (iPhone shortcut will call /wm/act to execute)
        return jsonify({
            'portal_id': portal_id,
            'action': action,
            'config': portal_config,
            'execute_url': f'/wm/act'
        })
        
    except FileNotFoundError as e:
        logger.error(f"Portals config not found: {e}")
        return jsonify({
            'error': 'Configuration error',
            'message': 'Portals configuration file not found'
        }), 500
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in portals config: {e}")
        return jsonify({
            'error': 'Configuration error',
            'message': 'Invalid portals configuration file'
        }), 500
    except Exception as e:
        logger.exception(f"Unexpected error in portal_handler: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@app.route('/wm/act', methods=['POST'])
async def action_handler():
    """
    Execute portal actions.
    
    Expected JSON body:
    {
        "portal_id": "dly",
        "action": "open_daily",
        ...
    }
    """
    try:
        data = await request.get_json()
        
        if not data:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Request body must be JSON'
            }), 400
        
        portal_id = data.get('portal_id')
        action = data.get('action')
        
        if not portal_id or not action:
            return jsonify({
                'error': 'Invalid request',
                'message': 'Missing portal_id or action'
            }), 400
        
        logger.info(f"Executing action: {action} for portal: {portal_id}")
        
        # Execute the action
        result = await action_registry.execute(action, data)
        
        if result.get('success'):
            return jsonify(result), 200
        else:
            return jsonify(result), 500
            
    except Exception as e:
        logger.exception(f"Unexpected error in action_handler: {e}")
        return jsonify({
            'error': 'Internal server error',
            'message': str(e),
            'success': False
        }), 500


@app.route('/health', methods=['GET'])
async def health_check():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'wintermute-portal-router'
    }), 200


@app.route('/wm/endpoints', methods=['GET'])
async def list_endpoints():
    """List available endpoints and basic usage."""
    return jsonify({
        'endpoints': [
            {
                'method': 'GET',
                'path': '/wm/p/<portal_id>',
                'description': 'Lookup portal info and action for a portal ID.'
            },
            {
                'method': 'POST',
                'path': '/wm/act',
                'description': 'Execute a portal action.'
            },
            {
                'method': 'GET',
                'path': '/wm/endpoints',
                'description': 'List available endpoints.'
            },
            {
                'method': 'GET',
                'path': '/health',
                'description': 'Health check.'
            }
        ]
    }), 200


if __name__ == '__main__':
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG
    )
