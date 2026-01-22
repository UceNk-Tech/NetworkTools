#!/bin/bash
# ==========================================
# NetworkTools Installer (Ucenk-D-Tech) v2.5
# ==========================================

set -e

# 1) Setup Storage & Repo
termux-setup-storage -y || true
pkg update -y && pkg upgrade -y

# 2) Install Toolchain Lengkap (Agar Build Pynacl Berhasil)
pkg install -y tur-repo
pkg install -y bash git python zsh figlet curl inetutils neofetch nmap php traceroute dnsutils clang rust pkg-config libffi openssl libsodium make

# 3) Update PIP & Setup Tools
pip install --upgrade pip setuptools wheel --break-system-packages

# 4) Install paket yang sudah pasti ada di PKG untuk meringankan PIP
pkg install -y python-cryptography || pip install cryptography --break-system-packages

# 5) Install Paramiko & PyNaCl via PIP dengan env variable khusus
# SODIUM_INSTALL=system memaksa pynacl memakai libsodium yang kita install di langkah 2
export SODIUM_INSTALL=system
pip install pynacl paramiko routeros-api speedtest-cli lolcat pysnmp --break-system-packages

# 6) Oh My Zsh (Unattended)
if [ -d "$HOME/.oh-my-zsh" ]; then rm -rf "$HOME/.oh-my-zsh"; fi
export KEEP_ZSHRC=yes
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# 7) Konfigurasi .zshrc (BANNER TETAP SESUAI PERMINTAAN)
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

# Alias utama
alias menu='clear && python $HOME/NetworkTools/menu.py'
alias update-tools='bash $HOME/NetworkTools/update.sh'
alias mikhmon='php -S 0.0.0.0:8080 -t $HOME/mikhmon'
EOF

chsh -s zsh || true
echo -e "\n======================================================"
echo "Selesai! Jika tidak ada error merah, silakan restart Termux."
echo "======================================================"
