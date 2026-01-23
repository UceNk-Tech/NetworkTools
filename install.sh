cat > ~/NetworkTools/install.sh << 'EOF'
#!/bin/bash
set -e

echo "======================================================"
echo "    INSTALLER UCENK D-TECH (PYTHON VERSION)"
echo "======================================================"

# 1. Update Paket
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch psmisc -y 

# 2. Install Python Libraries
# KITA INSTALL LOLCAT VIA PYTHON DI SINI
pip install routeros_api speedtest-cli requests scapy lolcat --break-system-packages

# 3. Setup ZSH
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 4. Setup Plugins
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

# 5. Config ZSHRC
cat > "$HOME/.zshrc" << 'EOFZSH'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Jika lolcat (python) tidak jalan, fallback biasa
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh'
EOFZSH

chmod +x ~/NetworkTools/*.sh ~/NetworkTools/*.py
echo "======================================================"
echo "INSTALASI SELESAI!"
echo "Ketik 'menu' atau buka ulang Termux."
echo "======================================================" | lolcat
EOF
