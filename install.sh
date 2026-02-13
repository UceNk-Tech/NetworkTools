#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.3
# Support: Multi-Profile, Rogue DHCP & AI Alice
# Author: Ucenk
# ==========================================
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. Update & Install SEMUA Dependencies
echo -e "${CYAN}[+] Installing System Packages (PHP, Git, Psmisc, Figlet)...${NC}"
pkg update && pkg upgrade -y
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap -y

# 2. Install Library Python Wajib
# Alice: Menambahkan 'google-generativeai' agar otak Alice langsung aktif!
echo -e "${CYAN}[+] Installing Python Libraries (Requests, RouterOS, AI Alice, etc)...${NC}"
pip install lolcat routeros-api speedtest-cli requests google-generativeai --break-system-packages

# 3. Setup Oh My Zsh & Plugins
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${CYAN}[+] Setting up Oh My Zsh...${NC}"
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

ZSH_PLUGINS="$HOME/.oh-my-zsh/custom/plugins/zsh-autosuggestions"
if [ ! -d "$ZSH_PLUGINS" ]; then
    echo -e "${CYAN}[+] Adding ZSH Plugins...${NC}"
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_PLUGINS" || true
fi

# 4. Setup Struktur Folder
echo -e "${CYAN}[+] Creating Directory Structure...${NC}"
mkdir -p ~/NetworkTools ~/session_mikhmon ~/tmp

# 5. Download Mikhmon Source
if [ ! -d "$HOME/mikhmonv3" ]; then
    echo -e "${CYAN}[+] Downloading Mikhmon Source...${NC}"
    git clone https://github.com/laksa19/mikhmonv3.git ~/mikhmonv3 || echo "Skip download, folder exist."
fi

# 6. Konfigurasi .zshrc (Optimal)
echo -e "${CYAN}[+] Configuring .zshrc...${NC}"
cat > "$HOME/.zshrc" << 'ZZZ'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
source $ZSH/oh-my-zsh.sh

# Custom Prompt Ucenk D-Tech
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Jalankan Menu Otomatis
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python "$HOME/NetworkTools/menu.py"
fi

# Alias shortcut
alias menu='python $HOME/NetworkTools/menu.py'
alias update='bash $HOME/NetworkTools/update.sh'
alias mikhmon='python -c "import sys; sys.path.append(\"$HOME/NetworkTools\"); from menu import run_mikhmon; run_mikhmon()"'
ZZZ

# 7. Finalisasi Permission
echo -e "${CYAN}[+] Setting Permissions...${NC}"
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

# Switch Shell ke ZSH
if [ "$SHELL" != "/data/data/com.termux/files/usr/bin/zsh" ]; then
    chsh -s zsh
fi

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP BERHASIL! SEMUA TOOLS SIAP DIGUNAKAN."
echo -e "  AI ALICE, DHCP Rogue & Brand Lookup AKTIF."
echo -e "  Buka ulang Termux untuk melihat hasilnya."
echo -e "===============================================${NC}"
