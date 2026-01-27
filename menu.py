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

# --- HANDLER LIBRARY ---
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

# --- KONFIGURASI WARNA ANSI ---
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
CYAN    = "\033[36m"
MAGENTA = "\033[35m"
WHITE   = "\033[37m"
RESET   = "\033[0m"

VAULT_FILE = os.path.join(os.path.dirname(__file__), "vault_session.json")

# --- DATABASE BRAND (OUI) ---
BRAND_MAP = {
    "94:A6:7E": "TP-Link", 
    "F4:F2:6D": "TP-Link", 
    "00:0C:42": "MikroTik", 
    "48:8F:5A": "ZTE"
}

def get_brand(mac):
    if not mac or mac == "N/A": 
        return "Unknown"
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

# --- SISTEM PROFILE & VAULT ---
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

def manage_profiles(): # Menu 99
    while True:
        vault = load_vault()
        os.system('clear')
        profiles = vault.get("profiles", {})
        p_keys = list(profiles.keys())
        
        print(f"{MAGENTA}======================================================{RESET}")
        print(f"{WHITE}              SETTING PROFILE JARINGAN                {RESET}")
        print(f"{MAGENTA}======================================================{RESET}")
        
        # Menampilkan Daftar Profile
        if not p_keys:
            print(f"{YELLOW} [!] Belum ada profile tersimpan.{RESET}")
        else:
            for i, p_name in enumerate(p_keys, 1):
                status = f"{GREEN}[Aktif]{RESET}" if p_name == vault.get('active_profile') else ""
                print(f" {i}. {p_name} {status}")
        
        print(f"{MAGENTA}======================================================{RESET}")
        print(f"{CYAN} 1. Add Profile")
        print(" 2. Select Profile (by Number)")
        print(" 3. Delete Profile (by Number)")
        print(f" 0. Exit{RESET}")
        print(f"{MAGENTA}======================================================{RESET}")
        
        opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()
        
        if opt == '1':
            print(f"\n{MAGENTA}====================== MIKROTIK ========================={RESET}")
            name = input(f"{WHITE}Nama Profile : {RESET}").strip()
            if not name: continue
            
            m_ip = input(f"{WHITE}MikroTik IP  : {RESET}")
            m_u  = input(f"{WHITE}User         : {RESET}")
            m_p  = getpass.getpass(f"{WHITE}Pass         : {RESET}")
            
            print(f"\n{MAGENTA}======================== OLT ============================{RESET}")
            o_ip = input(f"{WHITE}OLT IP       : {RESET}")
            o_u  = input(f"{WHITE}User         : {RESET}")
            o_p  = getpass.getpass(f"{WHITE}Pass         : {RESET}")
            o_b  = input(f"{WHITE}Brand (zte/fh): {RESET}").lower()
            
            profiles[name] = {
                "mikrotik": {"ip": m_ip, "user": m_u, "pass": m_p}, 
                "olt": {"ip": o_ip, "user": o_u, "pass": o_p, "brand": o_b}
            }
            vault["profiles"] = profiles
            vault["active_profile"] = name
            save_vault(vault)
            print(f"\n{GREEN}[✓] Profile {name} Berhasil Disimpan!{RESET}")
            input(f"{YELLOW}Tekan Enter...{RESET}")

        elif opt == '2':
            if not p_keys: continue
            idx = input(f"\n{WHITE}Masukkan Nomor Profile: {RESET}").strip()
            if idx.isdigit():
                idx = int(idx) - 1
                if 0 <= idx < len(p_keys):
                    selected = p_keys[idx]
                    vault["active_profile"] = selected
                    save_vault(vault)
                    print(f"{GREEN}[✓] Profile Aktif: {selected}{RESET}")
                    break

        elif opt == '3':
            if not p_keys: continue
            idx = input(f"\n{GREEN}Nomor Profile yang akan dihapus: {RESET}").strip()
            if idx.isdigit():
                idx = int(idx) - 1
                if 0 <= idx < len(p_keys):
                    target = p_keys[idx]
                    confirm = input(f"{YELLOW}Hapus {target}? (y/n): {RESET}").lower()
                    if confirm == 'y':
                        del profiles[target]
                        vault["profiles"] = profiles
                        if vault.get("active_profile") == target:
                            vault["active_profile"] = ""
                        save_vault(vault)
                        print(f"{GREEN}[✓] Profile Berhasil Dihapus.{RESET}")
                        input(f"{YELLOW}Tekan Enter...{RESET}")

        elif opt == '0':
            break

def get_credentials(target):
    v = load_vault()
    act = v.get("active_profile")
    if not act: 
        return None
    return v["profiles"][act].get(target)

