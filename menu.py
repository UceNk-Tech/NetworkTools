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

# =====================================================
# FUNGSI OLT
# =====================================================

def run_olt_telnet_onu():
    creds = get_credentials("olt")
    try:
        target = input(f"{CYAN} Input nomor (Slot/PON/ID): {RESET}").strip()
        if not target: return
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:"); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:"); tn.write(creds['pass'].encode() + b"\n")
        time.sleep(1); tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")
        command = f"show pon onu information gpon-olt_{target}\n"
        tn.write(command.encode('ascii'))
        time.sleep(1.5)
        print(f"\n{WHITE}{tn.read_very_eager().decode('ascii', errors='ignore')}{RESET}")
        tn.close()
    except Exception as e: print(f"{RED}Error OLT: {e}{RESET}")

def run_olt_reset_onu():
    creds = get_credentials("olt")
    try:
        # 1. Input Koordinat (misal 1/1/1)
        coord = input(f"{CYAN}Masukkan Koordinat (Slot/PON/Port, misal 1/1/1): {RESET}").strip()
        if not coord: return
        
        # 2. Input ID ONU (misal 1)
        oid = input(f"{CYAN}Masukkan ID ONU (contoh: 1): {RESET}").strip()
        if not oid: return

        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:"); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:"); tn.write(creds['pass'].encode() + b"\n")
        time.sleep(1); tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")

        # 3. PERBAIKAN: Format perintah show yang benar untuk spesifik ID
        # Format: show pon onu information gpon-olt_1/1/1 onu 1
        show_cmd = f"show pon onu information gpon-olt_{coord} onu {oid}\n"
        
        print(f"\n{YELLOW}[*] Menampilkan detail ONU ID {oid} di port {coord}...{RESET}")
        tn.write(show_cmd.encode('ascii'))
        time.sleep(1.5)
        print(f"{WHITE}{tn.read_very_eager().decode('ascii', errors='ignore')}{RESET}")

        # 4. Peringatan dan Konfirmasi
        # Untuk management, formatnya tetap pakai gpon-onu_1/1/1:1
        mng_path = f"gpon-onu_1/{coord}:{oid}"
        
        print(f"\n{RED}======================================================")
        print(f" [!] PERINGATAN: ONU {mng_path} AKAN DI-REBOOT!")
        print(f"======================================================{RESET}")
        confirm = input(f"{YELLOW}Ketik 'y' untuk REBOOT atau 'n' untuk BATAL: {RESET}").lower()
        
        if confirm == 'y':
            tn.write(f"pon-onu-mng {mng_path}\nreboot\n".encode())
            print(f"{GREEN}[V] Perintah Reboot berhasil dikirim!{RESET}")
        else:
            print(f"{BLUE}[i] Operasi dibatalkan.{RESET}")
        
        tn.close()
    except Exception as e: print(f"{RED}Error OLT: {e}{RESET}")

# --- FUNGSI LAIN TETAP SAMA ---
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
            script_resource = api.get_resource('/system/script')
            all_scripts = script_resource.get()
            targets = [s for s in all_scripts if "mikhmon" in s.get('name', '').lower() or "mikhmon" in s.get('comment', '').lower()]
            if not targets: print(f"{RED}[!] Tidak ditemukan script.{RESET}")
            else:
                confirm = input(f"\n{RED}Hapus {len(targets)} script? (y/n): {RESET}").lower()
                if confirm == 'y':
                    for s in targets: script_resource.remove(id=s.get('id'))
                    print(f"{GREEN}[V] Berhasil.{RESET}")
        conn.disconnect()
    except Exception as e: print(f"{RED}Error MT: {e}{RESET}")

def run_olt_config_onu():
    creds = get_credentials("olt")
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:"); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:"); tn.write(creds['pass'].encode() + b"\n")
        time.sleep(1); tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")
        tn.write(b"show gpon onu uncfg\n")
        time.sleep(2)
        print(f"{WHITE}{tn.read_very_eager().decode()}{RESET}")
        target = input(f"{CYAN}Masukkan Koordinat (Slot/PON/ID, misal 1/1/1): {RESET}").strip()
        if not target or "/" not in target: return
        s, p, oid = target.split("/")
        mode = "Hotspot" if input(f"Mode (1. Hotspot / 2. PPPoE): ").strip() == "1" else "PPPoE"
        sn, vlan, name = input("SN: ").strip(), input("VLAN: ").strip(), input("Nama: ").strip()
        cmds = ["conf t", f"interface gpon-olt_1/{s}/{p}", f"onu {oid} type ALL sn {sn}", "exit",
                f"interface gpon-onu_1/{s}/{p}:{oid}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1",
                f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit",
                f"pon-onu-mng gpon-onu_1/{s}/{p}:{oid}", f"service 1 gemport 1 vlan {vlan}"]
        if mode == "Hotspot":
            cmds.append(f"vlan port wifi_0/1 mode gtag vlan {vlan}")
            for i in range(1, 5): cmds.append(f"vlan port eth_0/{i} mode tag vlan {vlan}")
        else:
            u, pw = input("User: ").strip(), input("Pass: ").strip()
            cmds.append(f"wan-ip mode pppoe username {u} password {pw} vlan-profile pppoe host 1")
        cmds.extend(["end", "write"])
        for cmd in cmds: tn.write(cmd.encode() + b"\n"); time.sleep(0.3)
        print(f"{GREEN}[V] Berhasil!{RESET}"); tn.close()
    except Exception as e: print(f"{RED}Error: {e}{RESET}")

def show_sticky_header():
    os.system('clear')
    os.system('echo "======================================================" | lolcat')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat')
    os.system('echo "======================================================" | lolcat')
    print(f"{YELLOW}1. Mikhmon  2. User Aktif  3. DHCP Alert  4. Hapus Script")
    print(f"9. Lihat ONU  10. Config ONU  11. Reset ONU  22. Update  0. Keluar{RESET}")

def main():
    while True:
        show_sticky_header()
        c = input(f"{CYAN}Pilih Nomor: {RESET}").strip()
        if c == '1':
            os.system("fuser -k 8080/tcp > /dev/null 2>&1")
            os.system('php -S 127.0.0.1:8080 -t ~/mikhmonv3')
        elif c in ['2', '3', '4']: run_mt(c)
        elif c == '9': run_olt_telnet_onu()
        elif c == '10': run_olt_config_onu()
        elif c == '11': run_olt_reset_onu()
        elif c == '22':
            os.system('cd $HOME/NetworkTools && git pull && bash install.sh')
            break
        elif c == '0': break
        input(f"\n{YELLOW}Enter untuk kembali...{RESET}")

if __name__ == "__main__": main()
