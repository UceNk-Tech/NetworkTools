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
    prompt = "ZXAN" if creds.get('brand') == 'zte' else "OLT"
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        
        # Login Process
        tn.read_until(b"Username:", timeout=5)
        tn.write(creds['user'].encode('utf-8') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(creds['pass'].encode('utf-8') + b"\n")
        
        time.sleep(1) # Tunggu login stabil
        
        output = ""
        for cmd in commands:
            tn.write((cmd + "\n").encode('utf-8'))
            # Beri jeda antar perintah agar OLT tidak pusing (terutama ZTE)
            time.sleep(1.2) 
            output += tn.read_very_eager().decode('utf-8', errors='ignore')
            
        tn.close()
        return output
    except Exception as e:
        print(f"{RED}Error Telnet: {e}{RESET}")
        return None

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
    except Exception as e: print(f"{RED}Error: {e}{RESET}")

def hapus_laporan_mikhmon():
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{RED}[!] Profile MikroTik belum diset. Pilih menu 22 dulu.{RESET}")
        return

    print(f"\n{CYAN}[+] Menghubungkan ke MikroTik {creds['ip']}...{RESET}")
    try:
        conn = routeros_api.RouterOsApiPool(
            creds['ip'], 
            username=creds['user'], 
            password=creds['pass'], 
            port=8728, 
            plaintext_login=True
        )
        api = conn.get_api()
        resource = api.get_resource('/system/script')
        
        # 1. Pindai script yang namanya mengandung 'mikhmon'
        print(f"{CYAN}[+] Memindai script laporan Mikhmon...{RESET}")
        all_scripts = resource.get()
        
        # Filter script yang ada komentar atau nama 'mikhmon' sesuai gambar
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

def bandwidth_usage_report(): # Menu 5
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum diset.{RESET}")
        return

    print(f"\n{CYAN}[+] Menghubungkan ke MikroTik {creds['ip']}...{RESET}")
    print(f"{WHITE}[*] Mengambil data traffic (Tekan Ctrl+C untuk berhenti)...{RESET}\n")
    
    try:
        pool = routeros_api.RouterOsApiPool(
            creds['ip'], 
            username=creds['user'], 
            password=creds['pass'], 
            plaintext_login=True
        )
        api = pool.get_api()
        resource = api.get_resource('/interface')

        print(f"{MAGENTA}{'INTERFACE':<20} {'TX (Upload)':<15} {'RX (Download)':<15}{RESET}")
        print(f"{WHITE}" + "-"*52 + f"{RESET}")

        # Loop sederhana untuk monitoring real-time singkat
        for _ in range(1): # Kamu bisa ganti range jika ingin looping terus
            interfaces = resource.get()
            for iface in interfaces:
                name = iface.get('name')
                # Mengambil data byte/detik dan konversi ke unit yang mudah dibaca
                tx_bps = int(iface.get('tx-byte', 0)) * 8
                rx_bps = int(iface.get('rx-byte', 0)) * 8
                
                def format_speed(bps):
                    if bps > 1000000: return f"{round(bps/1000000, 2)} Mbps"
                    if bps > 1000: return f"{round(bps/1000, 2)} Kbps"
                    return f"{bps} bps"

                # Tampilkan hanya interface yang aktif (running) agar tidak penuh
                if iface.get('running') == 'true':
                    print(f"{CYAN}{name:<20}{RESET} {YELLOW}{format_speed(tx_bps):<15}{RESET} {GREEN}{format_speed(rx_bps):<15}{RESET}")
        
        pool.disconnect()
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[-] Monitoring dihentikan.{RESET}")
    except Exception as e:
        print(f"{YELLOW}[!] Error: {e}{RESET}")


def backup_restore_mikrotik(): # Menu 6
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

def snmp_monitoring(): # Menu 7
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum aktif.{RESET}")
        return

    print(f"\n{CYAN}=== SNMP MONITORING MIKROTIK ==={RESET}")
    print(f"{WHITE}[*] Mengambil data sistem via API...{RESET}")
    
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()

        # 1. Resource System
        res_data = api.get_resource('/system/resource').get()
        res = res_data[0] if res_data else {}
        
        # 2. Routerboard Info
        rb_data = api.get_resource('/system/routerboard').get()
        rb = rb_data[0] if rb_data else {}
        
        # 3. Health (Voltage/Temp)
        health = api.get_resource('/system/health').get()

        print(f"\n{MAGENTA}--------------------------------------------------{RESET}")
        print(f"{WHITE}MODEL PERANGKAT : {GREEN}{res.get('board-name', 'Unknown')} ({res.get('architecture-name', 'N/A')}){RESET}")
        print(f"{WHITE}SERIAL NUMBER   : {GREEN}{rb.get('serial-number', 'N/A')}{RESET}")
        print(f"{WHITE}UPTIME          : {GREEN}{res.get('uptime', 'N/A')}{RESET}")
        print(f"{WHITE}ROUTEROS VER    : {GREEN}{res.get('version', 'N/A')}{RESET}")
        print(f"{MAGENTA}--------------------------------------------------{RESET}")
        
        # Load Stats
        cpu_load = res.get('cpu-load', '0')
        free_mem = int(res.get('free-memory', 0)) / 1024 / 1024
        total_mem = int(res.get('total-memory', 0)) / 1024 / 1024
        
        print(f"{WHITE}CPU LOAD       : {YELLOW}{cpu_load}%{RESET}")
        print(f"{WHITE}FREE MEMORY    : {YELLOW}{round(free_mem, 1)} MB / {round(total_mem, 1)} MB{RESET}")
        
        # Iterasi Health dengan proteksi NoneType
        if health:
            for h in health:
                name = h.get('name')
                value = h.get('value')
                # Cek jika name tidak None sebelum di-upper
                if name:
                    label = str(name).upper()
                    print(f"{WHITE}{label:<14} : {YELLOW}{value}{RESET}")
                elif value: # Jika nama tidak ada tapi nilai ada
                    print(f"{WHITE}SENSOR         : {YELLOW}{value}{RESET}")
        
        print(f"{MAGENTA}--------------------------------------------------{RESET}")

        pool.disconnect()
    except Exception as e:
        print(f"{YELLOW}[!] Gagal SNMP Scan: {e}{RESET}")


def log_viewer_mikrotik(): # Menu 8
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

            # Pewarnaan yang aman (Simple & Stable)
            color = WHITE
            low_msg = message.lower() # Kita pisah variabelnya di sini supaya tidak error
            
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
        

def list_onu(): # Menu 9
    creds = get_credentials("olt")
    if not creds: 
        print(f"{RED}[!] Profile OLT belum diset.{RESET}")
        return
        
    p = input(f"{WHITE}Input Port (contoh 1/3/1): {RESET}")
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}[+] Mengambil daftar semua ONU di port {p}...{RESET}")
    
    if brand == 'zte':
        # Perintah 'show pon onu information' adalah yang paling lengkap untuk ZTE
        cmds = [
            "terminal length 0", 
            "end", 
            f"show pon onu information gpon-olt_{p}"
        ]
    else:
        cmds = ["terminal length 0", "end", f"show onu status port {p}"]
        
    output = telnet_olt_execute(creds, cmds)
    
    if output:
        print(f"\n{WHITE}==== DAFTAR ONU TERDAFTAR (PORT {p}) ===={RESET}")
        print(f"{WHITE}{output}{RESET}")
    else:
        print(f"{RED}[!] Gagal mengambil data atau port kosong.{RESET}")
        

