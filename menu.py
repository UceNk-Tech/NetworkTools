#!/usr/bin/env python3
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

import re
import os
import time
import sys
import json
import getpass
from datetime import datetime
import telnetlib

# Handler library
try:
    import requests
except ImportError:
    os.system("pip install requests --break-system-packages")
    import requests

try:
    import routeros_api
except ImportError:
    os.system("pip install routeros-api --break-system-packages")
    import routeros_api

# Warna ANSI
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
CYAN    = "\033[36m"
MAGENTA = "\033[35m"
WHITE   = "\033[37m"
RESET   = "\033[0m"

VAULT_FILE = os.path.join(os.path.dirname(__file__), "vault_session.json")

# --- DATABASE BRAND (OUI) ---
BRAND_MAP = {"94:A6:7E": "TP-Link", "F4:F2:6D": "TP-Link", "00:0C:42": "MikroTik", "48:8F:5A": "ZTE"}

def get_brand(mac):
    if not mac or mac == "N/A": return "Unknown"
    prefix = mac.upper()[:8]
    if prefix in BRAND_MAP: return BRAND_MAP[prefix]
    try:
        resp = requests.get(f"https://api.maclookup.app/v2/macs/{mac}", timeout=2)
        if resp.status_code == 200: return resp.json().get('company', "Unknown Brand")
    except: pass
    return "Unknown/Offline"

# --- SISTEM PROFILE ---
def load_vault():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'r') as f: return json.load(f)
        except: return {"active_profile": None, "profiles": {}}
    return {"active_profile": None, "profiles": {}}

def save_vault(data):
    with open(VAULT_FILE, 'w') as f: json.dump(data, f, indent=4)

def manage_profiles():
    while True:
        vault = load_vault()
        os.system('clear')
        print(f"{MAGENTA}======================================================{RESET}")
        print(f"{WHITE}              SETTING PROFILE JARINGAN               {RESET}")
        print(f"{MAGENTA}======================================================{RESET}")
        profiles = vault.get("profiles", {})
        for i, p_name in enumerate(profiles.keys(), 1):
            status = f"{GREEN}[Aktif]{RESET}" if p_name == vault.get('active_profile') else ""
            print(f" {i}. {p_name} {status}")
        print(f"\n{CYAN}[A] Tambah  [S] Pilih  [D] Hapus  [0] Kembali{RESET}")
        opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").lower()
        if opt == 'a':
            name = input("Nama Profile: ").strip()
            if name:
                m_ip = input("MikroTik IP: "); m_u = input("User: "); m_p = getpass.getpass("Pass: ")
                o_ip = input("OLT IP: "); o_u = input("User: "); o_p = getpass.getpass("Pass: "); o_b = input("Brand (zte/fiberhome): ")
                profiles[name] = {"mikrotik":{"ip":m_ip,"user":m_u,"pass":m_p}, "olt":{"ip":o_ip,"user":o_u,"pass":o_p,"brand":o_b}}
                vault["profiles"] = profiles; vault["active_profile"] = name; save_vault(vault)
        elif opt == 's':
            name = input("Nama Profile: ").strip()
            if name in profiles: vault["active_profile"] = name; save_vault(vault); break
        elif opt == '0': break

def get_credentials(target):
    v = load_vault(); act = v.get("active_profile")
    if not act: return None
    return v["profiles"][act].get(target)

def telnet_olt_execute(creds, commands):
    if not creds: return None
    prompt = "ZXAN#" if creds.get('brand') == 'zte' else "OLT#"
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:", timeout=5); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:", timeout=5); tn.write(creds['pass'].encode() + b"\n")
        tn.read_until(prompt.encode(), timeout=5)
        tn.write(b"terminal length 0\n")
        time.sleep(0.5)
        out = ""
        for cmd in commands:
            tn.write((cmd + "\n").encode())
            time.sleep(1.5 if "show" in cmd else 0.8)
            out += tn.read_very_eager().decode('utf-8', errors='ignore')
        tn.close(); return out.strip()
    except Exception as e: return f"Error Telnet: {e}"

