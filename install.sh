#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# REVISI: Jalur Pip Speedtest (Anti e_type & Unknown ISP)
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
# Kita gunakan || true agar jika repo lama error, script tetap jalan ke tahap pip
pkg update -y || echo -e "${YELLOW}[!] Repo lama terdeteksi, melanjutkan...${NC}"
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar -y

# 2. Install Speedtest CLI (REVISI TOTAL)
echo -e "${CYAN}[+] Membersihkan file hantu & instalasi lama...${NC}"
# Hapus file binary yang bikin error "unexpected e_type: 2"
rm -f $PREFIX/bin/speedtest
rm -f $PREFIX/bin/speedtest-cli

echo -e "${CYAN}[+] Installing Speedtest CLI via Pip...${NC}"
# Menggunakan pip karena lebih universal untuk HP 32-bit maupun 64-bit
pip install speedtest-cli --break-system-packages

echo -e "${GREEN}[✓] Speedtest-cli berhasil terpasang.${NC}"

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
    git clone https://github.com/zsh-users/zsh-users/zsh-autosuggestions "$ZSH_PLUGINS" || true
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
# Gunakan alias ke speedtest-cli agar tidak pusing versi
alias speedtest='speedtest-cli --secure'
ZZZ

# 7. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP BERHASIL! ISP SEKARANG AKAN TERDETEKSI."
echo -e "  Gunakan Menu 19 untuk mencoba."
echo -e "===============================================${NC}"