def config_onu_logic(): # Menu 10
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum diset.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    found_sn = ""
    
    print(f"\n{MAGENTA}=== MONITOR & REGISTRASI ONU ==={RESET}")
    p = input(f"{WHITE}Input Port Lokasi (contoh 1/4/1): {RESET}").strip()

    # --- 1. SCAN UNCONFIGURED ---
    print(f"\n{CYAN}[+] Memeriksa ONU Unconfigured...{RESET}")
    cmd_scan = ["terminal length 0", "enable", "show gpon onu uncfg"] if brand == 'zte' else ["terminal length 0", f"show onu unconfigured port {p}"]
    res_unconfig = telnet_olt_execute(creds, cmd_scan)
    
    if res_unconfig and any(x in res_unconfig.upper() for x in ["FHTT", "ZTEG", "SN", "ONUINDEX"]):
        print(f"\n{YELLOW}⚠️  ONU TERDETEKSI (Hasil Scan):{RESET}")
        print(f"{WHITE}{res_unconfig}{RESET}")
        sn_match = re.search(r'(FHTT|ZTEG)[0-9A-Z]{8,}', res_unconfig.upper())
        if sn_match:
            found_sn = sn_match.group(0)
            print(f"{GREEN}[✓] SN Otomatis Disimpan: {found_sn}{RESET}")
    else:
        print(f"{CYAN}[i] Scan Selesai: Tidak menemukan ONU baru yang unconfigured.{RESET}")

    while True:
        # --- 2. PILIH TINDAKAN ---
        print(f"\n{MAGENTA}--- PILIH TINDAKAN (PORT {p}) ---{RESET}")
        print(f" 1. {YELLOW}Scan ONU ID Kosong (Cari nomor bolong){RESET}")
        print(f" 2. {CYAN}Registrasi ZTE (Hotspot){RESET}")
        print(f" 3. {CYAN}Registrasi ZTE (PPPoE){RESET}")
        print(f" 4. {WHITE}Registrasi FH (Hotspot){RESET}")
        print(f" 5. {WHITE}Registrasi FH (PPPoE){RESET}")
        print(f" 6. {GREEN}Cek Status & Power Optik{RESET}") 
        print(f" 0. {YELLOW}Keluar/Kembali{RESET}")
        
        opt = input(f"\n{YELLOW}Pilih aksi (0-6): {RESET}")

        if opt == '0' or not opt: 
            break

        # --- OPTION 1: SCAN ID KOSONG ----
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
                        print(f"{CYAN}[i] Tidak ada nomor bolong (ID 1 sampai {max_id} terisi).{RESET}")
                    print(f"\n{GREEN}[+] SARAN ID BARU: {max_id + 1}{RESET}")
                    print(f"{MAGENTA}--------------------------------------------------{RESET}")
            continue

        # --- OPTION 6: OPTICAL POWER ---
        if opt == '6':
            print(f"\n{CYAN}[+] Menampilkan Laporan Optical Power Port {p}...{RESET}")
            cmds = ["terminal length 0", "enable", f"show pon optical-power gpon-olt_{p}"] if brand == 'zte' else ["terminal length 0", f"show onu optical-power {p}"]
            output = telnet_olt_execute(creds, cmds)
            
            print(f"\n{WHITE}LAPORAN REDAMAN PORT {p}:{RESET}")
            print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
            if output:
                for line in output.splitlines():
                    if "dbm" in line.lower() and "show" not in line.lower():
                        if found_sn and found_sn in line.upper():
                            print(f"{GREEN}>>> {line.strip()} (ONU BARU){RESET}")
                        else:
                            print(f"{YELLOW}    {line.strip()}{RESET}")
            print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
            continue

        # --- PROSES REGISTRASI ---
        if opt in ['2', '3', '4', '5']:
            onu_id = input(f"{WHITE}Masukkan ID ONU (misal 16): {RESET}").strip()
            sn = input(f"{WHITE}Masukkan SN ONU [{found_sn}]: {RESET}").strip() or found_sn
            vlan = input(f"{WHITE}VLAN ID: {RESET}").strip()
            name = input(f"{WHITE}Nama Pelanggan: {RESET}").strip().replace(" ", "_")
            
            cmds = []
            
            # ZTE HOTSPOT (2)
            if opt == '2':
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1",
                    f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    f"vlan port wifi_0/1 mode tag vlan {vlan}", f"vlan port eth_0/1 mode tag vlan {vlan}",
                    "security-mgmt 1 state enable mode forward protocol web", "end", "write"
                ]
            
            # ZTE PPPOE (3) - REVISED
            elif opt == '3':
                user = input(f"{WHITE}User PPPoE: {RESET}").strip()
                pw = input(f"{WHITE}Pass PPPoE: {RESET}").strip()
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1",
                    "exit", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    f"wan-ip 1 mode pppoe username {user} password {pw} vlan {vlan} priority 0",
                    "security-mgmt 1 state enable mode forward protocol web", "end", "write"
                ]

            # FH HOTSPOT (4)
            elif opt == '4':
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1",
                    "exit", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    f"vlan port wifi_0/1 mode tag vlan {vlan}", "end", "write"
                ]

            # FH PPPOE (5) - REVISED
            elif opt == '5':
                user = input(f"{WHITE}User PPPoE: {RESET}").strip()
                pw = input(f"{WHITE}Pass PPPoE: {RESET}").strip()
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1",
                    "exit", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", "wan 1 mode pppoe",
                    f"wan 1 pppoe username {user} password {pw}", f"wan 1 vlan {vlan} priority 0",
                    "wan 1 service-type internet", "wan 1 binding-port eth_0/1 wifi_0/1", "end", "write"
                ]

            if cmds:
                print(f"\n{CYAN}[*] Mengirim konfigurasi PPPoE/Hotspot...{RESET}")
                result = telnet_olt_execute(creds, cmds)
                print(f"{GREEN}[✓] Registrasi Selesai!{RESET}")
                break

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

