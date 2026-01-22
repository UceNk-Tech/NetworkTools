#!/bin/bash
# ==========================================
# NetworkTools Installer (Ucenk-D-Tech) v2.0 — Termux Safe & Build-Ready
# ==========================================

set -e

# 0) Pastikan environment Termux
export PREFIX="/data/data/com.termux/files/usr"
export CFLAGS="-I$PREFIX/include"
export LDFLAGS="-L$PREFIX/lib"
export RUSTFLAGS="-C target-cpu=native"

# 1) Update & base packages
pkg update -y && pkg upgrade -y
pkg install -y bash git python python-pip zsh figlet curl inetutils neofetch nmap php traceroute dnsutils

# 2) Toolchain & libs untuk build cryptography/paramiko (wajib di Termux)
pkg install -y clang rust pkg-config libffi openssl

# 3) Python packages
#    - Install cryptography dulu dengan opsi aman (hindari wheel yang tidak ada di Termux)
#    - Lalu paramiko & modul lain
pip install --no-binary :all: cryptography==41.0.7
pip install routeros-api speedtest-cli lolcat paramiko pysnmp

# 4) Oh My Zsh (unattended)
if [ -d "$HOME/.oh-my-zsh" ]; then
  rm -rf "$HOME/.oh-my-zsh"
fi
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# 5) Zsh autosuggestions
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions || true

# 6) Prompt, banner, neofetch, alias (sesuai format yang kamu minta)
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git zsh-autosuggestions)
source $ZSH/oh-my-zsh.sh

PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# --- TAMPILAN BANNER ---
clear
echo "======================================================" | lolcat
figlet -f slant "Ucenk D-Tech" | lolcat
echo "      Author: Ucenk  |  Premium Network Management System" | lolcat
echo "======================================================" | lolcat
echo " Welcome back, Ucenk D-Tech!" | lolcat
echo "" | lolcat

# Logo Ubuntu Paksa
neofetch --ascii_distro ubuntu

# --- INSTRUKSI UTAMA ---
echo " Ketik 'mikhmon' untuk menjalankan server." | lolcat
echo " Ketik 'telnet_IP OLT' untuk management OLT." | lolcat
echo " Ketik 'menu' untuk membuka tools." | lolcat
echo " Ketik 'update-tools' untuk menarik update terbaru." | lolcat

# Alias utama
alias menu='clear && python $HOME/NetworkTools/menu.py'
alias update-tools='bash $HOME/NetworkTools/update.sh'
alias mikhmon='php -S 0.0.0.0:8080 -t $HOME/mikhmon'
EOF

# 7) Default shell & hush login
chsh -s zsh || true
touch "$HOME/.hushlogin"

echo "======================================================"
echo "Install selesai. Restart Termux, lalu ketik 'menu'."
echo "======================================================"
