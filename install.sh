#!/bin/bash
set -e
REPO_DIR="$HOME/NetworkTools"

# Install tools yang dibutuhkan (Termasuk psmisc untuk fuser)
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch lolcat psmisc -y 

# Config .zshrc
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Start Menu Otomatis
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh'
EOF

chmod +x $REPO_DIR/*.py $REPO_DIR/*.sh
echo "Selesai, Ucenk! Sekarang semua menu sudah kembali berfungsi." | lolcat
