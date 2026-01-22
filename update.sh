#!/bin/bash
# ==========================================
# Update Script untuk NetworkTools
# ==========================================

cd ~/NetworkTools || exit

echo "======================================================"
echo "   Update NetworkTools dari GitHub..."
echo "======================================================"

# Tarik update terbaru dari branch main
git pull origin main

# Jalankan ulang installer untuk apply perubahan
bash install.sh

echo "======================================================"
echo "   Update selesai! Restart Termux lalu ketik 'menu'."
echo "======================================================"
