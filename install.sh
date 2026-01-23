#!/bin/bash
# ==========================================
# INSTALLER CONFIG (SETUP ZSH & TAMPILAN)
# Paket sudah diinstall via command awal
# ==========================================
set -e

GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}[+] Setup Oh My Zsh...${NC}"
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

echo -e "${GREEN}[+] Setup Plugin ZSH Autosuggestions...${NC}"
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

echo -e "${GREEN}[+] Configuring ZSHRC...${NC}"
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

# Prompt Ucenk D-Tech
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Jalankan Menu Otomatis
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

alias menu='python $HOME/NetworkTools/menu.py'
alias update='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh'
EOF

echo -e "${GREEN}[+] Setting Permissions...${NC}"
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
chmod +x $SCRIPT_DIR/*.py $SCRIPT_DIR/*.sh

echo -e "${GREEN}[+] Switching to ZSH...${NC}"
chsh -s zsh

echo -e "${GREEN}DONE! Buka ulang Termux.${NC}"
