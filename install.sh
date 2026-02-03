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

# 2. Install Speedtest CLI (REVISI FINAL - BYPASS REPO MATI)
echo -e "${CYAN}[+] Menjalankan Prosedur Emergency Speedtest...${NC}"

# Hapus sisa binary hantu yang bikin error e_type: 2
rm -f $PREFIX/bin/speedtest
rm -f $PREFIX/bin/speedtest-cli

# Karena repo pkg kamu mati (termux.net), kita pakai Pip secara paksa
# Ini cara paling direkomendasikan di forum Termux untuk kasus repo mati
echo -e "${CYAN}[+] Memasang lewat Jalur Python (Anti-Error)...${NC}"
python3 -m pip install --upgrade speedtest-cli --break-system-packages

# Kita buatkan link agar perintah 'speedtest' bisa dipanggil
ln -sf $(which speedtest-cli) $PREFIX/bin/speedtest

if [ -f "$PREFIX/bin/speedtest-cli" ]; then
    echo -e "${GREEN}[✓] Speedtest terpasang sempurna via Python Path.${NC}"
else
    # Jalur Darurat: Ambil script mentah jika pip gagal
    curl -L https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -o $PREFIX/bin/speedtest-cli
    chmod +x $PREFIX/bin/speedtest-cli
    echo -e "${GREEN}[✓] Speedtest terpasang via Raw Script GitHub.${NC}"
fi

# 3. Beri izin eksekusi (Kunci utama agar bisa dijalankan)
chmod +x $PREFIX/bin/speedtest-cli

# 4. Buat symlink agar bisa dipanggil dengan nama 'speedtest' juga
ln -sf $PREFIX/bin/speedtest-cli $PREFIX/bin/speedtest

echo -e "${GREEN}[✓] Speedtest terpasang manual di $PREFIX/bin/speedtest-cli${NC}"


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
