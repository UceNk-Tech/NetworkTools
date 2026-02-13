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
import requests
import io
from contextlib import redirect_stdout

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

def mk_hotspot_active(): # Menu 2
    c = get_credentials("mikrotik")
    if not c: 
        print(f"{RED}[!] Profile belum diset.{RESET}")
        return
    try:
        pool = routeros_api.RouterOsApiPool(c['ip'], username=c['user'], password=c['pass'], plaintext_login=True)
        api = pool.get_api()
        # Mengambil semua resource tanpa filter limit
        act = api.get_resource('/ip/hotspot/active').get()
        
        print(f"\n{GREEN}>>> TOTAL USER AKTIF: {len(act)} {RESET}")
        
        # Header Tabel
        print(f"{WHITE}{'No':<4} | {'User':<15} | {'IP Address':<15} | {'Uptime':<10} | {'MAC Address':<18}{RESET}")
        print("-" * 75)

        # Loop SEMUA user tanpa batasan [:]
        for i, user in enumerate(act, start=1):
            u_name = user.get('user', 'N/A')
            u_ip   = user.get('address', 'N/A')
            u_time = user.get('uptime', '0s')
            u_mac  = user.get('mac-address', 'N/A')
            
            # Highlight warna hijau untuk pelanggan (bukan admin)
            color = GREEN if u_name.lower() != 'admin' else YELLOW
            print(f" {i:<3} | {color}{u_name:<15}{RESET} | {u_ip:<15} | {CYAN}{u_time:<10}{RESET} | {u_mac:<18}")
            
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
            tanya = f"{CYAN}>>> Hapus semua script laporan ini? {YELLOW}(y/n){RED}: {RESET}"
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

def bandwidth_usage_report(): # Menu 5 - LIVE TRAFFIC
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{YELLOW}[!] Profile MikroTik belum diset.{RESET}")
        return

    print(f"\n{CYAN}[+] Monitoring Live Traffic Ethernet: {creds['ip']}{RESET}")
    print(f"{WHITE}[*] Tekan Ctrl+C untuk berhenti dan kembali ke menu.{RESET}\n")
    
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()
        resource = api.get_resource('/interface')

        def format_speed(bps):
            if bps >= 1000000: return f"{round(bps/1000000, 2)} Mbps"
            if bps >= 1000: return f"{round(bps/1000, 2)} Kbps"
            return f"{int(bps)} bps"

        prev_data = {}
        first_run = True
        num_interfaces = 0

        while True:
            # Filter hanya port fisik ethernet/sfp
            all_interfaces = resource.get()
            active_eth = [i for i in all_interfaces if i.get('type') in ['ether', 'sfp']]
            
            current_time = time.time()
            
            # Jika bukan baris pertama, naikkan kursor sebanyak jumlah interface + header
            if not first_run:
                # Naik sebanyak jumlah interface yang ditampilkan + 2 baris header
                sys.stdout.write(f"\033[{num_interfaces + 2}F")

            # Cetak Header
            print(f"{MAGENTA}{'INTERFACE':<20} | {'TX (UPLOAD)':<15} | {'RX (DOWNLOAD)':<15}{RESET}")
            print(f"{WHITE}{'-'*55}{RESET}")

            count = 0
            for iface in active_eth:
                name = iface.get('name')
                tx_byte = int(iface.get('tx-byte', 0))
                rx_byte = int(iface.get('rx-byte', 0))

                if name in prev_data:
                    last_tx, last_rx, last_time = prev_data[name]
                    interval = current_time - last_time
                    
                    tx_bps = ((tx_byte - last_tx) * 8) / interval
                    rx_bps = ((rx_byte - last_rx) * 8) / interval

                    # \033[K digunakan untuk menghapus sisa karakter di baris tersebut agar tidak tumpang tindih
                    print(f"{CYAN}{name:<20}{RESET} | {YELLOW}{format_speed(tx_bps):<15}{RESET} | {GREEN}{format_speed(rx_bps):<15}{RESET}\033[K")
                else:
                    # Tampilan awal saat data delta belum ada
                    print(f"{CYAN}{name:<20}{RESET} | {YELLOW}{'0 bps':<15}{RESET} | {GREEN}{'0 bps':<15}{RESET}\033[K")
                
                prev_data[name] = (tx_byte, rx_byte, current_time)
                count += 1

            num_interfaces = count
            first_run = False
            sys.stdout.flush()
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        # Pindahkan kursor ke paling bawah setelah selesai agar tidak menimpa saat balik ke menu
        print(f"\n\n{YELLOW}[-] Monitoring dihentikan. Kembali ke menu utama...{RESET}")
        if 'pool' in locals(): pool.disconnect()
    except Exception as e:
        print(f"\n{RED}[!] Error: {e}{RESET}")
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

    print(f"\n{CYAN}=== LOG VIEWER MIKROTIK ==={RESET}")
    try:
        pool = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = pool.get_api()
        logs = api.get_resource('/log').get()
        last_logs = logs[-50:]

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


