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
        print(f"{WHITE}             SETTING PROFILE JARINGAN               {RESET}")
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

# --- FUNGSI TOOLS ---
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

def run_mikhmon():
    print(f"\n{CYAN}[+] Menyiapkan Mikhmon Server...{RESET}")
    mikhmon_path = os.path.expanduser("~/mikhmonv3")
    session_path = os.path.expanduser("~/session_mikhmon")
    tmp_path = os.path.expanduser("~/tmp")

    # 1. Pastikan folder mikhmon ada, kalau belum download dulu
    if not os.path.exists(mikhmon_path):
        print(f"{YELLOW}[*] Mendownload file Mikhmon...{RESET}")
        os.system(f"git clone https://github.com/laksa19/mikhmonv3.git {mikhmon_path}")

    # 2. Pastikan folder session & tmp ada
    os.makedirs(session_path, exist_ok=True)
    os.makedirs(tmp_path, exist_ok=True)

    # 3. JURUS SAKTI: Buat custom.ini agar PHP tidak pakai jalur sistem yang terkunci
    # Ini menghapus error 'Permission Denied' dan 'Lock' secara permanen
    with open(os.path.join(tmp_path, "custom.ini"), "w") as f:
        f.write("opcache.enable=0\n")
        f.write(f'session.save_path="{session_path}"\n')
        f.write(f'sys_temp_dir="{tmp_path}"\n')
        f.write("display_errors=Off\n")

    # 4. Bersihkan port 8080 jika masih nyangkut
    os.system("fuser -k 8080/tcp > /dev/null 2>&1")

    print(f"{GREEN}[!] Mikhmon Aktif: http://127.0.0.1:8080{RESET}")
    print(f"{RED}[!] Tekan Ctrl+C untuk Berhenti & Kembali ke Menu{RESET}\n")
    
    # Jalankan dengan export agar PHP membaca custom.ini kita
    cmd = f"export PHP_INI_SCAN_DIR={tmp_path} && php -S 127.0.0.1:8080 -t {mikhmon_path}"
    
    try:
        os.system(cmd)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}[-] Server Mikhmon dimatikan.{RESET}")
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

def telnet_olt_execute(creds, commands):
    if not creds: return None
    prompt = "ZXAN#" if creds.get('brand') == 'zte' else "OLT#"
    try:
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=15)
        tn.read_until(b"Username:", timeout=5)
        tn.write(creds['user'].encode('utf-8') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(creds['pass'].encode('utf-8') + b"\n")
        
        # Masuk ke prompt utama
        tn.read_until(prompt.encode('utf-8'), timeout=5)
        
        # FORCE: Matikan paging agar semua data keluar sekaligus
        tn.write(b"terminal length 0\n")
        time.sleep(0.5)
        
        output = ""
        for cmd in commands:
            tn.write((cmd + "\n").encode('utf-8'))
            # Beri jeda lebih lama untuk perintah 'show' yang datanya banyak
            if "show" in cmd:
                time.sleep(2.0) 
            else:
                time.sleep(0.8)
            
            # Baca semua data yang ada di buffer
            output += tn.read_very_eager().decode('utf-8', errors='ignore')
            
        tn.close()
        return output.strip()
    except Exception as e:
        print(f"{RED}Error Telnet: {e}{RESET}")
        return None

def mikrotik_hotspot_active():
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{RED}[!] Profile belum diset.{RESET}")
        return
    try:
        conn = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True)
        api = conn.get_api()
        active = api.get_resource('/ip/hotspot/active').get()
        print(f"\n{GREEN}>>> TOTAL USER AKTIF: {len(active)} {RESET}")
        for user in active[:10]:
            print(f" - {user.get('user')} | IP: {user.get('address')}")
        conn.disconnect()
    except Exception as e: print(f"{RED}Error: {e}{RESET}")

def list_onu_aktif():
    creds = get_credentials("olt")
    if not creds: 
        print(f"{RED}[!] Profile OLT belum diset.{RESET}")
        return
        
    p = input(f"{WHITE}Input Port (contoh 1/3/1): {RESET}")
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}[+] Mengambil daftar semua ONU di port {p}...{RESET}")
    
    if brand == 'zte':
        # Kita pakai 'terminal length 0' agar tidak ada --More--
        # Perintah 'show pon onu information' adalah yang paling lengkap
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