# --- CORE EXECUTION ---
def telnet_olt_execute(creds, commands):
    if not creds: 
        return None
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.write(b"\n")
        
        tn.read_until(b"Username:", timeout=5)
        tn.write(creds['user'].encode('utf-8') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(creds['pass'].encode('utf-8') + b"\n")
        
        time.sleep(1) 
        
        output = ""
        for cmd in commands:
            tn.write((cmd + "\n").encode('utf-8'))
            if "show " in cmd:
                time.sleep(2.0)
            else:
                time.sleep(0.8)
            
            while True:
                part = tn.read_very_eager().decode('utf-8', errors='ignore')
                output += part
                if not part: 
                    break
                time.sleep(0.5) 
            
        tn.close()
        return output
    except Exception as e:
        print(f"{RED}Error Telnet: {e}{RESET}")
        return None

# --- MIKROTIK TOOLS (1-8) ---
def run_mikhmon(): 
    print(f"\n{CYAN}[+] Menyiapkan Mikhmon Server...{RESET}")
    mikhmon_path = os.path.expanduser("~/mikhmonv3")
    session_path = os.path.expanduser("~/session_mikhmon")
    tmp_path = os.path.expanduser("~/tmp")
    
    if not os.path.exists(mikhmon_path):
        print(f"{YELLOW}[*] Mendownload Mikhmon...{RESET}")
        os.system(f"git clone https://github.com/laksa19/mikhmonv3.git {mikhmon_path}")
        
    os.makedirs(session_path, exist_ok=True)
    os.makedirs(tmp_path, exist_ok=True)
    
    with open(os.path.join(tmp_path, "custom.ini"), "w") as f:
        f.write(f"opcache.enable=0\nsession.save_path=\"{session_path}\"\nsys_temp_dir=\"{tmp_path}\"\ndisplay_errors=Off\n")
    
    os.system("fuser -k 8080/tcp > /dev/null 2>&1")
    print(f"{GREEN}[!] Mikhmon Aktif: http://127.0.0.1:8080{RESET}")
    print(f"{YELLOW}[!] Tekan Ctrl+C untuk Berhenti{RESET}\n")
    
    try:
        os.system(f"export PHP_INI_SCAN_DIR={tmp_path} && php -S 127.0.0.1:8080 -t {mikhmon_path}")
    except KeyboardInterrupt: 
        print(f"\n{YELLOW}[-] Server dimatikan.{RESET}")

def mk_hotspot_active(): 
    c = get_credentials("mikrotik")
    if not c: 
        print(f"{RED}[!] Profile belum diset.{RESET}")
        return
    try:
        pool = routeros_api.RouterOsApiPool(c['ip'], username=c['user'], password=c['pass'], plaintext_login=True)
        api = pool.get_api()
        act = api.get_resource('/ip/hotspot/active').get()
        print(f"\n{GREEN}>>> TOTAL USER AKTIF: {len(act)} {RESET}")
        for user in act[:10]: 
            print(f" - {user.get('user')} | IP: {user.get('address')}")
        pool.disconnect()
    except Exception as e: 
        print(f"{RED}Error: {e}{RESET}")

def cek_dhcp_rogue():
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{RED}[!] Profile belum diset.{RESET}")
        return
    print(f"\n{CYAN}[+] Memindai Rogue DHCP di {creds['ip']}...{RESET}")
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = conn.get_api()
        alerts = api.get_resource('/ip/dhcp-server/alert').get()
        
        found_rogue = False
        for al in alerts:
            mac = al.get('unknown-server')
            interface = al.get('interface', 'N/A')
            if mac and mac != "":
                found_rogue = True
                print(f"{RED}![ROGUE DETECTED] MAC: {mac} | Brand: {get_brand(mac)} | Int: {interface}{RESET}")
        
        if not found_rogue:
            print(f"{GREEN}[✓] Kondisi Aman. Tidak ada DHCP Rogue terdeteksi pada interface:{RESET}")
            for al in alerts:
                print(f" - {al.get('interface')}")
        conn.disconnect()
    except Exception as e: 
        print(f"{RED}Error: {e}{RESET}")

def hapus_laporan_mikhmon():
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{RED}[!] Profile MikroTik belum diset.{RESET}")
        return

    # Teks ini HARUSNYA tidak ada variabel {creds['ip']}
    print(f"\n{CYAN}[+] Menghubungkan ke MikroTik...{RESET}")
    
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = conn.get_api()
        
        # Tarik data identity
        ident = api.get_resource('/system/identity').get()
        r_name = ident[0].get('name', 'MikroTik')
        
        print(f"{GREEN}[✓] Terhubung ke: {MAGENTA}{r_name}{RESET}")
        
        resource = api.get_resource('/system/script')
        print(f"{CYAN}[+] Memindai script...{RESET}")
        
        all_s = resource.get()
        m_scripts = [s for s in all_s if 'mikhmon' in s.get('name', '').lower() or 'mikhmon' in s.get('comment', '').lower()]
        count = len(m_scripts)

        if count == 0:
            print(f"{GREEN}[✓] MikroTik {r_name} Bersih!{RESET}")
        else:
            print(f"{YELLOW}[!] Terdeteksi {WHITE}{count}{YELLOW} script di {MAGENTA}{r_name}{RESET}")
            
            # PAKSA WARNA: Merah dulu, lalu Kuning, lalu Merah lagi
            tanya = f"{RED}>>> Hapus semua script laporan ini? {YELLOW}(y/n){RED}: {RESET}"
            confirm = input(tanya).lower()
            
            if confirm == 'y':
                print(f"{CYAN}[*] Menghapus {count} script...{RESET}")
                for s in m_scripts:
                    try:
                        resource.remove(id=s['id'])
                    except:
                        pass
                print(f"{GREEN}[✓] Sukses dibersihkan!{RESET}")
            else:
                print(f"{MAGENTA}[-] Batal.{RESET}")
        conn.disconnect()
    except Exception:
        print(f"{RED}[!] Gagal Konek. Cek API MikroTik.{RESET}")

def bandwidth_usage_report(): 
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum diset.{RESET}")
        return

    print(f"\n{CYAN}[+] Menghubungkan ke MikroTik {creds['ip']}...{RESET}")
    print(f"{WHITE}[*] Mengambil data traffic (Tekan Ctrl+C untuk berhenti)...{RESET}\n")
    
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()
        resource = api.get_resource('/interface')

        print(f"{MAGENTA}{'INTERFACE':<20} {'TX (Upload)':<15} {'RX (Download)':<15}{RESET}")
        print(f"{WHITE}" + "-"*52 + f"{RESET}")

        for _ in range(1): 
            interfaces = resource.get()
            for iface in interfaces:
                name = iface.get('name')
                tx_bps = int(iface.get('tx-byte', 0)) * 8
                rx_bps = int(iface.get('rx-byte', 0)) * 8
                
                def format_speed(bps):
                    if bps > 1000000: return f"{round(bps/1000000, 2)} Mbps"
                    if bps > 1000: return f"{round(bps/1000, 2)} Kbps"
                    return f"{bps} bps"

                if iface.get('running') == 'true':
                    print(f"{CYAN}{name:<20}{RESET} {YELLOW}{format_speed(tx_bps):<15}{RESET} {GREEN}{format_speed(rx_bps):<15}{RESET}")
        
        pool.disconnect()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[-] Monitoring dihentikan.{RESET}")
    except Exception as e:
        print(f"{YELLOW}[!] Error: {e}{RESET}")

def backup_restore_mikrotik(): 
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum aktif.{RESET}")
        return

    print(f"\n{CYAN}=== BACKUP & RESTORE MIKROTIK ==={RESET}")
    print("1. Buat Backup Baru (.backup & .rsc)")
    print("2. Lihat Daftar File Backup")
    print("0. Kembali")
    
    pilih = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()

        if pilih == '1':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"Backup_Ucenk_{timestamp}"
            print(f"{CYAN}[*] Membuat file .backup...{RESET}")
            api.get_binary_resource('/').call('system/backup/save', {'name': filename})
            print(f"{CYAN}[*] Membuat file .rsc (Export)...{RESET}")
            api.get_binary_resource('/').call('export', {'file': filename})
            print(f"{GREEN}[✓] Backup Berhasil disimpan dengan nama: {filename}{RESET}")

        elif pilih == '2':
            print(f"\n{WHITE}Daftar File di MikroTik:{RESET}")
            files = api.get_resource('/file').get()
            print(f"{MAGENTA}{'NAMA FILE':<40} {'UKURAN':<12} {'WAKTU':<20}{RESET}")
            print("-" * 75)
            for f in files:
                if 'backup' in f.get('name') or 'rsc' in f.get('name'):
                    name = f.get('name')
                    size = f.get('size', '0')
                    date = f.get('creation-time', 'N/A')
                    print(f"{WHITE}{name:<40} {size:<12} {date:<20}{RESET}")
        pool.disconnect()
    except Exception as e:
        print(f"{YELLOW}[!] Error: {e}{RESET}")

def snmp_monitoring(): 
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum aktif.{RESET}")
        return

    print(f"\n{CYAN}=== SNMP MONITORING MIKROTIK ==={RESET}")
    print(f"{WHITE}[*] Mengambil data sistem via API...{RESET}")
    
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()

        res_data = api.get_resource('/system/resource').get()
        res = res_data[0] if res_data else {}
        rb_data = api.get_resource('/system/routerboard').get()
        rb = rb_data[0] if rb_data else {}
        health = api.get_resource('/system/health').get()

        print(f"\n{MAGENTA}--------------------------------------------------{RESET}")
        print(f"{WHITE}MODEL PERANGKAT : {GREEN}{res.get('board-name', 'Unknown')} ({res.get('architecture-name', 'N/A')}){RESET}")
        print(f"{WHITE}SERIAL NUMBER   : {GREEN}{rb.get('serial-number', 'N/A')}{RESET}")
        print(f"{WHITE}UPTIME          : {GREEN}{res.get('uptime', 'N/A')}{RESET}")
        print(f"{WHITE}ROUTEROS VER    : {GREEN}{res.get('version', 'N/A')}{RESET}")
        print(f"{MAGENTA}--------------------------------------------------{RESET}")
        
        cpu_load = res.get('cpu-load', '0')
        free_mem = int(res.get('free-memory', 0)) / 1024 / 1024
        total_mem = int(res.get('total-memory', 0)) / 1024 / 1024
        
        print(f"{WHITE}CPU LOAD       : {YELLOW}{cpu_load}%{RESET}")
        print(f"{WHITE}FREE MEMORY    : {YELLOW}{round(free_mem, 1)} MB / {round(total_mem, 1)} MB{RESET}")
        
        if health:
            for h in health:
                name = h.get('name')
                value = h.get('value')
                if name:
                    label = str(name).upper()
                    print(f"{WHITE}{label:<14} : {YELLOW}{value}{RESET}")
                elif value: 
                    print(f"{WHITE}SENSOR         : {YELLOW}{value}{RESET}")
        print(f"{MAGENTA}--------------------------------------------------{RESET}")
        pool.disconnect()
    except Exception as e:
        print(f"{YELLOW}[!] Gagal SNMP Scan: {e}{RESET}")

def log_viewer_mikrotik(): 
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum aktif.{RESET}")
        return

    print(f"\n{CYAN}=== LOG VIEWER MIKROTIK (15 Baris Terakhir) ==={RESET}")
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()
        logs = api.get_resource('/log').get()
        last_logs = logs[-15:]

        print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
        for l in last_logs:
            time_log = l.get('time')
            message = l.get('message', '')
            topics = l.get('topics', '')
            color = WHITE
            low_msg = message.lower()
            
            if "error" in topics or "critical" in topics:
                color = YELLOW
            elif "hotspot" in topics:
                color = CYAN
            elif "login" in low_msg or "logged in" in low_msg:
                color = GREEN
            
            print(f"{CYAN}{time_log}{RESET} {color}{message}{RESET}")
        print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
        pool.disconnect()
    except Exception as e:
        print(f"{YELLOW}[!] Gagal mengambil log: {e}{RESET}")


# --- MIKROTIK TOOLS (1-8) ---
def run_mikhmon(): 
    print(f"\n{CYAN}[+] Menyiapkan Mikhmon Server...{RESET}")
    mikhmon_path = os.path.expanduser("~/mikhmonv3")
    session_path = os.path.expanduser("~/session_mikhmon")
    tmp_path = os.path.expanduser("~/tmp")
    
    if not os.path.exists(mikhmon_path):
        print(f"{YELLOW}[*] Mendownload Mikhmon...{RESET}")
        os.system(f"git clone https://github.com/laksa19/mikhmonv3.git {mikhmon_path}")
        
    os.makedirs(session_path, exist_ok=True)
    os.makedirs(tmp_path, exist_ok=True)
    
    with open(os.path.join(tmp_path, "custom.ini"), "w") as f:
        f.write(f"opcache.enable=0\nsession.save_path=\"{session_path}\"\nsys_temp_dir=\"{tmp_path}\"\ndisplay_errors=Off\n")
    
    os.system("fuser -k 8080/tcp > /dev/null 2>&1")
    print(f"{GREEN}[!] Mikhmon Aktif: http://127.0.0.1:8080{RESET}")
    print(f"{RED}[!] Tekan Ctrl+C untuk Berhenti{RESET}\n")
    
    try:
        os.system(f"export PHP_INI_SCAN_DIR={tmp_path} && php -S 127.0.0.1:8080 -t {mikhmon_path}")
    except KeyboardInterrupt: 
        print(f"\n{YELLOW}[-] Server dimatikan.{RESET}")

def mk_hotspot_active(): 
    c = get_credentials("mikrotik")
    if not c: 
        print(f"{RED}[!] Profile belum diset.{RESET}")
        return
    try:
        pool = routeros_api.RouterOsApiPool(c['ip'], username=c['user'], password=c['pass'], plaintext_login=True)
        api = pool.get_api()
        act = api.get_resource('/ip/hotspot/active').get()
        print(f"\n{GREEN}>>> TOTAL USER AKTIF: {len(act)} {RESET}")
        for user in act[:10]: 
            print(f" - {user.get('user')} | IP: {user.get('address')}")
        pool.disconnect()
    except Exception as e: 
        print(f"{RED}Error: {e}{RESET}")

def cek_dhcp_rogue():
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{RED}[!] Profile belum diset.{RESET}")
        return
    print(f"\n{CYAN}[+] Memindai Rogue DHCP di {creds['ip']}...{RESET}")
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = conn.get_api()
        alerts = api.get_resource('/ip/dhcp-server/alert').get()
        
        found_rogue = False
        for al in alerts:
            mac = al.get('unknown-server')
            interface = al.get('interface', 'N/A')
            if mac and mac != "":
                found_rogue = True
                print(f"{RED}![ROGUE DETECTED] MAC: {mac} | Brand: {get_brand(mac)} | Int: {interface}{RESET}")
        
        if not found_rogue:
            print(f"{GREEN}[✓] Kondisi Aman. Tidak ada DHCP Rogue terdeteksi pada interface:{RESET}")
            for al in alerts:
                print(f" - {al.get('interface')}")
        conn.disconnect()
    except Exception as e: 
        print(f"{RED}Error: {e}{RESET}")

def hapus_laporan_mikhmon():
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{RED}[!] Profile MikroTik belum diset. Pilih menu 22 dulu.{RESET}")
        return

    print(f"\n{CYAN}[+] Menghubungkan ke MikroTik {creds['ip']}...{RESET}")
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = conn.get_api()
        resource = api.get_resource('/system/script')
        
        print(f"{CYAN}[+] Memindai script laporan Mikhmon...{RESET}")
        all_scripts = resource.get()
        mikhmon_scripts = [s for s in all_scripts if 'mikhmon' in s.get('name', '').lower() or 'mikhmon' in s.get('comment', '').lower()]
        count = len(mikhmon_scripts)

        if count == 0:
            print(f"{GREEN}[✓] Tidak ditemukan script laporan Mikhmon. MikroTik bersih!{RESET}")
        else:
            print(f"{YELLOW}[!] Terdeteksi {WHITE}{count}{YELLOW} script laporan Mikhmon di MikroTik.{RESET}")
            confirm = input(f"{RED}>>> Hapus semua script laporan ini? (y/n): {RESET}").lower()
            if confirm == 'y':
                print(f"{CYAN}[*] Menghapus {count} script... (Mohon tunggu){RESET}")
                for s in mikhmon_scripts:
                    try:
                        resource.remove(id=s['id'])
                    except:
                        pass
                print(f"{GREEN}[✓] Sukses! {count} script laporan telah dibersihkan dari MikroTik.{RESET}")
            else:
                print(f"{MAGENTA}[-] Penghapusan dibatalkan.{RESET}")
        conn.disconnect()
    except Exception as e:
        print(f"{RED}[!] Error: {e}{RESET}")

def bandwidth_usage_report(): 
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum diset.{RESET}")
        return

    print(f"\n{CYAN}[+] Menghubungkan ke MikroTik {creds['ip']}...{RESET}")
    print(f"{WHITE}[*] Mengambil data traffic (Tekan Ctrl+C untuk berhenti)...{RESET}\n")
    
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()
        resource = api.get_resource('/interface')

        print(f"{MAGENTA}{'INTERFACE':<20} {'TX (Upload)':<15} {'RX (Download)':<15}{RESET}")
        print(f"{WHITE}" + "-"*52 + f"{RESET}")

        for _ in range(1): 
            interfaces = resource.get()
            for iface in interfaces:
                name = iface.get('name')
                tx_bps = int(iface.get('tx-byte', 0)) * 8
                rx_bps = int(iface.get('rx-byte', 0)) * 8
                
                def format_speed(bps):
                    if bps > 1000000: return f"{round(bps/1000000, 2)} Mbps"
                    if bps > 1000: return f"{round(bps/1000, 2)} Kbps"
                    return f"{bps} bps"

                if iface.get('running') == 'true':
                    print(f"{CYAN}{name:<20}{RESET} {YELLOW}{format_speed(tx_bps):<15}{RESET} {GREEN}{format_speed(rx_bps):<15}{RESET}")
        
        pool.disconnect()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[-] Monitoring dihentikan.{RESET}")
    except Exception as e:
        print(f"{YELLOW}[!] Error: {e}{RESET}")

def backup_restore_mikrotik(): 
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum aktif.{RESET}")
        return

    print(f"\n{CYAN}=== BACKUP & RESTORE MIKROTIK ==={RESET}")
    print("1. Buat Backup Baru (.backup & .rsc)")
    print("2. Lihat Daftar File Backup")
    print("0. Kembali")
    
    pilih = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()

        if pilih == '1':
            timestamp = datetime.now().strftime("%Y%m%d_%H%M")
            filename = f"Backup_Ucenk_{timestamp}"
            print(f"{CYAN}[*] Membuat file .backup...{RESET}")
            api.get_binary_resource('/').call('system/backup/save', {'name': filename})
            print(f"{CYAN}[*] Membuat file .rsc (Export)...{RESET}")
            api.get_binary_resource('/').call('export', {'file': filename})
            print(f"{GREEN}[✓] Backup Berhasil disimpan dengan nama: {filename}{RESET}")

        elif pilih == '2':
            print(f"\n{WHITE}Daftar File di MikroTik:{RESET}")
            files = api.get_resource('/file').get()
            print(f"{MAGENTA}{'NAMA FILE':<40} {'UKURAN':<12} {'WAKTU':<20}{RESET}")
            print("-" * 75)
            for f in files:
                if 'backup' in f.get('name') or 'rsc' in f.get('name'):
                    name = f.get('name')
                    size = f.get('size', '0')
                    date = f.get('creation-time', 'N/A')
                    print(f"{WHITE}{name:<40} {size:<12} {date:<20}{RESET}")
        pool.disconnect()
    except Exception as e:
        print(f"{YELLOW}[!] Error: {e}{RESET}")

def snmp_monitoring(): 
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum aktif.{RESET}")
        return

    print(f"\n{CYAN}=== SNMP MONITORING MIKROTIK ==={RESET}")
    print(f"{WHITE}[*] Mengambil data sistem via API...{RESET}")
    
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()

        res_data = api.get_resource('/system/resource').get()
        res = res_data[0] if res_data else {}
        rb_data = api.get_resource('/system/routerboard').get()
        rb = rb_data[0] if rb_data else {}
        health = api.get_resource('/system/health').get()

        print(f"\n{MAGENTA}--------------------------------------------------{RESET}")
        print(f"{WHITE}MODEL PERANGKAT : {GREEN}{res.get('board-name', 'Unknown')} ({res.get('architecture-name', 'N/A')}){RESET}")
        print(f"{WHITE}SERIAL NUMBER   : {GREEN}{rb.get('serial-number', 'N/A')}{RESET}")
        print(f"{WHITE}UPTIME          : {GREEN}{res.get('uptime', 'N/A')}{RESET}")
        print(f"{WHITE}ROUTEROS VER    : {GREEN}{res.get('version', 'N/A')}{RESET}")
        print(f"{MAGENTA}--------------------------------------------------{RESET}")
        
        cpu_load = res.get('cpu-load', '0')
        free_mem = int(res.get('free-memory', 0)) / 1024 / 1024
        total_mem = int(res.get('total-memory', 0)) / 1024 / 1024
        
        print(f"{WHITE}CPU LOAD       : {YELLOW}{cpu_load}%{RESET}")
        print(f"{WHITE}FREE MEMORY    : {YELLOW}{round(free_mem, 1)} MB / {round(total_mem, 1)} MB{RESET}")
        
        if health:
            for h in health:
                name = h.get('name')
                value = h.get('value')
                if name:
                    label = str(name).upper()
                    print(f"{WHITE}{label:<14} : {YELLOW}{value}{RESET}")
                elif value: 
                    print(f"{WHITE}SENSOR         : {YELLOW}{value}{RESET}")
        print(f"{MAGENTA}--------------------------------------------------{RESET}")
        pool.disconnect()
    except Exception as e:
        print(f"{YELLOW}[!] Gagal SNMP Scan: {e}{RESET}")

def log_viewer_mikrotik(): 
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum aktif.{RESET}")
        return

    print(f"\n{CYAN}=== LOG VIEWER MIKROTIK (15 Baris Terakhir) ==={RESET}")
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()
        logs = api.get_resource('/log').get()
        last_logs = logs[-15:]

        print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
        for l in last_logs:
            time_log = l.get('time')
            message = l.get('message', '')
            topics = l.get('topics', '')
            color = WHITE
            low_msg = message.lower()
            
            if "error" in topics or "critical" in topics:
                color = YELLOW
            elif "hotspot" in topics:
                color = CYAN
            elif "login" in low_msg or "logged in" in low_msg:
                color = GREEN
            
            print(f"{CYAN}{time_log}{RESET} {color}{message}{RESET}")
        print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
        pool.disconnect()
    except Exception as e:
        print(f"{YELLOW}[!] Gagal mengambil log: {e}{RESET}")

# --- OLT TOOLS (9-14) ---
def list_onu(): 
    creds = get_credentials("olt")
    if not creds: 
        print(f"{RED}[!] Profile OLT belum diset.{RESET}")
        return
        
    p = input(f"{WHITE}Input Port (contoh 1/2/1): {RESET}")
    brand = creds.get('brand', 'zte').lower()
    print(f"\n{CYAN}[+] Mengambil daftar semua ONU di port {p}...{RESET}")
    
    if brand == 'zte':
        cmds = ["terminal length 0", "end", f"show pon onu information gpon-olt_{p}"]
    else:
        cmds = ["terminal length 0", "end", f"show onu status port {p}"]
        
    output = telnet_olt_execute(creds, cmds)
    if output:
        # --- Bagian Revisi: Membersihkan Output ---
        lines = output.splitlines()
        filtered_lines = [
            line for line in lines 
            if "The password is not strong" not in line 
            and "ZXAN#" not in line
        ]
        clean_output = "\n".join(filtered_lines).strip()
        # ------------------------------------------

        print(f"\n{WHITE}==== DAFTAR ONU TERDAFTAR (PORT {p}) ===={RESET}")
        print(f"{WHITE}{clean_output}{RESET}")
    else:
        print(f"{RED}[!] Gagal mengambil data atau port kosong.{RESET}")

def config_onu_logic(): 
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum diset.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    found_sn = ""
    print(f"\n{MAGENTA}=== MONITOR & REGISTRASI ONU ==={RESET}")
    p = input(f"{WHITE}Input Port Lokasi (contoh 1/2/1): {RESET}").strip()

    print(f"\n{CYAN}[+] Memeriksa ONU Unconfigured...{RESET}")
    cmd_scan = ["terminal length 0", "enable", "show gpon onu uncfg"] if brand == 'zte' else ["terminal length 0", f"show onu unconfigured port {p}"]
    res_unconfig = telnet_olt_execute(creds, cmd_scan)
    
    if res_unconfig:
        # Filter output scan awal agar bersih dari prompt dan warning password
        clean_res = "\n".join([line for line in res_unconfig.splitlines() if "ZXAN" not in line and "% The password" not in line and line.strip()])
        
        if any(x in clean_res.upper() for x in ["FHTT", "ZTEG", "SN", "ONUINDEX"]):
            print(f"\n{YELLOW}⚠️  ONU TERDETEKSI (Hasil Scan):{RESET}")
            print(f"{WHITE}--------------------------------------------------{RESET}")
            print(f"{WHITE}{clean_res}{RESET}")
            print(f"{WHITE}--------------------------------------------------{RESET}")
            sn_match = re.search(r'(FHTT|ZTEG)[0-9A-Z]{8,}', clean_res.upper())
            if sn_match:
                found_sn = sn_match.group(0)
                print(f"{GREEN}[✓] SN Otomatis Disimpan: {found_sn}{RESET}")
        else:
            print(f"{YELLOW}[i] Scan Selesai: Tidak menemukan ONU baru unregister.{RESET}")
    else:
        print(f"{RED}[!] Gagal mengambil data scan.{RESET}")

    while True:
        print(f"\n{MAGENTA}--- PILIH TINDAKAN (PORT {p}) ---{RESET}")
        print(f" 1. {YELLOW}Scan ONU ID Kosong (Cari nomor kosong){RESET}")
        print(f" 2. {GREEN}Registrasi ZTE (Hotspot){RESET}")
        print(f" 3. {GREEN}Registrasi ZTE (PPPoE){RESET}")
        print(f" 4. {GREEN}Registrasi FH (Hotspot){RESET}")
        print(f" 5. {GREEN}Registrasi FH (PPPoE){RESET}")
        print(f" 6. {CYAN}Cek Detail Power Optik Unconfigured{RESET}") 
        print(f" 0. {YELLOW}Keluar/Kembali{RESET}")
        
        opt = input(f"\n{YELLOW}Pilih (0-6): {RESET}")
        if opt == '0' or not opt: 
            break

        if opt == '1':
            print(f"\n{CYAN}[*] Menganalisa daftar ID di port {p}...{RESET}")
            cmd_list = ["terminal length 0", "enable", f"show gpon onu state gpon-olt_{p}"] if brand == 'zte' else ["terminal length 0", f"show onu status port {p}"]
            res_list = telnet_olt_execute(creds, cmd_list)
            if res_list:
                ids_found = re.findall(r':(\d{1,3})\s+', res_list)
                ids_int = sorted(list(set([int(x) for x in ids_found])))
                if not ids_int:
                    print(f"{CYAN}[i] Port {p} terlihat kosong. Silakan pakai ID 1.{RESET}")
                else:
                    max_id = max(ids_int)
                    missing_ids = [x for x in range(1, max_id + 1) if x not in ids_int]
                    print(f"{MAGENTA}--------------------------------------------------{RESET}")
                    if missing_ids:
                        print(f"{YELLOW}[!] ID KOSONG (Siap Pakai):{RESET}")
                        chunks = [map(str, missing_ids[i:i + 10]) for i in range(0, len(missing_ids), 10)]
                        for chunk in chunks: print(f"{WHITE}    {', '.join(chunk)}{RESET}")
                    else:
                        print(f"{YELLOW}[i] Tidak ada nomor Kosong (ID 1 sampai {max_id} terisi).{RESET}")
                    print(f"\n{GREEN}[+] SARAN ID BARU: {max_id + 1}{RESET}")
                    print(f"{MAGENTA}--------------------------------------------------{RESET}")
            continue

        if opt == '6':
            if not found_sn:
                print(f"{RED}[!] Tidak ada SN terdeteksi. Silakan Scan (Opsi 1) terlebih dahulu.{RESET}")
                continue
            
            print(f"\n{CYAN}[*] Mencari ID aman untuk pengecekan...{RESET}")
            cmd_check = ["terminal length 0", f"show gpon onu state gpon-olt_{p}"]
            res_check = telnet_olt_execute(creds, cmd_check)
            test_id = "128"
            if res_check:
                ids_in_use = re.findall(r':(\d+)\s+', res_check)
                if ids_in_use:
                    used_ints = [int(x) for x in ids_in_use]
                    if 128 in used_ints: test_id = str(max(used_ints) + 1)

            print(f"{CYAN}[+] Memulai Diagnosa Cepat untuk SN: {found_sn}{RESET}")
            print(f"{CYAN}[+] Pinjam jalur ONU ID {test_id} sementara untuk Cek...{RESET}") 
            
            cmds = [
                "conf t",
                f"interface gpon-olt_{p}",
                f"onu {test_id} type ALL sn {found_sn}",
                "exit",
                "terminal length 0",
                f"show pon power attenuation gpon-onu_{p}:{test_id}",
                "conf t",
                f"interface gpon-olt_{p}",
                f"no onu {test_id}",
                "end"
            ]
            output = telnet_olt_execute(creds, cmds)
            
            print(f"\n{WHITE}DETAIL POWER & ATTENUATION ONU (PRE-CONFIG):{RESET}")
            print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
            if output:
                lines = output.splitlines()
                show_table = False
                for line in lines:
                    if "OLT" in line and "ONU" in line: show_table = True
                    # Matikan show_table jika bertemu prompt atau perintah config
                    if any(x in line for x in ["ZXAN", "conf t", "exit", "no onu", "terminal length", "end"]): show_table = False
                    
                    if show_table and line.strip() and "% The password" not in line:
                        print(f"{YELLOW}{line}{RESET}")

                for line in lines:
                    if "down" in line.lower() and "Rx" in line:
                        m = re.findall(r"Rx\s*:\s*(-?\d+\.\d+)", line)
                        if m:
                            rx = float(m[0])
                            color = GREEN if rx > -25.0 else YELLOW if rx > -27.0 else RED
                            print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
                            print(f"{WHITE}Hasil Analisa (Rx ONU): {color}{rx} dBm{RESET}")
            else:
                print(f"{RED}[!] Gagal mendapatkan respon dari OLT.{RESET}")
            print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
            print(f"{CYAN}[i] Status: ID {test_id} telah dihapus kembali. Port Bersih.{RESET}")
            continue

        if opt in ['2', '3', '4', '5']:
            onu_id = input(f"{WHITE}Masukkan ID ONU (misal 16): {RESET}").strip()
            sn = input(f"{WHITE}Masukkan SN ONU [{found_sn}]: {RESET}").strip() or found_sn
            vlan = input(f"{WHITE}VLAN ID: {RESET}").strip()
            name = input(f"{WHITE}Nama Pelanggan: {RESET}").strip().replace(" ", "_")
            cmds = []
            
            if opt == '2': # ZTE HOTSPOT
                cmds = ["conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit", f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit", f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}", f"vlan port wifi_0/1 mode tag vlan {vlan}", f"vlan port eth_0/1 mode tag vlan {vlan}", "security-mgmt 1 state enable mode forward protocol web", "end", "write"]
            elif opt == '3': # ZTE PPPOE
                user = input(f"{WHITE}User PPPoE: {RESET}").strip(); pw = input(f"{WHITE}Pass PPPoE: {RESET}").strip()
                cmds = ["conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit", f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1", "exit", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}", f"wan-ip 1 mode pppoe username {user} password {pw} vlan {vlan} priority 0", "security-mgmt 1 state enable mode forward protocol web", "end", "write"]
            elif opt == '4': # FH HOTSPOT
                cmds = ["conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit", f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1", "exit", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}", f"vlan port wifi_0/1 mode tag vlan {vlan}", "end", "write"]
            elif opt == '5': # FH PPPOE
                user = input(f"{WHITE}User PPPoE: {RESET}").strip(); pw = input(f"{WHITE}Pass PPPoE: {RESET}").strip()
                cmds = ["conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit", f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1", "exit", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", f"pon-onu-mng gpon-onu_{p}:{onu_id}", "wan 1 mode pppoe", f"wan 1 pppoe username {user} password {pw}", f"wan 1 vlan {vlan} priority 0", "wan 1 service-type internet", "wan 1 binding-port eth_0/1 wifi_0/1", "end", "write"]

            if cmds:
                print(f"\n{CYAN}[*] Mengirim konfigurasi...{RESET}")
                telnet_olt_execute(creds, cmds)
                print(f"{GREEN}[✓] Registrasi Selesai!{RESET}")



def restart_onu(): 
    creds = get_credentials("olt")
    if not creds: 
        print(f"{RED}[!] Profile OLT belum diset.{RESET}")
        return
        
    print(f"\n{YELLOW}=== RESTART/REBOOT ONU ==={RESET}")
    port = input(f"{WHITE}Port (contoh 1/2/1): {RESET}").strip()
    onu_id = input(f"{WHITE}Nomor ONU: {RESET}").strip()
    
    # Cek dulu apakah ONU-nya ada/online
    print(f"{CYAN}[*] Mengecek status ONU {port}:{onu_id}...{RESET}")
    output = telnet_olt_execute(creds, [f"show gpon onu state gpon-olt_{port} {onu_id}"])
    
    if output:
        found = False
        for line in output.splitlines():
            if f"{port}:{onu_id}" in line:
                print(f"\n{WHITE}INFO ONU:{RESET}")
                print(f"{YELLOW}{line}{RESET}")
                found = True
        
        if not found:
            print(f"{RED}[!] ONU tidak ditemukan pada port tersebut.{RESET}")
            return

        confirm = input(f"\n{RED}>>> Restart ONU ini sekarang? (y/n): {RESET}").lower()
        if confirm == 'y':
            print(f"{CYAN}[*] Mengirim perintah reboot...{RESET}")
            # Perintah ZTE untuk reboot ONU
            commands = [
                "conf t",
                f"pon-onu-mng gpon-onu_{port}:{onu_id}",
                "reboot",
                "exit",
                "end"
            ]
            telnet_olt_execute(creds, commands)
            print(f"{GREEN}[✓] Perintah Reboot berhasil dikirim ke ONU {port}:{onu_id}.{RESET}")
            print(f"{WHITE}[!] ONU akan offline sekitar 1-2 menit untuk proses booting.{RESET}")
        else:
            print(f"{MAGENTA}[-] Restart dibatalkan.{RESET}")
    else:
        print(f"{RED}[!] Gagal terhubung ke OLT.{RESET}")

def reset_onu(): 
    creds = get_credentials("olt")
    if not creds: return
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{GREEN}=== RESET ONU (SAFE MODE) ==={RESET}")
    port = input(f"{WHITE}Masukkan Port (1/2/1): {RESET}").strip()
    onu_id = input(f"{WHITE}Masukkan Nomor ONU (1): {RESET}").strip()
    
    # Pesan loading agar user tahu proses sedang berjalan
    print(f"\n{CYAN}[*] Mohon tunggu, sedang mendapatkan informasi ONU...{RESET}")
    
    if brand == 'zte':
        check_cmds = ["terminal length 0", "end", f"show gpon onu detail-info gpon-onu_{port}:{onu_id}"]
    else:
        check_cmds = ["terminal length 0", "end", f"show onu info port {port} ont {onu_id}"]
        
    output = telnet_olt_execute(creds, check_cmds)
    
    if output and "Invalid" not in output:
        print(f"\n{YELLOW}{output}{RESET}")
        
        # Menggunakan warna kuning pada (y/n)
        tanya = f"{CYAN}>>> Reset ONU {port}:{onu_id} ini? {YELLOW}(y/n){RED}: {RESET}"
        if input(tanya).lower() == 'y':
            print(f"{CYAN}[*] Sedang memproses reset ONU...{RESET}")
            # Perintah menghapus (reset) ONU dari database OLT
            telnet_olt_execute(creds, ["conf t", f"interface gpon-olt_{port}", f"no onu {onu_id}", "end", "write"])
            print(f"{GREEN}[✓] ONU Berhasil direset (dihapus dari OLT).{RESET}")
        else:
            print(f"{MAGENTA}[-] Reset dibatalkan.{RESET}")
    else: 
        print(f"{RED}[!] Data tidak ditemukan atau ONU tidak terdaftar.{RESET}")
        

def check_optical_power_fast():
    creds = get_credentials("olt")
    if not creds: return
    
    brand = creds.get('brand', 'zte').lower()
    print(f"\n{CYAN}=== CEK STATUS & POWER OPTIK ONU ==={RESET}")
    port = input(f"{WHITE}Masukkan Port (contoh 1/2/1): {RESET}").strip()
    onu_id = input(f"{WHITE}NO ONU: {RESET}").strip()
    
    print(f"\n{CYAN}[*] Mohon tunggu, sedang berkomunikasi dengan ONU...{RESET}")

    if brand == 'fiberhome':
        cmds = ["terminal length 0", f"show onu optical-power {port} {onu_id}"]
    else: 
        cmds = [
            "terminal length 0", 
            f"show pon power attenuation gpon-onu_{port}:{onu_id}"
        ]
    
    output = telnet_olt_execute(creds, cmds)
    
    print(f"\n{WHITE}HASIL DIAGNOSA ONU {onu_id} @ PORT {port}:{RESET}")
    print(f"{MAGENTA}--------------------------------------------------------------------------------------------------------------------------------------{RESET}")
    
    if output:
        # --- PROSES PEMBERSIHAN OUTPUT ---
        lines = output.splitlines()
        clean_lines = []
        for line in lines:
            l_strip = line.strip()
            # Sembunyikan banner password, prompt ZXAN, dan baris kosong di awal
            if not l_strip or "% The password" in line or "ZXAN#" in line or "terminal length" in line:
                continue
            clean_lines.append(line)
        
        clean_output = "\n".join(clean_lines)
        
        # Tampilkan tabel yang sudah bersih
        print(f"{YELLOW}{clean_output}{RESET}")
        print(f"{MAGENTA}--------------------------------------------------------------------------------------------------------------------------------------{RESET}")

        # --- LOGIKA PENGAMBILAN RX ONU (BARIS DOWN) ---
        rx_val = None
        for line in clean_lines:
            # Kita cari baris 'down' dan ambil angka Rx (bukan Tx)
            if "down" in line.lower() and "Rx" in line:
                # Regex mencari angka negatif (Rx biasanya negatif)
                matches = re.findall(r"Rx\s*:\s*(-?\d+\.\d+)", line)
                if matches:
                    rx_val = float(matches[0])
                    break
        
        if rx_val is not None:
            if rx_val < -27.0:
                color, status = RED, "CRITICAL (DROP)"
            elif rx_val < -25.0:
                color, status = YELLOW, "WARNING (REDAUP)"
            else:
                color, status = GREEN, "NORMAL (BAGUS)"
            
            print(f"{WHITE}Identity ONU       : {MAGENTA}{port}:{onu_id}{RESET}")
            print(f"{WHITE}Redaman (Rx ONU)   : {color}{rx_val} dBm{RESET}")
            print(f"{WHITE}Kondisi            : {color}{status}{RESET}")
        else:
            print(f"{YELLOW}[!] Analisa otomatis gagal. Silakan baca tabel di atas.{RESET}")
    else:
        print(f"{RED}[!] Gagal koneksi ke OLT.{RESET}")

    print(f"{MAGENTA}--------------------------------------------------------------------------------------------------------------------------------------{RESET}")


def port_vlan(): 
    c = get_credentials("olt")
    p = input("ONU (1/1/1:1): "); v = input("VLAN: ")
    cmds = ["conf t", f"pon-onu-mng gpon-onu_{p}", f"vlan port eth_0/1 mode tag vlan {v}", "end", "write"]
    print(telnet_olt_execute(c, cmds))


def alarm_event_viewer(): # Menu 15
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum aktif.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}=== ALARM & EVENT VIEWER OLT ==={RESET}")
    print(" 1. Lihat Alarm Aktif (Current Alarms)")
    print(" 2. Lihat Riwayat Event (Event Log)")
    print(" 0. Kembali")
    
    opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()
    if opt == '0' or not opt: return

    print(f"\n{CYAN}[*] Mengambil data...{RESET}")
    
    if brand == 'zte':
        # Kita tambahkan 'enable' untuk memastikan hak akses penuh
        if opt == '1':
            cmds = ["terminal length 0", "enable", "show alarm current"]
        else:
            # Gunakan 'show alarm history' yang paling standar
            cmds = ["terminal length 0", "enable", "show alarm history"]
    else:
        # Untuk Fiberhome
        if opt == '1':
            cmds = ["terminal length 0", "show alarm active"]
        else:
            cmds = ["terminal length 0", "show event log"]

    output = telnet_olt_execute(creds, cmds)
    
    print(f"\n{WHITE}HASIL LAPORAN ALARM/EVENT:{RESET}")
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
    
    if output:
        lines = output.splitlines()
        has_data = False
        for line in lines:
            l_low = line.lower()
            
            # Filter baris echo dan prompt agar bersih
            if any(x in l_low for x in ["terminal length", "enable", "show alarm", "zxan#", "zxan>"]):
                continue
            
            # Cek jika ada error
            if "%error" in l_low:
                print(f"{RED}[!] Error OLT: Perintah tidak dikenali oleh firmware ini.{RESET}")
                print(f"{WHITE}[i] Coba ketik manual 'show alarm ?' di OLT untuk cek perintah history.{RESET}")
                break
            
            # Tampilkan baris yang berisi data
            if line.strip():
                has_data = True
                # Highlight alarm krusial
                if any(x in l_low for x in ["critical", "major", "los", "dyinggasp", "off-line"]):
                    print(f"{YELLOW}{line.strip()}{RESET}")
                else:
                    print(f"{WHITE}{line.strip()}{RESET}")
        
        if not has_data and "%error" not in output.lower():
            print(f"{GREEN}[✓] Tidak ada alarm atau log tersimpan.{RESET}")
    else:
        print(f"{YELLOW}[!] OLT tidak memberikan respon.{RESET}")
        
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")


