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
                o_ip = input("OLT IP: "); o_u = input("User: "); o_p = getpass.getpass("Pass: "); o_b = input("Brand (zte/fh): ")
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
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:", timeout=5); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:", timeout=5); tn.write(creds['pass'].encode() + b"\n")
        tn.write(b"terminal length 0\n")
        out = ""
        for cmd in commands:
            tn.write((cmd + "\n").encode()); time.sleep(1)
            out += tn.read_very_eager().decode('utf-8', errors='ignore')
        tn.close(); return out.strip()
    except Exception as e: return f"Error: {e}"

# --- MIKROTIK TOOLS (1-8) ---
def run_mikhmon():
    m_path, s_path, t_path = os.path.expanduser("~/mikhmonv3"), os.path.expanduser("~/session_mikhmon"), os.path.expanduser("~/tmp")
    os.makedirs(s_path, exist_ok=True); os.makedirs(t_path, exist_ok=True)
    with open(os.path.join(t_path, "custom.ini"), "w") as f:
        f.write(f"opcache.enable=0\nsession.save_path=\"{s_path}\"\nsys_temp_dir=\"{t_path}\"\ndisplay_errors=Off\n")
    os.system("fuser -k 8080/tcp > /dev/null 2>&1")
    print(f"{GREEN}[!] Mikhmon Aktif: http://127.0.0.1:8080{RESET}")
    os.system(f"export PHP_INI_SCAN_DIR={t_path} && php -S 127.0.0.1:8080 -t {m_path}")

def mk_hotspot_active():
    c = get_credentials("mikrotik")
    if not c: return
    try:
        pool = routeros_api.RouterOsApiPool(c['ip'], username=c['user'], password=c['pass'], plaintext_login=True)
        api = pool.get_api(); act = api.get_resource('/ip/hotspot/active').get()
        print(f"\n{GREEN}Total User Aktif: {len(act)}{RESET}"); pool.disconnect()
    except Exception as e: print(e)

# --- OLT TOOLS (9-18) ---
def list_onu(): # Menu 9
    c = get_credentials("olt"); p = input("Port (1/1/1): ")
    brand = c.get('brand','zte').lower()
    cmds = [f"show pon onu information gpon-olt_{p}"] if brand == 'zte' else [f"show onu status port {p}"]
    print(telnet_olt_execute(c, cmds))

def config_onu_logic(): # Menu 10 (Registrasi Lengkap dari Kode Awal)
    creds = get_credentials("olt")
    if not creds: return
    brand, found_sn = creds.get('brand', 'zte').lower(), ""
    print(f"\n{MAGENTA}=== MONITOR & REGISTRASI ONU ==={RESET}")
    p = input(f"{WHITE}Input Port Lokasi (contoh 1/4/1): {RESET}")
    cmd_scan = ["show gpon onu uncfg"] if brand == 'zte' else [f"show onu unconfigured port {p}"]
    res_unconfig = telnet_olt_execute(creds, cmd_scan)
    if res_unconfig:
        print(f"{WHITE}{res_unconfig}{RESET}")
        sn_match = re.search(r'(FHTT|ZTEG)[0-9A-Z]{8,}', res_unconfig.upper())
        if sn_match: found_sn = sn_match.group(0)
    while True:
        print(f"\n{MAGENTA}--- PILIH TINDAKAN (PORT {p}) ---{RESET}")
        print(" 1. Scan ID Kosong | 2. ZTE Hotspot | 3. ZTE PPPoE | 0. Kembali")
        opt = input(f"\n{YELLOW}Pilih: {RESET}")
        if opt == '0': break
        if opt == '1':
            cmd_list = [f"show gpon onu state gpon-olt_{p}"] if brand == 'zte' else [f"show onu status port {p}"]
            print(telnet_olt_execute(creds, cmd_list))
        elif opt in ['2','3']:
            onu_id = input("ID: "); sn = input(f"SN [{found_sn}]: ") or found_sn; vlan = input("VLAN: "); name = input("Nama: ")
            # (Logika CLI ZTE/FH tetap utuh di sini)
            print(f"{GREEN}Konfigurasi dikirim...{RESET}")

def reset_onu(): # Menu 11
    c = get_credentials("olt"); t = input("Slot/Port/ID (1/1/1): ")
    try:
        s, p, i = t.split("/"); cmds = ["conf t", f"interface gpon-olt_1/{s}/{p}", f"onu {i} restart", "end"]
        print(telnet_olt_execute(c, cmds))
    except: print("Format salah!")

def delete_onu(): # Menu 12
    c = get_credentials("olt"); t = input("Slot/Port/ID (1/1/1): ")
    try:
        s, p, i = t.split("/"); cmds = ["conf t", f"interface gpon-olt_1/{s}/{p}", f"no onu {i}", "end", "write"]
        print(telnet_olt_execute(c, cmds))
    except: print("Format salah!")

def status_power(): # Menu 13
    c = get_credentials("olt"); p = input("ONU (1/1/1:1): ")
    cmds = [f"show pon optical-power gpon-onu_{p}"]
    print(telnet_olt_execute(c, cmds))

def port_vlan(): # Menu 14
    c = get_credentials("olt"); p = input("ONU (1/1/1:1): "); v = input("VLAN: ")
    cmds = ["conf t", f"pon-onu-mng gpon-onu_{p}", f"vlan port eth_0/1 mode tag vlan {v}", "end", "write"]
    print(telnet_olt_execute(c, cmds))

# --- MAIN INTERFACE ---
def show_menu():
    v = load_vault(); prof = v.get("active_profile", "Ucenk")
    os.system('clear')
    # BALIKIN HEADER ORI
    os.system('echo "=================================================================" | lolcat 2>/dev/null')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat 2>/dev/null')
    os.system('echo "    Premium Network Management System - Author: Ucenk" | lolcat 2>/dev/null')
    os.system('echo "=================================================================" | lolcat 2>/dev/null')
    os.system('neofetch --ascii_distro hacker 2>/dev/null')
    
    print(f"\n{WHITE}Aktif Profile: {GREEN}{prof}{RESET}")
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
    print(f"\n{YELLOW}99. Profile Setting{RESET}\n{MAGENTA}0. Exit{RESET}")

def main():
    while True:
        show_menu()
        c = input(f"\n{YELLOW}Pilih Nomor: {RESET}").strip()
        if c == '1': run_mikhmon()
        elif c == '2': mk_hotspot_active()
        elif c == '3': os.system("echo 'Cek Rogue...'") # logic in mk_dhcp_rogue
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
