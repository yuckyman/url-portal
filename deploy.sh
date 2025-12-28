#!/bin/bash
# Deployment script for Wintermute Portal Router
# Run this on yuckbox to set up the portal server

set -e

REPO_PATH="/home/ian/WINTERMUTE"
PORTAL_SERVER_PATH="/home/ian/scripts/url-portal"
PORTALS_JSON_PATH="$REPO_PATH/0_admin/00_index/portals.json"

echo "Deploying Wintermute Portal Router..."

# 1. Create portal server directory
echo "Creating portal server directory..."
mkdir -p "$PORTAL_SERVER_PATH"

# 2. Copy files (assuming we're running from the local url-portal directory)
# This would be run from the local machine:
# scp -r portal-server/* ian@yuckbox:/home/ian/scripts/url-portal/

# 3. Install Python dependencies
echo "Installing Python dependencies..."
cd "$PORTAL_SERVER_PATH"
python3 -m pip install --user -r requirements.txt || pip3 install --user -r requirements.txt

# 4. Create portals.json if it doesn't exist
if [ ! -f "$PORTALS_JSON_PATH" ]; then
    echo "Creating portals.json..."
    mkdir -p "$(dirname "$PORTALS_JSON_PATH")"
    cat > "$PORTALS_JSON_PATH" << 'EOF'
{
  "dly": {
    "action": "open_daily"
  },
  "h2o": {
    "action": "add_water",
    "delta": 64
  },
  "new": {
    "action": "new_file"
  },
  "mac": {
    "action": "open_on_mac"
  },
  "agent": {
    "action": "spawn_agent"
  }
}
EOF
    echo "Created portals.json at $PORTALS_JSON_PATH"
    
    # Commit the new file to git
    cd "$REPO_PATH"
    git add "0_admin/00_index/portals.json"
    git commit -m "add portals.json configuration" || echo "Git commit skipped (may need manual commit)"
else
    echo "portals.json already exists at $PORTALS_JSON_PATH"
fi

# 5. Verify git configuration
echo "Verifying git configuration..."
cd "$REPO_PATH"
git config user.name "Wintermute Portal" || git config --global user.name "Wintermute Portal"
git config user.email "portal@wintermute.local" || git config --global user.email "portal@wintermute.local"

echo ""
echo "Deployment complete!"
echo ""
echo "To run the server:"
echo "  cd $PORTAL_SERVER_PATH"
echo "  python3 app.py"
echo ""
echo "Or set up as a systemd service for automatic startup."

