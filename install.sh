#!/bin/bash
set -e

# Otomatis mendeteksi di mana script ini berjalan
# Jadi tidak error walaupun Anda menjalankannya dari dalam folder NetworkTools
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

echo -e "\e[32m[+] Mulai Instalasi Network Tools by Ucenk D-Tech...\e[0m"

# 1. Update & Install All Required Packages
# HAPUS 'lolcat' dari daftar pkg install, karena itu bukan paket Termux standar
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch ruby psmisc -y 

# 2. Install Lolcat via Ruby Gem (MEMPERBAIKI ERROR: Unable to locate package)
if ! command -v lolcat &> /dev/null; then
    echo "[*] Menginstal Lolcat via Ruby Gem..."
    gem install lolcat
else
    echo "[*] Lolcat sudah terinstal."
fi

# 3. Install Python Packages
# Menambahkan --upgrade untuk memastikan library terbaru
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
# Kita timpa .zshrc agar konfigurasi Ucenk D-Tech terpasang rapi
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

# 6. Izin Eksekusi
# Menggunakan SCRIPT_DIR agar path benar meski script dijalankan di mana saja
chmod +x $SCRIPT_DIR/*.py $SCRIPT_DIR/*.sh 2>/dev/null || true

echo ""
echo "INSTALASI SELESAI! Silakan buka ulang Termux atau ketik 'zsh'." | lolcat
