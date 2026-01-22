#!/bin/bash
# ==========================================
# Update Script untuk NetworkTools
# ==========================================

set -e
cd "$HOME/NetworkTools"

echo "======================================================"
echo "    Menarik update dari GitHub (branch: main)..."
echo "======================================================"

# Reset perubahan lokal agar tidak konflik saat pull
git reset --hard
git pull origin main

# Pastikan file bisa dieksekusi
chmod +x install.sh update.sh menu.py

echo "Menjalankan ulang konfigurasi environment..."
# Kita hanya jalankan bagian penting dari install tanpa hapus data
pkg update -y
pip install --upgrade pip --break-system-packages || pip install --upgrade pip

echo "======================================================"
echo "    Update selesai! Ketik 'menu' untuk memulai."
echo "======================================================"
