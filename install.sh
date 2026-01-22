#!/bin/bash
# ==========================================
# NetworkTools All-in-One Installer
# Author: Ucenk D-Tech (Auto-complete Integrated)
# ==========================================

set -e
HOME_DIR="$HOME"
REPO_DIR="$HOME/NetworkTools"

echo "======================================================"
echo "    Memulai Instalasi & Integrasi Auto-complete..."
echo "======================================================"

# 1. Update & Paket Dasar
pkg update -y && pkg upgrade -y
pkg install -y zsh git python neofetch lolcat php termux-api

# 2. Instalasi Oh My Zsh (Jika belum ada)
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "[*] Menginstall Oh My Zsh..."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 3. Instal Plugin Auto-complete & Syntax Highlighting
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom/plugins"
mkdir -p "$ZSH_CUSTOM"

echo "[*] Menginstall Plugin Auto-suggestion..."
[ ! -d "$ZSH_CUSTOM/zsh-autosuggestions" ] && git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/zsh-autosuggestions"
[ ! -d "$ZSH_CUSTOM/zsh-syntax-highlighting" ] && git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/zsh-syntax-highlighting"

# 4. Konfigurasi .zshrc (Agar Plugin Aktif)
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"

# Plugin yang diaktifkan
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)

source $ZSH/oh-my-zsh.sh

# Prompt Custom Ucenk D-Tech
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Tampilan Startup Otomatis
clear
neofetch
[ -f "$HOME/NetworkTools/menu.py" ] && python $HOME/NetworkTools/menu.py

# Aliases
alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git pull && bash install.sh'
alias mikhmon='php -S 0.0.0.0:8080 -t $HOME/mikhmon'
EOF

# 5. Library Python & Izin
pip install routeros-api speedtest-cli lolcat --break-system-packages || true
chmod +x $REPO_DIR/menu.py $REPO_DIR/install.sh $REPO_DIR/update.sh

# Set Default Shell ke ZSH
chsh -s zsh

echo "======================================================"
echo "    INSTALASI SELESAI!"
echo "    Auto-complete AKTIF. Silakan buka ulang Termux."
echo "======================================================"
