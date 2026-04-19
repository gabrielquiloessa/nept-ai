#!/usr/bin/env bash

# =====================================
# Nept Recon Framework - Installer Pro
# =====================================

set -e

echo ""
echo "====================================="
echo "    Nept Recon Framework Installer"
echo "====================================="
echo ""

if [ -d "/data/data/com.termux" ]; then
    PLATFORM="termux"
    BIN_DIR="$PREFIX/bin"
    SUDO=""
else
    PLATFORM="linux"
    BIN_DIR="/usr/local/bin"
    SUDO="sudo"
fi

echo "[+] Platform detected: $PLATFORM"

echo "[+] Installing basic dependencies..."
if [ "$PLATFORM" = "termux" ]; then
    pkg update -y
    pkg install -y python python-pip git
else
    $SUDO apt update -y
    $SUDO apt install -y python3 python3-pip python3-venv git -y
fi

echo "[+] Creating a Python virtual environment (venv)..."
if [ -d "venv" ]; then
    echo "[!] The virtual environment already exists, therefore creating a new one is unnecessary..."
else
    python3 -m venv venv
fi

echo "[+] Updating pip and installing the dependency..."
./venv/bin/pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    ./venv/bin/pip install -r requirements.txt
else
    echo "[!] WARNING: requirements.txt not found!"
fi

chmod +x main.py

echo "[+] Setting up the global 'nept' command..."

INSTALL_PATH=$(pwd)

cat <<EOF > nept_wrapper
#!/usr/bin/env bash
$INSTALL_PATH/venv/bin/python3 $INSTALL_PATH/main.py "\$@"
EOF

if [ "$PLATFORM" = "termux" ]; then
    mv nept_wrapper $BIN_DIR/nept
    chmod +x $BIN_DIR/nept
else
    $SUDO mv nept_wrapper $BIN_DIR/nept
    $SUDO chown root:root $BIN_DIR/nept
    $SUDO chmod +x $BIN_DIR/nept
fi

if [ -f "./nept" ]; then
    rm ./nept
fi

echo ""
echo "====================================="
echo "       INSTALLATION COMPLETE!"
echo "====================================="
echo ""
echo "  nept --console"
echo "  nept httpinfo -t example.com"
echo ""
