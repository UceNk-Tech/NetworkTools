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

# Handler untuk library requests (Fitur MAC Lookup & Brand Detection)
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

# --- DATABASE INTERNAL BRAND (OUI) ---
BRAND_MAP = {
    "94:A6:7E": "TP-Link", "F4:F2:6D": "TP-Link", "00:0C:42": "MikroTik", 
    "48:8F:5A": "ZTE", "D0:16:B4": "ZTE", "CC:2D:21": "Huawei",
    "70:A8:E3": "Tenda", "C0:25:E9": "TOTOLINK"
}

def get_brand(mac):
    """Cek brand berdasarkan MAC Address"""
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
                print(f"{GREEN}[+] Switch ke Profile: {name}{RESET}")
                time.sleep(1)
                break
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
    # Fungsi registrasi ONU yang ada di kode awal anda
    creds = get_credentials("olt")
    if not creds: return
    # (Kode monitor/registrasi anda tetap di sini)
    pass

def reset_onu_safe():
    """Menu 11: Reset ONU dengan detail lengkap (Cek Sebelum Hapus)"""
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
    else:
        print(f"{RED}[!] Data tidak ditemukan.{RESET}")

def delete_onu_fast():
    """Menu 12: Delete ONU dengan tampilan tabel ringkas (Mode Cepat)"""
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

def check_optical_power_fast():
    """Menu 13: Cek Power Optik - Versi Anti-Gagal & Debug Mode"""
    creds = get_credentials("olt")
    if not creds: 
        print(f"{RED}[!] Profile OLT belum aktif.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}=== CEK OPTICAL POWER ONU (SMART VIEW) ==={RESET}")
    print(f"{WHITE}Brand OLT Terdeteksi: {YELLOW}{brand.upper()}{RESET}")
    port = input(f"{WHITE}Port (contoh 1/1/1): {RESET}").strip()
    onu_id = input(f"{WHITE}ONU ID (contoh 1): {RESET}").strip()
    
    # Kumpulan skenario perintah yang akan dicoba
    if brand == 'fiberhome':
        cmds_to_try = [f"show onu optical-power {port} {onu_id}"]
    else:
        # Skenario ZTE: Masuk mode enable dulu, baru cek
        cmds_to_try = [
            f"show pon optical-power gpon-olt_{port} {onu_id}",
            f"show pon optical-power gpon-onu_{port}:{onu_id}",
            f"show gpon onu detail-info gpon-onu_{port}:{onu_id}"
        ]
        
    output = ""
    
    # Alice tambahkan 'enable' di awal untuk OLT ZTE
    base_cmds = ["terminal length 0"]
    if brand == 'zte':
        base_cmds.append("enable") # Memastikan hak akses penuh
        # Masukkan password enable jika OLT memintanya (opsional, tergantung config OLT)
        if creds.get('pass'): base_cmds.append(creds['pass']) 
    
    print(f"{CYAN}[*] Sedang berkomunikasi dengan OLT...{RESET}")
    
    for cmd in cmds_to_try:
        current_cmds = base_cmds + [cmd]
        raw = telnet_olt_execute(creds, current_cmds)
        
        # Validasi: Jika output mengandung angka atau tabel, berarti sukses
        if raw and any(x in raw for x in ["dBm", "Power", "Voltage", "Temp"]):
            output = raw
            break
        output = raw # Simpan untuk debug jika semua gagal
            
    print(f"\n{WHITE}HASIL DIAGNOSA {brand.upper()} ONU {port}:{onu_id}:{RESET}")
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
    
    if "dBm" in output:
        print(f"{GREEN}[✓] STATUS: ONU ONLINE / DATA DITERIMA{RESET}")
        
        # Cari baris yang spesifik milik ONU tersebut
        lines = output.splitlines()
        for line in lines:
            if "dBm" in line and (onu_id in line or port in line):
                print(f"{YELLOW}{line.strip()}{RESET}")
            elif any(x in line.lower() for x in ["temp", "volt", "input", "output"]):
                print(f"{CYAN}{line.strip()}{RESET}")
    
    elif "---" in output or "N/A" in output or "offline" in output.lower():
        print(f"{RED}[!] STATUS: ONU OFFLINE / LOS{RESET}")
        print(f"{YELLOW}[i] Deteksi: Sinyal laser tidak sampai ke ONU.{RESET}")
    
    else:
        # MODE DEBUG: Jika tetap gagal, tampilkan apa yang dikatakan OLT
        print(f"{RED}[!] Perintah Ditolak atau Format Salah.{RESET}")
        print(f"{WHITE}Respon Terakhir OLT:{RESET}")
        print(f"{CYAN}{output}{RESET}")
        print(f"\n{YELLOW}[i] Tips: Coba masukkan port tanpa gpon-olt (misal: 1/1/1 saja){RESET}")
            
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
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
    print(f"9. Lihat ONU Terdaftar       13. {CYAN}Cek Power Optic (Quick){RESET}")
    print(f"10. Registrasi ONU           14. Alarm & Event Viewer")
    print(f"11. Reset ONU (Detail)       15. Backup & Restore OLT")
    print(f"12. {RED}Delete ONU (Quick){RESET}       16. Traffic Report per PON")

    print(f"\n{GREEN}--- NETWORK TOOLS ---{RESET}")
    print(f"17. Speedtest CLI            20. Ping & Traceroute")
    print(f"18. Nmap Scan                21. DNS Tools")
    print(f"19. MAC Lookup               22. {YELLOW}PROFILE SETTINGS{RESET}")
    print(f"\n{MAGENTA}0. Keluar{RESET}")

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
        elif c == '13': check_optical_power_fast()
        elif c == '17': os.system("speedtest-cli --simple")
        elif c == '19':
            mac = input("Masukkan MAC: ")
            print(f"Brand: {get_brand(mac)}")
        elif c == '22': manage_profiles()
        elif c == '0': sys.exit()
        
        if c != '22' and c != '0' and c != '': 
            input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__":
    main()
