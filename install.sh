#!/bin/bash
# ==========================================
# NetworkTools All-in-One Installer
# Author: Ucenk D-Tech
# ==========================================

set -e
REPO_DIR="$HOME/NetworkTools"

# 1. Update & Install
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch lolcat -y || pip install lolcat --break-system-packages

# 2. Config .zshrc
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

# --- CUSTOM PROMPT UCENK D-TECH ---
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# --- STARTUP TAMPILAN ---
# Langsung jalankan menu.py karena show_sticky_header sudah mengatur urutan Banner -> Neofetch
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

# Shortcut Aliases
alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh'
EOF

chmod +x $REPO_DIR/*.py $REPO_DIR/*.sh
echo "Update Selesai! Banner & Menu 1 sudah diperbaiki." | lolcat
