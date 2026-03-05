#!/bin/bash
# Enable systemd in WSL2 and install k3s
# Requires Windows 11 22H2 or later

set -e

echo "╔════════════════════════════════════════════════════════════════╗"
echo "║  Enable systemd in WSL2 and Install k3s                       ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Check if we're in WSL
if ! grep -qi microsoft /proc/version; then
    echo "ERROR: This script is for WSL only"
    exit 1
fi

echo "Step 1: Enable systemd in WSL..."
echo ""

# Create or update /etc/wsl.conf
sudo tee /etc/wsl.conf > /dev/null <<EOF
[boot]
systemd=true

[network]
generateResolvConf=true
EOF

echo "✓ systemd enabled in /etc/wsl.conf"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "IMPORTANT: WSL needs to be restarted!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "1. Close this terminal"
echo "2. In Windows PowerShell, run:"
echo "   wsl --shutdown"
echo ""
echo "3. Wait 10 seconds, then reopen WSL"
echo ""
echo "4. Verify systemd is running:"
echo "   systemctl --version"
echo ""
echo "5. Then install k3s:"
echo "   ./k8s/install-k3s-single.sh"
echo ""