# --- CORE EXECUTION (Alice Engine) ---
def telnet_olt_execute(creds, cmds):
    RED = '\033[0;31m'; GREEN = '\033[0;32m'; YELLOW = '\033[0;33m'
    CYAN = '\033[0;36m'; RESET = '\033[0m'
    
    try:
        tn = telnetlib.Telnet(creds['ip'], timeout=15)
        
        # Proses Login
        tn.read_until(b"Username:", timeout=5)
        tn.write(creds['user'].encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(creds['pass'].encode('ascii') + b"\n")
        
        time.sleep(1)
        
        # Persiapan Mode
        tn.write(b"end\n")
        tn.write(b"enable\n")
        tn.write(b"terminal length 0\n")
        time.sleep(0.5)
        
        tn.read_very_eager()
        
        full_output = ""
        for cmd in cmds:
            tn.write(cmd.encode('ascii') + b"\n")
            res = tn.read_until(b"#", timeout=15).decode('ascii', errors='ignore')
            full_output += res
            time.sleep(0.2)
            
        tn.write(b"exit\n")
        tn.close()
        return full_output
    except Exception as e:
        print(f"{RED}[!] Telnet Error: {e}{RESET}")
        return None

# --- OLT TOOLS: LIST ONU AKTIF ---
def list_onu(): 
    creds = get_credentials("olt")
    if not creds: return
        
    p = input(f"{WHITE}Input Port (1/1/1): {RESET}").strip()
    print(f"\n{CYAN}[+] Meminta data ONU aktif di port {p}...{RESET}")
    
    cmds = [f"show pon onu information gpon-olt_{p}"]
    output = telnet_olt_execute(creds, cmds)
    
    print(f"\n{WHITE}==== HASIL PEMBACAAN OLT (PORT {p}) ===={RESET}")
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
    
    if output:
        lines = output.splitlines()
        found_data = False
        for line in lines:
            if f"{p}:" in line or "SN(" in line.upper():
                if "show " not in line.lower():
                    print(f"{WHITE}{line.strip()}{RESET}")
                    found_data = True
        
        if not found_data:
            print(f"{YELLOW}[!] Tidak ada ONU aktif terdeteksi di port {p}.{RESET}")
    else:
        print(f"{RED}[!] Gagal mengambil data OLT.{RESET}")
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
    

# --- MONITOR & REGISTRASI LENGKAP (VERSI FULL UTUH TANPA POTONGAN) ---
def config_onu_logic(): 
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum diset.{RESET}")
        return
    
    found_sn = ""
    saran_id_global = ""
    brand = creds.get('brand', 'zte').lower()
    
    # --- STEP 1: SCAN UNCONFIGURED ---
    print(f"\n{CYAN}[+] Memeriksa ONU Unconfigured...{RESET}")
    cmd_scan = ["show gpon onu uncfg"]
    res_unconfig = telnet_olt_execute(creds, cmd_scan)
    
    if res_unconfig:
        clean_res = [l.strip() for l in res_unconfig.splitlines() if any(x in l.upper() for x in ["FHTT", "ZTEG", "SN"])]
        if clean_res:
            print(f"\n{YELLOW}⚠️  ONU TERDETEKSI:{RESET}")
            print(f"{WHITE}--------------------------------------------------{RESET}")
            for r in clean_res:
                if "show" not in r.lower(): print(f"{WHITE}{r}{RESET}")
            print(f"{WHITE}--------------------------------------------------{RESET}")
            sn_match = re.search(r'(FHTT|ZTEG)[0-9A-Z]{8,}', res_unconfig.upper())
            if sn_match:
                found_sn = sn_match.group(0)
                print(f"{GREEN}[✓] SN Otomatis Disimpan: {found_sn}{RESET}")
        else:
            print(f"{YELLOW}[i] Tidak ada ONU uncfg.{RESET}")

    # --- STEP 2: INPUT PORT & AUTO CARI ID ---
    p = input(f"\n{WHITE}Input Port Lokasi (contoh 1/1/1): {RESET}").strip()
    if not p: return

    print(f"{CYAN}[*] Menganalisa ID kosong di port {p}...{RESET}")
    res_list = telnet_olt_execute(creds, [f"show pon onu information gpon-olt_{p}"])
    
    if res_list:
        ids_found = re.findall(rf"{re.escape(p)}:(\d+)", res_list)
        ids_int = sorted(list(set([int(x) for x in ids_found])))
        if not ids_int: saran_id_global = "1"
        else:
            max_id = max(ids_int)
            missing = [x for x in range(1, max_id + 1) if x not in ids_int]
            saran_id_global = str(missing[0]) if missing else str(max_id + 1)
        print(f"{GREEN}[✓] SARAN ONU ID: {saran_id_global}{RESET}")

    # --- LOOPING UTAMA MENU ---
    while True:
        print(f"\n{MAGENTA}--- PILIH JENIS TINDAKAN ---{RESET}")
        print(f" 1. {GREEN}Registrasi ZTE (Hotspot Only){RESET}")
        print(f" 2. {GREEN}Registrasi ZTE (Hotspot + PPPoE){RESET}")
        print(f" 3. {GREEN}Registrasi FH  (Hotspot Only){RESET}")
        print(f" 4. {CYAN}Cek Detail Power Optik Unconfigured{RESET}") 
        print(f" 0. {YELLOW}Batal/Keluar{RESET}")

        opt = input(f"\n{YELLOW}Pilih (0-4): {RESET}").strip()
        
        if opt == '0' or not opt: 
            break

        # --- OPSI 4: CEK OPTIK DENGAN TUNGGU SINKRON ---
        if opt == '4':
            if not found_sn: 
                print(f"{RED}[!] SN tidak ditemukan. Tidak bisa cek.{RESET}")
                continue 
            
            test_id = "128"
            print(f"\n{CYAN}[+] Meminjam ID {test_id} untuk diagnosa...{RESET}")
            
            # Daftarkan ONU sementara
            telnet_olt_execute(creds, ["conf t", f"interface gpon-olt_{p}", f"onu {test_id} type ALL sn {found_sn}", "exit"])
            
            got_signal = False
            for attempt in range(1, 5):
                print(f"{YELLOW}[Attempt {attempt}/4] Menunggu ONU sinkron & membaca redaman...{RESET}")
                time.sleep(5)
                
                check_cmds = ["terminal length 0"]
                if brand == 'fiberhome': check_cmds.append(f"show onu optical-power {p} {test_id}")
                else: check_cmds.append(f"show pon power attenuation gpon-onu_{p}:{test_id}")
                
                output = telnet_olt_execute(creds, check_cmds)
                
                if output:
                    lines = output.splitlines()
                    clean_lines = []
                    rx_val = None
                    
                    for line in lines:
                        ls = line.strip()
                        if not ls or any(x in ls for x in ["ZXAN", "config", "Successful", "terminal length", "show pon", "Info", "Error", "marker", "^"]):
                            continue
                        clean_lines.append(line)
                        if "down" in line.lower() and "Rx" in line:
                            matches = re.findall(r"Rx\s*:\s*(-?\d+\.\d+)", line)
                            if matches: rx_val = float(matches[0])

                    if rx_val is not None:
                        got_signal = True
                        clean_output = "\n".join(clean_lines)
                        print(f"\n{WHITE}HASIL DIAGNOSA (SN: {found_sn}):{RESET}")
                        print(f"{MAGENTA}--------------------------------------------------------------------------------------------------------------------------------------{RESET}")
                        print(f"{YELLOW}{clean_output}{RESET}")
                        print(f"{MAGENTA}--------------------------------------------------------------------------------------------------------------------------------------{RESET}")
                        
                        if rx_val < -27.0: color, status = RED, "CRITICAL (DROP)"
                        elif rx_val < -25.0: color, status = YELLOW, "WARNING (REDAUP)"
                        else: color, status = GREEN, "NORMAL (BAGUS)"
                        
                        print(f"{WHITE}Identity ONU        : {MAGENTA}{p}:{test_id} (Temp){RESET}")
                        print(f"{WHITE}Redaman (Rx ONU)    : {color}{rx_val} dBm{RESET}")
                        print(f"{WHITE}Kondisi             : {color}{status}{RESET}")
                        print(f"{MAGENTA}--------------------------------------------------------------------------------------------------------------------------------------{RESET}")
                        break

            if not got_signal:
                print(f"{RED}[!] Data Rx belum terbaca (ONU belum up atau kabel putus).{RESET}")
            
            # Hapus kembali ONU pancingan
            telnet_olt_execute(creds, ["conf t", f"interface gpon-olt_{p}", f"no onu {test_id}", "end"])
            continue 

       # --- PROSES REGISTRASI (OPSI 1-3) ---
        if opt in ['1', '2', '3']:
            onu_id = input(f"{WHITE}Masukkan ID ONU [Saran: {saran_id_global}]: {RESET}").strip() or saran_id_global
            sn = input(f"{WHITE}Masukkan SN ONU [{found_sn}]: {RESET}").strip() or found_sn
            raw_name = input(f"{WHITE}Nama Pelanggan: {RESET}").strip()
            name = raw_name.replace(" ", "_")
            cmds = []

            if opt == '1': # ZTE HOTSPOT ONLY
                vlan = input(f"{WHITE}VLAN Hotspot: {RESET}")
                prof = input(f"{WHITE}Tcont Profile [{CYAN}default/{YELLOW}server]: {RESET}") or "default"
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL-ONT sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", f"description 1$${raw_name}$$",
                    f"tcont 1 profile {prof}", "gemport 1 tcont 1", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}",
                    "exit", f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    "interface wifi wifi_0/1 state unlock", f"vlan port wifi_0/1 mode tag vlan {vlan}",
                    f"vlan port eth_0/1 mode tag vlan {vlan}", f"vlan port eth_0/2 mode tag vlan {vlan}",
                    "security-mgmt 212 state enable mode forward protocol web", "end", "write"
                ]

            elif opt == '2': # ZTE MIX (PPPoE + Hotspot)
                vp = input(f"{WHITE}VLAN PPPoE: {RESET}").strip()
                vh = input(f"{WHITE}VLAN Hotspot: {RESET}").strip()
                prof = input(f"{WHITE}Tcont Profile [{CYAN}default/{YELLOW}server]: {RESET}").strip() or "default"
                u = input(f"{WHITE}User PPPoE: {RESET}").strip()
                pw = input(f"{WHITE}Pass PPPoE: {RESET}").strip()
                auto_v_w = f"VLAN{vp}-PPPOE"
                ssid = input(f"{WHITE}Nama SSID Hotspot: {RESET}").strip()
                
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL-ONT sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", f"description 1$${raw_name}$$",
                    f"tcont 1 profile {prof}", f"tcont 2 profile {prof}", "gemport 1 tcont 1", "gemport 2 tcont 2",
                    f"service-port 1 vport 1 user-vlan {vp} vlan {vp}", f"service-port 2 vport 2 user-vlan {vh} vlan {vh}", "exit",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vp}", f"service 2 gemport 2 vlan {vh}",
                    f"wan-ip 1 mode pppoe username {u} password {pw} vlan-profile {auto_v_w} host 1",
                    "security-mgmt 212 state enable mode forward protocol web", "interface wifi wifi_0/2 state unlock",
                    "ssid auth wep wifi_0/2 open-system", f"ssid ctrl wifi_0/2 name {ssid}", f"vlan port wifi_0/2 mode tag vlan {vh}",
                    f"vlan port eth_0/1 mode tag vlan {vp}", f"vlan port eth_0/2 mode tag vlan {vp}", f"vlan port eth_0/3 mode tag vlan {vp}",
                    "end", "write"
                ]

            elif opt == '3': # FIBERHOME HOTSPOT
                prof = input(f"{WHITE}Profile Tcont [{CYAN}default/{YELLOW}server]: {RESET}").strip() or "default"
                vlan = input(f"{WHITE}Vlan ID: {RESET}").strip()
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", f"description 1$${raw_name}$$",
                    f"tcont 1 profile {prof}", "gemport 1 tcont 1", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}",
                    "exit", f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    "vlan port veip_1 mode hybrid", f"vlan port wifi_0/1 mode tag vlan {vlan}",
                    f"vlan port eth_0/1 mode tag vlan {vlan}", f"vlan port eth_0/2 mode tag vlan {vlan}",
                    "dhcp", "end", "write"
                ]

            if cmds:
                print(f"\n{CYAN}[*] Mengirim konfigurasi ke OLT...{RESET}")
                telnet_olt_execute(creds, cmds)
                print(f"{GREEN}[✓] Registrasi Selesai!{RESET}")
                
                # --- AUTO CEK OPTIK SETELAH REGISTRASI ---
                print(f"\n{CYAN}[*] Menunggu ONU online untuk cek redaman...{RESET}")
                got_signal_final = False
                for attempt in range(1, 5):
                    print(f"{YELLOW}[Attempt {attempt}/4] Mencoba baca optik...{RESET}")
                    time.sleep(5) 
                    
                    check_cmds = ["terminal length 0"]
                    if brand == 'fiberhome': 
                        check_cmds.append(f"show onu optical-power {p} {onu_id}")
                    else: 
                        check_cmds.append(f"show pon power attenuation gpon-onu_{p}:{onu_id}")
                    
                    output = telnet_olt_execute(creds, check_cmds)
                    
                    if output:
                        rx_val = None
                        lines = output.splitlines()
                        for line in lines:
                            # Mengambil baris 'down' agar dapat Rx sisi ONU
                            if "down" in line.lower() and "Rx" in line:
                                match = re.search(r"Rx\s*:\s*(-?\d+\.\d+)", line)
                                if match:
                                    rx_val = float(match.group(1))
                                    break
                        
                        if rx_val is not None:
                            got_signal_final = True
                            if rx_val < -27.0: color, status = RED, "CRITICAL (DROP)"
                            elif rx_val < -25.0: color, status = YELLOW, "WARNING (REDAUP)"
                            else: color, status = GREEN, "NORMAL (BAGUS)"
                            
                            print(f"\n{WHITE}HASIL CEK AKHIR:{RESET}")
                            print(f"{MAGENTA}---------------------------------------------{RESET}")
                            print(f"{WHITE}Identity ONU        : {MAGENTA}{p}:{onu_id}{RESET}")
                            print(f"{WHITE}Redaman (Rx ONU)    : {color}{rx_val} dBm{RESET}")
                            print(f"{WHITE}Kondisi             : {color}{status}{RESET}")
                            print(f"{MAGENTA}---------------------------------------------{RESET}")
                            break
                
                if not got_signal_final:
                    print(f"{RED}[!] ONU belum terdeteksi Online atau Rx ONU tidak terbaca.{RESET}")

                # --- BAGIAN KEMBALI KE MENU UTAMA ---
                input(f"\n{WHITE}Tekan Enter untuk kembali ke Menu Utama...{RESET}")
                return # Ini yang bikin dia langsung keluar ke menu awal
                

