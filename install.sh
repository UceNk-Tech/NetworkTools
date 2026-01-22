#!/bin/bash
# ==========================================
# NetworkTools Installer (Ucenk-D-Tech) v2.0 — Termux Safe & Build-Ready
# ==========================================

set -e

# 0) Pastikan environment Termux & Direktori
export PREFIX="/data/data/com.termux/files/usr"
mkdir -p "$HOME/NetworkTools"

# 1) Update & base packages
pkg update -y && pkg upgrade -y
# Tambahkan tur-repo untuk cryptography yang sudah jadi (mencegah error build rust)
pkg install -y tur-repo
pkg install -y bash git python python-pip zsh figlet curl inetutils neofetch nmap php traceroute dnsutils clang rust pkg-config libffi openssl python-cryptography

# 2) Python packages
# Gunakan --break-system-packages jika di Python versi terbaru Termux
pip install --upgrade pip
pip install routeros-api speedtest-cli lolcat paramiko pysnmp --break-system-packages || pip install routeros-api speedtest-cli lolcat paramiko pysnmp

# 3) Oh My Zsh (unattended fix)
if [ -d "$HOME/.oh-my-zsh" ]; then
  rm -rf "$HOME/.oh-my-zsh"
fi
# Menggunakan env KEEP_ZSHRC agar tidak menimpa .zshrc yang kita buat nanti
export KEEP_ZSHRC=yes
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# 4) Zsh plugins
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
mkdir -p "$ZSH_CUSTOM/plugins"
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
  git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

# 5) Prompt, banner, neofetch (Tampilan dipertahankan)
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

# 6) Default shell & hush login
chsh -s zsh || true
touch "$HOME/.hushlogin"

echo "======================================================"
echo "Install selesai. Restart Termux, lalu ketik 'menu'."
echo "======================================================"
