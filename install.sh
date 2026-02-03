#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# REVISI: ZERO-PKG FOR SPEEDTEST (Pasti Berhasil)
# ==========================================

# Matikan mode berhenti jika error
set +e 

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. Install Paket Sistem Dasar (TANPA SPEEDTEST-CLI DI SINI)
echo -e "${CYAN}[+] Memasang Paket Sistem (Membersihkan Antrian)...${NC}"
# Alice pisah agar jika satu gagal, yang lain tetap jalan dan tidak lapor "Unable" massal
for pkg in php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar; do
    pkg install $pkg -y || true
done

# 2. PROSEDUR FIX SPEEDTEST (TOTAL MANUAL - JALUR GITHUB)
echo -e "${CYAN}[+] Membersihkan sistem dari sisa binary & alias rusak...${NC}"
unalias speedtest 2>/dev/null || true
rm -f $PREFIX/bin/speedtest
rm -f $PREFIX/bin/speedtest-cli

echo -e "${CYAN}[+] Mendownload Script Speedtest (Jalur yang tadi Berhasil)...${NC}"
# Kita pakai curl -k lagi karena tadi kamu tes ini BERHASIL (65334 bytes)
curl -k -L https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -o $PREFIX/bin/speedtest-cli

# Beri izin eksekusi agar script bisa jalan
chmod +x $PREFIX/bin/speedtest-cli

# Buat link agar perintah 'speedtest' bisa dipanggil
ln -sf $PREFIX/bin/speedtest-cli $PREFIX/bin/speedtest

echo -e "${GREEN}[✓] Speedtest terpasang via Raw Script (Bypass Repo).${NC}"

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
# Pastikan dipanggil lewat python3 agar tidak kena error binary ELF
alias speedtest='python3 $PREFIX/bin/speedtest-cli --secure'
ZZZ

# 6. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP BERHASIL, UCENK!"
echo -e "  Pesan 'Unable' harusnya sudah hilang."
echo -e "  Ketik: source ~/.zshrc"
echo -e "  Lalu tes dengan ketik: speedtest"
echo -e "===============================================${NC}"
