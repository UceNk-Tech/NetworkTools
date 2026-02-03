#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# Support: Multi-Profile & Rogue DHCP Check
# REVISI: Official Speedtest CLI (Fix Unknown ISP)
# ==========================================
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. Update & Install System Packages
echo -e "${CYAN}[+] Installing System Packages (PHP, Git, Python, Nmap)...${NC}"
pkg update && pkg upgrade -y
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar -y

# 2. Install Official Speedtest CLI (Solusi Pasti Jalan)
echo -e "${CYAN}[+] Installing Speedtest CLI via Package Manager...${NC}"
# Hapus file binary lama yang bikin error e_type
rm -f $PREFIX/bin/speedtest
# Install langsung via repo Termux (Sistem akan pilihkan arsitektur yang cocok)
pkg install speedtest-cli -y
echo -e "${GREEN}[✓] Speedtest CLI berhasil terpasang via PKG.{NC}"

# 3. Install Library Python
echo -e "${CYAN}[+] Installing Python Libraries...${NC}"
pip install lolcat routeros-api requests --break-system-packages

# 4. Setup Oh My Zsh & Plugins
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${CYAN}[+] Setting up Oh My Zsh...${NC}"
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

ZSH_PLUGINS="$HOME/.oh-my-zsh/custom/plugins/zsh-autosuggestions"
if [ ! -d "$ZSH_PLUGINS" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_PLUGINS" || true
fi

# 5. Setup Struktur Folder
mkdir -p ~/NetworkTools ~/session_mikhmon ~/tmp

# 6. Konfigurasi .zshrc
echo -e "${CYAN}[+] Configuring .zshrc...${NC}"
cat > "$HOME/.zshrc" << 'ZZZ'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
source $ZSH/oh-my-zsh.sh

PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python "$HOME/NetworkTools/menu.py"
fi

alias menu='python $HOME/NetworkTools/menu.py'
alias speedtest='speedtest --accept-license --accept-gdpr'
ZZZ

# 7. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP BERHASIL! ISP SEKARANG AKAN TERDETEKSI."
echo -e "  Silakan restart Termux Anda."
echo -e "===============================================${NC}"