def check_optical_power_fast():
    """Menu 13: Cek Power Optik - Split Input & Yellow Alert Version"""
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum aktif.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}=== CEK STATUS & POWER OPTIK ONU ==={RESET}")
    # Input dipisah sesuai permintaan Ucenk
    port = input(f"{WHITE}Masukkan Port (contoh 1/1/1): {RESET}").strip()
    onu_id = input(f"{WHITE}ONU ID: {RESET}").strip()
    target = f"{port}:{onu_id}"
    
    if brand == 'fiberhome':
        cmds = ["terminal length 0", f"show onu optical-power {port} {onu_id}"]
    else:
        # Strategi ZTE (V1.2 / V2.1)
        cmds = [
            "terminal length 0",
            "enable",
            f"show gpon onu state gpon-olt_{port} {onu_id}",
            f"show pon optical-power gpon-onu_{target}",
            f"show gpon onu detail-info gpon-onu_{target}"
        ]

    print(f"\n{CYAN}[*] Menghubungkan ke OLT...{RESET}")
    output = telnet_olt_execute(creds, cmds)
    
    print(f"\n{WHITE}HASIL DIAGNOSA UNTUK ONU {onu_id}:{RESET}")
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
    
    if not output:
        print(f"{YELLOW}[!] Gagal mengambil data. Periksa koneksi ke OLT.{RESET}")
        return

    lines = output.splitlines()
    found_data = False

    for line in lines:
        line_clean = line.strip()
        l_low = line_clean.lower()
        
        # Abaikan baris perintah agar output bersih
        if any(x in l_low for x in ["show ", "terminal length", "enable"]):
            continue

        # 1. Cek Status Offline/LOS - Sekarang Warna Kuning (YELLOW)
        if any(x in l_low for x in ["offline", "dyinggasp", "los", "logging"]):
            print(f"{YELLOW}[!] STATUS ONU: OFFLINE ({line_clean}){RESET}")
            found_data = True
        
        # 2. Cek Status Working (Online)
        elif "working" in l_low:
            print(f"{GREEN}[✓] STATUS ONU: ONLINE (WORKING){RESET}")
            found_data = True

        # 3. Ambil data Power (dBm)
        elif "dbm" in l_low:
            if "not online" in l_low or "n/a" in l_low:
                print(f"{YELLOW}>>> POWER OPTIK: Tidak Terdeteksi (ONU sedang mati){RESET}")
            else:
                print(f"{GREEN}>>> {line_clean}{RESET}")
            found_data = True
        
        # 4. Info Tambahan (Channel, Authpass, Phase, dll)
        elif any(x in l_low for x in ["channel", "multicast", "authpass", "time", "cause", "phase"]):
            print(f"    {line_clean}")
            found_data = True

    if not found_data:
        if "Invalid" in output or "%" in output:
            print(f"{YELLOW}[!] Error: Perintah tidak dikenal atau ONU belum terdaftar.{RESET}")
            print(f"{WHITE}[i] Tips: Pastikan port {port} dan ID {onu_id} sudah benar.{RESET}")
        else:
            print(f"{WHITE}Respon OLT:{RESET}\n{output}")
            
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")