def monitor_optical_power():
    creds = get_credentials("olt")
    if not creds: 
        print(f"{RED}[!] Profile OLT belum diset.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    found_sn = ""
    
    print(f"\n{MAGENTA}=== MONITOR & REGISTRASI ONU ==={RESET}")
    p = input(f"{WHITE}Input Port Lokasi (contoh 1/4/1): {RESET}")

    # --- 1. SCAN UNCONFIGURED ---
    print(f"\n{CYAN}[+] Memeriksa ONU Unconfigured...{RESET}")
    # Tambah 'terminal length 0' agar output tidak terpotong
    cmd_scan = ["terminal length 0", "end", "show gpon onu uncfg"] if brand == 'zte' else ["terminal length 0", "end", f"show onu unconfigured port {p}"]
    res_unconfig = telnet_olt_execute(creds, cmd_scan)
    
    if res_unconfig and any(x in res_unconfig.upper() for x in ["FHTT", "ZTEG", "SN"]):
        print(f"\n{YELLOW}⚠️  ONU TERDETEKSI (Hasil Scan):{RESET}")
        print(f"{WHITE}{res_unconfig}{RESET}")
        sn_match = re.search(r'(FHTT|ZTEG)[0-9A-Z]{8,}', res_unconfig.upper())
        if sn_match:
            found_sn = sn_match.group(0)
            print(f"\n{GREEN}[✓] SN Otomatis Disimpan: {found_sn}{RESET}")
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
        print(f" 0. {RED}Keluar/Kembali{RESET}")
        
        opt = input(f"\n{YELLOW}Pilih aksi (0-6): {RESET}")

        if opt == '0' or not opt: 
            break

        # --- FUNGSI SCAN ID KOSONG ----
        if opt == '1':
            print(f"\n{CYAN}[*] Menganalisa daftar ID di port {p}...{RESET}")
            # Kita pakai 'show gpon onu state' karena formatnya lebih konsisten untuk ditarik angkanya
            cmd_list = ["terminal length 0", "end", f"show gpon onu state gpon-olt_{p}"] if brand == 'zte' else ["terminal length 0", "end", f"show onu status port {p}"]
            res_list = telnet_olt_execute(creds, cmd_list)
            
            if res_list:
                # REGEX BARU: Mencari angka setelah ':' dan sebelum spasi/tab
                # Contoh: 1/3/1:116 -> akan ambil 116
                ids_found = re.findall(r':(\d{1,3})\s+', res_list)
                
                # Ubah ke list angka, hilangkan duplikat, dan urutkan
                ids_int = sorted(list(set([int(x) for x in ids_found])))
                
                if not ids_int:
                    print(f"{CYAN}[i] Port {p} terlihat kosong. Silakan pakai ID 1.{RESET}")
                else:
                    max_id = max(ids_int)
                    # Deteksi semua ID yang tidak ada di list dari 1 sampai max_id
                    missing_ids = [x for x in range(1, max_id + 1) if x not in ids_int]
                    
                    print(f"{MAGENTA}--------------------------------------------------{RESET}")
                    if missing_ids:
                        # Kita tampilkan per baris kalau banyak, supaya tidak pusing bacanya
                        print(f"{YELLOW}[!] ID KOSONG (Siap Pakai):{RESET}")
                        # Pecah missing_ids jadi string per 10 angka supaya rapi
                        chunks = [map(str, missing_ids[i:i + 10]) for i in range(0, len(missing_ids), 10)]
                        for chunk in chunks:
                            print(f"{WHITE}    {', '.join(chunk)}{RESET}")
                    else:
                        print(f"{CYAN}[i] Tidak ada nomor bolong (ID 1 sampai {max_id} terisi penuh).{RESET}")
                    
                    print(f"{GREEN}[+] ID TERAKHIR TERPAKAI: {max_id}{RESET}")
                    print(f"{GREEN}[+] SARAN ID BARU        : {max_id + 1}{RESET}")
                    print(f"{MAGENTA}--------------------------------------------------{RESET}")
            else:
                print(f"{RED}[!] OLT tidak merespon perintah scan ID.{RESET}")
            continue

        # --- OPTICAL POWER ---
        if opt == '6':
            print(f"\n{CYAN}[+] Menampilkan Laporan Optical Power Port {p}...{RESET}")
            cmds = ["end", f"show pon optical-power gpon-olt_{p}"] if brand == 'zte' else ["end", f"show onu optical-power {p}"]
            output = telnet_olt_execute(creds, cmds)
            print(f"\n{WHITE}{output}{RESET}")
            continue

        # --- PROSES INPUT PARAMETER REGISTRASI ---
        if opt in ['2', '3', '4', '5']:
            onu_id = input(f"{WHITE}Masukkan ID ONU (misal 16): {RESET}")
            sn = input(f"{WHITE}Masukkan SN ONU [{found_sn}]: {RESET}") or found_sn
            vlan = input(f"{WHITE}VLAN ID: {RESET}")
            name = input(f"{WHITE}Nama Pelanggan: {RESET}").replace(" ", "_")
            
            cmds = []
            
            # ZTE LOGIC
            if opt == '2': # ZTE HOTSPOT
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1",
                    f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    f"vlan port wifi_0/1 mode tag vlan {vlan}", f"vlan port eth_0/1 mode tag vlan {vlan}",
                    "security-mgmt 212 state enable mode forward protocol web", "end", "write"
                ]
            elif opt == '3': # ZTE PPPOE
                user = input(f"{WHITE}User PPPoE: {RESET}")
                pw = input(f"{WHITE}Pass PPPoE: {RESET}")
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", "tcont 1 profile server", "gemport 1 tcont 1",
                    f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    f"wan-ip mode pppoe {user} password {pw} vlan-profile pppoe host 1",
                    "security-mgmt 212 state enable mode forward protocol web", "end", "write"
                ]
            
            # FIBERHOME LOGIC
            elif opt == '4': # FH HOTSPOT
                cmds = [
                    "con t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", f"description 1$${name}$$",
                    "tcont 1 profile server", "gemport 1 tcont 1",
                    f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    "vlan port veip_1 mode hybrid", f"vlan port wifi_0/1 mode tag vlan {vlan}", 
                    "dhcp", "end", "write"
                ]
            elif opt == '5': # FH PPPOE
                cmds = [
                    "con t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", f"description 1$${name}$$",
                    "tcont 1 profile server", "gemport 1 tcont 1",
                    f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    "vlan port veip_1 mode hybrid", f"vlan port wifi_0/1 mode tag vlan {vlan}",
                    "dhcp", "end", "write"
                ]

            if cmds:
                print(f"\n{CYAN}[*] Mengirim konfigurasi & Save (Write)...{RESET}")
                result = telnet_olt_execute(creds, cmds)
                print(f"{GREEN}[✓] Registrasi & Write Selesai!{RESET}")
                print(f"{WHITE}{result}{RESET}")
                # Langsung keluar ke menu utama setelah registrasi sukses
                break


