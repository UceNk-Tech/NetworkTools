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

# 1. Update & Install Paket Sistem (Termasuk sshpass & nmap)
pkg update -y && pkg upgrade -y
pkg install -y bash git python zsh figlet curl inetutils neofetch nmap php traceroute dnsutils clang rust pkg-config libffi openssl libsodium make sshpass

# 2. Install Library Python dengan Bypass Flag
pip install routeros-api speedtest-cli lolcat pysnmp --break-system-packages || true

# 3. Membuat file config.py secara otomatis (Jika belum ada)
# Ini agar Ucenk tidak perlu setting manual lagi
if [ ! -f "$REPO_DIR/config.py" ]; then
    echo "Membuat konfigurasi default..."
    cat > "$REPO_DIR/config.py" << EOF
# Konfigurasi Rahasia Ucenk D-Tech
OLT_IP = "192.168.80.100"
OLT_USER = "zte"
OLT_PASS = "zte"

MT_IP = "192.168.88.1"
MT_USER = "admin"
MT_PASS = ""
EOF
fi

# 4. Membuat .gitignore agar config.py aman dari GitHub
cat > "$REPO_DIR/.gitignore" << EOF
config.py
__pycache__/
*.env
EOF

# 5. Konfigurasi Alias & Environment di .zshrc
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git zsh-autosuggestions)
source $ZSH/oh-my-zsh.sh

PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

clear
figlet -f slant "Ucenk D-Tech" | lolcat
echo " Welcome back, Ucenk D-Tech!" | lolcat

alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh'
alias mikhmon='chmod -R 755 $HOME/mikhmon && php -S 0.0.0.0:8080 -t $HOME/mikhmon'
EOF

# 6. Perbaikan Izin Eksekusi
chmod +x $REPO_DIR/install.sh
chmod +x $REPO_DIR/menu.py

echo "======================================================"
echo "    INSTALASI SELESAI!"
echo "    Ketik 'source ~/.zshrc' atau buka ulang Termux."
echo "    Lalu ketik 'menu' untuk mulai."
echo "======================================================"
