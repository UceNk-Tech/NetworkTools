#!/bin/bash
# ==========================================
# NetworkTools All-in-One Installer
# Author: Ucenk D-Tech
# ==========================================

set -e
REPO_DIR="$HOME/NetworkTools"

echo "======================================================"
echo "    Memulai Instalasi & Integrasi Auto-complete..."
echo "======================================================"

# 1. Update & Install Paket Sistem (Tanpa lolcat dulu di pkg)
pkg update -y && pkg upgrade -y
pkg install -y zsh git python figlet curl php nmap neofetch termux-api

# 2. Install Library Python & lolcat (Pasti Berhasil)
echo "[*] Memperbarui Library Python & Installing lolcat..."
pip install --upgrade pip
pip install routeros-api speedtest-cli requests scapy --break-system-packages || true
# Install lolcat versi python sebagai alternatif pkg
pip install lolcat --break-system-packages || true

# 3. Integrasi Oh My Zsh & Plugins (Auto-complete)
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

ZSH_CUSTOM="$HOME/.oh-my-zsh/custom/plugins"
mkdir -p "$ZSH_CUSTOM"
[ ! -d "$ZSH_CUSTOM/zsh-autosuggestions" ] && git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/zsh-autosuggestions"
[ ! -d "$ZSH_CUSTOM/zsh-syntax-highlighting" ] && git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/zsh-syntax-highlighting"

# 4. Konfigurasi .zshrc
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
source $ZSH/oh-my-zsh.sh

PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

clear
neofetch
[ -f "$HOME/NetworkTools/menu.py" ] && python $HOME/NetworkTools/menu.py

alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git pull && bash install.sh'
alias mikhmon='php -S 0.0.0.0:8080 -t $HOME/mikhmon'
EOF

chmod +x $REPO_DIR/*.py $REPO_DIR/*.sh
chsh -s zsh

echo "======================================================"
echo "    INSTALASI SELESAI! Silakan buka ulang Termux."
echo "======================================================"