# --- MENU 11: REBOOT / RESTART ONU ---
def restart_onu():
    creds = get_credentials("olt")
    if not creds: return
    
    RED = '\033[0;31m'; GREEN = '\033[0;32m'; YELLOW = '\033[0;33m'
    CYAN = '\033[0;36m'; MAGENTA = '\033[0;35m'; WHITE = '\033[0;37m'; RESET = '\033[0m'
    
    print(f"\n{YELLOW}=== REBOOT / RESTART ONU ==={RESET}")
    port = input(f"{WHITE}Masukkan Port (contoh 1/1/1): {RESET}").strip()
    onu_id = input(f"{WHITE}Masukkan Nomor ONU: {RESET}").strip()
    
    if not port or not onu_id:
        print(f"{RED}[!] Input tidak lengkap!{RESET}"); return

    print(f"\n{CYAN}[*] Mengambil info ONU {port}:{onu_id}...{RESET}")
    # Alice: Pakai detail-info supaya SN-nya pasti keluar
    check_cmd = ["terminal length 0", f"show gpon onu detail-info gpon-onu_{port}:{onu_id}"]
    output = telnet_olt_execute(creds, check_cmd)
    
    if output and "No related" not in output:
        print(f"\n{YELLOW}--- DETAIL ONU DITEMUKAN ---{RESET}")
        # Alice: Tampilkan semua baris yang ada isinya biar SN kelihatan
        lines = output.splitlines()
        for line in lines:
            if any(x in line for x in [":", "SN", "State", "Phase", "Model", "Type"]):
                if "show" not in line: print(f"{WHITE}{line.strip()}{RESET}")
        
        print(f"{MAGENTA}-------------------------------------------{RESET}")
        confirm = input(f"{CYAN}Yakin mau REBOOT ONU ini? {YELLOW}(y/n): {RESET}").lower()
        
        if confirm == 'y':
            print(f"{YELLOW}[*] Mengirim perintah restart...{RESET}")
            # Alice: Tambahin 'conf t' supaya perintahnya lebih prioritas
            reboot_cmds = [
                "conf t",
                f"request gpon onu restart gpon-onu_{port}:{onu_id}",
                "end"
            ]
            telnet_olt_execute(creds, reboot_cmds)
            print(f"{GREEN}[✓] Perintah Reboot terkirim. (Cek lampu PON di modem){RESET}")
        else:
            print(f"{MAGENTA}[-] Reboot dibatalkan.{RESET}")
    else:
        print(f"{RED}[!] ONU tidak ditemukan atau OLT sibuk.{RESET}")


