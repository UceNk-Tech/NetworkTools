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
            if not alerts: print(f"\n{GREEN}[OK] DHCP Aman.{RESET}")
            else:
                for a in alerts: print(f"{RED}[ALERT] Interface: {a.get('interface')} - MAC: {a.get('mac-address')}{RESET}")
        elif menu_type == '4':
            scripts = api.get_resource('/system/script')
            to_del = [s for s in scripts.get() if 'mikhmon' in s.get('comment', '').lower()]
            if not to_del: print(f"{YELLOW}Tidak ada script laporan mikhmon.{RESET}")
            else:
                print(f"Ditemukan {len(to_del)} item."); conf = input("Hapus? (y/n): ").lower()
                if conf == 'y':
                    for s in to_del: scripts.remove(id=s.get('id'))
                    print(f"{GREEN}Laporan Mikhmon telah dibersihkan.{RESET}")
        conn.disconnect()
    except Exception as e: print(f"{RED}Error: {e}{RESET}")

# --- FUNGSI OLT (NOMOR 9 - REVISI: CUKUP INPUT SLOT) ---
def run_olt_telnet_onu():
    creds = get_credentials("olt")
    try:
        print(f"\n{MAGENTA}==== OLT ONU SCANNER PER SLOT ===={RESET}")
        slot = input(f"{CYAN} Masukkan Nomor Slot (contoh: 2): {RESET}").strip()
        
        if not slot:
            print(f"{RED}Slot tidak boleh kosong!{RESET}"); return

        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:"); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:"); tn.write(creds['pass'].encode() + b"\n")
        time.sleep(1)
        
        tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")
        
        # Alice buat looping otomatis dari PON 1 sampai 16
        print(f"{YELLOW}[*] Menarik data seluruh ONU di Slot {slot} (PON 1-16)...{RESET}")
        
        # Looping untuk setiap PON di slot tersebut
        for pon_no in range(1, 17):
            full_port = f"gpon-olt_1/{slot}/{pon_no}"
            print(f"{CYAN}[>] Memeriksa Port {full_port}...{RESET}")
            
            command = f"show pon onu information {full_port}\n"
            tn.write(command.encode())
            time.sleep(1) # Delay singkat agar buffer tidak penuh
            
            output = tn.read_very_eager().decode()
            if "No related information to be found" not in output:
                print(f"{WHITE}{output}{RESET}")
            else:
                print(f"{RED}Port {pon_no}: Kosong / Tidak ada ONU.{RESET}")

        tn.write(b"exit\n")
        tn.close()
        print(f"{GREEN}\n[V] Scanning Slot {slot} Selesai.{RESET}")
    except Exception as e:
        print(f"{RED}Error OLT: {e}{RESET}")

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
                f.write(f"opcache.enable=0\nsession.save_path=\"{sess_dir}\"\n")
            os.system("fuser -k 8080/tcp > /dev/null 2>&1")
            print(f"{GREEN}Mikhmon: http://127.0.0.1:8080{RESET}")
            os.system(f'export PHP_INI_SCAN_DIR={tmp_dir}; php -S 127.0.0.1:8080 -t {mikhmon_dir}')
        elif c in ['2', '3', '4']: run_mt(c)
        elif c == '9': run_olt_telnet_onu()
        elif c == '22':
            os.system('cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh')
            break
        elif c == '0': break
        input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

if __name__ == "__main__":
    main()
