#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# REVISI: Fix Repo & Official Speedtest (Manual PKG)
# ==========================================
set -e

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. Update & Install System Packages
echo -e "${CYAN}[+] Checking System Packages...${NC}"
pkg update -y || true

# 2. Fix Repository & Install Speedtest CLI (CARA MANUAL TERAMPUH)
echo -e "${CYAN}[+] Memperbaiki alamat Repository yang mati...${NC}"
# Alice ganti paksa termux.net yang mati ke server resmi yang aktif
sed -i 's|termux.net|packages.termux.org/apt/termux-main|g' $PREFIX/etc/apt/sources.list

echo -e "${CYAN}[+] Membersihkan file binary rusak (e_type error)...${NC}"
rm -f $PREFIX/bin/speedtest
rm -f $PREFIX/bin/speedtest-cli

echo -e "${CYAN}[+] Mengupdate database paket baru...${NC}"
apt update -y

echo -e "${CYAN}[+] Menginstall Speedtest CLI via PKG...${NC}"
# Sekarang pkg install pasti bisa menemukan paketnya
apt install speedtest-cli -y

echo -e "${GREEN}[✓] Speedtest-cli berhasil terpasang via Repositori Baru.${NC}"

# 3. Install Library Python
echo -e "${CYAN}[+] Installing Python Libraries...${NC}"
pip install lolcat routeros-api requests --break-system-packages

# 4. Setup Oh My Zsh & Plugins (Tetap sama)
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
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
# Gunakan alias yang benar
alias speedtest='speedtest-cli'
ZZZ

# 7. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP BERHASIL! REPO SUDAH DIPERBAIKI."
echo -e "  Silakan coba Menu 19 sekarang."
echo -e "===============================================${NC}"
