#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
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
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap -y

# 2. Install Library Python
echo -e "${CYAN}[+] Installing Python Libraries...${NC}"
pip install lolcat routeros-api speedtest-cli requests --break-system-packages

# 3. Setup Oh My Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${CYAN}[+] Setting up Oh My Zsh...${NC}"
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 4. Konfigurasi .zshrc (Tampilan & Auto-Menu)
echo -e "${CYAN}[+] Configuring .zshrc (Custom Prompt & Auto-run)...${NC}"
cat > "$HOME/.zshrc" << 'ZZZ'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
source $ZSH/oh-my-zsh.sh

# Prompt Khas Ucenk D-Tech
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# Jalankan Menu Otomatis
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python3 "$HOME/NetworkTools/menu.py"
fi

alias menu='python3 $HOME/NetworkTools/menu.py'
ZZZ

# 5. RAHASIA OTOMATIS: Paksa Bash panggil ZSH
# Ini agar saat pertama kali buka Termux, tampilan default langsung dilewati
echo -e "${CYAN}[+] Setting ZSH as default permanently...${NC}"
echo "exec zsh" > "$HOME/.bashrc"
chsh -s zsh || true

# 6. Finalisasi Permission
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP SELESAI! UCENK D-TECH SIAP PAKAI."
echo -e "  Sekarang tutup Termux dan buka lagi."
echo -e "===============================================${NC}"

# Langsung masuk ke tampilan baru sekarang juga
exec zsh
