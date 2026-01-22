#!/usr/bin/env python3
import os, time, telnetlib, sys, json

# Warna ANSI untuk UI yang rapi
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

VAULT_FILE = os.path.join(os.path.dirname(__file__), "vault_session.json")

def load_vault():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"olt": {}, "mikrotik": {}}
    return {"olt": {}, "mikrotik": {}}

def save_vault(data):
    with open(VAULT_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_credentials(target_type):
    vault = load_vault()
    data = vault.get(target_type, {})
    if not data or not data.get('ip'):
        header()
        print(f"\n{YELLOW}[!] Setup Login {target_type.upper()} (Tersimpan Lokal){RESET}")
        data = {}
        data['ip'] = input(f" Masukkan IP {target_type}: ").strip()
        data['user'] = input(f" Masukkan Username: ").strip()
        import getpass
        data['pass'] = getpass.getpass(f" Masukkan Password: ").strip()
        vault[target_type] = data
        save_vault(vault)
    return data

def header():
    os.system('clear')
    print(f"{MAGENTA}======================================================{RESET}")
    print(f"{GREEN}   Ucenk D-Tech - Private Management System          {RESET}")
    print(f"{WHITE}      (Mikrotik: API 8728 | OLT: Telnet 23)          {RESET}")
    print(f"{MAGENTA}======================================================{RESET}")

# ---------- ENGINE MIKROTIK (API 8728) ----------

def run_mt_api(menu_type):
    try:
        import routeros_api
    except ImportError:
        print(f"{RED}Error: Library 'routeros-api' tidak ditemukan!{RESET}")
        return

    creds = get_credentials("mikrotik")
    
    try:
        connection = routeros_api.RouterOsApiPool(
            creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True
        )
        api = connection.get_api()
        
        if menu_type == '1':
            print(f"{CYAN}Monitor Traffic Interface...{RESET}")
            res = api.get_resource('/interface').get()
            for i in res: print(f"[{i.get('name')}] Running: {i.get('running')}")
                
        elif menu_type == '2':
            active = api.get_resource('/ip/hotspot/active').get()
            print(f"\n{GREEN}Total Hotspot Aktif: {len(active)}{RESET}")
            for u in active: print(f"User: {u.get('user'):<15} IP: {u.get('address'):<15}")
        
        elif menu_type == '3':
            print(f"{CYAN}Scanning Script Laporan Mikhmon di System Script...{RESET}")
            script_res = api.get_resource('/system/script')
            all_scripts = script_res.get()
            
            # SCANNING: Mencari kata 'mikhmon' di kolom Comment (seperti di screenshot)
            to_delete = [s for s in all_scripts if 'mikhmon' in s.get('comment', '').lower()]
            
            if not to_delete:
                print(f"{YELLOW}Tidak ditemukan script dengan komentar 'mikhmon'.{RESET}")
                print(f"Pastikan kolom 'Comment' di Mikrotik berisi kata 'mikhmon'.")
            else:
                print(f"{WHITE}Ditemukan {len(to_delete)} script laporan Mikhmon.{RESET}")
                print(f"{CYAN}Contoh 3 data teratas:{RESET}")
                for s in to_delete[:3]:
                    print(f" - Nama: {s.get('name')} | Comment: {s.get('comment')}")
                
                print(f"\n{RED}PERINGATAN: Ini akan menghapus {len(to_delete)} item dari System Script.{RESET}")
                confirm = input(f"{YELLOW}Hapus semua script laporan ini? (y/n): {RESET}").lower()
                
                if confirm == 'y':
                    print(f"{MAGENTA}Proses menghapus... Mohon tunggu...{RESET}")
                    count = 0
                    for s in to_delete:
                        script_res.remove(id=s.get('id'))
                        count += 1
                    
                    # Bersihkan System Note (Totalan laporan Mikhmon biasanya di sini)
                    try:
                        api.get_resource('/system/note').set(note="")
                        print(f"{GREEN}System Note dikosongkan.{RESET}")
                    except: pass
                    
                    print(f"{GREEN}Berhasil menghapus {count} script laporan Mikhmon.{RESET}")
                else:
                    print(f"{BLUE}Penghapusan dibatalkan. Data tetap aman.{RESET}")

        elif menu_type == '4':
            alerts = api.get_resource('/ip/dhcp-server/alert').get()
            if not alerts: print(f"{YELLOW}Aman. Tidak ada Rogue DHCP terdeteksi.{RESET}")
            else:
                for a in alerts: print(f"{RED}[ALERT] Int: {a.get('interface')} | Mac: {a.get('mac-address')}{RESET}")

        connection.disconnect()
    except Exception as e:
        print(f"{RED}Mikrotik API Error: {e}{RESET}")

# ---------- ENGINE OLT (TELNET PORT 23) ----------

def run_olt_telnet(cmds):
    creds = get_credentials("olt")
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:", timeout=5)
        tn.write(creds['user'].encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(creds['pass'].encode('ascii') + b"\n")
        time.sleep(1)
        tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#", timeout=5)
        output = ""
        for c in cmds:
            tn.write(c.encode('ascii') + b"\n")
            time.sleep(2) # Jeda krusial untuk OLT ZTE
            output += tn.read_very_eager().decode('ascii')
        tn.write(b"exit\n")
        return output if output.strip() else "Tidak ada data dari OLT."
    except Exception as e:
        return f"Error: {e}"

# ---------- MAIN MENU ----------

def main():
    while True:
        header()
        print(f" 1. Monitor Traffic Interface   2. User Aktif Hotspot")
        print(f" 3. Hapus Script Lap Mikhmon    4. Cek DHCP Alert (Rogue)")
        print("-" * 54)
        print(f" 15. OLT: List ONU per Slot     16. OLT: Optical Power")
        print(f" 88. Fix Permission Mikhmon     99. Logout (Ganti IP)")
        print(f"  0. Keluar")
        
        c = input(f"\n{WHITE}Pilih Menu: {RESET}").strip()
        if c in ['1', '2', '3', '4']:
            run_mt_api(c); input(f"\n{YELLOW}Tekan Enter...{RESET}")
        elif c == '15':
            slot = input("Nomor Slot (Contoh 1): ")
            if slot: 
                print(f"{CYAN}Menghubungkan ke OLT...{RESET}")
                print(run_olt_telnet([f"show pon onu information gpon-olt_1/{slot}/1"]))
            input(f"\n{YELLOW}Tekan Enter...{RESET}")
        elif c == '99':
            if os.path.exists(VAULT_FILE): os.remove(VAULT_FILE)
            print(f"{RED}Data login dihapus!{RESET}"); time.sleep(1)
        elif c == '0': break

if __name__ == "__main__":
    main()
            