# --- MENU 12: RESET / HAPUS ONU ---
def reset_onu(): 
    creds = get_credentials("olt")
    if not creds: return
    
    RED = '\033[0;31m'; GREEN = '\033[0;32m'; YELLOW = '\033[0;33m'
    CYAN = '\033[0;36m'; MAGENTA = '\033[0;35m'; WHITE = '\033[0;37m'; RESET = '\033[0m'
    
    print(f"\n{RED}=== RESET / HAPUS ONU (DELETE) ==={RESET}")
    port = input(f"{WHITE}Masukkan Port (contoh 1/1/1): {RESET}").strip()
    onu_id = input(f"{WHITE}Masukkan Nomor ONU: {RESET}").strip()
    
    if not port or not onu_id:
        print(f"{RED}[!] Input tidak lengkap!{RESET}"); return

    print(f"\n{CYAN}[*] Mengambil data ONU {port}:{onu_id}...{RESET}")
    # Alice: Samakan pakai detail-info biar SN-nya muncul
    check_cmd = ["terminal length 0", f"show gpon onu detail-info gpon-onu_{port}:{onu_id}"]
    output = telnet_olt_execute(creds, check_cmd)
    
    if output and "No related" not in output:
        print(f"\n{YELLOW}--- DETAIL ONU YANG AKAN DIHAPUS ---{RESET}")
        lines = output.splitlines()
        for line in lines:
            if any(x in line for x in [":", "SN", "State", "Phase", "Model"]):
                if "show" not in line: print(f"{WHITE}{line.strip()}{RESET}")
        
        print(f"{MAGENTA}-------------------------------------------{RESET}")
        confirm = input(f"{CYAN}Yakin mau HAPUS ONU ini? {YELLOW}(y/n): {RESET}").lower()
        
        if confirm == 'y':
            print(f"{YELLOW}[*] Memproses penghapusan...{RESET}")
            reset_cmds = [
                "conf t",
                f"interface gpon-olt_{port}",
                f"no onu {onu_id}",
                "end",
                "write"
            ]
            telnet_olt_execute(creds, reset_cmds)
            print(f"{GREEN}[✓] ONU {port}:{onu_id} BERHASIL DIHAPUS.{RESET}")
        else:
            print(f"{MAGENTA}[-] Dibatalkan oleh user.{RESET}")
    else:
        print(f"{RED}[!] ONU tidak ditemukan.{RESET}")



