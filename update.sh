rm -f ~/NetworkTools/update.sh && cat > ~/NetworkTools/update.sh << 'EOF'
#!/bin/bash
set -e
REPO_DIR="$HOME/NetworkTools"
REPO_URL="https://github.com/Ucenk-D-Tech/NetworkTools"
echo "======================================================" | lolcat 2>/dev/null || echo "======================================================"
echo "    CHECKING UPDATES (UCENK D-TECH)..." 
echo "======================================================" | lolcat 2>/dev/null || echo "======================================================"
if [ -f "$REPO_DIR/vault_session.json" ]; then cp "$REPO_DIR/vault_session.json" /tmp/vault_backup.json; fi
if [ -d "$REPO_DIR/.git" ]; then
  cd "$REPO_DIR"
  git reset --hard HEAD
  git clean -fd
  git pull origin main
else
  echo "[*] Mode Zip: Mengunduh update terbaru..."
  curl -L "$REPO_URL/archive/refs/heads/main.zip" -o /tmp/update_tools.zip
  unzip -o /tmp/update_tools.zip -d /tmp
  cp -rf /tmp/NetworkTools-main/* "$REPO_DIR/"
  rm -rf /tmp/update_tools.zip /tmp/NetworkTools-main
fi
if [ -f /tmp/vault_backup.json ]; then cp /tmp/vault_backup.json "$REPO_DIR/vault_session.json"; rm /tmp/vault_backup.json; fi
pkg update -y
pkg install -y git python php curl figlet neofetch nmap openssh psmisc || true
pip install --upgrade routeros-api speedtest-cli requests scapy pysnmp lolcat --break-system-packages || true
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom"
if [ -d "$ZSH_CUSTOM/plugins/zsh-autosuggestions" ]; then
  cd "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
  git pull
  cd - > /dev/null
fi
chmod +x "$REPO_DIR"/*.py "$REPO_DIR"/*.sh 2>/dev/null || true
echo "======================================================" | lolcat 2>/dev/null || echo "======================================================"
echo "    UPDATE SELESAI!" 
echo "======================================================" | lolcat 2>/dev/null || echo "======================================================"
EOF
chmod +x ~/NetworkTools/update.sh