def backup_restore_olt(): # Menu 16
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum aktif.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}=== BACKUP CONFIGURATION OLT ==={RESET}")
    print(" 1. Tampilkan Running-Config (Manual Copy)")
    print(" 2. Backup via FTP (Simpan ke Server)")
    print(" 0. Kembali")
    
    opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()
    if opt == '0' or not opt: return

    if opt == '1':
        print(f"\n{CYAN}[*] Mengambil seluruh konfigurasi (Mohon tunggu, ini mungkin lama)...{RESET}")
        if brand == 'zte':
            cmds = ["terminal length 0", "enable", "show running-config"]
        else:
            cmds = ["terminal length 0", "show current-config"]
            
        output = telnet_olt_execute(creds, cmds)
        if output:
            filename = f"Backup_OLT_{datetime.now().strftime('%Y%m%d')}.txt"
            with open(filename, "w") as f:
                f.write(output)
            print(f"{GREEN}[✓] Konfigurasi berhasil ditarik dan disimpan ke file: {filename}{RESET}")
            print(f"{WHITE}[i] Kamu bisa melihat isi file tersebut untuk backup manual.{RESET}")
        else:
            print(f"{YELLOW}[!] Gagal menarik konfigurasi.{RESET}")

    elif opt == '2':
        # Fitur ini biasanya butuh server FTP aktif di PC Ucenk
        ftp_ip = input(f"{WHITE}Masukkan IP FTP Server: {RESET}").strip()
        user = input(f"{WHITE}User FTP: {RESET}").strip()
        pw = input(f"{WHITE}Pass FTP: {RESET}").strip()
        
        print(f"\n{CYAN}[*] Mengirim perintah backup ke FTP...{RESET}")
        if brand == 'zte':
            cmds = [
                "enable",
                f"upload configuration ftp {ftp_ip} user {user} password {pw} config.dat"
            ]
        else:
            cmds = ["copy running-config ftp"] # Contoh FH

        result = telnet_olt_execute(creds, cmds)
        print(f"{GREEN}[✓] Perintah backup dikirim. Silakan cek di server FTP kamu.{RESET}")

    print(f"{MAGENTA}-----------------------------------------------------------------------{RESET}")


