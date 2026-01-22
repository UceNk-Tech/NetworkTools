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

def get_credentials(target_type):
    vault = load_vault()
    data = vault.get(target_type, {})
    if not data or not data.get('ip'):
        print(f"\n{YELLOW}[!] Setup Login {target_type.upper()}{RESET}")
        data = {'ip': input(f" IP: ").strip(), 'user': input(f" User: ").strip()}
        import getpass
        data['pass'] = getpass.getpass(f" Pass: ").strip()
        vault[target_type] = data
        save_vault(vault)
    return data

def show_sticky_header():
    """Urutan Visual: Banner Figlet (Atas) -> Neofetch Ubuntu (Bawah) -> List Menu"""
    os.system('clear')
    os.system('echo "======================================================" | lolcat')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat')
    os.system('echo "      Author: Ucenk  |  Premium Network Management System" | lolcat')
    os.system('echo "======================================================" | lolcat')
    os.system('echo " Welcome back, Ucenk D-Tech!" | lolcat')
    os.system('neofetch --ascii_distro ubuntu')
    
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

# --- FUNGSI MIKROTIK (KEMBALI BERFUNGSI) ---
def run_mt(menu_type):
    try:
        import routeros_api
        creds = get_credentials("mikrotik")
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = conn.get_api()
        
        if menu_type == '2':
            active = api.get_resource('/ip/hotspot/active').get()
            print(f"\n{GREEN}>>> TOTAL USER AKTIF: {len(active)} USER{RESET}")
        elif menu_type == '3':
            alerts = api.get_resource('/ip/dhcp-server/alert').get()
            if not alerts:
                print(f"\n{GREEN}[OK] DHCP Aman, tidak ada Rogue DHCP.{RESET}")
            else:
                for a in alerts: print(f"{RED}[ALERT] Interface: {a.get('interface')} - MAC: {a.get('mac-address')}{RESET}")
        elif menu_type == '4':
            scripts = api.get_resource('/system/script')
            to_del = [s for s in scripts.get() if 'mikhmon' in s.get('comment', '').lower()]
            if not to_del:
                print(f"{YELLOW}Tidak ada script laporan mikhmon.{RESET}")
            else:
                print(f"Ditemukan {len(to_del)} item."); conf = input("Hapus? (y/n): ").lower()
                if conf == 'y':
                    for s in to_del: scripts.remove(id=s.get('id'))
                    print(f"{GREEN}Laporan Mikhmon telah dibersihkan.{RESET}")
        conn.disconnect()
    except Exception as e:
        print(f"{RED}Error Mikrotik: {e}{RESET}")

# --- FUNGSI OLT (NOMOR 9) ---
def run_olt_telnet(cmds):
    creds = get_credentials("olt")
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:"); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:"); tn.write(creds['pass'].encode() + b"\n")
        time.sleep(1); tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")
        out = ""
        for c in cmds:
            tn.write(c.encode() + b"\n"); time.sleep(1)
            out += tn.read_very_eager().decode()
        tn.write(b"exit\n"); return out
    except Exception as e: return f"Error OLT: {e}"

def main():
    while True:
        show_sticky_header()
        c = input(f"{CYAN}Pilih Nomor: {RESET}").strip()
        
        if c == '1':
            mikhmon_dir = os.path.expanduser("~/mikhmonv3")
            tmp_dir = os.path.expanduser("~/tmp")
            sess_dir = os.path.expanduser("~/session_mikhmon")
            if not os.path.exists(mikhmon_dir):
                print(f"{YELLOW}[!] Download Mikhmonv3...{RESET}")
                os.system(f"git clone https://github.com/laksa19/mikhmonv3.git {mikhmon_dir}")
            os.system(f"mkdir -p {tmp_dir} {sess_dir}")
            with open(os.path.join(tmp_dir, "custom.ini"), "w") as f:
                f.write("opcache.enable=0\n")
                f.write(f'session.save_path="{sess_dir}"\n')
            os.system("fuser -k 8080/tcp > /dev/null 2>&1")
            print(f"{GREEN}Mikhmon berjalan di http://127.0.0.1:8080{RESET}")
            os.system(f'export PHP_INI_SCAN_DIR={tmp_dir}; php -S 127.0.0.1:8080 -t {mikhmon_dir}')
            
        elif c in ['2', '3', '4']:
            run_mt(c) # Memanggil fungsi Mikrotik yang tadi hilang
            
        elif c == '9':
            print(f"{YELLOW}Mencari ONU Aktif...{RESET}")
            result = run_olt_telnet(["show pon onu information"])
            print(f"\n{WHITE}{result}{RESET}")
            
        elif c == '22':
            os.system('cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh')
            break
        elif c == '0': break
        input(f"\n{YELLOW}Tekan Enter untuk kembali ke Menu Utama...{RESET}")

if __name__ == "__main__":
    main()
