cat > ~/NetworkTools/update.sh << 'EOF'
#!/bin/bash
set -e

REPO_DIR="$HOME/NetworkTools"
REPO_URL="https://github.com/Ucenk-D-Tech/NetworkTools"

echo "======================================================" | lolcat 2>/dev/null || echo "======================================================"
echo "    CHECKING UPDATES (UCENK D-TECH)..." 
echo "======================================================" | lolcat 2>/dev/null || echo "======================================================"

# 0. Backup Login User
if [ -f "$REPO_DIR/vault_session.json" ]; then
    echo "[*] Backup login user..."
    cp "$REPO_DIR/vault_session.json" /tmp/vault_backup.json
fi

# 1. Cek Mode Update (Git atau Zip)
if [ -d "$REPO_DIR/.git" ]; then
    # MODE GIT
    echo "[*] Mode Git: Pulling update..."
    cd "$REPO_DIR"
    git reset --hard HEAD
    git clean -fd
    git pull origin main
else
    # MODE ZIP (FALLBACK)
    echo "[*] Mode Zip: Mengunduh update terbaru dari GitHub..."
    
    # Download ZIP
    curl -L "$REPO_URL/archive/refs/heads/main.zip" -o /tmp/update_tools.zip
    
    # Ekstrak
    echo "[*] Mengekstrak file..."
    unzip -o /tmp/update_tools.zip -d /tmp
    
    # Timpa file lama
    echo "[*] Menimpa file lama..."
    cp -rf /tmp/NetworkTools-main/* "$REPO_DIR/"
    
    # Bersihkan
    rm -rf /tmp/update_tools.zip /tmp/NetworkTools-main
fi

# 2. Kembalikan Login User
if [ -f /tmp/vault_backup.json ]; then
    echo "[*] Memulihkan login user..."
    cp /tmp/vault_backup.json "$REPO_DIR/vault_session.json"
    rm /tmp/vault_backup.json
fi

# 3. Update Paket Sistem
echo "[*] Memverifikasi paket sistem..."
pkg update -y
pkg install -y git python php curl figlet neofetch nmap openssh psmisc || true

echo "[*] Memperbarui library Python..."
pip install --upgrade routeros-api speedtest-cli requests scapy pysnmp lolcat --break-system-packages || true

# 4. Update Plugin ZSH
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
if [ -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
    echo "[*] Memperbarui plugin ZSH..."
    cd "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
    git pull
    cd - > /dev/null
fi

# 5. Izin Eksekusi
echo "[*] Mengatur permission..."
chmod +x "$REPO_DIR"/*.py "$REPO_DIR"/*.sh 2>/dev/null || true

echo "======================================================" | lolcat 2>/dev/null || echo "======================================================"
echo "    UPDATE SELESAI!" 
echo "======================================================" | lolcat 2>/dev/null || echo "======================================================"
EOF