# --- MIKROTIK TOOLS (1-8) ---
def run_mikhmon(): # Menu 1
    print(f"\n{CYAN}[+] Menyiapkan Mikhmon Server...{RESET}")
    mikhmon_path = os.path.expanduser("~/mikhmonv3")
    session_path = os.path.expanduser("~/session_mikhmon")
    tmp_path = os.path.expanduser("~/tmp")
    if not os.path.exists(mikhmon_path):
        print(f"{YELLOW}[*] Mendownload Mikhmon...{RESET}")
        os.system(f"git clone https://github.com/laksa19/mikhmonv3.git {mikhmon_path}")
    os.makedirs(session_path, exist_ok=True); os.makedirs(t_path := tmp_path, exist_ok=True)
    with open(os.path.join(t_path, "custom.ini"), "w") as f:
        f.write(f"opcache.enable=0\nsession.save_path=\"{session_path}\"\nsys_temp_dir=\"{t_path}\"\ndisplay_errors=Off\n")
    os.system("fuser -k 8080/tcp > /dev/null 2>&1")
    print(f"{GREEN}[!] Mikhmon Aktif: http://127.0.0.1:8080{RESET}")
    print(f"{RED}[!] Tekan Ctrl+C untuk Berhenti{RESET}\n")
    try:
        os.system(f"export PHP_INI_SCAN_DIR={t_path} && php -S 127.0.0.1:8080 -t {mikhmon_path}")
    except KeyboardInterrupt: print(f"\n{YELLOW}[-] Server dimatikan.{RESET}")

def mk_hotspot_active(): # Menu 2
    c = get_credentials("mikrotik")
    if not c: print(f"{RED}[!] Profile belum diset.{RESET}"); return
    try:
        pool = routeros_api.RouterOsApiPool(c['ip'], username=c['user'], password=c['pass'], plaintext_login=True)
        api = pool.get_api(); act = api.get_resource('/ip/hotspot/active').get()
        print(f"\n{GREEN}>>> TOTAL USER AKTIF: {len(act)} {RESET}")
        for user in act[:10]: print(f" - {user.get('user')} | IP: {user.get('address')}")
        pool.disconnect()
    except Exception as e: print(f"{RED}Error: {e}{RESET}")

def cek_dhcp_rogue(): # Menu 3
    creds = get_credentials("mikrotik")
    if not creds: return
    print(f"\n{CYAN}[+] Memeriksa Rogue DHCP...{RESET}")
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = conn.get_api(); alerts = api.get_resource('/ip/dhcp-server/alert').get()
        found = False
        for al in alerts:
            mac = al.get('unknown-server')
            if mac:
                found = True
                print(f"{RED}![ROGUE DETECTED] MAC: {mac} | Brand: {get_brand(mac)} | Int: {al.get('interface')}{RESET}")
        if not found: print(f"{GREEN}[✓] Kondisi Aman.{RESET}")
        conn.disconnect()
    except Exception as e: print(f"{RED}Error: {e}{RESET}")

def hapus_laporan_mikhmon(): # Menu 4
    creds = get_credentials("mikrotik")
    if not creds: return
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = conn.get_api(); res = api.get_resource('/system/script')
        scripts = [s for s in res.get() if 'mikhmon' in s.get('name','').lower()]
        if not scripts: print(f"{GREEN}[✓] Script Bersih!{RESET}")
        else:
            if input(f"{YELLOW}Hapus {len(scripts)} script? (y/n): {RESET}").lower() == 'y':
                for s in scripts: res.remove(id=s['id'])
                print(f"{GREEN}[✓] Berhasil dihapus.{RESET}")
        conn.disconnect()
    except Exception as e: print(e)

