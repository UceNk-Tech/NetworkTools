#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# Author: Ucenk
# Optimization: Instant Launch & Path Fix
# ==========================================
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. Update & Install Dependencies
echo -e "${CYAN}[+] Installing System Packages...${NC}"
pkg update && pkg upgrade -y
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap wget -y

# 2. Install Library Python & FORCE FIX PATH
echo -e "${CYAN}[+] Installing Python Libraries & Fixing Path...${NC}"
pip install lolcat routeros-api speedtest-cli requests --break-system-packages

# Memasukkan path bin python ke sistem agar perintah 'speedtest-cli' ditemukan
mkdir -p $PREFIX/bin
ln -sf $HOME/.local/bin/speedtest-cli $PREFIX/bin/speedtest-cli 2>/dev/null || true
ln -sf $HOME/.local/bin/speedtest-cli $PREFIX/bin/speedtest 2>/dev/null || true

# 3. Setup Oh My Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${CYAN}[+] Setting up Oh My Zsh...${NC}"
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 4. Matikan Banner Termux
touch $HOME/.hushlogin

# 5. Konfigurasi .zshrc
echo -e "${CYAN}[+] Configuring .zshrc (Instant Auto-run)...${NC}"
cat > "$HOME/.zshrc" << 'ZZZ'
# Tambahkan path manual agar perintah python terdeteksi
export PATH="$HOME/.local/bin:$PATH"

# Jalankan menu di awal agar tidak ada jeda loading plugin
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    clear
    python3 "$HOME/NetworkTools/menu.py"
fi

export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
source $ZSH/oh-my-zsh.sh

# Prompt Khas Ucenk D-Tech
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Alias shortcut
alias menu='python3 $HOME/NetworkTools/menu.py'
alias update='bash $HOME/NetworkTools/update.sh'
alias speedtest='speedtest-cli'
alias mikhmon='python3 -c "import sys; sys.path.append(\"$HOME/NetworkTools\"); from menu import run_mikhmon; run_mikhmon()"'
ZZZ

# 6. Paksa Bash panggil ZSH
echo "exec zsh" > "$HOME/.bashrc"
chsh -s zsh || true

# 7. Finalisasi Permission
echo -e "${CYAN}[+] Setting Permissions...${NC}"
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP SELESAI! UCENK D-TECH SIAP PAKAI."
echo -e "  Sekarang sistem akan otomatis masuk ke ZSH."
echo -e "===============================================${NC}"

# Jalankan dengan PATH yang benar sekarang juga
export PATH="$HOME/.local/bin:$PATH"
exec zsh
