#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.3
# Author: Ucenk
# Fitur: Speedtest Fix, Instant Launch, Silent
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

# 2. Install Library Python & FORCE FIX SPEEDTEST
echo -e "${CYAN}[+] Installing Python Libraries & Fixing Speedtest...${NC}"
pip install lolcat routeros-api requests --break-system-packages

# Download binary speedtest langsung ke folder sistem Termux agar bisa dipanggil python
# Menggunakan source sivel/speedtest.py yang stabil
wget -qO $PREFIX/bin/speedtest-cli https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py
chmod +x $PREFIX/bin/speedtest-cli
ln -sf $PREFIX/bin/speedtest-cli $PREFIX/bin/speedtest 2>/dev/null || true

# 3. Setup Oh My Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${CYAN}[+] Setting up Oh My Zsh...${NC}"
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 4. Matikan Banner Termux (MOTD) agar loading instan
touch $HOME/.hushlogin

# 5. Konfigurasi .zshrc (Setting Tampilan & Auto-Run Menu)
echo -e "${CYAN}[+] Configuring .zshrc...${NC}"
cat > "$HOME/.zshrc" << 'ZZZ'
# Jalankan menu di awal agar tidak ada jeda loading plugin
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    clear
    # Menjalankan menu python
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
# Fix DeprecationWarning agar tampilan bersih di menu 19
alias speedtest-cli='python3 -W ignore $PREFIX/bin/speedtest-cli'
alias speedtest='python3 -W ignore $PREFIX/bin/speedtest-cli'
alias mikhmon='python3 -c "import sys; sys.path.append(\"$HOME/NetworkTools\"); from menu import run_mikhmon; run_mikhmon()"'
ZZZ

# 6. Paksa Bash panggil ZSH (Agar PERMANEN sejak awal)
echo "exec zsh" > "$HOME/.bashrc"
chsh -s zsh || true

# 7. Finalisasi Permission
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP SELESAI! UCENK D-TECH SIAP PAKAI."
echo -e "  Langsung otomatis masuk ke ZSH & Menu."
echo -e "===============================================${NC}"

# Masuk ke ZSH sekarang juga
exec zsh