def traffic_report_pon(): # Menu 17 (OLT Tools)
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum aktif.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}=== TRAFFIC REPORT PER PON PORT ==={RESET}")
    port = input(f"{WHITE}Masukkan Port PON (contoh 1/1/1): {RESET}").strip()
    
    print(f"\n{CYAN}[*] Mengambil data statistik trafik...{RESET}")
    
    if brand == 'zte':
        # Perintah untuk melihat throughput real-time pada port PON ZTE
        cmds = [
            "terminal length 0", 
            "enable", 
            f"show interface gpon-olt_{port}"
        ]
    else:
        # Untuk Fiberhome
        cmds = ["terminal length 0", f"show interface pon {port}"]

    output = telnet_olt_execute(creds, cmds)
    
    print(f"\n{WHITE}LAPORAN TRAFIK PORT {port}:{RESET}")
    print(f"{MAGENTA}----------------------------------------------------------------------{RESET}")
    
    if output:
        lines = output.splitlines()
        found = False
        for line in lines:
            l_low = line.lower()
            # Cari baris yang mengandung data input/output rate
            if any(x in l_low for x in ["input rate", "output rate", "bits/sec", "throughput"]):
                # Highlight data trafik dengan warna Hijau
                print(f"{GREEN}{line.strip()}{RESET}")
                found = True
            elif "description" in l_low or "state" in l_low:
                print(f"{WHITE}{line.strip()}{RESET}")
        
        if not found:
            # Jika output detail tidak muncul, tampilkan semua yang relevan
            print(f"{WHITE}{output}{RESET}")
    else:
        print(f"{YELLOW}[!] Gagal mengambil data trafik.{RESET}")
        
    print(f"{MAGENTA}-----------------------------------------------------------------------{RESET}")


