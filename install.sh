#!/bin/bash
# ==========================================
# NetworkTools All-in-One Installer
# Author: Ucenk D-Tech
# ==========================================

set -e
REPO_DIR="$HOME/NetworkTools"

echo "======================================================" | lolcat
echo "    Sinkronisasi & Perbaikan Environment..." | lolcat
echo "======================================================" | lolcat

# 1. Update Paket
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch lolcat -y || pip install lolcat --break-system-packages
pip install routeros-api speedtest-cli requests scapy --break-system-packages || true

# 2. Oh My Zsh & Plugins
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom/plugins"
mkdir -p "$ZSH_CUSTOM"
[ ! -d "$ZSH_CUSTOM/zsh-autosuggestions" ] && git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/zsh-autosuggestions"
[ ! -d "$ZSH_CUSTOM/zsh-syntax-highlighting" ] && git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/zsh-syntax-highlighting"

# 3. Konfigurasi .zshrc (Tampilan yang Ucenk minta)
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

# --- CUSTOM PROMPT UCENK D-TECH ---
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# --- TAMPILAN STARTUP ---
clear
neofetch --ascii_distro ubuntu
echo "======================================================" | lolcat
figlet -f slant "Ucenk D-Tech" | lolcat
echo "      Author: Ucenk  |  Premium Network Management System" | lolcat
echo "======================================================" | lolcat
echo " Welcome back, Ucenk D-Tech!" | lolcat

# Jalankan Menu Otomatis
[ -f "$HOME/NetworkTools/menu.py" ] && python $HOME/NetworkTools/menu.py

# Aliases
alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh'
alias mikhmon='[ ! -d $HOME/mikhmon ] && mkdir -p $HOME/mikhmon; php -S 0.0.0.0:8080 -t $HOME/mikhmon'
EOF

# 4. Git Security & Izin
cat > "$REPO_DIR/.gitignore" << EOF
vault_session.json
__pycache__/
*.pyc
EOF
chmod +x $REPO_DIR/*.py $REPO_DIR/*.sh

echo "======================================================" | lolcat
echo "    INSTALASI SELESAI! Silakan buka ulang Termux." | lolcat
echo "======================================================" | lolcat
