#!/usr/bin/env python3
import os, time, telnetlib, sys, json

# Warna ANSI untuk UI
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

# File rahasia di local Termux
VAULT_FILE = os.path.join(os.path.dirname(__file__), "vault_session.json")

def load_vault():
    if os.path.exists(VAULT_FILE):
        with open(VAULT_FILE, 'r') as f:
            try: return json.load(f)
            except: return {"olt": {}, "mikrotik": {}}
    return {"olt": {}, "mikrotik": {}}

def save_vault(data):
    with open(VAULT_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_credentials(target_type):
    vault = load_vault()
    data = vault.get(target_type, {})
    if not data or not data.get('ip'):
        header()
        print(f"\n{YELLOW}[!] Setup {target_type.upper()} (Tersimpan di Local Termux){RESET}")
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

# ---------- ENGINE MIKROTIK (API PORT 8728) ----------

def run_mt_api(menu_type):
    try:
        import routeros_api
    except ImportError:
        print(f"{RED}Error: Library 'routeros-api' tidak ditemukan!{RESET}")
        return

    creds = get_credentials("mikrotik")
    try:
        # Menggunakan class RouterOsApi (Versi Terbaru)
        connection = routeros_api.RouterOsApi(
            creds['ip'], user=creds['user'], password=creds['pass'], port=8728
        )
        api = connection.get_api()
        
        if menu_type == '1':
            print(f"{CYAN}Monitor Traffic Interface...{RESET}")
            resource = api.get_resource('/interface')
            for i in resource.get():
                print(f"[{i.get('name')}] Type: {i.get('type')} | L2MTU: {i.get('l2mtu')} | Running: {i.get('running')}")
                
        elif menu_type == '2':
            active = api.get_resource('/ip/hotspot/active').get()
            print(f"\n{GREEN}Total Hotspot Aktif: {len(active)}{RESET}")
            print(f"{'USER':<15} {'ADDRESS':<15} {'UPTIME':<10}")
            print("-" * 45)
            for u in active:
                print(f"{u.get('user'):<15} {u.get('address'):<15} {u.get('uptime'):<10}")
        
        elif menu_type == '3':
            u_res = api.get_resource('/ip/hotspot/user')
            all_u = u_res.get()
            count = 0
            for u in all_u:
                # Cek jika comment mengandung 'vc-' dan uptime sudah mencapai limit
                if "vc-" in u.get('comment', '') and u.get('limit-uptime') == u.get('uptime'):
                    u_res.remove(id=u.get('id'))
                    count += 1
            print(f"{GREEN}Berhasil menghapus {count} voucher expired.{RESET}")
            
        elif menu_type == '4':
            alerts = api.get_resource('/ip/dhcp-server/alert').get()
            if not alerts: print(f"{YELLOW}Tidak ada DHCP Alert.{RESET}")
            else: print(alerts)

        connection.disconnect()
    except Exception as e:
        print(f"{RED}Mikrotik API Error: {e}{RESET}")
        print(f"{YELLOW}Saran: Cek IP/User/Pass atau status Service API (8728) di Mikrotik.{RESET}")

# ---------- ENGINE OLT (TELNET PORT 23) ----------

def run_olt_telnet(cmds):
    creds = get_credentials("olt")
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:", timeout=5)
        tn.write(creds['user'].encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(creds['pass'].encode('ascii') + b"\n")
        
        # Masuk ke mode terminal luas
        tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")
        
        output = ""
        for c in cmds:
            tn.write(c.encode('ascii') + b"\n")
            output += tn.read_until(b"ZXAN#", timeout=15).decode('ascii')
        
        tn.write(b"exit\n")
        return output
    except Exception as e:
        return f"{RED}OLT Telnet Error: {e}{RESET}\n{YELLOW}Pastikan Telnet Port 23 aktif di OLT.{RESET}"

# ---------- MAIN INTERFACE ----------

def main():
    while True:
        header()
        print(f"{GREEN} 1. Monitor Traffic Interface   {CYAN} 2. User Aktif Hotspot")
        print(f"{YELLOW} 3. Hapus Voucher Expired       {RED} 4. Cek DHCP Alert")
        print(f"{MAGENTA}------------------------------------------------------")
        print(f"{MAGENTA} 15. OLT: List ONU per Slot     {BLUE} 16. OLT: Optical Power")
        print(f"{WHITE} 88. Fix Permission Mikhmon     {RED} 99. Logout (Reset Data Local)")
        print(f"{RED}  0. Keluar")
        
        c = input(f"\n{WHITE}Pilih Menu: {RESET}").strip()

        if c in ['1', '2', '3', '4']:
            run_mt_api(c)
            input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")
        elif c == '15':
            slot = input("Masukkan Nomor Slot (Contoh 2): ")
            if slot:
                print(run_olt_telnet([f"show pon onu information gpon-olt_1/{slot}/1"]))
            input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")
        elif c == '16':
            slot = input("Slot: "); onu = input("ONU ID: ")
            if slot and onu:
                print(run_olt_telnet([f"show pon onu rx-power gpon-onu_1/{slot}/1:{onu}"]))
            input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")
        elif c == '88':
            os.system("chmod -R 755 $HOME/mikhmon")
            print(f"{GREEN}Izin folder Mikhmon diperbaiki.{RESET}")
            time.sleep(1)
        elif c == '99':
            if os.path.exists(VAULT_FILE):
                os.remove(VAULT_FILE)
                print(f"{RED}Sesi dihapus. Anda akan diminta login ulang di menu berikutnya.{RESET}")
            time.sleep(1)
        elif c == '0':
            print(f"{CYAN}Terima kasih, Ucenk!{RESET}")
            break

if __name__ == "__main__":
    main()
