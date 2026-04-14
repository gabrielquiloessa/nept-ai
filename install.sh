#!/usr/bin/env bash

# ===============================
# Nept Recon Framework Installer
# ===============================

set -e

echo ""
echo "====================================="
echo "   Nept Recon Framework Installer"
echo "====================================="
echo ""

# -------------------------
# Detect OS
# -------------------------
if [ -d "/data/data/com.termux" ]; then
    PLATFORM="termux"
else
    PLATFORM="linux"
fi

echo "[+] Detected platform: $PLATFORM"

# -------------------------
# Update system
# -------------------------
echo "[+] Updating system..."

if [ "$PLATFORM" = "termux" ]; then
    pkg update -y && pkg upgrade -y
    pkg install -y python git
else
    sudo apt update -y && sudo apt upgrade -y
    sudo apt install -y python3 python3-pip git
fi

# -------------------------
# Create virtualenv (optional but pro)
# -------------------------
echo "[+] Setting up environment..."

python3 -m pip install --upgrade pip

# -------------------------
# Install requirements
# -------------------------
echo "[+] Installing dependencies..."

pip install -r requirements.txt

# -------------------------
# Permissions
# -------------------------
chmod +x main.py
chmod +x install.sh

# -------------------------
# Create shortcut (Termux only)
# -------------------------
if [ "$PLATFORM" = "termux" ]; then
    echo "[+] Creating shortcut command..."

    mkdir -p $PREFIX/bin

    echo '#!/usr/bin/env bash
python3 '"$(pwd)"'/main.py "$@"' > $PREFIX/bin/nept

    chmod +x $PREFIX/bin/nept

    echo "[+] You can now run: nept"
fi

# -------------------------
# Final
# -------------------------
echo ""
echo "[+] Installation completed successfully!"
echo ""

if [ "$PLATFORM" = "termux" ]; then
    echo "Usage:"
    echo "  nept --console"
    echo "  nept recon -t example.com --ai"
else
    echo "Usage:"
    echo "  python3 main.py --console"
    echo "  python3 main.py recon -t example.com --ai"
fi

echo ""
echo "====================================="
echo "   Happy Hacking - Nept "
echo "====================================="
