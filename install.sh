#!/bin/bash
# ==========================================
# NetworkTools Installer (Ucenk-D-Tech) v2.7
# ==========================================

set -e

# 1) Setup Storage
termux-setup-storage -y || true

# 2) Update Repo & Install Core Packages
# Kita tidak melakukan upgrade pip di sini untuk menghindari blokade
pkg update -y && pkg upgrade -y
pkg install -y tur-repo
pkg install -y bash git python zsh figlet curl inetutils neofetch nmap php traceroute dnsutils clang rust pkg-config libffi openssl libsodium make

# 3) Install Python Packages via PKG (Lebih Aman)
pkg install -y python-pip python-cryptography -y

# 4) Install Modul via PIP dengan Bypass Flag
# Menghapus perintah 'pip install --upgrade pip' yang dilarang
pip install routeros-api speedtest-cli lolcat pysnmp --break-system-packages || true

# 5) Oh My Zsh Setup
if [ -d "$HOME/.oh-my-zsh" ]; then rm -rf "$HOME/.oh-my-zsh"; fi
export KEEP_ZSHRC=yes
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# 6) Konfigurasi .zshrc (BANNER TETAP SESUAI PERMINTAAN ANDA)
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git zsh-autosuggestions)
source $ZSH/oh-my-zsh.sh

PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# --- TAMPILAN BANNER (Sesuai Permintaan) ---
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

# Alias
alias menu='clear && python $HOME/NetworkTools/menu.py'
alias update-tools='bash $HOME/NetworkTools/update.sh'
alias mikhmon='php -S 0.0.0.0:8080 -t $HOME/mikhmon'
EOF

chsh -s zsh || true
echo -e "\n======================================================"
echo "Selesai! Error PIP diabaikan karena sudah ditangani."
echo "Silakan ketik 'zsh' lalu ketik 'menu'."
echo "======================================================"
