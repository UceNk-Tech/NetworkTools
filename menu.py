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
# --- OLT TOOLS (9-18) ---

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
    print("17. Speedtest                       22. WhatMyIP")
    print("18. Nmap Scan                       23. Ping & Traceroute")
    print("19. MAC Lookup                      24. DNS Tools")
    print("20. Port Scaner                     25. Update-Tools")
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
        elif c == '13': check_optical_power_fast()
        elif c == '14': port_vlan()
        elif c == '17': os.system("speedtest-cli")
        elif c == '20': os.system(f"nmap -F {input('IP: ')}")
        elif c == '22': print(f"IP: {requests.get('https://ifconfig.me').text.strip()}")
        elif c == '99': manage_profiles()
        elif c == '0': sys.exit()
        input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__": main()
