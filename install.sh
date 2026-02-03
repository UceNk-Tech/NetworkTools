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

# 1. FIX REPO (Tambahkan ini agar tidak UNABLE)
echo -e "${CYAN}[+] Fixing Repository Mirrors...${NC}"
sed -i 's|termux.net|packages.termux.org/apt/termux-main|g' $PREFIX/etc/apt/sources.list || true

# 2. Update & Install SEMUA Dependencies
echo -e "${CYAN}[+] Installing System Packages...${NC}"
# Kita hapus binary rusak dulu agar tidak e_type error
rm -f $PREFIX/bin/speedtest $PREFIX/bin/speedtest-cli
pkg update -y || true
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap wget -y || true

# 3. Install Library Python Wajib
echo -e "${CYAN}[+] Installing Python Libraries...${NC}"
# Speedtest dipasang lewat PIP karena PKG kamu sedang bermasalah
pip install lolcat routeros-api speedtest-cli requests --break-system-packages

# 4. Setup Oh My Zsh & Plugins
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

ZSH_PLUGINS="$HOME/.oh-my-zsh/custom/plugins/zsh-autosuggestions"
if [ ! -d "$ZSH_PLUGINS" ]; then
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_PLUGINS" || true
fi

# 5. Setup Struktur Folder & Mikhmon
mkdir -p ~/NetworkTools ~/session_mikhmon ~/tmp
if [ ! -d "$HOME/mikhmonv3" ]; then
    git clone https://github.com/laksa19/mikhmonv3.git ~/mikhmonv3 || echo "Skip."
fi

# 6. Konfigurasi .zshrc
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
echo -e "\n${GREEN}SETUP BERHASIL! Silakan restart Termux.${NC}"