def port_vlan(): # Menu 14
    c = get_credentials("olt"); p = input("ONU (1/1/1:1): "); v = input("VLAN: ")
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

    print(f"\n{CYAN}[*] Mengambil data dari OLT...{RESET}")
    
    if brand == 'zte':
        # Penyesuaian perintah ZTE agar lebih universal
        if opt == '1':
            # Untuk alarm yang sedang aktif
            cmds = ["terminal length 0", "show alarm current"]
        else:
            # Perintah history yang lebih umum di ZTE
            cmds = ["terminal length 0", "show alarm history all"]
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
        # Bersihkan output dari echo perintah
        lines = output.splitlines()
        for line in lines:
            l_low = line.lower()
            # Filter baris sampah/prompt
            if any(x in l_low for x in ["terminal length", "show alarm", "zxan#", "zxan>"]):
                continue
            
            # Deteksi error dari OLT
            if "%error" in l_low:
                print(f"{RED}[!] OLT Command Error: {line.strip()}{RESET}")
                print(f"{WHITE}[i] Coba ganti perintah ke: 'show alarm history' tanpa 'all' jika manual.{RESET}")
                continue

            # Highlight status krusial
            if any(x in l_low for x in ["critical", "major", "los", "dyinggasp", "off-line"]):
                print(f"{YELLOW}{line.strip()}{RESET}")
            else:
                print(f"{WHITE}{line.strip()}{RESET}")
    else:
        print(f"{YELLOW}[!] Tidak ada respon dari OLT.{RESET}")
        
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
            # Catatan: Perintah upload bervariasi tergantung versi firmware
        else:
            cmds = ["copy running-config ftp"] # Contoh FH

        result = telnet_olt_execute(creds, cmds)
        print(f"{GREEN}[✓] Perintah backup dikirim. Silakan cek di server FTP kamu.{RESET}")

    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")


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
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
    
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
        
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")


