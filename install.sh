#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# REVISI: FIX SOURCES.LIST & MANUAL BYPASS
# OWNER: UCENK D-TECH
# ==========================================

# Matikan mode berhenti jika error
set +e 

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. FIX REPOSITORY (Memulihkan Jantung Termux)
echo -e "${CYAN}[+] Memperbaiki Konfigurasi Repositori yang Hilang...${NC}"
mkdir -p $PREFIX/etc/apt/
# Kita buat ulang file sources.list karena tadi terdeteksi "No such file"
echo "deb https://packages.termux.org/apt/termux-main stable main" > $PREFIX/etc/apt/sources.list

# Update database paket
apt update -y || true

# 2. Install System Packages
echo -e "${CYAN}[+] Installing System Packages (PHP, Git, Python, Nmap)...${NC}"
apt install php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar -y || true

# 3. FIX SPEEDTEST (ANTI E_TYPE & ANTI UNABLE)
echo -e "${CYAN}[+] Membersihkan Alias & Binary Rusak...${NC}"
# Hapus alias lama yang bikin error
unalias speedtest 2>/dev/null || true
# Hapus binary penyebab e_type: 2
rm -f $PREFIX/bin/speedtest
rm -f $PREFIX/bin/speedtest-cli

echo -e "${CYAN}[+] Mengunduh Speedtest Manual dari GitHub...${NC}"
# Jalur manual agar tidak kena "Unable to locate"
curl -k -L https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -o $PREFIX/bin/speedtest-cli
chmod +x $PREFIX/bin/speedtest-cli
# Buat symlink agar perintah 'speedtest' bisa dipanggil
ln -sf $PREFIX/bin/speedtest-cli $PREFIX/bin/speedtest

echo -e "${GREEN}[✓] Speedtest Berhasil Terpasang Manual.${NC}"

# 4. Install Library Python
echo -e "${CYAN}[+] Installing Python Libraries...${NC}"
pip install lolcat routeros-api requests --break-system-packages || true

# 5. Setup Oh My Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${CYAN}[+] Setting up Oh My Zsh...${NC}"
    sh -c "$(curl -k -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

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
# Alias yang benar tanpa menabrak sistem
alias speedtest='speedtest-cli --secure'
ZZZ

# 7. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP BERHASIL! REPO & SPEEDTEST DIPERBAIKI."
echo -e "  Silakan ketik: source ~/.zshrc"
echo -e "  Lalu coba Menu 19."
echo -e "===============================================${NC}"
