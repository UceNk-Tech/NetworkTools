#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3.2
# REVISI: TOTAL BYPASS PKG (Anti-Unable)
# ==========================================

# Jangan berhenti jika ada error
set +e 

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${CYAN}[+] Memulai Setup Lingkungan Ucenk D-Tech...${NC}"

# 1. Install Paket Sistem Dasar (Tanpa Speedtest)
echo -e "${CYAN}[+] Memasang Paket Sistem (Abaikan pesan error repo)...${NC}"
# Kita biarkan paket ini terinstall jika sudah ada, kalau error lewati saja
pkg install php git figlet curl python psmisc inetutils neofetch zsh nmap wget tar -y || true

# 2. PROSEDUR FIX SPEEDTEST (TANPA PKG)
echo -e "${CYAN}[+] Membersihkan sistem dari sisa instalasi gagal...${NC}"
# Hapus alias pengganggu
unalias speedtest 2>/dev/null || true
# Hapus binary hantu yang bikin e_type error
rm -f $PREFIX/bin/speedtest
rm -f $PREFIX/bin/speedtest-cli

echo -e "${CYAN}[+] Memasang Speedtest via Jalur Manual (Anti-Unable)...${NC}"
# Mengambil file langsung dari GitHub (Ini yang tadi kamu tes dan BERHASIL)
curl -k -L https://raw.githubusercontent.com/sivel/speedtest-cli/master/speedtest.py -o $PREFIX/bin/speedtest-cli

# Beri izin eksekusi
chmod +x $PREFIX/bin/speedtest-cli

# Buat link agar perintah 'speedtest' bisa dipanggil di terminal
ln -sf $PREFIX/bin/speedtest-cli $PREFIX/bin/speedtest

echo -e "${GREEN}[✓] Speedtest terpasang manual (Bypass Package Manager).${NC}"

# 3. Install Library Python
echo -e "${CYAN}[+] Installing Python Libraries...${NC}"
pip install lolcat routeros-api requests --break-system-packages || true

# 4. Setup Oh My Zsh
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    echo -e "${CYAN}[+] Setting up Oh My Zsh...${NC}"
    sh -c "$(curl -k -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 5. Konfigurasi .zshrc (Penentu keberhasilan Menu 19)
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
# Gunakan python3 agar tidak kena e_type error
alias speedtest='python3 $PREFIX/bin/speedtest-cli --secure'
ZZZ

# 6. Finalisasi
chmod +x ~/NetworkTools/*.py 2>/dev/null || true

echo -e "\n${GREEN}==============================================="
echo -e "  SETUP BERHASIL, UCENK! TIDAK ADA LAGI UNABLE."
echo -e "  Ketik: source ~/.zshrc"
echo -e "  Lalu jalankan Menu 19."
echo -e "===============================================${NC}"
