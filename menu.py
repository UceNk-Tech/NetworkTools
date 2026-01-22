#!/usr/bin/env python3
import os, time, telnetlib, sys, json
import readline 

# Warna ANSI
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

VAULT_FILE = os.path.join(os.path.dirname(__file__), "vault_session.json")

def load_vault():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'r') as f: return json.load(f)
        except: return {"olt": {}, "mikrotik": {}}
    return {"olt": {}, "mikrotik": {}}

def save_vault(data):
    with open(VAULT_FILE, 'w') as f: json.dump(data, f, indent=4)

def show_sticky_header():
    """Urutan Visual: Banner Figlet -> Neofetch Ubuntu -> List Menu"""
    os.system('clear')
    # 1. Tampilan Banner Paling Atas
    os.system('echo "======================================================" | lolcat')
    figlet_cmd = 'figlet -f slant "Ucenk D-Tech"'
    os.system(f'{figlet_cmd} | lolcat')
    os.system('echo "      Author: Ucenk  |  Premium Network Management System" | lolcat')
    os.system('echo "======================================================" | lolcat')
    os.system('echo " Welcome back, Ucenk D-Tech!" | lolcat')
    
    # 2. Neofetch Ubuntu di bawah banner
    os.system('neofetch --ascii_distro ubuntu')
    
    # 3. Tabel Menu
    os.system('echo "Ketik nomor untuk menjalankan menu yang ada inginkan" | lolcat')
    os.system('echo "=============================" | lolcat')
    os.system('echo "Mikrotik Management Tools" | lolcat')
    os.system('echo "=============================" | lolcat')
    print(f"{WHITE}1. Jalankan Mikhmon Server        5. Bandwidth Usage Report (CSV)")
    print(f"2. Total User Aktif Hotspot       6. Backup & Restore Config MikroTik")
    print(f"3. Cek DHCP Alert (Rogue DHCP)    7. SNMP Monitoring (placeholder)")
    print(f"4. Hapus Laporan Mikhmon          8. Log Viewer MikroTik{RESET}")
    
    os.system('echo "=============================" | lolcat')
    os.system('echo "OLT Management Tools" | lolcat')
    os.system('echo "=============================" | lolcat')
    print(f"{WHITE}9. Lihat semua ONU (Aktif)        10. Konfigurasi ONU")
    print(f"11. Reset ONU                     12. Port & VLAN Config")
    print(f"13. Alarm & Event Viewer          14. Backup & Restore Config OLT")
    print(f"15. Traffic Report per PON (CSV)  16. Auto Audit Script (daily){RESET}")

    os.system('echo "=============================" | lolcat')
    os.system('echo "Network Tools" | lolcat')
    os.system('echo "=============================" | lolcat')
    print(f"{WHITE}17. Speedtest CLI                 20. Ping & Traceroute")
    print(f"18. Nmap Scan                     21. DNS Tools (Lookup / Reverse)")
    print(f"19. MAC Lookup                    22. Update-tools{RESET}")
    print(f"{MAGENTA}====================================================={RESET}")

def main():
    while True:
        show_sticky_header()
        c = input(f"{CYAN}Pilih Nomor: {RESET}").strip()
        
        if c == '1':
            # SOLUSI ANTI-LOCK (DIADAPTASI DARI REFERENSI)
            mikhmon_dir = os.path.expanduser("~/mikhmonv3")
            tmp_dir = os.path.expanduser("~/tmp")
            sess_dir = os.path.expanduser("~/session_mikhmon")
            
            print(f"{YELLOW}[*] Menyiapkan environment mikhmon (Anti-Lock)...{RESET}")
            os.system(f"mkdir -p {tmp_dir} {sess_dir}")
            
            # Buat custom PHP config di dalam tmp
            with open(os.path.join(tmp_dir, "custom.ini"), "w") as f:
                f.write("opcache.enable=0\n")
                f.write(f'session.save_path="{sess_dir}"\n')
            
            # Kill proses lama di port 8080 agar tidak bentrok
            os.system("fuser -k 8080/tcp > /dev/null 2>&1")
            
            print(f"{GREEN}Mikhmon berjalan di http://127.0.0.1:8080{RESET}")
            # Jalankan dengan PHP_INI_SCAN_DIR
            os.system(f'export PHP_INI_SCAN_DIR={tmp_dir}; php -S 127.0.0.1:8080 -t {mikhmon_dir}')
            
        elif c == '22':
            print(f"{YELLOW}[*] Updating & Auto-Refreshing...{RESET}")
            os.system('cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh')
            break
        elif c == '0': break
        input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

if __name__ == "__main__":
    main()