# --- MENU 13: CEK POWER OPTIC/REDAMAN ---
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
    print(f"\n{CYAN}=== MAC LOOKUP ==={RESET}")
    mac = input(f"{WHITE}MAC Address: {RESET}").strip()
    
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
        print(f"\n{GREEN}[✓] VENDOR: {vendor}{RESET}")
    print(f"{MAGENTA}--------------------------------------------------{RESET}")


def port_scanner_tool(): # Menu 22
    print(f"\n{CYAN}=== PORT SCANNER ==={RESET}")
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
    domain = input(f"{WHITE}Domain (contoh google.com): {RESET}").strip()
    
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
        print(f"{CYAN}[*] Mendapatkan kode terbaru dari GitHub...{RESET}")
        
        # Coba paksa sinkronisasi ke branch main atau master
        result = os.popen("git reset --hard origin/main 2>&1").read()
        
        if "HEAD is now at" in result:
            print(f"\n{GREEN}[✓] BERHASIL! Kode sudah paling baru (Main).{RESET}")
        else:
            # Jika main gagal, coba master
            result_master = os.popen("git reset --hard origin/master 2>&1").read()
            if "HEAD is now at" in result_master:
                print(f"\n{GREEN}[✓] BERHASIL! Kode sudah paling baru.{RESET}")
            else:
                print(f"{RED}[!] Gagal sinkronisasi. Cek koneksi internet atau URL repo.{RESET}")
                print(f"{WHITE}Log: {result_master.strip()}{RESET}")

    except Exception as e:
        print(f"{RED}[!] Error: {e}{RESET}")
    
    print(f"{MAGENTA}--------------------------------------------------{RESET}")