def auto_audit_olt(): # Menu 18 (OLT Tools)
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum aktif.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}=== AUTO AUDIT OLT SYSTEM ==={RESET}")
    print(f"{WHITE}[*] Memulai audit kesehatan jaringan...{RESET}")
    
    if brand == 'zte':
        # Perintah audit cepat untuk ZTE
        cmds = [
            "terminal length 0",
            "enable",
            "show pon power attenuation gpon-olt_1/1/1", # Ganti sesuai port utama
            "show gpon onu state gpon-olt_1/1/1",
            "show alarm current severity critical"
        ]
    else:
        # Untuk Fiberhome
        cmds = ["show card", "show port state", "show pon power attenuation"]

    output = telnet_olt_execute(creds, cmds)
    
    print(f"\n{WHITE}HASIL AUDIT OTOMATIS:{RESET}")
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
    
    if output:
        lines = output.splitlines()
        for line in lines:
            l_low = line.lower()
            
            # Deteksi Sinyal Lemah (Audit Power)
            if "dbm" in l_low:
                try:
                    # Mencari nilai numerik power, biasanya -27dBm ke atas itu buruk
                    power_val = float(''.join(filter(lambda x: x in "0123456789.-", line.split()[-1])))
                    if power_val < -27.0:
                        print(f"{RED}[BAD SIGNAL] {line.strip()}{RESET}")
                    else:
                        print(f"{GREEN}[OK] {line.strip()}{RESET}")
                except:
                    print(f"{WHITE}{line.strip()}{RESET}")
            
            # Deteksi ONU Offline
            elif any(x in l_low for x in ["offline", "los", "dyinggasp"]):
                print(f"{YELLOW}[OFFLINE/ALARM] {line.strip()}{RESET}")
            
            elif "working" in l_low or "online" in l_low:
                print(f"{GREEN}[ONLINE] {line.strip()}{RESET}")
            else:
                if line.strip() and "zxan" not in l_low:
                    print(f"{WHITE}{line.strip()}{RESET}")
    else:
        print(f"{YELLOW}[!] Audit gagal. Periksa koneksi ke OLT.{RESET}")
        
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")



