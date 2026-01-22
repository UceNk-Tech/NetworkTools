#!/bin/bash
# ==========================================
# Auto-Repair & Update Script (Ucenk D-Tech)
# ==========================================

REPO_DIR="$HOME/NetworkTools"

echo "======================================================"
echo "    Sinkronisasi Tools & Perbaikan Environment..."
echo "======================================================"

# 1. Tarik update terbaru dari GitHub
# Tetap mempertahankan vault_session.json karena sudah di .gitignore
cd $REPO_DIR
echo "[*] Menarik data terbaru dari GitHub..."
git reset --hard
git pull origin main

# 2. Pastikan paket sistem lengkap
echo "[*] Memverifikasi paket sistem (sshpass, nmap, dll)..."
pkg update -y
pkg install sshpass nmap figlet php lolcat inetutils -y

# 3. Pastikan Library Python lengkap & terbaru
# Ditambah requests & scapy untuk mendukung menu baru
echo "[*] Memperbarui library Python..."
pip install --upgrade pip
pip install routeros-api speedtest-cli lolcat requests scapy pysnmp --break-system-packages || true

# 4. Keamanan: Pastikan .gitignore tetap ada agar data lokal tidak bocor
cat > "$REPO_DIR/.gitignore" << EOF
vault_session.json
__pycache__/
*.pyc
.env
EOF

# 5. Beri izin eksekusi ulang
chmod +x menu.py update.sh install.sh

echo "======================================================"
echo "    UPDATE SELESAI!"
echo "    Semua library telah disinkronkan."
echo "    Silakan ketik 'menu' atau buka ulang Termux."
echo "======================================================"
