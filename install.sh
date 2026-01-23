#!/bin/bash
# ==========================================
# ALL-IN-ONE INSTALLER (UCENK D-TEECH)
# Clone -> Run -> Ready to Use
# ==========================================
set -e

# Warna untuk log instalasi
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${GREEN}================================================"
echo "    INSTALLER SIAP PAKAI - UCENK D-TECH"
echo "================================================${NC}"

# 1. Update & Install Paket Dasar
# Kita tidak install ruby, karena pakai python-lolcat
pkg update -y
pkg install -y git python zsh figlet neofetch php nmap psmisc curl

# 2. Install Library Python & Lolcat
echo -e "${GREEN}[+] Installing Python Libraries & Lolcat...${NC}"
pip install --upgrade pip
pip install routeros_api speedtest-cli requests scapy lolcat --break-system-packages

# 3. Setup Oh My Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${GREEN}[+] Installing Oh My Zsh...${NC}"
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 4. Setup Plugin ZSH Autosuggestions
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
if [ ! -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    echo -e "${GREEN}[+] Installing ZSH Autosuggestions...${NC}"
    git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
fi

# 5. Konfigurasi .zshrc (Tampilan & Startup Otomatis)
echo -e "${GREEN}[+] Configuring ZSHRC for Cool Look...${NC}"
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

# Prompt Keren Ucenk D-Tech
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# STARTUP OTOMATIS: Jalankan Menu saat buka Termux
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

# Aliases
alias menu='python $HOME/NetworkTools/menu.py'
alias update='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh'
EOF

# 6. Izin Eksekusi (Agar script bisa jalan)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
chmod +x $SCRIPT_DIR/*.py $SCRIPT_DIR/*.sh

# 7. Ubah Default Shell ke ZSH (Wajib agar tampilan aktif otomatis)
echo -e "${GREEN}[+] Setting ZSH as default shell...${NC}"
chsh -s zsh

echo -e "${GREEN}================================================"
echo "    INSTALASI SELESAI!"
echo "    Restart Termux untuk efek penuh."
echo "================================================${NC}"
