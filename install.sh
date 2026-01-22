#!/bin/bash
# ==========================================
# NetworkTools All-in-One Installer
# Author: Ucenk D-Tech
# ==========================================
#!/bin/bash
# ==========================================
# NetworkTools All-in-One Installer
# Author: Ucenk D-Tech
# ==========================================

set -e
REPO_DIR="$HOME/NetworkTools"

# 1. Update & Install
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch lolcat psmisc -y 

# 2. Oh My Zsh & Plugin
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 3. Konfigurasi .zshrc
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

# --- CUSTOM PROMPT UCENK D-TECH ---
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# --- STARTUP DASHBOARD ---
# Langsung jalankan menu.py (Urutan Banner & Neofetch sudah ada di dalam menu.py)
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh'
EOF

chmod +x $REPO_DIR/*.py $REPO_DIR/*.sh
echo "Berhasil diinstal! Silakan ketik 'menu' atau buka ulang Termux." | lolcat
set -e
REPO_DIR="$HOME/NetworkTools"

echo "======================================================" | lolcat
echo "    Sinkronisasi & Perbaikan Environment..." | lolcat
echo "======================================================" | lolcat

# 1. Update Paket
pkg update -y
pkg install zsh git python figlet curl php nmap neofetch lolcat -y || pip install lolcat --break-system-packages
pip install routeros_api speedtest-cli requests scapy --break-system-packages || true

# 2. Oh My Zsh & Plugins
if [ ! -d "$HOME/.oh-my-zsh" ]; then
    sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi
ZSH_CUSTOM="$HOME/.oh-my-zsh/custom/plugins"
mkdir -p "$ZSH_CUSTOM"
[ ! -d "$ZSH_CUSTOM/zsh-autosuggestions" ] && git clone https://github.com/zsh-users/zsh-autosuggestions "$ZSH_CUSTOM/zsh-autosuggestions"
[ ! -d "$ZSH_CUSTOM/zsh-syntax-highlighting" ] && git clone https://github.com/zsh-users/zsh-syntax-highlighting "$ZSH_CUSTOM/zsh-syntax-highlighting"

# 3. Konfigurasi .zshrc
cat > "$HOME/.zshrc" << 'EOF'
export ZSH="$HOME/.oh-my-zsh"
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
[ -f $ZSH/oh-my-zsh.sh ] && source $ZSH/oh-my-zsh.sh

# --- CUSTOM PROMPT UCENK D-TECH ---
PROMPT='%F{green}[Ucenk %F{cyan}D-Tech%F{white}]%F{yellow} ~ $ %f'

# --- STARTUP DASHBOARD ---
if [ -f "$HOME/NetworkTools/menu.py" ]; then
    python $HOME/NetworkTools/menu.py
fi

# Aliases
alias menu='python $HOME/NetworkTools/menu.py'
alias update-tools='cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh'
EOF

chmod +x $REPO_DIR/*.py $REPO_DIR/*.sh
echo "Berhasil! Pilih Menu 22 untuk melihat efek Auto-Refresh." | lolcat