def reset_onu():
    creds = get_credentials("olt")
    if not creds: return
    t = input("Slot/Port/ID (1/1/1): ")
    try:
        s, p, oid = t.split("/")
        cmds = ["conf t", f"interface gpon-olt_1/{s}/{p}", f"no onu {oid}", "end"]
        print(telnet_olt_execute(creds, cmds))
    except:
        print(f"{RED}Format salah!{RESET}")

def show_menu():
    vault = load_vault()
    prof = vault.get("active_profile", "None (Pilih menu 22)")
    os.system('clear')
    os.system('echo "=================================================================" | lolcat 2>/dev/null')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat 2>/dev/null')
    os.system('echo "      Premium Network Management System - Author: Ucenk" | lolcat 2>/dev/null')
    os.system('echo "=================================================================" | lolcat 2>/dev/null')
    os.system('neofetch --ascii_distro hacker 2>/dev/null')
    
    print(f"\n{WHITE}Aktif Profile: {GREEN}{prof}{RESET}")
    
    print(f"{GREEN}--- MIKROTIK TOOLS ---{RESET}")
    print(f"1. Jalankan Mikhmon Server          5. Bandwidth Usage Report")
    print(f"2. Total User Aktif Hotspot         6. Backup & Restore MikroTik")
    print(f"3. Cek DHCP Alert (Rogue)           7. SNMP Monitoring")
    print(f"4. Hapus Laporan Mikhmon            8. Log Viewer MikroTik")

    print(f"\n{GREEN}--- OLT TOOLS ---{RESET}")
    print(f"9. Lihat ONU Terdaftar              13. Alarm & Event Viewer")
    print(f"10. Konfigurasi ONU (ZTE/FH)        14. Backup & Restore OLT")
    print(f"{RED}11. Reset ONU{RESET}                       15. Traffic Report per PON")
    print(f"12. Port & VLAN Config              16. Auto Audit Script")

    print(f"\n{GREEN}--- NETWORK TOOLS ---{RESET}")
    print(f"17. Speedtest CLI                   20. Ping & Traceroute")
    print(f"18. Nmap Scan                       21. DNS Tools")
    print(f"19. MAC Lookup                      {YELLOW}22. PROFILE SETTINGS{RESET}")

    print(f"\n{MAGENTA}0. Keluar{RESET}")
    print(f"{YELLOW}Pilih Nomor: {RESET}", end="")

def main():
    while True:
        show_menu()
        c = input().strip()
        if c == '1': run_mikhmon()
        elif c == '2': mikrotik_hotspot_active()
        elif c == '3': cek_dhcp_rogue()
        elif c == '4': hapus_laporan_mikhmon()
        elif c == '9': list_onu_aktif()
        elif c == '10': monitor_optical_power()
        elif c == '11': reset_onu()
        elif c == '17': os.system("speedtest-cli --simple")
        elif c == '19':
            mac = input("Masukkan MAC Address: ")
            print(f"{CYAN}Brand: {get_brand(mac)}{RESET}")
        elif c == '22': manage_profiles()
        elif c == '0': 
            print(f"{GREEN}Sampai jumpa lagi, Bro!{RESET}")
            sys.exit()
        elif c: 
            print(f"{YELLOW}Fitur {c} sedang dikembangkan.{RESET}")
        
        input(f"\n{YELLOW}Tekan Enter...{RESET}")

if __name__ == "__main__":
    main()
