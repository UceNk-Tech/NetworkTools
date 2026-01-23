cat > ~/NetworkTools/install.sh << 'EOF'
#!/bin/bash
set -e

echo "======================================================" | lolcat 2>/dev/null || echo "======================================================"
echo "    MEMULAI PERBAIKAN SISTEM UCENK D-TECH..." 
echo "======================================================"

# 1. Install Paket Dasar (HILANGKAN lolcat dari sini)
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch ruby psmisc -y

# 2. Install Lolcat VIA GEM (Satu-satunya cara yang benar)
if ! command -v lolcat &> /dev/null; then
    echo "[*] Menginstal Lolcat (Ruby Gem)..."
    gem install lolcat
else
    echo "[i] Lolcat sudah ada."
fi

# 3. Install Python Packages
pip install --upgrade pip
pip install routeros_api speedtest-cli requests scapy --break-system-packages

# 4. Install Oh My Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 5. Install Plugin ZSH Autosuggestions
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

# 6. Setup ZSHRC
cat > "$HOME/.zshrc" << 'EOFZSH'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh'
EOFZSH

# 7. Permission & Selesai
chmod +x ~/NetworkTools/*.sh ~/NetworkTools/*.py
echo ""
echo "SELESAI! Buka ulang Termux." | lolcat
EOF
