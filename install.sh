cat > install.sh << 'EOF'
#!/bin/bash
set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "\e[32m[+] Memperbarui Script & Instalasi Ulang...\e[0m"

# 1. Update & Install All Required Packages
pkg update -y
# HAPUS lolcat dari sini, karena itu bukan paket Termux standar
pkg install zsh git python figlet curl php nmap neofetch ruby psmisc -y 

# 2. Install Lolcat via Ruby Gem (SOLUSI ERROR)
if ! command -v lolcat &> /dev/null; then
    echo "[*] Menginstal Lolcat via Ruby Gem..."
    gem install lolcat
else
    echo "[*] Lolcat sudah terinstal."
fi

# 3. Install Python Packages
pip install --upgrade pip
pip install routeros_api speedtest-cli requests scapy --break-system-packages || true

# 4. Oh My Zsh & Plugins Setup
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo "[*] Menginstal Oh My Zsh..."
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# Clone plugin zsh-autosuggestions jika belum ada
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    echo "[*] Menginstal Plugin ZSH Autosuggestions..."
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

# 5. ZSHRC Configuration
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

# 6. Izin Eksekusi
chmod +x $SCRIPT_DIR/*.py $SCRIPT_DIR/*.sh 2>/dev/null || true

echo ""
echo "INSTALASI SELESAI! Silakan buka ulang Termux atau ketik 'zsh'." | lolcat
EOF
