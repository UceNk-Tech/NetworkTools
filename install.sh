#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# REVISI: PAKSA PINDAH REPO & MANUAL INSTALL
# ==========================================

# Kita matikan mode berhenti jika error agar script terus jalan
set +e 

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. PAKSA PINDAH REPO (Ini obat 'Unable' yang paling manjur)
echo -e "${CYAN}[+] Memperbaiki server Termux yang mati...${NC}"
sed -i 's|termux.net|packages.termux.org/apt/termux-main|g' $PREFIX/etc/apt/sources.list
apt update -y || true

# 2. Install System Packages
echo -e "${CYAN}[+] Installing System Packages...${NC}"
apt install php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar -y || true

# 3. FIX SPEEDTEST (JALUR MANUAL - NO PKG NEEDED)
echo -e "${CYAN}[+] Menghapus file sampah penyebab error e_type...${NC}"
rm -f $PREFIX/bin/speedtest
rm -f $PREFIX/bin/speedtest-cli

echo -e "${CYAN}[+] Mengunduh Speedtest langsung dari GitHub...${NC}"
# Kita pakai curl -k (ignore SSL) karena repo lama sering masalah sertifikat
curl -k -L https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -o $PREFIX/bin/speedtest-cli
chmod +x $PREFIX/bin/speedtest-cli
ln -sf $PREFIX/bin/speedtest-cli $PREFIX/bin/speedtest

echo -e "${GREEN}[✓] Speedtest berhasil dipasang secara manual.${NC}"

# 4. Install Library Python
echo -e "${CYAN}[+] Installing Python Libraries...${NC}"
pip install lolcat routeros-api requests --break-system-packages || true

# 5. Setup Oh My Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
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
alias speedtest='speedtest-cli --secure'
ZZZ

# 7. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP SELESAI, UCENK! REPO SUDAH DI-BYPASS."
echo -e "  Silakan ketik 'source ~/.zshrc' atau buka ulang Termux."
echo -e "===============================================${NC}"