def nmap_scan_tool(): # Menu 20
    print(f"\n{CYAN}=== NMAP NETWORK SCANNER ==={RESET}")
    print(f"{WHITE}Contoh: 192.168.1.1 atau 192.168.1.0/24{RESET}")
    target = input(f"{YELLOW}Masukkan IP/Subnet Target: {RESET}").strip()
    
    if not target:
        print(f"{YELLOW}[!] Target tidak boleh kosong.{RESET}")
        return

    print(f"\n{CYAN}[*] Memulai scanning pada {target}...{RESET}")
    print(f"{WHITE}[i] Menggunakan mode Fast Scan (-F)...{RESET}\n")
    
    try:
        os.system(f"nmap -F -v {target}")
    except Exception as e:
        print(f"{YELLOW}[!] Gagal menjalankan Nmap: {e}{RESET}")
        print(f"{WHITE}[i] Pastikan nmap sudah terinstall (pkg install nmap / apt install nmap).{RESET}")
    
    print(f"\n{MAGENTA}--------------------------------------------------{RESET}")


def mac_lookup_tool(): # Menu 21
    print(f"\n{CYAN}=== MAC LOOKUP / VENDOR CHECK ==={RESET}")
    mac = input(f"{WHITE}Masukkan MAC Address (contoh AA:BB:CC): {RESET}").strip()
    
    if not mac:
        print(f"{YELLOW}[!] MAC tidak boleh kosong.{RESET}")
        return

    print(f"{CYAN}[*] Mencari vendor...{RESET}")
    
    prefix = mac.upper().replace("-", ":")[:8]
    vendor = BRAND_MAP.get(prefix)

    if vendor:
        print(f"\n{GREEN}[✓] HASIL (Local): {vendor}{RESET}")
    else:
        vendor = get_brand(mac)
        print(f"\n{GREEN}[✓] HASIL (Online): {vendor}{RESET}")
    print(f"{MAGENTA}--------------------------------------------------{RESET}")


