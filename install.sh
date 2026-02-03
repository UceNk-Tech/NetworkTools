#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# REVISI FINAL: BYPASS GPG ERROR & SYMLINK FIX
# ==========================================

# Jangan berhenti jika ada error repo
set +e 

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. Update & Install System Packages (Abaikan Error GPG)
echo -e "${CYAN}[+] Checking System Packages...${NC}"
# Kita tidak pakai pkg upgrade agar tidak sangkut di error GPG
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar -y || true

# 2. Fix Speedtest (MENGGUNAKAN FILE YANG SUDAH KAMU DOWNLOAD)
echo -e "${CYAN}[+] Membersihkan Alias & Binary Rusak...${NC}"
# Hapus alias yang tadi error saat ls/file
unalias speedtest 2>/dev/null || true
rm -f $PREFIX/bin/speedtest

# Jika file belum ada, download ulang secara aman
if [ ! -f "$PREFIX/bin/speedtest-cli" ]; then
    echo -e "${CYAN}[+] Mengunduh ulang script Speedtest...${NC}"
    curl -k -L https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -o $PREFIX/bin/speedtest-cli
fi

chmod +x $PREFIX/bin/speedtest-cli
# Buat link agar bisa dipanggil dengan nama 'speedtest'
ln -sf $PREFIX/bin/speedtest-cli $PREFIX/bin/speedtest

echo -e "${GREEN}[✓] Speedtest dipasang manual (Bypass Package Manager).${NC}"

# 3. Install Library Python
echo -e "${CYAN}[+] Installing Python Libraries...${NC}"
pip install lolcat routeros-api requests --break-system-packages || true

# 4. Setup Oh My Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -k -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 5. Konfigurasi .zshrc
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
# Pastikan alias memanggil python3 untuk menghindari error ELF
alias speedtest='python3 $PREFIX/bin/speedtest-cli --secure'
ZZZ

# 6. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP SELESAI! BYPASS GPG BERHASIL."
echo -e "  Ketik: source ~/.zshrc"
echo -e "  Lalu ketik: speedtest"
echo -e "===============================================${NC}"
