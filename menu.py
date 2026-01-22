#!/usr/bin/env python3
import os, time, telnetlib, sys, json

# Warna ANSI
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

# File rahasia hanya di lokal Termux (Masuk ke .gitignore)
VAULT_FILE = os.path.join(os.path.dirname(__file__), "vault_session.json")

def load_vault():
    if os.path.exists(VAULT_FILE):
        with open(VAULT_FILE, 'r') as f:
            return json.load(f)
    return {"olt": {}, "mikrotik": {}}

def save_vault(data):
    with open(VAULT_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def get_credentials(target_type):
    vault = load_vault()
    data = vault.get(target_type, {})
    
    if not data:
        print(f"\n{YELLOW}[!] Data {target_type.upper()} belum ada di local.{RESET}")
        data['ip'] = input(f" Masukkan IP {target_type}: ").strip()
        data['user'] = input(f" Masukkan Username: ").strip()
        import getpass
        data['pass'] = getpass.getpass(f" Masukkan Password: ").strip()
        
        # Simpan ke local
        vault[target_type] = data
        save_vault(vault)
        print(f"{GREEN}[+] Data tersimpan di local Termux.{RESET}")
    return data

def header():
    os.system('clear')
    print(f"{MAGENTA}======================================================{RESET}")
    print(f"{GREEN}   Ucenk D-Tech - Private Management System          {RESET}")
    print(f"{WHITE}      (Data stored locally in Termux Vault)          {RESET}")
    print(f"{MAGENTA}======================================================{RESET}")

def pause():
    input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

# ---------- ENGINE KONEKSI ----------

def run_mt_cmd(cmd):
    creds = get_credentials("mikrotik")
    ssh_base = f"sshpass -p '{creds['pass']}' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 {creds['user']}@{creds['ip']}"
    os.system(f"{ssh_base} '{cmd}'")

def run_olt_cmds(cmds):
    creds = get_credentials("olt")
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:", timeout=5); tn.write(creds['user'].encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=5); tn.write(creds['pass'].encode('ascii') + b"\n")
        tn.write(b"terminal length 0\n")
        res = ""
        for c in cmds:
            tn.write(c.encode('ascii') + b"\n")
            res += tn.read_until(b"ZXAN#", timeout=15).decode('ascii')
        tn.write(b"exit\n")
        return res
    except Exception as e: return f"{RED}Error: {e}{RESET}"

# ---------- MAIN MENU ----------

def main():
    while True:
        header()
        print(f"{GREEN} 1. Monitor Traffic Interface   {CYAN} 2. User Aktif Hotspot")
        print(f"{YELLOW} 3. Hapus Voucher Expired       {RED} 4. Cek DHCP Alert")
        print(f"{MAGENTA}------------------------------------------------------")
        print(f"{MAGENTA} 15. OLT: List ONU Aktif        {BLUE} 16. OLT: Optical Power")
        print(f"{CYAN} 88. Fix Permission Mikhmon     {WHITE} 99. Reset Local Data (Logout)")
        print(f"{RED}  0. Keluar")
        
        c = input(f"\n{WHITE}Pilih Menu: {RESET}").strip()

        if c == '1': run_mt_cmd("/interface monitor-traffic [find] once") ; pause()
        elif c == '2': run_mt_cmd("/ip hotspot active print") ; pause()
        elif c == '3': run_mt_cmd("/ip hotspot user remove [find where comment~\"vc-\" and uptime=limit-uptime]") ; pause()
        elif c == '4': run_mt_cmd("/ip dhcp-server alert print") ; pause()
        elif c == '15':
            slot = input("Masukkan Slot: ")
            print(run_olt_cmds([f"show pon onu information gpon-olt_1/{slot}/1"])) ; pause()
        elif c == '99':
            if os.path.exists(VAULT_FILE):
                os.remove(VAULT_FILE)
                print(f"{RED}Data local dihapus!{RESET}")
            time.sleep(1)
        elif c == '0': break
        elif c == '88': os.system("chmod -R 755 $HOME/mikhmon") ; time.sleep(1)

if __name__ == "__main__":
    main()