# --- OLT TOOLS (9-18) ---
def list_onu(): # Menu 9
    c = get_credentials("olt")
    if not c: return
    p = input(f"{WHITE}Input Port (contoh 1/3/1): {RESET}")
    brand = c.get('brand','zte').lower()
    cmds = ["terminal length 0", "end", f"show pon onu information gpon-olt_{p}"] if brand == 'zte' else ["terminal length 0", "end", f"show onu status port {p}"]
    print(f"\n{WHITE}==== DAFTAR ONU TERDAFTAR (PORT {p}) ===={RESET}")
    print(telnet_olt_execute(c, cmds))

def config_onu_logic(): # Menu 10
    creds = get_credentials("olt")
    if not creds: return
    brand, found_sn = creds.get('brand', 'zte').lower(), ""
    print(f"\n{MAGENTA}=== MONITOR & REGISTRASI ONU ==={RESET}")
    p = input(f"{WHITE}Input Port Lokasi (contoh 1/4/1): {RESET}")

    # Scan Unconfigured
    print(f"{CYAN}[+] Memeriksa ONU Unconfigured...{RESET}")
    cmd_scan = ["terminal length 0", "end", "show gpon onu uncfg"] if brand == 'zte' else ["terminal length 0", "end", f"show onu unconfigured port {p}"]
    res_unconfig = telnet_olt_execute(creds, cmd_scan)
    if res_unconfig and any(x in res_unconfig.upper() for x in ["FHTT", "ZTEG", "SN"]):
        print(f"{WHITE}{res_unconfig}{RESET}")
        sn_match = re.search(r'(FHTT|ZTEG)[0-9A-Z]{8,}', res_unconfig.upper())
        if sn_match: found_sn = sn_match.group(0); print(f"{GREEN}[✓] SN Ditemukan: {found_sn}{RESET}")

    while True:
        print(f"\n{MAGENTA}--- PILIH TINDAKAN (PORT {p}) ---{RESET}")
        print(" 1. Scan ID Kosong | 2. ZTE Hotspot | 3. ZTE PPPoE | 4. FH Hotspot | 5. FH PPPoE | 6. Power Optik | 0. Kembali")
        opt = input(f"\n{YELLOW}Pilih aksi: {RESET}")
        if opt == '0': break
        
        if opt == '1':
            cmd_list = ["terminal length 0", f"show gpon onu state gpon-olt_{p}"] if brand == 'zte' else ["terminal length 0", f"show onu status port {p}"]
            res_list = telnet_olt_execute(creds, cmd_list)
            if res_list:
                ids = sorted(list(set([int(x) for x in re.findall(r':(\d{1,3})\s+', res_list)])))
                max_id = max(ids) if ids else 0
                missing = [x for x in range(1, max_id + 1) if x not in ids]
                print(f"{YELLOW}ID Kosong: {missing if missing else 'None'}{RESET}")
                print(f"{GREEN}Saran ID Baru: {max_id + 1}{RESET}")
            continue

        if opt == '6':
            cmds = ["end", f"show pon optical-power gpon-olt_{p}"] if brand == 'zte' else ["end", f"show onu optical-power {p}"]
            print(telnet_olt_execute(creds, cmds)); continue

        if opt in ['2','3','4','5']:
            onu_id = input("ID: "); sn = input(f"SN [{found_sn}]: ") or found_sn; vlan = input("VLAN: "); name = input("Nama: ").replace(" ","_")
            cmds = []
            if opt == '2': # ZTE HOTSPOT
                cmds = ["conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit", f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit", f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}", f"vlan port wifi_0/1 mode tag vlan {vlan}", f"vlan port eth_0/1 mode tag vlan {vlan}", "security-mgmt 212 state enable mode forward protocol web", "end", "write"]
            elif opt == '3': # ZTE PPPOE
                u = input("User PPPoE: "); pw = input("Pass: ")
                cmds = ["conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit", f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit", f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}", f"wan-ip mode pppoe {u} password {pw} vlan-profile pppoe host 1", "end", "write"]
            elif opt in ['4','5']: # FH
                cmds = ["con t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit", f"interface gpon-onu_{p}:{onu_id}", f"name {name}", f"description 1$${name}$$", "tcont 1 profile server", "gemport 1 tcont 1", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit", f"pon-onu-mng gpon-onu_{p}:{onu_id}", "dhcp", "end", "write"]
            
            if cmds: print(telnet_olt_execute(creds, cmds)); print(f"{GREEN}[✓] Selesai!{RESET}"); break

def reset_onu(): # Menu 11
    creds = get_credentials("olt")
    if not creds: return
    brand = creds.get('brand', 'zte').lower()
    print(f"\n{RED}=== RESET ONU (SAFE MODE) ==={RESET}")
    port = input(f"{WHITE}Masukkan Port (1/1/1): {RESET}").strip()
    onu_id = input(f"{WHITE}Masukkan Nomor ONU (1): {RESET}").strip()
    if brand == 'zte':
        check_cmds = ["terminal length 0", "end", f"show gpon onu detail-info gpon-onu_{port}:{onu_id}"]
    else:
        check_cmds = ["terminal length 0", "end", f"show onu info port {port} ont {onu_id}"]
    output = telnet_olt_execute(creds, check_cmds)
    if output and "Invalid" not in output:
        print(f"\n{YELLOW}{output}{RESET}")
        confirm = input(f"\n{RED}Hapus ONU {port}:{onu_id} ini? (y/n): {RESET}").lower()
        if confirm == 'y':
            del_cmds = ["conf t", f"interface gpon-olt_{port}", f"no onu {onu_id}", "end", "write"]
            telnet_olt_execute(creds, del_cmds)
            print(f"{GREEN}[✓] ONU Berhasil dihapus dan tersimpan.{RESET}")
    else: print(f"{RED}[!] Data tidak ditemukan.{RESET}")

def delete_onu(): # Menu 12
    creds = get_credentials("olt")
    if not creds: return
    print(f"\n{RED}=== DELETE ONU (FAST TABLE VIEW) ==={RESET}")
    port = input(f"{WHITE}Port (1/3/1): {RESET}").strip()
    onu_id = input(f"{WHITE}ONU ID: {RESET}").strip()
    cmd = [f"show gpon onu state gpon-olt_{port} {onu_id}"]
    output = telnet_olt_execute(creds, cmd)
    if output:
        print(f"\n{WHITE}HASIL CEK ONU:{RESET}")
        print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
        for line in output.splitlines():
            if f"{port}:{onu_id}" in line: print(f"{YELLOW}{line}{RESET}")
        print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
        if input(f"{RED}Konfirmasi Hapus? (y/n): {RESET}").lower() == 'y':
            telnet_olt_execute(creds, ["conf t", f"interface gpon-olt_{port}", f"no onu {onu_id}", "end", "write"])
            print(f"{GREEN}[✓] ONU {port}:{onu_id} Terhapus.{RESET}")

def status_power(): # Menu 13
    creds = get_credentials("olt")
    if not creds: return
    brand = creds.get('brand', 'zte').lower()
    print(f"\n{CYAN}=== CEK OPTICAL POWER ONU (SMART VIEW) ==={RESET}")
    port = input(f"{WHITE}Port (contoh 1/1/1): {RESET}").strip()
    onu_id = input(f"{WHITE}ONU ID (contoh 1): {RESET}").strip()
    if brand == 'fiberhome': cmds_to_try = [f"show onu optical-power {port} {onu_id}"]
    else: cmds_to_try = [f"show pon optical-power gpon-onu_{port}:{onu_id}", f"show gpon onu detail-info gpon-onu_{port}:{onu_id}"]
    print(f"{CYAN}[*] Sedang berkomunikasi dengan OLT...{RESET}")
    output = ""
    for cmd in cmds_to_try:
        raw = telnet_olt_execute(creds, ["terminal length 0", "enable", cmd] if brand == 'zte' else ["terminal length 0", cmd])
        if raw and any(x in raw for x in ["dBm", "Power", "Voltage", "Temp"]):
            output = raw; break
        output = raw
    print(f"\n{WHITE}HASIL DIAGNOSA {brand.upper()} ONU {port}:{onu_id}:{RESET}")
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
    if "dBm" in output:
        print(f"{GREEN}[✓] STATUS: ONU ONLINE / DATA DITERIMA{RESET}")
        for line in output.splitlines():
            if "dBm" in line or any(x in line.lower() for x in ["temp", "volt", "input", "output"]): print(f"{YELLOW}{line.strip()}{RESET}")
    elif "offline" in output.lower() or "LOS" in output: print(f"{RED}[!] STATUS: ONU OFFLINE / LOS{RESET}")
    else: print(f"{RED}[!] Perintah Ditolak atau Format Salah.{RESET}\n{CYAN}{output}{RESET}")
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")

def port_vlan(): # Menu 14
    c = get_credentials("olt"); p = input("ONU (1/1/1:1): "); v = input("VLAN: ")
    cmds = ["conf t", f"pon-onu-mng gpon-onu_{p}", f"vlan port eth_0/1 mode tag vlan {v}", "end", "write"]
    print(telnet_olt_execute(c, cmds))

# --- MAIN INTERFACE ---
def show_menu():
    v = load_vault(); prof = v.get("active_profile", "Ucenk")
    os.system('clear')
    os.system('echo "=================================================================" | lolcat 2>/dev/null')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat 2>/dev/null')
    os.system('echo "    Premium Network Management System - Author: Ucenk" | lolcat 2>/dev/null')
    os.system('echo "=================================================================" | lolcat 2>/dev/null')
    os.system('neofetch --ascii_distro hacker 2>/dev/null')
    
    print(f"\n{WHITE}Aktif Profile: {GREEN}{prof}{RESET}")
    print(f"                                    {CYAN}--- MIKROTIK TOOLS ---{RESET}")
    print("1. Jalankan Mikhmon Server          5. Bandwidth Usage Report")
    print("2. Total User Aktif Hotspot          6. Backup & Restore MikroTik")
    print("3. Cek DHCP Alert (Rogue)            7. SNMP Monitoring")
    print("4. Hapus Laporan Mikhmon              8. Log Viewer MikroTik")
    print(f"\n                                    {CYAN}--- OLT TOOLS ---{RESET}")
    print("9. Lihat ONU Terdaftar              14. Port & VLAN Config")
    print("10. Konfigurasi ONU (ZTE/FH)        15. Alarm & Event Viewer")
    print("11. Reset ONU                       16. Backup & Restore OLT")
    print("12. Delete ONU                      17. Traffic Report per PON")
    print("13. Cek Status Power Optic          18. Auto Audit Script")
    print(f"\n                                    {CYAN}--- NETWORK TOOLS ---{RESET}")
    print("17. Speedtest CLI                    22. WhatMyIP")
    print("18. Nmap Scan                        23. Ping & Traceroute")
    print("19. MAC Lookup                       24. DNS Tools")
    print("20. Port Scaner                      25. Update-Tools")
    print(f"\n{YELLOW}99. Profile Setting{RESET}\n{MAGENTA}0. Exit{RESET}")

def main():
    while True:
        show_menu()
        c = input(f"\n{YELLOW}Pilih Nomor: {RESET}").strip()
        if c == '1': run_mikhmon()
        elif c == '2': mk_hotspot_active()
        elif c == '3': cek_dhcp_rogue()
        elif c == '4': hapus_laporan_mikhmon()
        elif c == '9': list_onu()
        elif c == '10': config_onu_logic()
        elif c == '11': reset_onu()
        elif c == '12': delete_onu()
        elif c == '13': status_power()
        elif c == '14': port_vlan()
        elif c == '17': os.system("speedtest-cli")
        elif c == '20': os.system(f"nmap -F {input('IP: ')}")
        elif c == '22': print(f"IP: {requests.get('https://ifconfig.me').text.strip()}")
        elif c == '99': manage_profiles()
        elif c == '0': sys.exit()
        input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__": main()
