# PF9 Server Hardening & Remote Management Guide

## Overview

This guide covers 6 areas for your Ubuntu server at `ssh.plainspokenfoundrynine.com`:

1. SSH Key Authentication (no passwords)
2. Firewall Hardening
3. Auto-deploy pf9-store on git push
4. Automatic Security Updates
5. Server Monitoring & Uptime Alerts
6. Automatic Backups

---

## 1. SSH Key Authentication

### On your Windows machine (PowerShell):

```powershell
# Generate an SSH key (press Enter to accept defaults, no passphrase needed)
ssh-keygen -t ed25519 -C "markp@pf9"

# Copy the public key to the server
type $env:USERPROFILE\.ssh\id_ed25519.pub | ssh xfree143@ssh.plainspokenfoundrynine.com "mkdir -p ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```

### Test key-based login:
```powershell
ssh xfree143@ssh.plainspokenfoundrynine.com
```

If it logs in without asking for a password, it's working.

### Then disable password auth on the server (SSH in first):
```bash
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
echo "PasswordAuthentication no" | sudo tee -a /etc/ssh/sshd_config.d/no-password.conf
sudo systemctl restart sshd
```

---

## 2. Firewall Hardening

Since everything goes through Cloudflare Tunnel, the server doesn't need any ports open to the internet.

```bash
# Enable UFW with default deny
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH from local network only (in case tunnel is down)
sudo ufw allow from 192.168.1.0/24 to any port 22

# Enable the firewall
sudo ufw enable

# Verify
sudo ufw status verbose
```

> Note: Cloudflare Tunnel connects outbound from your server, so it works even with all incoming ports blocked.

---

## 3. Auto-deploy pf9-store on Git Push

### Option A: GitHub Actions with SSH (requires secrets setup)

The deploy.yml workflow is already in the repo. You need to set up GitHub secrets.

#### Generate a deploy key on the server:
```bash
sudo ssh-keygen -t ed25519 -f /opt/deploy-key -N "" -C "github-deploy"
sudo cat /opt/deploy-key.pub >> ~/.ssh/authorized_keys
```

#### Add GitHub Secrets (in the repo Settings → Secrets → Actions):
- `SERVER_HOST`: `ssh.plainspokenfoundrynine.com`
- `SERVER_USER`: `xfree143`
- `DEPLOY_SSH_KEY`: Contents of `/opt/deploy-key` (the private key)

> Note: GitHub Actions SSH won't work through Cloudflare Tunnel without extra setup. See Option B instead.

### Option B: Simple webhook with cron (recommended)

This is simpler — a cron job checks for updates every minute:

```bash
# Create the update script
sudo tee /opt/pf9-store-pull.sh << 'EOF'
#!/bin/bash
cd /opt/pf9-store
git fetch origin main --quiet
LOCAL=$(git rev-parse HEAD)
REMOTE=$(git rev-parse origin/main)
if [ "$LOCAL" != "$REMOTE" ]; then
    git pull origin main --quiet
    systemctl reload nginx
    echo "$(date): pf9-store updated to $(git rev-parse --short HEAD)" >> /var/log/pf9-deploy.log
fi
EOF

sudo chmod +x /opt/pf9-store-pull.sh

# Add to cron (runs every minute)
(sudo crontab -l 2>/dev/null; echo "* * * * * /opt/pf9-store-pull.sh") | sudo crontab -

# Create log file
sudo touch /var/log/pf9-deploy.log
```

Now any push to `main` will auto-deploy within 60 seconds.

---

## 4. Automatic Security Updates