def nmap_scan_tool(): # Menu 19
    print(f"\n{CYAN}=== NMAP NETWORK SCANNER ==={RESET}")
    print(f"{WHITE}Contoh: 192.168.1.1 atau 192.168.1.0/24{RESET}")
    target = input(f"{YELLOW}Masukkan IP/Subnet Target: {RESET}").strip()
    
    if not target:
        print(f"{YELLOW}[!] Target tidak boleh kosong.{RESET}")
        return

    print(f"\n{CYAN}[*] Memulai scanning pada {target}...{RESET}")
    print(f"{WHITE}[i] Menggunakan mode Fast Scan (-F)...{RESET}\n")
    
    # Menjalankan nmap dengan mode -F (Fast Scan) agar tidak terlalu lama
    # -v untuk verbose agar Ucenk bisa lihat prosesnya
    try:
        os.system(f"nmap -F -v {target}")
    except Exception as e:
        print(f"{YELLOW}[!] Gagal menjalankan Nmap: {e}{RESET}")
        print(f"{WHITE}[i] Pastikan nmap sudah terinstall (pkg install nmap / apt install nmap).{RESET}")
    
    print(f"\n{MAGENTA}--------------------------------------------------{RESET}")


def mac_lookup_tool(): # Menu 20 (Sesuai urutan baru)
    print(f"\n{CYAN}=== MAC LOOKUP / VENDOR CHECK ==={RESET}")
    mac = input(f"{WHITE}Masukkan MAC Address (contoh AA:BB:CC): {RESET}").strip()
    
    if not mac:
        print(f"{YELLOW}[!] MAC tidak boleh kosong.{RESET}")
        return

    print(f"{CYAN}[*] Mencari vendor...{RESET}")
    
    # Cek Database Lokal dulu
    prefix = mac.upper().replace("-", ":")[:8]
    vendor = BRAND_MAP.get(prefix)

    if vendor:
        print(f"\n{GREEN}[✓] HASIL (Local): {vendor}{RESET}")
    else:
        # Cek Online
        vendor = get_brand(mac)
        print(f"\n{GREEN}[✓] HASIL (Online): {vendor}{RESET}")
    print(f"{MAGENTA}--------------------------------------------------{RESET}")

