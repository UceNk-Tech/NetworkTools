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
# FUNGSI-FUNGSI (MIKROTIK & OLT)
# =====================================================

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
            # Revisi Menu 4: Menghapus Script yang mengandung nama mikhmon
            print(f"{YELLOW}[*] Menghapus Laporan/Script Mikhmon...{RESET}")
            scripts = api.get_resource('/system/script')
            all_scripts = scripts.get()
            count = 0
            for s in all_scripts:
                if "mikhmon" in s.get('name', '').lower():
                    scripts.remove(id=s.get('id'))
                    count += 1
            print(f"{GREEN}[V] Berhasil menghapus {count} script mikhmon.{RESET}")
        
        conn.disconnect()
    except Exception as e: print(f"{RED}Error: {e}{RESET}")

def run_olt_telnet_onu():
    creds = get_credentials("olt")
    try:
        # Revisi Menu 9: Input bebas (Slot/PON/ID) dan kirim murni ke OLT
        print(f"\n{CYAN}Contoh: 1/1/1 (untuk cek 1 ONU){RESET}")
        target = input(f"{CYAN} Masukkan nomor: {RESET}").strip()
        if not target: return
        
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:"); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:"); tn.write(creds['pass'].encode() + b"\n")
        time.sleep(1); tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")
        
        # Mengirim perintah murni sesuai input Ucenk
        cmd = f"show pon onu information gpon-olt_1/{target}\n"
        print(f"{YELLOW}[*] Mengirim: {cmd.strip()}{RESET}")
        
        tn.write(cmd.encode('ascii'))
        time.sleep(1.5)
        
        out = tn.read_very_eager().decode('ascii', errors='ignore')
        print(f"\n{WHITE}{out}{RESET}")
        tn.close()
    except Exception as e: print(f"{RED}Error OLT: {e}{RESET}")

def run_olt_config_onu():
    creds = get_credentials("olt")
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:"); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:"); tn.write(creds['pass'].encode() + b"\n")
        time.sleep(1); tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")

        print(f"\n{YELLOW}[*] Mencari ONU uncfg...{RESET}")
        tn.write(b"show gpon onu uncfg\n")
        time.sleep(2)
        print(f"{WHITE}{tn.read_very_eager().decode()}{RESET}")
        
        print(f"{MAGENTA}==== REGISTRASI ONU BARU ===={RESET}")
        target = input(f"{CYAN}Masukkan Koordinat (Slot/PON/ID, misal 2/1/1): {RESET}").strip()
        if not target or "/" not in target: return
        s, p, oid = target.split("/")
        
        mode = "Hotspot" if input(f"Mode (1. Hotspot / 2. PPPoE): ").strip() == "1" else "PPPoE"
        sn = input("SN ONU: ").strip()
        vlan = input("VLAN ID: ").strip()
        name = input("Nama: ").strip()
        onu_type = input("Type (ALL): ").strip() or "ALL"
        
        cmds = ["conf t", f"interface gpon-olt_1/{s}/{p}", f"onu {oid} type {onu_type} sn {sn}", "exit",
                f"interface gpon-onu_1/{s}/{p}:{oid}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1",
                f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit",
                f"pon-onu-mng gpon-onu_1/{s}/{p}:{oid}", f"service 1 gemport 1 vlan {vlan}"]
        
        if mode == "Hotspot":
            cmds.append(f"vlan port wifi_0/1 mode gtag vlan {vlan}")
            for i in range(1, 5): cmds.append(f"vlan port eth_0/{i} mode tag vlan {vlan}")
        else:
            u, pw = input("User PPPoE: ").strip(), input("Pass PPPoE: ").strip()
            cmds.append(f"wan-ip mode pppoe username {u} password {pw} vlan-profile pppoe host 1")
        
        cmds.extend(["security-mgmt 212 state enable mode forward protocol web", "end", "write"])
        for cmd in cmds: tn.write(cmd.encode() + b"\n"); time.sleep(0.3)
        print(f"{GREEN}[V] Berhasil!{RESET}"); tn.close()
    except Exception as e: print(f"{RED}Error: {e}{RESET}")

# =====================================================
# TAMPILAN DASHBOARD
# =====================================================

def show_sticky_header():
    os.system('clear')
    os.system('echo "======================================================" | lolcat')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat')
    os.system('echo "      Author: Ucenk  |  Premium Network Management System" | lolcat')
    os.system('echo "======================================================" | lolcat')
    os.system('neofetch --ascii_distro ubuntu')
    
    print(f"{YELLOW}--- MIKROTIK TOOLS ---{RESET}")
    print(f"1. Jalankan Mikhmon Server        5. Bandwidth Usage Report")
    print(f"2. Total User Aktif Hotspot       6. Backup & Restore Config")
    print(f"3. Cek DHCP Alert (Rogue)         7. SNMP Monitoring")
    print(f"4. Hapus Laporan Mikhmon          8. Log Viewer MikroTik")
    
    print(f"\n{YELLOW}--- OLT TOOLS ---{RESET}")
    print(f"9. Lihat ONU Terdaftar            13. Alarm & Event Viewer")
    print(f"10. Konfigurasi ONU (ZTE/FH)      14. Backup & Restore OLT")
    print(f"11. Reset ONU                     15. Traffic Report per PON")
    print(f"12. Port & VLAN Config            16. Auto Audit Script")
    
    print(f"\n{YELLOW}--- NETWORK TOOLS ---{RESET}")
    print(f"17. Speedtest CLI                 20. Ping & Traceroute")
    print(f"18. Nmap Scan                     21. DNS Tools")
    print(f"19. MAC Lookup                    22. Update-tools")
    print(f"{MAGENTA}0. Keluar{RESET}")
    os.system('echo "======================================================" | lolcat')

def main():
    while True:
        show_sticky_header()
        c = input(f"{CYAN}Pilih Nomor: {RESET}").strip()
        if c == '1':
            m_dir = os.path.expanduser("~/mikhmonv3")
            tmp, sess = os.path.expanduser("~/tmp"), os.path.expanduser("~/session_mikhmon")
            if not os.path.exists(m_dir): os.system(f"git clone https://github.com/laksa19/mikhmonv3.git {m_dir}")
            os.system(f"mkdir -p {tmp} {sess}")
            with open(os.path.join(tmp, "custom.ini"), "w") as f: f.write(f"opcache.enable=0\nsession.save_path=\"{sess}\"\n")
            os.system("fuser -k 8080/tcp > /dev/null 2>&1")
            os.system(f'export PHP_INI_SCAN_DIR={tmp}; php -S 127.0.0.1:8080 -t {m_dir}')
        elif c in ['2', '3', '4']: run_mt(c)
        elif c == '9': run_olt_telnet_onu()
        elif c == '10': run_olt_config_onu()
        elif c == '22':
            os.system('cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh')
            break
        elif c == '0': break
        input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

if __name__ == "__main__": main()
