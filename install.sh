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
# Detectar Plataforma
# -------------------------
if [ -d "/data/data/com.termux" ]; then
    PLATFORM="termux"
    BIN_DIR="$PREFIX/bin"
    SUDO=""
else
    PLATFORM="linux"
    BIN_DIR="/usr/local/bin"
    SUDO="sudo"
fi

echo "[+] Plataforma detectada: $PLATFORM"

# -------------------------
# Instalar Dependências do Sistema
# -------------------------
echo "[+] Instalando dependências base..."

if [ "$PLATFORM" = "termux" ]; then
    pkg update -y
    # No Termux, python-pip e venv já vêm no pacote python, 
    # mas garantimos a instalação do python-pip por segurança.
    pkg install -y python python-pip git
else
    $SUDO apt update -y
    $SUDO apt install -y python3 python3-pip python3-venv git
fi

# -------------------------
# Criar Ambiente Virtual (venv)
# -------------------------
echo "[+] Criando ambiente virtual Python (venv)..."
python3 -m venv venv

# -------------------------
# Instalar Requisitos no venv
# -------------------------
echo "[+] Instalando dependências no ambiente isolado..."
# Usamos o pip de dentro do venv para evitar o erro de ambiente externo
./venv/bin/pip install --upgrade pip
if [ -f "requirements.txt" ]; then
    ./venv/bin/pip install -r requirements.txt
else
    echo "[!] requirements.txt não encontrado!"
fi

# -------------------------
# Permissões
# -------------------------
chmod +x main.py

# -------------------------
# Criar Atalho 'nept'
# -------------------------
echo "[+] Configurando o comando 'nept'..."

# O atalho agora aponta para o Python do venv
CAT_CMD="cat <<EOF > $BIN_DIR/nept
#!/usr/bin/env bash
$(pwd)/venv/bin/python3 $(pwd)/main.py \"\$@\"
EOF"

if [ "$PLATFORM" = "termux" ]; then
    eval "$CAT_CMD"
else
    $SUDO bash -c "$CAT_CMD"
fi

chmod +x $BIN_DIR/nept

# -------------------------
# Finalização
# -------------------------
echo ""
echo "[+] Instalação concluída com sucesso!"
echo "[+] O Nept está isolado no diretório ./venv"
echo ""
echo "Disponible Commands:"
echo "  nept --console"
echo "  nept recon -t example.com"
echo ""
echo "Or try:"
echo "  python3 main.py --console"
echo "  python3 main.py recon -t example.com"
echo ""
echo "====================================="