def port_scanner_tool(): # Menu 21
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


def what_my_ip(): # Menu 22
    print(f"\n{CYAN}=== CEK INFORMASI IP PUBLIK ==={RESET}")
    print(f"{WHITE}[*] Mengambil data dari server...{RESET}")
    
    try:
        # Mengambil data lengkap dari API ip-api.com
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
            # Fallback jika ip-api gagal, pakai ifconfig.me (hanya IP saja)
            ip_simple = requests.get('https://ifconfig.me', timeout=5).text.strip()
            print(f"\n{GREEN}[✓] IP Publik: {ip_simple}{RESET}")
            
    except Exception as e:
        print(f"{YELLOW}[!] Gagal mengambil informasi IP: {e}{RESET}")

def ping_traceroute_tool(): # Menu 23
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
        # -c 5 artinya ping dilakukan 5 kali
        os.system(f"ping -c 5 {target}")
    elif opt == '2':
        print(f"\n{CYAN}[*] Menjalankan Traceroute ke {target}...{RESET}")
        print(f"{WHITE}[i] Mohon tunggu, ini mungkin memakan waktu beberapa saat.{RESET}\n")
        # Menggunakan mtr atau traceroute (tergantung ketersediaan di sistem)
        os.system(f"traceroute {target} 2>/dev/null || mtr -rw {target}")
    else:
        return

    print(f"\n{MAGENTA}--------------------------------------------------{RESET}")

def dns_tools(): # Menu 24
    print(f"\n{CYAN}=== DNS LOOKUP TOOLS ==={RESET}")
    domain = input(f"{WHITE}Masukkan Domain (contoh google.com atau mikhmon.online): {RESET}").strip()
    
    if not domain:
        print(f"{YELLOW}[!] Domain tidak boleh kosong.{RESET}")
        return

    print(f"\n{MAGENTA}--- PILIH INFORMASI DNS ---{RESET}")
    print(" 1. Cek IP Address (A Record)")
    print(" 2. Cek Name Server (NS Record)")
    print(" 3. Cek Semua Record (MX, TXT, NS, A)")
    print(" 0. Kembali")
    
    opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()

    print(f"\n{CYAN}[*] Mengambil data DNS untuk {domain}...{RESET}\n")
    
    try:
        if opt == '1':
            os.system(f"nslookup -type=A {domain}")
        elif opt == '2':
            os.system(f"nslookup -type=NS {domain}")
        elif opt == '3':
            # Menggunakan perintah 'dig' jika ada, jika tidak pakai nslookup
            os.system(f"dig {domain} ANY +short || nslookup -type=any {domain}")
        else:
            return
    except Exception as e:
        print(f"{YELLOW}[!] Gagal melakukan lookup: {e}{RESET}")

    print(f"\n{MAGENTA}--------------------------------------------------{RESET}")


