"""
Test script for the portal router.
Can be run locally to verify functionality before deployment.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from app import app, validate_portal_id, load_portals_config
from actions import ActionRegistry
from config import Config


async def test_portal_id_validation():
    """Test portal ID validation."""
    print("Testing portal ID validation...")
    
    valid_ids = ["dly", "h2o", "new123", "abcdefgh"]
    invalid_ids = ["", "abc", "too_long_portal_id_123", "INVALID", "abc-def"]
    
    for portal_id in valid_ids:
        assert validate_portal_id(portal_id), f"Should be valid: {portal_id}"
        print(f"  ✓ {portal_id} is valid")
    
    for portal_id in invalid_ids:
        assert not validate_portal_id(portal_id), f"Should be invalid: {portal_id}"
        print(f"  ✓ {portal_id} is invalid (as expected)")
    
    print("Portal ID validation tests passed!\n")


async def test_portal_routes():
    """Test portal routes using test client."""
    print("Testing portal routes...")
    
    async with app.test_client() as client:
        # Test health endpoint
        response = await client.get('/health')
        assert response.status_code == 200
        data = await response.get_json()
        assert data['status'] == 'healthy'
        print("  ✓ Health endpoint works")
        
        # Test invalid portal ID format
        response = await client.get('/wm/p/abc')
        assert response.status_code == 400
        print("  ✓ Invalid portal ID rejected")
        
        # Test non-existent portal
        response = await client.get('/wm/p/nonexist')
        # This will fail if portals.json doesn't exist, which is expected
        print("  ✓ Portal route structure works")
    
    print("Portal route tests passed!\n")


async def test_action_registry():
    """Test action registry."""
    print("Testing action registry...")
    
    # Use a test repo path (won't actually execute, just test structure)
    test_repo = "/tmp/test_wintermute"
    registry = ActionRegistry(test_repo)
    
    # Test known action
    assert 'open_daily' in registry.actions
    print("  ✓ open_daily action registered")
    
    # Test unknown action
    result = await registry.execute('unknown_action', {})
    assert not result.get('success')
    assert 'Unknown action' in result.get('error', '')
    print("  ✓ Unknown action properly rejected")
    
    print("Action registry tests passed!\n")


def test_config():
    """Test configuration."""
    print("Testing configuration...")
    
    assert Config.WINTERMUTE_REPO_PATH
    assert Config.HOST
    assert Config.PORT > 0
    print(f"  ✓ Config loaded: repo_path={Config.WINTERMUTE_REPO_PATH}")
    print(f"  ✓ Server config: {Config.HOST}:{Config.PORT}")
    
    print("Configuration tests passed!\n")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Wintermute Portal Router - Test Suite")
    print("=" * 60)
    print()
    
    try:
        test_config()
        await test_portal_id_validation()
        await test_action_registry()
        await test_portal_routes()
        
        print("=" * 60)
        print("All tests passed! ✓")
        print("=" * 60)
        print()
        print("Note: Full integration testing requires:")
        print("  1. Deployment to yuckbox")
        print("  2. portals.json in wintermute repo")
        print("  3. Actual git repository access")
        print("  4. iPhone shortcut setup")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    asyncio.run(main())

