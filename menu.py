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

# Handler untuk library requests
try:
    import requests
except ImportError:
    print("\033[31m[!] Library 'requests' belum ada. Menginstall otomatis...\033[0m")
    os.system("pip install requests --break-system-packages")
    import requests

# Cek dependensi sistem
try:
    import telnetlib
except ImportError:
    print("telnetlib tidak ditemukan.")
    sys.exit(1)

try:
    import routeros_api
except ImportError:
    print("Install routeros-api: pip install routeros-api --break-system-packages")
    sys.exit(1)

# Warna ANSI
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
CYAN    = "\033[36m"
MAGENTA = "\033[35m"
WHITE   = "\033[37m"
RESET   = "\033[0m"

VAULT_FILE = os.path.join(os.path.dirname(__file__), "vault_session.json")

# --- DATABASE INTERNAL BRAND ---
BRAND_MAP = {
    "94:A6:7E": "TP-Link", "F4:F2:6D": "TP-Link", "00:0C:42": "MikroTik", 
    "48:8F:5A": "ZTE", "D0:16:B4": "ZTE", "CC:2D:21": "Huawei",
    "70:A8:E3": "Tenda", "C0:25:E9": "TOTOLINK"
}

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
        print(f" Profile Aktif: {GREEN}{vault.get('active_profile', 'BELUM ADA')}{RESET}")
        profiles = vault.get("profiles", {})
        for i, p_name in enumerate(profiles.keys(), 1):
            status = f"{GREEN}[Aktif]{RESET}" if p_name == vault.get('active_profile') else ""
            print(f" {i}. {p_name} {status}")
        print(f"\n{CYAN}[A] Tambah  [S] Pilih  [D] Hapus  [0] Kembali{RESET}")
        opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").lower()
        if opt == 'a':
            name = input("Nama Profile: ").strip()
            if name:
                m_ip = input("MikroTik IP: "); m_user = input("User: "); m_pass = getpass.getpass("Pass: ")
                o_ip = input("OLT IP: "); o_user = input("User: "); o_pass = getpass.getpass("Pass: ")
                o_brand = input("Brand (zte/fiberhome): ").lower() or "zte"
                profiles[name] = {"mikrotik": {"ip": m_ip, "user": m_user, "pass": m_pass}, "olt": {"ip": o_ip, "user": o_user, "pass": o_pass, "brand": o_brand}}
                vault["profiles"] = profiles; vault["active_profile"] = name; save_vault(vault)
        elif opt == 's':
            name = input("Nama Profile: ").strip()
            if name in profiles: vault["active_profile"] = name; save_vault(vault); break
        elif opt == '0': break

def get_credentials(target_type):
    vault = load_vault()
    active = vault.get("active_profile")
    if not active: return None
    return vault["profiles"][active].get(target_type)

def telnet_olt_execute(creds, commands):
    if not creds: return None
    brand = creds.get('brand', 'zte').lower()
    prompt = "ZXAN#" if brand == 'zte' else "OLT#"
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:", timeout=5); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:", timeout=5); tn.write(creds['pass'].encode() + b"\n")
        tn.write(b"terminal length 0\n")
        output = ""
        for cmd in commands:
            tn.write((cmd + "\n").encode()); time.sleep(1)
            output += tn.read_very_eager().decode('utf-8', errors='ignore')
        tn.close(); return output.strip()
    except Exception as e: return f"Error: {e}"

# --- 1-8 MIKROTIK TOOLS (ORISINAL) ---
def run_mikhmon():
    mikhmon_path = os.path.expanduser("~/mikhmonv3")
    session_path = os.path.expanduser("~/session_mikhmon")
    tmp_path = os.path.expanduser("~/tmp")
    if not os.path.exists(mikhmon_path): os.system(f"git clone https://github.com/laksa19/mikhmonv3.git {mikhmon_path}")
    os.makedirs(session_path, exist_ok=True); os.makedirs(tmp_path, exist_ok=True)
    with open(os.path.join(tmp_path, "custom.ini"), "w") as f:
        f.write("opcache.enable=0\nsession.save_path=\""+session_path+"\"\nsys_temp_dir=\""+tmp_path+"\"\ndisplay_errors=Off\n")
    os.system("fuser -k 8080/tcp > /dev/null 2>&1")
    print(f"{GREEN}[!] Mikhmon Aktif di Port 8080{RESET}")
    os.system(f"export PHP_INI_SCAN_DIR={tmp_path} && php -S 127.0.0.1:8080 -t {mikhmon_path}")

def mikrotik_hotspot_active():
    creds = get_credentials("mikrotik")
    if not creds: return
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = conn.get_api(); active = api.get_resource('/ip/hotspot/active').get()
        print(f"\n{GREEN}Total Aktif: {len(active)}{RESET}")
        conn.disconnect()
    except Exception as e: print(e)

def cek_dhcp_rogue():
    creds = get_credentials("mikrotik")
    if not creds: return
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = conn.get_api(); alerts = api.get_resource('/ip/dhcp-server/alert').get()
        for al in alerts:
            mac = al.get('unknown-server')
            if mac: print(f"{RED}Rogue: {mac} | Brand: {get_brand(mac)}{RESET}")
        conn.disconnect()
    except Exception as e: print(e)

def hapus_laporan_mikhmon():
    creds = get_credentials("mikrotik")
    if not creds: return
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = conn.get_api(); resource = api.get_resource('/system/script')
        scripts = [s for s in resource.get() if 'mikhmon' in s.get('name', '').lower()]
        for s in scripts: resource.remove(id=s['id'])
        print(f"{GREEN}Laporan dibersihkan.{RESET}"); conn.disconnect()
    except Exception as e: print(e)

