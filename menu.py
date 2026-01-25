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

BRAND_MAP = {
    "94:A6:7E": "TP-Link", "F4:F2:6D": "TP-Link", "00:0C:42": "MikroTik", 
    "48:8F:5A": "ZTE", "D0:16:B4": "ZTE", "CC:2D:21": "Huawei",
    "70:A8:E3": "Tenda", "C0:25:E9": "TOTOLINK"
}

def get_brand(mac):
    if not mac or mac == "N/A": return "Unknown"
    prefix = mac.upper()[:8]
    if prefix in BRAND_MAP:
        return BRAND_MAP[prefix]
    try:
        resp = requests.get(f"https://api.maclookup.app/v2/macs/{mac}", timeout=2)
        if resp.status_code == 200:
            return resp.json().get('company', "Unknown Brand")
    except:
        pass
    return "Unknown/Offline"

# --- SISTEM PROFILE ---
def load_vault():
    if os.path.exists(VAULT_FILE):
        try:
            with open(VAULT_FILE, 'r') as f:
                return json.load(f)
        except:
            return {"active_profile": None, "profiles": {}}
    return {"active_profile": None, "profiles": {}}

def save_vault(data):
    with open(VAULT_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def manage_profiles():
    while True:
        vault = load_vault()
        os.system('clear')
        print(f"{MAGENTA}======================================================{RESET}")
        print(f"{WHITE}              SETTING PROFILE JARINGAN               {RESET}")
        print(f"{MAGENTA}======================================================{RESET}")
        print(f" Profile Aktif saat ini: {GREEN}{vault.get('active_profile', 'BELUM ADA')}{RESET}")
        print(f"{MAGENTA}------------------------------------------------------{RESET}")
        
        profiles = vault.get("profiles", {})
        if not profiles:
            print(f"{YELLOW} [!] Belum ada profile tersimpan.{RESET}")
        else:
            for i, p_name in enumerate(profiles.keys(), 1):
                status = f"{GREEN}[Aktif]{RESET}" if p_name == vault.get('active_profile') else ""
                print(f" {i}. {p_name} {status}")
        
        print(f"\n{CYAN}[A] Tambah Profile    [S] Pilih Profile    [D] Hapus    [0] Kembali{RESET}")
        opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").lower()
        
        if opt == 'a':
            name = input(f"\n{WHITE}Nama Profile (ex: Kantor_Pusat): {RESET}").strip()
            if name:
                print(f"{CYAN}--- Login MikroTik ---{RESET}")
                m_ip = input(" IP Address: ")
                m_user = input(" Username: ")
                m_pass = getpass.getpass(" Password: ")
                print(f"{CYAN}--- Login OLT ---{RESET}")
                o_ip = input(" IP Address: ")
                o_user = input(" Username: ")
                o_pass = getpass.getpass(" Password: ")
                o_brand = input(" Brand (zte/fiberhome): ").lower() or "zte"
                
                profiles[name] = {
                    "mikrotik": {"ip": m_ip, "user": m_user, "pass": m_pass},
                    "olt": {"ip": o_ip, "user": o_user, "pass": o_pass, "brand": o_brand}
                }
                vault["profiles"] = profiles
                vault["active_profile"] = name
                save_vault(vault)
                print(f"\n{GREEN}[+] Profile {name} Berhasil Disimpan!{RESET}")
                time.sleep(1.5)
        elif opt == 's':
            if not profiles: continue
            name = input(f"\n{WHITE}Ketik Nama Profile untuk diaktifkan: {RESET}").strip()
            if name in profiles:
                vault["active_profile"] = name
                save_vault(vault)
                print(f"{GREEN}[+] Switch ke Profile: {name}{RESET}"); time.sleep(1); break
            else:
                print(f"{RED}[!] Nama tidak ditemukan.{RESET}"); time.sleep(1)
        elif opt == 'd':
            if not profiles: continue
            name = input(f"\n{RED}Ketik Nama Profile yang akan dihapus: {RESET}").strip()
            if name in profiles:
                del profiles[name]
                if vault["active_profile"] == name: vault["active_profile"] = None
                save_vault(vault)
                print(f"{YELLOW}[-] Profile dihapus.{RESET}"); time.sleep(1)
        elif opt == '0':
            break

def get_credentials(target_type):
    vault = load_vault()
    active = vault.get("active_profile")
    if not active or active not in vault["profiles"]:
        return None
    return vault["profiles"][active].get(target_type)

def telnet_olt_execute(creds, commands):
    if not creds: return None
    prompt = "ZXAN#" if creds.get('brand') == 'zte' else "OLT#"
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=15)
        tn.read_until(b"Username:", timeout=5)
        tn.write(creds['user'].encode('utf-8') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(creds['pass'].encode('utf-8') + b"\n")
        tn.read_until(prompt.encode('utf-8'), timeout=5)
        tn.write(b"terminal length 0\n")
        time.sleep(0.5)
        output = ""
        for cmd in commands:
            tn.write((cmd + "\n").encode('utf-8'))
            time.sleep(1.5 if "show" in cmd else 0.5)
            output += tn.read_very_eager().decode('utf-8', errors='ignore')
        tn.close()
        return output.strip()
    except Exception as e:
        print(f"{RED}Error Telnet: {e}{RESET}")
        return None

# --- MIKROTIK TOOLS ---
def cek_dhcp_rogue():
    creds = get_credentials("mikrotik")
    if not creds: return
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = conn.get_api()
        alerts = api.get_resource('/ip/dhcp-server/alert').get()
        found = False
        for al in alerts:
            mac = al.get('unknown-server')
            if mac:
                found = True
                print(f"{RED}![ROGUE] MAC: {mac} | Brand: {get_brand(mac)}{RESET}")
        if not found: print(f"{GREEN}[✓] Kondisi Aman.{RESET}")
        conn.disconnect()
    except Exception as e: print(f"Error: {e}")

def run_mikhmon():
    mikhmon_path = os.path.expanduser("~/mikhmonv3")
    os.makedirs(mikhmon_path, exist_ok=True)
    os.system(f"php -S 127.0.0.1:8080 -t {mikhmon_path}")

def hapus_laporan_mikhmon():
    creds = get_credentials("mikrotik")
    if not creds: return
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = conn.get_api()
        res = api.get_resource('/system/script')
        m_scripts = [s for s in res.get() if 'mikhmon' in s.get('name', '').lower()]
        for s in m_scripts: res.remove(id=s['id'])
        print(f"{GREEN}[✓] {len(m_scripts)} Script Laporan dibersihkan.{RESET}")
        conn.disconnect()
    except Exception as e: print(f"Error: {e}")

def mikrotik_hotspot_active():
    creds = get_credentials("mikrotik")
    if not creds: return
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = conn.get_api()
        active = api.get_resource('/ip/hotspot/active').get()
        print(f"{GREEN}Total User Aktif: {len(active)}{RESET}")
        conn.disconnect()
    except Exception as e: print(f"Error: {e}")

# --- OLT TOOLS ---
def list_onu_aktif():
    creds = get_credentials("olt")
    p = input("Input Port (1/3/1): ")
    brand = creds.get('brand', 'zte')
    cmd = [f"show pon onu information gpon-olt_{p}"] if brand == 'zte' else [f"show onu status port {p}"]
    print(telnet_olt_execute(creds, cmd))

def monitor_optical_power():
    creds = get_credentials("olt")
    p = input("Port: ")
    # ... (Isi fungsi monitor seperti kode awal anda)
    pass

def reset_onu_safe():
    """Menu 11: Reset ONU dengan detail lengkap"""
    creds = get_credentials("olt")
    print(f"\n{RED}=== RESET ONU (SAFE MODE) ==={RESET}")
    port = input("Masukkan Port (1/1/1): ").strip()
    onu_id = input("Masukkan ONU ID (1): ").strip()
    cmd = [f"show gpon onu detail-info gpon-onu_{port}:{onu_id}"]
    output = telnet_olt_execute(creds, cmd)
    if output:
        print(f"\n{YELLOW}{output}{RESET}")
        if input("Hapus ONU ini? (y/n): ").lower() == 'y':
            del_cmd = ["conf t", f"interface gpon-olt_{port}", f"no onu {onu_id}", "end", "write"]
            telnet_olt_execute(creds, del_cmd)
            print(f"{GREEN}[✓] Berhasil dihapus.{RESET}")

def delete_onu_fast():
    """Menu 12: Delete ONU dengan tampilan tabel ringkas"""
    creds = get_credentials("olt")
    print(f"\n{RED}=== DELETE ONU (FAST TABLE VIEW) ==={RESET}")
    port = input("Port (1/3/1): ").strip()
    onu_id = input("ONU ID: ").strip()
    cmd = [f"show gpon onu state gpon-olt_{port} {onu_id}"]
    output = telnet_olt_execute(creds, cmd)
    if output:
        print(f"\n{WHITE}HASIL CEK ONU:{RESET}")
        print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
        for line in output.splitlines():
            if f"{port}:{onu_id}" in line: print(f"{YELLOW}{line}{RESET}")
        print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
        if input("Konfirmasi Hapus? (y/n): ").lower() == 'y':
            telnet_olt_execute(creds, ["conf t", f"interface gpon-olt_{port}", f"no onu {onu_id}", "end", "write"])
            print(f"{GREEN}[✓] ONU {port}:{onu_id} Terhapus.{RESET}")

def check_optical_power_single():
    """Menu 13: Cek Power Optik ONU Tertentu"""
    creds = get_credentials("olt")
    print(f"\n{CYAN}=== CEK OPTICAL POWER ONU ==={RESET}")
    port = input("Port (1/3/1): ").strip()
    onu_id = input("ONU ID: ").strip()
    cmd = [f"show pon optical-power gpon-onu_{port}:{onu_id}"]
    output = telnet_olt_execute(creds, cmd)
    print(f"\n{WHITE}--------------------------------------------------{RESET}")
    print(f"{GREEN}{output}{RESET}")
    print(f"{WHITE}--------------------------------------------------{RESET}")

def show_menu():
    vault = load_vault()
    prof = vault.get("active_profile", "None")
    os.system('clear')
    print(f"{MAGENTA}================================================================={RESET}")
    print(f"{WHITE}    Ucenk D-Tech Premium Network System | Profile: {GREEN}{prof}{RESET}")
    print(f"{MAGENTA}================================================================={RESET}")
    
    print(f"\n{GREEN}--- MIKROTIK TOOLS ---{RESET}")
    print(f"1. Jalankan Mikhmon          5. Bandwidth Report")
    print(f"2. Total User Hotspot        6. Backup & Restore")
    print(f"3. Cek DHCP Rogue            7. SNMP Monitoring")
    print(f"4. Hapus Laporan Mikhmon     8. Log Viewer")

    print(f"\n{GREEN}--- OLT TOOLS ---{RESET}")
    print(f"9. Lihat ONU Terdaftar       13. {CYAN}Cek Power Optic ONU{RESET}")
    print(f"10. Registrasi ONU           14. Alarm & Event Viewer")
    print(f"11. Reset ONU (Detail)       15. Backup & Restore OLT")
    print(f"12. {RED}Delete ONU (Quick){RESET}       16. Traffic Report per PON")

    print(f"\n{GREEN}--- NETWORK TOOLS ---{RESET}")
    print(f"17. Speedtest CLI            20. Ping & Traceroute")
    print(f"18. Nmap Scan                21. DNS Tools")
    print(f"19. MAC Lookup               22. {YELLOW}PROFILE SETTINGS{RESET}")
    print(f"\n0. Keluar")

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
        elif c == '11': reset_onu_safe()
        elif c == '12': delete_onu_fast()
        elif c == '13': check_optical_power_single()
        elif c == '17': os.system("speedtest-cli --simple")
        elif c == '19':
            mac = input("Masukkan MAC: ")
            print(f"Brand: {get_brand(mac)}")
        elif c == '22': manage_profiles()
        elif c == '0': sys.exit()
        
        if c != '22' and c != '0': input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__":
    main()
