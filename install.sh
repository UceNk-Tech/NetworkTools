#!/bin/bash
# ==========================================
# Installer Otomatis Ucenk D-Tech Pro v3
# ==========================================

# Update & install paket dasar
pkg update && pkg upgrade -y
pkg install -y php git figlet curl python inetutils neofetch zsh nmap

# Install pip packages
pip install lolcat routeros-api speedtest-cli

# Install Oh My Zsh
rm -rf ~/.oh-my-zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended

# Plugin autosuggestions
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

# Download Mikhmon
cd $HOME
rm -rf mikhmonv3 ~/session_mikhmon ~/tmp
git clone https://github.com/laksa19/mikhmonv3.git

# Konfigurasi prompt & alias
cat << 'EOF' > ~/.zshrc
export ZSH="$HOME/.oh-my-zsh"
ZSH_THEME="robbyrussell"
plugins=(git zsh-autosuggestions)
source $ZSH/oh-my-zsh.sh

PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

clear
figlet -f slant "Ucenk D-Tech" | lolcat
echo " Author: Ucenk | Premium Network Management System" | lolcat
neofetch --ascii_distro ubuntu

echo " Ketik 'mikhmon' untuk menjalankan server." | lolcat
echo " Ketik 'telnet (IP OLT)' untuk remote management OLT." | lolcat
echo " Ketik 'menu' untuk membuka tools lain." | lolcat

alias mikhmon='fuser -k 8080/tcp > /dev/null 2>&1; \
export PHP_INI_SCAN_DIR=$HOME/tmp; \
mkdir -p ~/tmp ~/session_mikhmon; \
echo "opcache.enable=0" > ~/tmp/custom.ini; \
echo "session.save_path=\"$HOME/session_mikhmon\"" >> ~/tmp/custom.ini; \
echo "Mikhmon berjalan di http://127.0.0.1:8080"; \
php -S 127.0.0.1:8080 -t ~/mikhmonv3'

alias menu='python $HOME/NetworkTools/menu.py'
EOF

# Set default shell
chsh -s zsh
touch ~/.hushlogin

echo "Berhasil! Restart Termux lalu ketik 'menu'."

# Alias untuk update tools
echo "alias update-tools='bash ~/NetworkTools/update.sh'" >> ~/.zshrc
