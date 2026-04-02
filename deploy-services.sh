#!/bin/bash
# ==============================================================================
# PF9 Deploy Script — TENANTLINKR, PERMITR, TASKFLOW
# Run this on the server (139.94.250.128) as root or with sudo
# Usage: sudo bash deploy-services.sh
# ==============================================================================

set -e

APPS_DIR="/opt"
GITHUB_USER="Xfree1433"
PYTHON="python3"

# App definitions: name, repo, port
declare -A APP_PORTS=(
    [tenantlinkr]=5002
    [permitr]=5003
    [taskflow]=5004
)
declare -A APP_REPOS=(
    [tenantlinkr]="tenantlinkr"
    [permitr]="permitr"
    [taskflow]="taskflow"
)

echo "=========================================="
echo "  PF9 Service Deploy Script"
echo "=========================================="
echo ""

# -----------------------------------------------
# Step 1: Clone repos if not already present
# -----------------------------------------------
for app in tenantlinkr permitr taskflow; do
    APP_PATH="$APPS_DIR/$app"
    REPO="https://github.com/$GITHUB_USER/${APP_REPOS[$app]}.git"

    echo "--- $app ---"
    if [ -d "$APP_PATH" ]; then
        echo "  Already cloned at $APP_PATH, pulling latest..."
        cd "$APP_PATH"
        git fetch origin
        git pull origin main || git pull origin master
    else
        echo "  Cloning $REPO → $APP_PATH..."
        git clone "$REPO" "$APP_PATH"
    fi
    echo ""
done

# -----------------------------------------------
# Step 2: Set up virtual environments & install deps
# -----------------------------------------------
for app in tenantlinkr permitr taskflow; do
    APP_PATH="$APPS_DIR/$app"
    echo "--- $app: Setting up venv ---"

    if [ ! -d "$APP_PATH/venv" ]; then
        $PYTHON -m venv "$APP_PATH/venv"
        echo "  Created venv"
    fi

    source "$APP_PATH/venv/bin/activate"
    pip install --upgrade pip -q
    pip install -r "$APP_PATH/requirements.txt" -q
    deactivate
    echo "  Dependencies installed"
    echo ""
done

# -----------------------------------------------
# Step 3: Create .env files if missing
# -----------------------------------------------
for app in tenantlinkr permitr taskflow; do
    APP_PATH="$APPS_DIR/$app"
    PORT=${APP_PORTS[$app]}
    ENV_FILE="$APP_PATH/.env"

    if [ ! -f "$ENV_FILE" ]; then
        echo "--- $app: Creating .env ---"
        SECRET=$(openssl rand -hex 32)
        cat > "$ENV_FILE" << ENVEOF
FLASK_ENV=production
SECRET_KEY=$SECRET
PORT=$PORT
APP_URL=https://${app}.plainspokenfoundrynine.com
ENVEOF
        # Add mail config placeholder for apps that need it
        if [ "$app" != "taskflow" ]; then
            cat >> "$ENV_FILE" << ENVEOF
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=CHANGEME
MAIL_PASSWORD=CHANGEME
MAIL_DEFAULT_SENDER=noreply@plainspokenfoundrynine.com
ENVEOF
        fi
        echo "  Created $ENV_FILE (edit MAIL settings!)"
    else
        echo "--- $app: .env already exists, skipping ---"
    fi
    echo ""
done

# -----------------------------------------------
# Step 4: Install systemd service files
# -----------------------------------------------
for app in tenantlinkr permitr taskflow; do
    APP_PATH="$APPS_DIR/$app"
    PORT=${APP_PORTS[$app]}
    SERVICE_FILE="/etc/systemd/system/pf9-${app}.service"

    echo "--- $app: Installing systemd service ---"
    cat > "$SERVICE_FILE" << SVCEOF
[Unit]
Description=PF9 ${app} (Flask/Waitress on port ${PORT})
After=network.target

[Service]
Type=simple
User=xfree143
Group=xfree143
WorkingDirectory=${APP_PATH}
Environment=PATH=${APP_PATH}/venv/bin:/usr/local/bin:/usr/bin
EnvironmentFile=${APP_PATH}/.env
ExecStart=${APP_PATH}/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SVCEOF

    systemctl daemon-reload
    systemctl enable "pf9-${app}.service"
    systemctl restart "pf9-${app}.service"

    echo "  Installed & started pf9-${app}.service on port ${PORT}"
    echo ""
done

# -----------------------------------------------
# Step 5: Verify
# -----------------------------------------------
echo "=========================================="
echo "  Verification"
echo "=========================================="
echo ""
sleep 3
for app in tenantlinkr permitr taskflow; do
    PORT=${APP_PORTS[$app]}
    STATUS=$(systemctl is-active "pf9-${app}.service" 2>/dev/null || echo "unknown")
    echo "  pf9-${app}: ${STATUS} (port ${PORT})"

    # Quick health check
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:${PORT}/" --max-time 3 2>/dev/null || echo "000")
    echo "    HTTP check: ${RESPONSE}"
    echo ""
done

echo "=========================================="
echo "  Done!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Edit .env files with real MAIL_USERNAME/MAIL_PASSWORD"
echo "  2. Update Cloudflare tunnel ports if needed:"
echo "     - permitr → localhost:5003"
echo "     - taskflow → localhost:5004"
echo "  3. Test: curl https://tenantlinkr.plainspokenfoundrynine.com"
echo "  4. Test: curl https://permitr.plainspokenfoundrynine.com"
echo "  5. Test: curl https://taskflow.plainspokenfoundrynine.com"
echo ""
echo "Manage services:"
echo "  sudo systemctl status pf9-tenantlinkr"
echo "  sudo systemctl restart pf9-permitr"
echo "  sudo journalctl -u pf9-taskflow -f"
