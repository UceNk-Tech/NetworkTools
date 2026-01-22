#!/bin/bash
# ==========================================
# Update Script untuk NetworkTools (Ucenk D-Tech)
# ==========================================

set -e
cd "$HOME/NetworkTools"

echo "======================================================" | lolcat
echo "    Menarik update dari GitHub (branch: main)..." | lolcat
echo "======================================================" | lolcat

# Reset perubahan lokal agar tidak konflik saat pull
git reset --hard
git pull origin main

# Pastikan file bisa dieksekusi
chmod +x install.sh update.sh menu.py

echo "Menjalankan ulang konfigurasi environment..." | lolcat

# --- PERBAIKAN DI SINI ---
# Kita update pkg, tapi JANGAN upgrade pip secara manual
pkg update -y

# Ganti upgrade pip dengan instalasi library pendukung yang diperlukan saja
# Menggunakan flag --break-system-packages agar diizinkan Termux
pip install routeros-api speedtest-cli lolcat pysnmp --break-system-packages || true

echo "======================================================" | lolcat
echo "    Update selesai! Ketik 'menu' untuk memulai." | lolcat
echo "======================================================" | lolcat
