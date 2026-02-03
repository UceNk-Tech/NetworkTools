#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# Support: Multi-Profile & Rogue DHCP Check
# Author: Ucenk
# REVISI: Clean Path & Hybrid Install
# ==========================================
# Matikan set -e sementara agar jika repo mati, script tidak berhenti total
set +e 

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. Update & Install SEMUA Dependencies
echo -e "${CYAN}[+] Installing System Packages (PHP, Git, Psmisc, Figlet)...${NC}"
# Bersihkan binary rusak yang bikin e_type error sebelum install
rm -f $PREFIX/bin/speedtest $PREFIX/bin/speedtest-cli

# Gunakan || true agar jika repo termux.net mati, script tetap lanjut ke bawah
pkg update && pkg upgrade -y || true
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar -y || true

# 2. Install Library Python Wajib
echo -e "${CYAN}[+] Installing Python Libraries (Requests, RouterOS, Speedtest)...${NC}"
# Kita pasang speedtest via pip karena repo pkg sedang bermasalah
pip install lolcat routeros-api speedtest-cli requests --break-system-packages

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
# Alias tambahan agar speedtest selalu menggunakan mode secure
alias speedtest='speedtest-cli --secure'
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
echo -e "  DHCP Rogue & Brand Lookup AKTIF."
echo -e "  Ketik: source ~/.zshrc untuk memulai."
echo -e "===============================================${NC}"
