cat > update.sh << 'EOF'
#!/bin/bash
set -e

echo "Update tools Ucenk D-Tech..."
pkg update -y && pkg upgrade -y
pkg install -y figlet neofetch git curl unzip ruby lolcat -y || true
gem install lolcat || true
pip install --upgrade routeros-api speedtest-cli requests --break-system-packages || true

chmod +x ~/NetworkTools/*.py ~/NetworkTools/*.sh
echo "Update selesai! Restart Termux atau ketik 'menu'."
EOF
