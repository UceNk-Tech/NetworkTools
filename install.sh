#!/bin/bash
set -e

REPO_DIR="$HOME/NetworkTools"

echo -e "\e[32m[+] Mulai Instalasi Network Tools by Ucenk D-Tech...\e[0m"

# 1. Update & Install All Required Packages
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch ruby psmisc -y 

# Install Lolcat (Ruby Gem) agar perintah 'echo | lolcat' berjalan
gem install lolcat || echo "Gagal install lolcat gem, mencoba pip..."

# Install Python Packages
pip install --upgrade pip
pip install routeros_api speedtest-cli requests scapy lolcat --break-system-packages || true

# 2. Oh My Zsh & Plugins Setup
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# FIX: Clone plugin zsh-autosuggestions agar tidak error saat load zshrc
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

# 3. ZSHRC Configuration
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

# Custom Prompt Ucenk D-Tech
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Startup Dashboard (Hanya jalan jika script ada)
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh'
EOF

# FIX: Pastikan direktori ada sebelum chmod
if [ -d "$REPO_DIR" ]; then
    chmod +x $REPO_DIR/*.py $REPO_DIR/*.sh 2>/dev/null || true
fi

echo ""
echo "REVISI SELESAI! Silakan buka ulang Termux atau ketik 'zsh'." | lolcat
