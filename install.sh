#!/bin/bash
# ==========================================
# NetworkTools All-in-One Installer
# Author: Ucenk D-Tech
# ==========================================

set -e
REPO_DIR="$HOME/NetworkTools"

# 1. Update & Install
pkg update -y
pkg install -zsh git python figlet curl php nmap neofetch lolcat -y || pip install lolcat --break-system-packages

# 2. Config .zshrc (DIPERTAHANKAN TAMPILANNYA)
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

# --- CUSTOM PROMPT ---
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# --- TAMPILAN BANNER AWAL ---
clear
neofetch --ascii_distro ubuntu
echo "======================================================" | lolcat
figlet -f slant "Ucenk D-Tech" | lolcat
echo "      Author: Ucenk  |  Premium Network Management System" | lolcat
echo "======================================================" | lolcat
echo " Welcome back, Ucenk D-Tech!" | lolcat

# Jalankan Menu
[ -f "$HOME/NetworkTools/menu.py" ] && python $HOME/NetworkTools/menu.py

alias menu='python $HOME/NetworkTools/menu.py'
EOF

chmod +x $REPO_DIR/*.py $REPO_DIR/*.sh
echo "Selesai! Tampilan sudah dikembalikan dan Menu 9 terintegrasi." | lolcat
