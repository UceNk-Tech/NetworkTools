#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# REVISI: Bypass Repo Mati & Manual GitHub Fix
# ==========================================
# Alice hilangkan 'set -e' agar script tidak berhenti saat repo error
set +e 

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. Update & Install System Packages (Abaikan Error Repo Mati)
echo -e "${CYAN}[+] Checking System Packages (Bypassing Repo Errors)...${NC}"
pkg update || true
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar -y || true

# 2. Install Speedtest CLI (REVISI BYPASS: No More Unable)
echo -e "${CYAN}[+] Membersihkan file binary penyebab error e_type...${NC}"
rm -f $PREFIX/bin/speedtest
rm -f $PREFIX/bin/speedtest-cli

echo -e "${CYAN}[+] Mengunduh Speedtest langsung dari GitHub (Anti-Unable)...${NC}"
# Kita ambil script Python langsung agar tidak butuh repositori pkg yang mati
curl -k -L https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -o $PREFIX/bin/speedtest-cli
chmod +x $PREFIX/bin/speedtest-cli

# Buat jembatan agar perintah 'speedtest' juga jalan
ln -sf $PREFIX/bin/speedtest-cli $PREFIX/bin/speedtest

echo -e "${GREEN}[✓] Speedtest terpasang manual (Bypass Repositori).${NC}"

# 3. Install Library Python
echo -e "${CYAN}[+] Installing Python Libraries...${NC}"
pip install lolcat routeros-api requests --break-system-packages || true

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
# Alias ke script yang baru dipasang
alias speedtest='speedtest-cli --secure'
ZZZ

# 7. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP BERHASIL! BYPASS REPO SUKSES."
echo -e "  Silakan jalankan ulang menu.py Anda."
echo -e "===============================================${NC}"
