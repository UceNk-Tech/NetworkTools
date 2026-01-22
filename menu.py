#!/usr/bin/env python3
import readline 
import os, time, telnetlib, sys, json

# Warna ANSI
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

# Penyimpanan lokal aman
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
        print(f"\n{YELLOW}[!] Setup Login {target_type.upper()} (Lokal){RESET}")
        data = {'ip': input(f" IP: ").strip(), 'user': input(f" User: ").strip()}
        import getpass
        data['pass'] = getpass.getpass(f" Pass: ").strip()
        vault[target_type] = data
        save_vault(vault)
    return data

def show_header():
    # Header persis sesuai request Ucenk
    os.system('echo "Ketik nomor untuk menjalankan menu yang ada inginkan" | lolcat')
    os.system('echo "=============================" | lolcat')
    os.system('echo "Mikrotik Management Tools" | lolcat')
    os.system('echo "=============================" | lolcat')
    print(f"{WHITE}1. Jalankan Mikhmon Server        5. Bandwidth Usage Report (CSV)")
    print(f"2. Total User Aktif Hotspot       6. Backup & Restore Config MikroTik")
    print(f"3. Cek DHCP Alert (Rogue DHCP)    7. SNMP Monitoring (placeholder)")
    print(f"4. Hapus Voucher Expired          8. Log Viewer MikroTik{RESET}")
    
    os.system('echo "=============================" | lolcat')
    os.system('echo "OLT Management Tools" | lolcat')
    os.system('echo "=============================" | lolcat')
    print(f"{WHITE}9. Lihat semua ONU                10. Konfigurasi ONU")
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
            print(f"User Aktif: {len(api.get_resource('/ip/hotspot/active').get())}")
        elif menu_type == '3':
            alerts = api.get_resource('/ip/dhcp-server/alert').get()
            print(alerts if alerts else "Aman.")
        elif menu_type == '4':
            # Scan berdasarkan komentar 'mikhmon' seperti di screenshot
            scripts = api.get_resource('/system/script')
            to_del = [s for s in scripts.get() if 'mikhmon' in s.get('comment', '').lower()]
            if not to_del: print("Tidak ada script laporan.")
            else:
                print(f"Ditemukan {len(to_del)} item."); conf = input("Hapus? (y/n): ").lower()
                if conf == 'y':
                    for s in to_del: scripts.remove(id=s.get('id'))
                    try: api.get_resource('/system/note').set(note="")
                    except: pass
                    print("Log dibersihkan.")
        conn.disconnect()
    except Exception as e: print(f"Error: {e}")

def main():
    while True:
        show_header()
        c = input(f"{CYAN}Pilih Nomor: {RESET}").strip()
        
        if c == '1':
            print(f"{GREEN}Menjalankan Mikhmon Server di port 8080...{RESET}")
            os.system('chmod -R 755 $HOME/mikhmon && php -S 0.0.0.0:8080 -t $HOME/mikhmon')
        elif c in ['2', '3', '4']:
            run_mt(c)
        elif c == '22':
            os.system('cd $HOME/NetworkTools && git pull && bash install.sh')
            break
        elif c == '0': break
        else: print(f"{YELLOW}Menu {c} belum aktif.{RESET}")
        
        input(f"\n{YELLOW}Tekan Enter...{RESET}")
        os.system('clear')

if __name__ == "__main__":
    main()