# --- 9-18 OLT TOOLS (REVISI NOMOR) ---
def list_onu_aktif(): # Menu 9
    creds = get_credentials("olt"); p = input("Port (1/1/1): ")
    brand = creds.get('brand', 'zte').lower()
    cmds = [f"show pon onu information gpon-olt_{p}"] if brand == 'zte' else [f"show onu status port {p}"]
    print(telnet_olt_execute(creds, cmds))

def monitor_optical_power(): # Menu 10 (Sesuai kode awal kamu untuk registrasi/scan)
    print(f"{CYAN}Menjalankan Konfigurasi ONU (ZTE/FH)...{RESET}")

def reset_onu(): # Menu 11 (REVISI)
    creds = get_credentials("olt"); t = input("Slot/Port/ID (1/1/1): ")
    try:
        s, p, oid = t.split("/")
        cmds = ["conf t", f"interface gpon-olt_1/{s}/{p}", f"onu {oid} restart", "end"]
        print(telnet_olt_execute(creds, cmds))
    except: print("Format salah!")

def delete_onu(): # Menu 12 (BARU)
    creds = get_credentials("olt"); t = input("Slot/Port/ID (1/1/1): ")
    brand = creds.get('brand', 'zte').lower()
    try:
        s, p, oid = t.split("/")
        if brand == 'zte':
            cmds = ["conf t", f"interface gpon-olt_1/{s}/{p}", f"no onu {oid}", "end", "write"]
        else:
            cmds = ["conf t", f"interface gpon-olt_1/{s}/{p}", f"onu {oid} delete", "end", "write"]
        print(telnet_olt_execute(creds, cmds))
    except: print("Format salah!")

def cek_power_optic(): # Menu 13 (BARU)
    creds = get_credentials("olt"); p = input("Port/ID (1/1/1:1): ")
    brand = creds.get('brand', 'zte').lower()
    cmds = [f"show pon optical-power gpon-onu_{p}"] if brand == 'zte' else [f"show onu optical-info {p}"]
    print(telnet_olt_execute(creds, cmds))

def port_vlan_config(): # Menu 14 (BARU)
    creds = get_credentials("olt"); p = input("ONU (1/1/1:1): "); v = input("VLAN ID: ")
    cmds = ["conf t", f"pon-onu-mng gpon-onu_{p}", f"vlan port eth_0/1 mode tag vlan {v}", "end", "write"]
    print(telnet_olt_execute(creds, cmds))

# --- 17-25 NETWORK TOOLS ---
def net_port_scanner(): # Menu 20
    target = input("Target IP: "); os.system(f"nmap -F {target}")

def net_whatmyip(): # Menu 22
    try: print(f"{CYAN}IP Publik: {requests.get('https://ifconfig.me').text.strip()}{RESET}")
    except: print("Gagal cek IP.")

def net_ping_trace(): # Menu 23
    target = input("Host/IP: "); os.system(f"ping -c 4 {target}; traceroute {target}")

def show_menu():
    v = load_vault(); prof = v.get("active_profile", "None")
    os.system('clear')
    print(f"{WHITE}Aktif Profile: {GREEN}{prof}{RESET}")
    print(f"                                    {CYAN}--- MIKROTIK TOOLS ---{RESET}")
    print("1. Jalankan Mikhmon Server          5. Bandwidth Usage Report")
    print("2. Total User Aktif Hotspot         6. Backup & Restore MikroTik")
    print("3. Cek DHCP Alert (Rogue)           7. SNMP Monitoring")
    print("4. Hapus Laporan Mikhmon            8. Log Viewer MikroTik")
    print(f"\n                                    {CYAN}--- OLT TOOLS ---{RESET}")
    print("9. Lihat ONU Terdaftar              14. Port & VLAN Config")
    print("10. Konfigurasi ONU (ZTE/FH)        15. Alarm & Event Viewer")
    print("11. Reset ONU                       16. Backup & Restore OLT")
    print("12. Delete ONU                      17. Traffic Report per PON")
    print("13. Cek Status Power Optic          18. Auto Audit Script")
    print(f"\n                                    {CYAN}--- NETWORK TOOLS ---{RESET}")
    print("17. Speedtest CLI                   22. WhatMyIP")
    print("18. Nmap Scan                       23. Ping & Traceroute")
    print("19. MAC Lookup                      24. DNS Tools")
    print("20. Port Scaner                     25. Update-Tools")
    print("21. Mac Lookup")
    print(f"\n{YELLOW}99. Profile Setting{RESET}")
    print(f"{MAGENTA}0. Exit{RESET}")

def main():
    while True:
        show_menu()
        c = input(f"\n{YELLOW}Pilih Nomor: {RESET}").strip()
        if c == '1': run_mikhmon()
        elif c == '2': mikrotik_hotspot_active()
        elif c == '3': cek_dhcp_rogue()
        elif c == '4': hapus_laporan_mikhmon()
        elif c == '9': list_onu_aktif()
        elif c == '10': monitor_optical_power()
        elif c == '11': reset_onu()
        elif c == '12': delete_onu()
        elif c == '13': cek_power_optic()
        elif c == '14': port_vlan_config()
        elif c == '17': os.system("speedtest-cli --simple")
        elif c == '18': os.system(f"nmap {input('Target: ')}")
        elif c == '20': net_port_scanner()
        elif c == '22': net_whatmyip()
        elif c == '23': net_ping_trace()
        elif c == '99': manage_profiles()
        elif c == '0': sys.exit()
        input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__": main()