```bash
# Install unattended-upgrades
sudo apt install unattended-upgrades apt-listchanges -y

# Enable automatic security updates
sudo dpkg-reconfigure -plow unattended-upgrades

# Configure (auto-reboot at 3am if needed)
sudo tee /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}";
    "${distro_id}:${distro_codename}-security";
    "${distro_id}ESMApps:${distro_codename}-apps-security";
    "${distro_id}ESM:${distro_codename}-infra-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::Remove-Unused-Kernel-Packages "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "true";
Unattended-Upgrade::Automatic-Reboot-Time "03:00";
EOF

# Enable the timer
sudo systemctl enable --now apt-daily.timer
sudo systemctl enable --now apt-daily-upgrade.timer
```

---

## 5. Server Monitoring & Uptime Alerts

### Basic monitoring with a free service (UptimeRobot):

1. Go to https://uptimerobot.com and create a free account
2. Add monitors for:
   - `https://app.plainspokenfoundrynine.com` (HTTP check)
   - `https://store.plainspokenfoundrynine.com` (HTTP check)
3. Set up email/SMS alerts for downtime

### On-server resource monitoring:

```bash
# Install Netdata (lightweight, web-based monitoring)
curl https://get.netdata.cloud/kickstart.sh > /tmp/netdata-kickstart.sh
sh /tmp/netdata-kickstart.sh --stable-channel

# Netdata runs on port 19999 by default
# Access locally: http://192.168.1.138:19999
```

### Simple disk/memory alert script:

```bash
sudo tee /opt/server-health-check.sh << 'EOF'
#!/bin/bash
LOGFILE="/var/log/server-health.log"

# Check disk usage
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ "$DISK_USAGE" -gt 85 ]; then
    echo "$(date): WARNING - Disk usage at ${DISK_USAGE}%" >> $LOGFILE
fi

# Check memory usage
MEM_USAGE=$(free | awk '/Mem/ {printf "%.0f", $3/$2 * 100}')
if [ "$MEM_USAGE" -gt 90 ]; then
    echo "$(date): WARNING - Memory usage at ${MEM_USAGE}%" >> $LOGFILE
fi

# Check services are running
for SERVICE in cloudflared nginx bridgr; do
    if ! systemctl is-active --quiet $SERVICE 2>/dev/null; then
        echo "$(date): ALERT - $SERVICE is down! Attempting restart..." >> $LOGFILE
        sudo systemctl restart $SERVICE
    fi
done
EOF

sudo chmod +x /opt/server-health-check.sh

# Run every 5 minutes
(sudo crontab -l 2>/dev/null; echo "*/5 * * * * /opt/server-health-check.sh") | sudo crontab -
sudo touch /var/log/server-health.log
```

---

## 6. Automatic Backups

```bash
# Create backup script
sudo tee /opt/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y-%m-%d_%H%M)
mkdir -p $BACKUP_DIR

# Backup BRIDGR database and config
tar -czf $BACKUP_DIR/bridgr-$DATE.tar.gz \
    /opt/bridgr/store_leads.db \
    /opt/bridgr/.env \
    /etc/cloudflared/config.yml \
    /etc/nginx/sites-available/ \
    2>/dev/null

# Backup pf9-store
tar -czf $BACKUP_DIR/pf9-store-$DATE.tar.gz /opt/pf9-store/ 2>/dev/null

# Keep only last 7 days of backups
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "$(date): Backup completed" >> /var/log/backup.log
EOF

sudo chmod +x /opt/backup.sh

# Run daily at 2am
(sudo crontab -l 2>/dev/null; echo "0 2 * * * /opt/backup.sh") | sudo crontab -
sudo touch /var/log/backup.log
sudo mkdir -p /opt/backups
```

---

## Quick Reference — Cron Jobs Summary

After everything is set up, `sudo crontab -l` should show:

```
* * * * * /opt/pf9-store-pull.sh
*/5 * * * * /opt/server-health-check.sh
0 2 * * * /opt/backup.sh
```

## Quick Reference — Services

```bash
sudo systemctl status cloudflared   # Cloudflare Tunnel
sudo systemctl status nginx          # Web server (store on :8080)
sudo systemctl status bridgr         # BRIDGR app
```
