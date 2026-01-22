#!/bin/bash
# ==========================================
# Update Script untuk NetworkTools
# ==========================================

set -e
cd "$HOME/NetworkTools"

echo "======================================================"
echo "   Menarik update dari GitHub (branch: main)..."
echo "======================================================"

git pull origin main

echo "Menjalankan ulang installer untuk apply perubahan..."
bash install.sh

echo "======================================================"
echo "   Update selesai! Restart Termux lalu ketik 'menu'."
echo "======================================================"
