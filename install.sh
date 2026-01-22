#!/bin/bash
set -e
REPO_DIR="$HOME/NetworkTools"

# 1. Update & Install All Required Packages
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch lolcat psmisc -y 
pip install routeros_api speedtest-cli requests scapy --break-system-packages || true

# 2. Oh My Zsh & Plugins Setup
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 3. ZSHRC Configuration
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Startup Dashboard
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh'
EOF

chmod +x $REPO_DIR/*.py $REPO_DIR/*.sh
echo "REVISI SELESAI! Silakan buka ulang Termux." | lolcat
