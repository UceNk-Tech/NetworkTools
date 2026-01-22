#!/usr/bin/env python3
import os, time, telnetlib, sys, json

# Import proteksi untuk library yang mungkin absen
try:
    import routeros_api
except ImportError:
    os.system("pip install routeros-api --break-system-packages")

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
        print(f"\n{YELLOW}[!] Setup Login {target_type.upper()} (Private Local Data){RESET}")
        data = {'ip': input(f" IP {target_type}: ").strip(), 'user': input(f" Username: ").strip()}
        import getpass
        data['pass'] = getpass.getpass(f" Password: ").strip()
        vault[target_type] = data
        save_vault(vault)
    return data

def header():
    os.system('echo "Ketik nomor untuk menjalankan menu yang ada inginkan" | lolcat')
    os.system('echo "=============================" | lolcat')
    os.system('echo "Mikrotik Management Tools" | lolcat')
    os.system('echo "=============================" | lolcat')
    print(f"{WHITE}1. Monitor Traffic Interface      5. Bandwidth Usage Report (CSV)")
    print(f"2. Total User Aktif Hotspot       6. Backup & Restore MikroTik")
    print(f"3. Cek DHCP Alert (Rogue)         7. SNMP Monitoring (placeholder)")
    print(f"4. Hapus Laporan Mikhmon          8. Log Viewer MikroTik{RESET}")
    
    os.system('echo "=============================" | lolcat')
    os.system('echo "OLT Management Tools" | lolcat')
    os.system('echo "=============================" | lolcat')
    print(f"{WHITE}9. Lihat Semua ONU                13. Alarm & Event Viewer")
    print(f"10. Konfigurasi ONU               14. Backup & Restore OLT")
    print(f"11. Reset ONU                     15. Traffic Report per PON")
    print(f"12. Port & VLAN Config            16. Auto Audit Script{RESET}")

    os.system('echo "=============================" | lolcat')
    os.system('echo "Network Tools" | lolcat')
    os.system('echo "=============================" | lolcat')
    print(f"{WHITE}17. Speedtest CLI                 20. Ping & Traceroute")
    print(f"18. Nmap Scan                     21. DNS Tools")
    print(f"19. MAC Lookup                    22. Update-tools{RESET}")
    print(f"{MAGENTA}====================================================={RESET}")

def run_mt_api(menu_type):
    creds = get_credentials("mikrotik")
    try:
        connection = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = connection.get_api()
        if menu_type == '1':
            res = api.get_resource('/interface').get()
            for i in res: print(f"[{i.get('name')}] Running: {i.get('running')}")
        elif menu_type == '2':
            active = api.get_resource('/ip/hotspot/active').get()
            print(f"{GREEN}Total Aktif: {len(active)}{RESET}")
        elif menu_type == '3':
            alerts = api.get_resource('/ip/dhcp-server/alert').get()
            if not alerts: print(f"{GREEN}Aman: Tidak ada Rogue DHCP.{RESET}")
            else: print(alerts)
        elif menu_type == '4':
            script_res = api.get_resource('/system/script')
            to_delete = [s for s in script_res.get() if 'mikhmon' in s.get('comment', '').lower()]
            if not to_delete: print(f"{YELLOW}Tidak ada script laporan.{RESET}")
            else:
                print(f"Ditemukan {len(to_delete)} script."); conf = input("Hapus? (y/n): ").lower()
                if conf == 'y':
                    for s in to_delete: script_res.remove(id=s.get('id'))
                    try: api.get_resource('/system/note').set(note="")
                    except: pass
                    print(f"{GREEN}Laporan dibersihkan.{RESET}")
        connection.disconnect()
    except Exception as e: print(f"{RED}MT Error: {e}{RESET}")

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
            tn.write(c.encode() + b"\n"); time.sleep(2)
            out += tn.read_very_eager().decode()
        tn.write(b"exit\n"); return out
    except Exception as e: return f"OLT Error: {e}"

def main():
    while True:
        header()
        c = input(f"{CYAN}Pilih Nomor: {RESET}").strip()
        if c in ['1','2','3','4']: run_mt_api(c)
        elif c == '9':
            slot = input("Masukkan Slot: ")
            if slot: print(run_olt_telnet([f"show pon onu information gpon-olt_1/{slot}/1"]))
        elif c == '22':
            os.system("cd $HOME/NetworkTools && git pull && bash install.sh")
            break
        elif c == '0': break
        input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__":
    main()