def update_tools_auto(): # Menu 25
    print(f"\n{CYAN}=== UPDATE & RESET TOOLS (AUTO GIT) ==={RESET}")
    
    # Cek apakah ini folder git atau bukan
    if not os.path.exists(".git"):
        print(f"{RED}[!] Error: Folder ini bukan repositori Git.{RESET}")
        print(f"{WHITE}[i] Kamu harus melakukan git clone ulang atau init di folder ini.{RESET}")
        repo_url = input(f"{YELLOW}Masukkan URL GitHub kamu: {RESET}").strip()
        if repo_url:
            print(f"{CYAN}[*] Menginisialisasi repositori...{RESET}")
            os.system("git init")
            os.system(f"git remote add origin {repo_url}")
            os.system("git fetch")
            os.system("git reset --hard origin/main")
        return

    # Jika folder Git sudah benar, jalankan reset
    confirm = input(f"{YELLOW}Lanjutkan Hard Reset ke origin/main? (y/n): {RESET}").lower()
    if confirm == 'y':
        print(f"\n{CYAN}[*] Sinkronisasi dengan GitHub...{RESET}")
        # Urutan perintah agar bersih
        os.system("git fetch origin")
        os.system("git checkout origin/main -- menu.py") # Update file menu.py saja
        os.system("git reset --hard origin/main")
        print(f"\n{GREEN}[✓] Sukses! Kode telah dipaksa mengikuti versi GitHub.{RESET}")
    else:
        print(f"{MAGENTA}[-] Update dibatalkan.{RESET}")

# --- MAIN INTERFACE ---
def show_menu():
    v = load_vault(); prof = v.get("active_profile", "Ucenk")
    os.system('clear')
    os.system('echo "=================================================================" | lolcat 2>/dev/null')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat 2>/dev/null')
    os.system('echo "        Premium Network Management System - Author: Ucenk" | lolcat 2>/dev/null')
    os.system('echo "=================================================================" | lolcat 2>/dev/null')
    os.system('neofetch --ascii_distro hacker 2>/dev/null')
    
    print(f"\n{WHITE}Profile Aktif: {GREEN}{prof}{RESET}")
    
    print(f"{CYAN}--- MIKROTIK TOOLS ---{RESET}")
    print("1.  Jalankan Mikhmon Server          5. Bandwidth Usage Report")
    print("2.  Total User Aktif Hotspot         6. Backup & Restore MikroTik")
    print("3.  Cek DHCP Alert (Rogue)           7. SNMP Monitoring")
    print("4.  Hapus Laporan Mikhmon            8. Log Viewer MikroTik")
    print(f"\n{CYAN}--- OLT TOOLS ---{RESET}")
    print("9.  Lihat ONU Terdaftar             14. Port & VLAN Config")
    print("10. Konfigurasi ONU (ZTE/FH)        15. Alarm & Event Viewer")
    print("11. Reset ONU                       16. Backup & Restore OLT")
    print("12. Delete ONU                      17. Traffic Report per PON")
    print("13. Cek Status Power Optic          18. Auto Audit Script")
    print(f"\n{CYAN}--- NETWORK TOOLS ---{RESET}")
    print("18. Speedtest                       22. WhatMyIP")
    print("19. Nmap Scan                       23. Ping & Traceroute")
    print("20. MAC Lookup                      24. DNS Tools")
    print("21. Port Scaner                     25. Update-Tools")
    print(f"\n{YELLOW}99. Profile Setting{RESET}\n{MAGENTA}0. Exit{RESET}")

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
        elif c == '11': reset_onu()
        elif c == '12': delete_onu()
        elif c == '13': check_optical_power_fast()
        elif c == '14': port_vlan()
        elif c == '15': alarm_event_viewer()
        elif c == '16': backup_restore_olt()
        elif c == '17': traffic_report_pon()
        elif c == '18': os.system("speedtest-cli")
        elif c == '19': nmap_scan_tool()
        elif c == '19': mac_lookup_tool()
        elif c == '21': port_scanner_tool()
        elif c == '22': what_my_ip()
        elif c == '23': ping_traceroute_tool()
        elif c == '24': dns_tools()
        elif c == '25': update_tools_auto()
        elif c == '99': manage_profiles()
        elif c == '0': sys.exit()
        input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__": main()
