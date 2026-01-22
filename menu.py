#!/usr/bin/env python3
import os, time, telnetlib, sys, json

# Warna ANSI
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
            creds['ip'], 
            username=creds['user'], 
            password=creds['pass'], 
            port=8728,
            plaintext_login=True
        )
        api = connection.get_api()
        
        if menu_type == '1':
            print(f"{CYAN}Mengambil Data Traffic...{RESET}")
            res = api.get_resource('/interface').get()
            for i in res:
                print(f"[{i.get('name')}] Running: {i.get('running')}")
                
        elif menu_type == '2':
            active = api.get_resource('/ip/hotspot/active').get()
            print(f"\n{GREEN}Total Hotspot Aktif: {len(active)}{RESET}")
            for u in active:
                print(f"User: {u.get('user'):<15} IP: {u.get('address'):<15}")
        
        elif menu_type == '3':
            u_res = api.get_resource('/ip/hotspot/user')
            count = 0
            for u in u_res.get():
                if "vc-" in u.get('comment', '') and u.get('limit-uptime') == u.get('uptime'):
                    u_res.remove(id=u.get('id'))
                    count += 1
            print(f"{GREEN}Hapus {count} voucher expired selesai.{RESET}")

        elif menu_type == '4':
            print(f"{CYAN}Mengecek DHCP Alert...{RESET}")
            # Menggunakan jalur resource yang benar
            alerts = api.get_resource('/ip/dhcp-server/alert').get()
            if not alerts:
                print(f"{YELLOW}Status: Aman. Tidak ada Rogue DHCP terdeteksi.{RESET}")
            else:
                for a in alerts:
                    print(f"{RED}[ALERT] Interface: {a.get('interface')} | Mac: {a.get('mac-address')}{RESET}")

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
            time.sleep(2) # Jeda agar data dari OLT masuk ke buffer
            output += tn.read_very_eager().decode('ascii')
        
        tn.write(b"exit\n")
        return output if output.strip() else f"{YELLOW}Data tidak ditemukan atau OLT sibuk.{RESET}"
    except Exception as e:
        return f"{RED}OLT Error: {e}{RESET}"

# ---------- MAIN MENU ----------

def main():
    while True:
        header()
        print(f" 1. Mikrotik: Monitor Traffic   2. Mikrotik: User Hotspot")
        print(f" 3. Mikrotik: Hapus Voucher     4. Mikrotik: DHCP Alert")
        print("-" * 54)
        print(f" 15. OLT: List ONU Aktif        16. OLT: Optical Power")
        print(f" 88. Fix Permission Mikhmon     99. Logout (Reset Data)")
        print(f"  0. Keluar")
        
        c = input(f"\n{WHITE}Pilih Menu: {RESET}").strip()

        if c in ['1', '2', '3', '4']:
            run_mt_api(c)
            input(f"\n{YELLOW}Tekan Enter...{RESET}")
        elif c == '15':
            slot = input("Nomor Slot: ")
            if slot:
                result = run_olt_telnet([f"show pon onu information gpon-olt_1/{slot}/1"])
                print(f"\n{GREEN}--- HASIL OLT ---{RESET}\n{result}")
            input(f"\n{YELLOW}Tekan Enter...{RESET}")
        elif c == '99':
            if os.path.exists(VAULT_FILE):
                os.remove(VAULT_FILE)
                print(f"{RED}Data lokal dihapus!{RESET}")
            time.sleep(1)
        elif c == '0':
            break

if __name__ == "__main__":
    main()
    
