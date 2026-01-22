#!/bin/bash
# ==========================================
# Auto-Repair & Update Script (Ucenk D-Tech)
# ==========================================

REPO_DIR="$HOME/NetworkTools"

echo "======================================================" | lolcat
echo "    Sinkronisasi Tools & Perbaikan Environment..." | lolcat
echo "======================================================" | lolcat

# 1. Tarik update terbaru dari GitHub
# Menggunakan reset --hard untuk menghindari error merge/conflict
cd $REPO_DIR
echo "[*] Membersihkan perubahan lokal & menarik update..." | lolcat
git reset --hard
git pull origin main

# 2. Verifikasi Paket Sistem
echo "[*] Memverifikasi paket sistem (sshpass, nmap, php, dll)..." | lolcat
pkg update -y
pkg install sshpass nmap figlet php lolcat inetutils neofetch -y || pip install lolcat --break-system-packages

# 3. Verifikasi Library Python
# Catatan: pip upgrade dihapus karena dilarang di Termux (mencegah error)
echo "[*] Memperbarui library Python yang dibutuhkan..." | lolcat
pip install routeros-api speedtest-cli requests scapy pysnmp --break-system-packages || true

# 4. Keamanan Data Lokal
# Memastikan vault_session.json (kredensial Ucenk) tidak ter-push ke publik
cat > "$REPO_DIR/.gitignore" << EOF
vault_session.json
__pycache__/
*.pyc
.env
EOF

# 5. Izin Eksekusi & Finalisasi
chmod +x menu.py update.sh install.sh

echo "======================================================" | lolcat
echo "    UPDATE SELESAI!" | lolcat
echo "    Semua fitur dan tampilan telah disinkronkan." | lolcat
echo "    Ketik 'menu' atau buka ulang Termux." | lolcat
echo "======================================================" | lolcat
