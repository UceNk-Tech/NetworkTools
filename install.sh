#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# REVISI: Direct Pip (Bypass Repo Termux.net yang Mati)
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
# Pakai || true supaya kalau repo termux.net error, script tidak berhenti
pkg update -y || true
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar -y

# 2. Install Speedtest CLI (REVISI KHUSUS: Jalur Pip Langsung)
echo -e "${CYAN}[+] Menghapus file binary yang menyebabkan error e_type...${NC}"
# Hapus semua file binary lama yang bikin error "unexpected e_type: 2"
rm -f $PREFIX/bin/speedtest
rm -f $PREFIX/bin/speedtest-cli

echo -e "${CYAN}[+] Installing Speedtest CLI via Pip (Bypass PKG)...${NC}"
# Kita langsung pakai pip karena pkg install speedtest-cli tidak ditemukan di repo kamu
pip install speedtest-cli --break-system-packages

echo -e "${GREEN}[✓] Speedtest-cli berhasil terpasang via Pip.${NC}"

# 3. Install Library Python Lainnya
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
# Alias ke speedtest-cli agar sinkron dengan instalasi pip
alias speedtest='speedtest-cli --secure'
ZZZ

# 7. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP BERHASIL! ERROR E_TYPE SUDAH DIBERSIHKAN."
echo -e "  Sekarang jalankan menu.py Anda."
echo -e "===============================================${NC}"