def tanya_alice():
    # --- API KEY (Pastikan Key ini Aktif) ---
    API_KEY = "AIzaSyArLs7KtWTwb7p02OUhZtNLDTx1YPvtdlM".strip()
    
    # ⚠️ PERUBAHAN PENTING: GANTI KE GEMINI-PRO
    # Kalau flash error, pakai ini. Ini model paling universal.
    MODEL = "gemini-pro"
    
    # URL API
    URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent?key={API_KEY}"
    
    # Warna Termux
    RED = '\033[0;31m'; CYAN = '\033[0;36m'; MAGENTA = '\033[0;35m'; YELLOW = '\033[0;33m'; RESET = '\033[0m'
    
    print(f"\n{MAGENTA}[✨ Alice - Gemini Pro]{RESET} {CYAN}Halo Ucenk! Siap bantu.{RESET}")
    print(f"{YELLOW}(Ketik '0' untuk kembali){RESET}")

    while True:
        try:
            user_input = input(f"{YELLOW}Ucenk [90]: {RESET}").strip()
            
            if user_input.lower() in ['0', 'keluar', 'exit']: 
                print(f"{CYAN}Alice Offline.{RESET}")
                break
            
            if not user_input: continue

            output_eksekusi = "Tidak ada data sistem tambahan."

            # --- 1. INTEGRASI OTOMATIS ---
            if any(k in user_input.lower() for k in ["hotspot", "mikrotik", "user"]):
                print(f"{CYAN}(Bentar, cek Mikrotik...){RESET}")
                f = io.StringIO()
                with redirect_stdout(f):
                    try:
                        if 'mk_hotspot_active' in globals(): mk_hotspot_active()
                        else: print("Fungsi mk_hotspot_active belum dimuat.")
                    except: pass
                output_eksekusi = f.getvalue()

            elif any(k in user_input.lower() for k in ["onu", "olt", "pon"]):
                print(f"{CYAN}(Bentar, cek OLT...){RESET}")
                f = io.StringIO()
                with redirect_stdout(f):
                    try:
                        if 'list_onu' in globals(): list_onu()
                        else: print("Fungsi list_onu belum dimuat.")
                    except: pass
                output_eksekusi = f.getvalue()

            # --- 2. KIRIM KE GOOGLE ---
            headers = {'Content-Type': 'application/json'}
            
            # Format Prompt Standar
            prompt_text = f"Kamu Alice (Asisten Ucenk). Data: {output_eksekusi}. Pertanyaan: {user_input}"

            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}]
            }

            response = requests.post(URL, headers=headers, json=payload)
            res_json = response.json()
            
            if response.status_code == 200:
                try:
                    jawaban = res_json['candidates'][0]['content']['parts'][0]['text']
                    print(f"\n{MAGENTA}Alice: {RESET}{jawaban.replace('**', '')}\n")
                except:
                    print(f"\n{RED}[!] Respon kosong.{RESET}")
            else:
                # Kalau masih error, berarti KEY-nya yang bermasalah, bukan kodenya.
                msg = res_json.get('error', {}).get('message', 'Unknown Error')
                print(f"\n{RED}[!] Error Google ({response.status_code}): {msg}{RESET}")

        except Exception as e:
            print(f"\n{RED}[!] Script Error: {e}{RESET}")



