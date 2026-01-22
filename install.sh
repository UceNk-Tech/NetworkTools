#!/bin/bash
# ==========================================
# NetworkTools All-in-One Installer
# Author: Ucenk D-Tech
# ==========================================

set -e
HOME_DIR="$HOME"
REPO_DIR="$HOME/NetworkTools"

echo "======================================================"
echo "    Memulai Instalasi & Sinkronisasi Environment..."
echo "======================================================"

# 1. Update & Install Paket Lengkap (Termasuk PHP untuk Mikhmon)
pkg update -y && pkg upgrade -y
pkg install -y bash git python zsh figlet curl inetutils neofetch nmap php \
    traceroute dnsutils clang rust pkg-config libffi openssl libsodium make \
    sshpass build-essential python-dev-is-python3 lolcat

# 2. Install Library Python
pip install --upgrade pip
pip install routeros-api speedtest-cli lolcat pysnmp requests scapy \
    pycryptodome terminaltables --break-system-packages || true

# 3. Git Security: Kredensial lokal tidak akan ter-push ke publik
mkdir -p "$REPO_DIR"
cat > "$REPO_DIR/.gitignore" << EOF
vault_session.json
__pycache__/
*.pyc
.env
EOF

# 4. Konfigurasi .zshrc: Menu otomatis tampil saat startup
echo "Configuring Startup..."
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
[ -f "$ZSH/oh-my-zsh.sh" ] && source "$ZSH/oh-my-zsh.sh"

# Prompt
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Tampilan Startup
clear
neofetch
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

# Aliases
alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh'
alias mikhmon='chmod -R 755 $HOME/mikhmon && php -S 0.0.0.0:8080 -t $HOME/mikhmon'
EOF

# 5. Izin Eksekusi
chmod +x $REPO_DIR/install.sh
chmod +x $REPO_DIR/menu.py

echo "======================================================"
echo "    INSTALASI SELESAI!"
echo "    Silakan buka ulang Termux."
echo "======================================================"