def port_scanner_tool(): # Menu 22
    print(f"\n{CYAN}=== PORT SCANNER (SPECIFIC TARGET) ==={RESET}")
    target = input(f"{WHITE}Masukkan IP Target: {RESET}").strip()
    
    if not target:
        print(f"{YELLOW}[!] IP Target tidak boleh kosong.{RESET}")
        return

    print(f"\n{MAGENTA}--- PILIH MODE SCAN ---{RESET}")
    print(" 1. Common Ports (Cek port standar: 21,22,23,80,443,8291)")
    print(" 2. Full Scan (Port 1-1000)")
    print(" 3. Custom Port (Input manual)")
    
    opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()

    if opt == '1':
        cmd = f"nmap -p 21,22,23,80,443,8291 {target}"
    elif opt == '2':
        cmd = f"nmap -p 1-1000 {target}"
    elif opt == '3':
        p_custom = input(f"{WHITE}Masukkan port (misal 80,8080): {RESET}")
        cmd = f"nmap -p {p_custom} {target}"
    else:
        return

    print(f"\n{CYAN}[*] Sedang memindai port pada {target}...{RESET}\n")
    os.system(cmd)
    print(f"\n{MAGENTA}--------------------------------------------------{RESET}")


def what_my_ip(): # Menu 23
    print(f"\n{CYAN}=== CEK INFORMASI IP PUBLIK ==={RESET}")
    print(f"{WHITE}[*] Mengambil data dari server...{RESET}")
    
    try:
        resp = requests.get('http://ip-api.com/json/', timeout=10).json()
        
        if resp.get('status') == 'success':
            print(f"\n{MAGENTA}--------------------------------------------------{RESET}")
            print(f"{WHITE}IP ADDRESS    : {GREEN}{resp.get('query')}{RESET}")
            print(f"{WHITE}ISP / AS      : {GREEN}{resp.get('isp')} ({resp.get('as')}){RESET}")
            print(f"{WHITE}NEGARA        : {GREEN}{resp.get('country')}{RESET}")
            print(f"{WHITE}KOTA / REGION : {GREEN}{resp.get('city')}, {resp.get('regionName')}{RESET}")
            print(f"{WHITE}TIMEZONE      : {GREEN}{resp.get('timezone')}{RESET}")
            print(f"{MAGENTA}--------------------------------------------------{RESET}")
        else:
            ip_simple = requests.get('https://ifconfig.me', timeout=5).text.strip()
            print(f"\n{GREEN}[✓] IP Publik: {ip_simple}{RESET}")
            
    except Exception as e:
        print(f"{YELLOW}[!] Gagal mengambil informasi IP: {e}{RESET}")


def ping_traceroute_tool(): # Menu 24
    print(f"\n{CYAN}=== PING & TRACEROUTE TOOLS ==={RESET}")
    target = input(f"{WHITE}Masukkan Host/IP (contoh google.com atau 8.8.8.8): {RESET}").strip()
    
    if not target:
        print(f"{YELLOW}[!] Host/IP tidak boleh kosong.{RESET}")
        return

    print(f"\n{MAGENTA}--- PILIH METODE ---{RESET}")
    print(" 1. Ping Test (Cek Latency/RTO)")
    print(" 2. Traceroute (Lacak Jalur/Hop)")
    print(" 0. Kembali")
    
    opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()

    if opt == '1':
        print(f"\n{CYAN}[*] Menjalankan Ping ke {target}...{RESET}")
        os.system(f"ping -c 5 {target}")
    elif opt == '2':
        print(f"\n{CYAN}[*] Menjalankan Traceroute ke {target}...{RESET}")
        print(f"{WHITE}[i] Mohon tunggu, ini mungkin memakan waktu beberapa saat.{RESET}\n")
        os.system(f"traceroute {target} 2>/dev/null || mtr -rw {target}")
    else:
        return

    print(f"\n{MAGENTA}--------------------------------------------------{RESET}")


