#!/bin/bash
# ==========================================
# Auto-Repair & Update Script (Ucenk D-Tech)
# ==========================================

set -e # Hentikan script jika ada error fatal

REPO_DIR="$HOME/NetworkTools"
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"

echo "======================================================" | lolcat
echo "    Sinkronisasi Tools & Perbaikan Environment..." | lolcat
echo "======================================================" | lolcat

# 0. Pastikan lolcat terinstal (Diperlukan untuk output warna)
if ! command -v lolcat &> /dev/null; then
    echo "[*] Lolcat belum terinstal, memasang..." | lolcat
    pkg install ruby -y
    gem install lolcat
fi

# 1. Cek & Tarik update terbaru dari GitHub
if [ -d "$REPO_DIR/.git" ]; then
    cd "$REPO_DIR"
    echo "[*] Membersihkan perubahan lokal & menarik update..." | lolcat
    git reset --hard HEAD
    git clean -fd
    git pull origin main
else
    echo "[!] Folder $REPO_DIR bukan repository git atau belum ada." | lolcat
fi

# 2. Verifikasi Paket Sistem
echo "[*] Memverifikasi paket sistem..." | lolcat
pkg update -y
# Install paket penting, abaikan jika sudah ada
pkg install -y git python php curl figlet neofetch nmap openssh ruby psmisc || true

# 3. Update Plugin ZSH (zsh-autosuggestions)
if [ -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    echo "[*] Memperbarui plugin zsh-autosuggestions..." | lolcat
    cd "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
    git pull
    cd - > /dev/null
fi

# 4. Verifikasi Library Python
echo "[*] Memperbarui library Python yang dibutuhkan..." | lolcat
# routeros-api (pakai strip) adalah nama pip, importnya routeros_api (underscore)
pip install --upgrade routeros-api speedtest-cli requests scapy pysnmp --break-system-packages || true

# 5. Keamanan Data Lokal (.gitignore)
# Memastikan vault_session.json tidak ikut ter-push/ter-reset
cat > "$REPO_DIR/.gitignore" << EOF
vault_session.json
__pycache__/
*.pyc
.env
.DS_Store
EOF

# 6. Izin Eksekusi & Finalisasi
if [ -d "$REPO_DIR" ]; then
    chmod +x "$REPO_DIR"/*.py "$REPO_DIR"/*.sh 2>/dev/null || true
fi

echo "======================================================" | lolcat
echo "    UPDATE SELESAI!" | lolcat
echo "    Semua fitur dan tampilan telah disinkronkan." | lolcat
echo "    Ketik 'menu' atau buka ulang Termux." | lolcat
echo "======================================================" | lolcat