def show_menu():
    v = load_vault(); prof = v.get("active_profile", "Ucenk")
    os.system('clear')
    os.system('echo "==================================================================" | lolcat 2>/dev/null')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat 2>/dev/null')
    os.system('echo "        Premium Network Management System - Author: Ucenk" | lolcat 2>/dev/null')
    os.system('echo "==================================================================" | lolcat 2>/dev/null')
 
    os.system('echo "============================ NOC TOOLS ===========================" | lolcat 2>/dev/null')
    print(f"\n{WHITE}                      PROFILE AKCTIVE: {GREEN}{prof}{RESET}")
    os.system('echo "==================================================================" | lolcat 2>/dev/null')
    
    print(f"\n{YELLOW}=== MIKROTIK TOOLS ===")

    print(f"\n{CYAN} 1.  Mikhmon Server                    5. Live Traffic Monitoring  ")
    print(f"\n{CYAN} 2.  Active Users Hotspot              6. MikroTik Backup & Restore")
    print(f"\n{CYAN} 3.  DHCP Alert (Rogue)                7. SNMP Monitoring          ")
    print(f"\n{CYAN} 4.  Remove Mikhmon Script             8. MikroTik Log Viewer       ")

    print(f"\n{YELLOW}=== OLT TOOLS ===")

    print(f"\n{CYAN} 9.  View Registered ONU              14. Port & VLAN Config       ")
    print(f"\n{CYAN} 10. ONU Configuration (ZTE/FH)       15. Alarm & Event Viewer     ")
    print(f"\n{CYAN} 11. Restart/Reboot ONU               16. Backup & Restore OLT     ")
    print(f"\n{CYAN} 12. Reset/Delete ONU                 17. Traffic Report per PON   ")
    print(f"\n{CYAN} 13. Check Optical Power (RX/TX)      18. Auto Audit Script        ")

    print(f"\n{YELLOW}=== NETWORK TOOLS ===")

    print(f"\n{CYAN} 19. Speedtest                        23. WhatMyIP                 ")
    print(f"\n{CYAN} 20. Nmap                             24. Ping & Traceroute        ")
    print(f"\n{CYAN} 21. MAC Lookup                       25. DNS Checker              ")
    print(f"\n{CYAN} 22. Port Scaner                      26. Update-Tools             ")
    print(f"\n{CYAN} 90. Tanya Alice (Asisten AI){RESET}\n{GREEN} 99. Profile Setting{RESET}\n{YELLOW} 0 . Exit{RESET}")
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
        elif c == '90': tanya_alice()
        elif c == '99': manage_profiles()
        elif c == '0': sys.exit()
        input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__": main()