def dns_tools(): # Menu 25
    print(f"\n{CYAN}=== DNS LOOKUP TOOLS ==={RESET}")
    domain = input(f"{WHITE}Masukkan Domain (contoh google.com): {RESET}").strip()
    
    if not domain:
        print(f"{YELLOW}[!] Domain tidak boleh kosong.{RESET}")
        return

    print(f"\n{MAGENTA}--- PILIH INFORMASI DNS ---{RESET}")
    print(" 1. Cek IP Address (A Record)")
    print(" 2. Cek Name Server (NS Record)")
    print(" 3. Cek Semua Record (MX, TXT, NS, A, TXT)")
    print(" 0. Kembali")
    
    opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()
    if opt == '0' or not opt: return

    print(f"\n{CYAN}[*] Mengambil data DNS untuk {domain}...{RESET}")
    
    # Mapping tipe record untuk API Google
    # Tipe 1=A, 2=NS, 15=MX, 16=TXT, 255=ANY
    type_map = {'1': 1, '2': 2, '3': 255}
    record_type = type_map.get(opt, 1)

    try:
        # Menggunakan Google Public DNS API (Sangat stabil)
        url = f"https://dns.google/resolve?name={domain}&type={record_type}"
        resp = requests.get(url, timeout=10)
        
        if resp.status_code != 200:
            print(f"{RED}[!] Server DNS Google merespon dengan kode: {resp.status_code}{RESET}")
            return
            
        data = resp.json()

        if "Answer" in data:
            print(f"\n{GREEN}HASIL LOOKUP ({domain}):{RESET}")
            print(f"{WHITE}{'-'*55}{RESET}")
            
            # Dictionary untuk menerjemahkan angka tipe DNS ke teks
            names = {1: "A", 2: "NS", 5: "CNAME", 15: "MX", 16: "TXT", 28: "AAAA"}
            
            for ans in data['Answer']:
                t_name = names.get(ans['type'], f"Type-{ans['type']}")
                val = ans['data']
                print(f" {YELLOW}[{t_name:<5}]{RESET} {val}")
        else:
            print(f"{RED}[!] Tidak ada record yang ditemukan untuk tipe tersebut.{RESET}")

    except Exception as e:
        print(f"{RED}[!] Error Koneksi: {e}{RESET}")

    print(f"\n{MAGENTA}--------------------------------------------------{RESET}")


def update_tools_auto(): # Menu 26
    print(f"\n{CYAN}=== UPDATE & RESET TOOLS (FORCE SYNC) ==={RESET}")
    repo_url = "https://github.com/USERNAME_KAMU/NAMA_REPO.git" # <-- GANTI DENGAN URL REPO KAMU
    
    # Cek apakah ini folder git
    if not os.path.exists(".git"):
        print(f"{YELLOW}[!] Folder ini bukan repository Git.{RESET}")
        confirm = input(f"{WHITE}Ingin menginisialisasi ulang Git di folder ini? (y/n): {RESET}").lower()
        if confirm == 'y':
            os.system("git init")
            os.system(f"git remote add origin {repo_url}")
            print(f"{GREEN}[✓] Git berhasil diinisialisasi.{RESET}")
        else:
            return

    print(f"{WHITE}[*] Membersihkan cache git lokal...{RESET}")
    try:
        os.system("git fetch --all")
        print(f"{CYAN}[*] Menarik kode terbaru dari GitHub...{RESET}")
        
        # Coba paksa sinkronisasi ke branch main atau master
        result = os.popen("git reset --hard origin/main 2>&1").read()
        
        if "HEAD is now at" in result:
            print(f"\n{GREEN}[✓] BERHASIL! Kode sudah paling baru (Main).{RESET}")
        else:
            # Jika main gagal, coba master
            result_master = os.popen("git reset --hard origin/master 2>&1").read()
            if "HEAD is now at" in result_master:
                print(f"\n{GREEN}[✓] BERHASIL! Kode sudah paling baru (Master).{RESET}")
            else:
                print(f"{RED}[!] Gagal sinkronisasi. Cek koneksi internet atau URL repo.{RESET}")
                print(f"{WHITE}Log: {result_master.strip()}{RESET}")

    except Exception as e:
        print(f"{RED}[!] Error: {e}{RESET}")
    
    print(f"{MAGENTA}--------------------------------------------------{RESET}")


def show_menu():
    v = load_vault(); prof = v.get("active_profile", "Ucenk")
    os.system('clear')
    os.system('echo "==================================================================" | lolcat 2>/dev/null')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat 2>/dev/null')
    os.system('echo "        Premium Network Management System - Author: Ucenk" | lolcat 2>/dev/null')
    os.system('echo "==================================================================" | lolcat 2>/dev/null')
    os.system('neofetch --ascii_distro hacker 2>/dev/null')
    os.system('echo "============================ NOC TOOLS ===========================" | lolcat 2>/dev/null')
    print(f"\n{WHITE}                      PROFILE AKCTIVE: {GREEN}{prof}{RESET}")
    os.system('echo "==================================================================" | lolcat 2>/dev/null')
    
    print(f"\n{YELLOW}=== MIKROTIK TOOLS ===")

    print(f"\n{CYAN} 1.  Mikhmon Server                    5. Bandwidth Usage Report   ")
    print(f"\n{CYAN} 2.  Total User Aktif Hotspot          6. Backup & Restore MikroTik")
    print(f"\n{CYAN} 3.  Cek DHCP Alert (Rogue)            7. SNMP Monitoring          ")
    print(f"\n{CYAN} 4.  Hapus Script Mikhmon              8. Log Viewer MikroTik      ")

    print(f"\n{YELLOW}=== OLT TOOLS ===")

    print(f"\n{CYAN} 9.  Lihat ONU Terdaftar              14. Port & VLAN Config       ")
    print(f"\n{CYAN} 10. Konfigurasi ONU (ZTE/FH)         15. Alarm & Event Viewer     ")
    print(f"\n{CYAN} 11. Restart ONU                      16. Backup & Restore OLT     ")
    print(f"\n{CYAN} 12. Reset/Delete ONU                 17. Traffic Report per PON   ")
    print(f"\n{CYAN} 13. Cek Power Optic (Redaman)        18. Auto Audit Script        ")

    print(f"\n{YELLOW}=== NETWORK TOOLS ===")

    print(f"\n{CYAN} 19. Speedtest                        23. WhatMyIP                 ")
    print(f"\n{CYAN} 20. Nmap Scan                        24. Ping & Traceroute        ")
    print(f"\n{CYAN} 21. MAC Lookup                       25. DNS Tools                ")
    print(f"\n{CYAN} 22. Port Scaner                      26. Update-Tools             ")
    print(f"\n{GREEN} 99. Profile Setting{RESET}\n{YELLOW} 0 . Exit{RESET}")
    os.system('echo "======================= github.com/UceNk-Tech =====================" | lolcat 2>/dev/null')





def main():
    while True:
        show_menu()
        c = input(f"\n{YELLOW}Pilih Nomor: {RESET}").strip()
        if c == '1': run_mikhmon()
        elif c == '2': mk_hotspot_active()
        elif c == '3': cek_dhcp_rogue()
        elif c == '4': hapus_laporan_mikhmon()
        elif c == '5': bandwidth_usage_report()
        elif c == '6': backup_restore_mikrotik()
        elif c == '7': snmp_monitoring()
        elif c == '8': log_viewer_mikrotik()
        elif c == '9': list_onu()
        elif c == '10': config_onu_logic()
        elif c == '11': restart_onu()
        elif c == '12': reset_onu()
        elif c == '13': check_optical_power_fast()
        elif c == '14': port_vlan()
        elif c == '15': alarm_event_viewer()
        elif c == '16': backup_restore_olt()
        elif c == '17': traffic_report_pon()
        elif c == '18': auto_audit_olt()    
        elif c == '19': os.system("speedtest-cli")
        elif c == '20': nmap_scan_tool()
        elif c == '21': mac_lookup_tool()
        elif c == '22': port_scanner_tool()
        elif c == '23': what_my_ip()
        elif c == '24': ping_traceroute_tool()
        elif c == '25': dns_tools()
        elif c == '26': update_tools_auto()
        elif c == '99': manage_profiles()
        elif c == '0': sys.exit()
        input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__": main()
