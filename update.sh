#!/bin/bash
# ==========================================
# Auto-Repair & Update Script (Ucenk D-Tech)
# ==========================================

REPO_DIR="$HOME/NetworkTools"

echo "======================================================"
echo "    Sinkronisasi Tools & Perbaikan Environment..."
echo "======================================================"

# 1. Tarik update terbaru dari GitHub
cd $REPO_DIR
git reset --hard
git pull origin main

# 2. Pastikan paket pendukung (sshpass, dll) terinstall
# Ini solusi agar Error 'sshpass not found' tidak muncul lagi
pkg update -y
pkg install sshpass nmap figlet -y

# 3. Pastikan Library Python aman
pip install routeros-api speedtest-cli lolcat --break-system-packages || true

# 4. Beri izin eksekusi ulang
chmod +x menu.py update.sh install.sh

# 5. Jalankan ulang konfigurasi shell
source ~/.zshrc

echo "======================================================"
echo "    UPDATE SELESAI! Semua fitur siap digunakan."
echo "======================================================"
