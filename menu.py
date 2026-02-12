import telnetlib
import routeros_api
import re
import os
import sys
import json
import requests
import time
from datetime import datetime

# --- KONFIGURASI WARNA & UI ---
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
RESET = "\033[0m"

# --- SYSTEM VAULT (Penyimpanan Profile) ---
def load_vault():
    if not os.path.exists("vault.json"):
        with open("vault.json", "w") as f:
            json.dump({"profiles": {}, "active_profile": "Ucenk"}, f)
    with open("vault.json", "r") as f:
        return json.load(f)

def save_vault(data):
    with open("vault.json", "w") as f:
        json.dump(data, f, indent=4)

def get_credentials(target):
    v = load_vault()
    prof = v.get("active_profile")
    if not prof or prof not in v["profiles"]:
        return None
    return v["profiles"][prof].get(target)

# --- MIKROTIK TOOLS ENGINE ---
def run_mikhmon(): # Menu 1
    print(f"\n{CYAN}=== MIKHMON SERVER (Termux/Linux) ==={RESET}")
    path = input(f"{WHITE}Masukkan path folder Mikhmon (Enter jika default): {RESET}").strip()
    if not path: path = "mikhmon"
    print(f"{GREEN}[*] Server berjalan di http://0.0.0.0:8080{RESET}")
    print(f"{YELLOW}[!] Tekan Ctrl+C untuk mematikan server.{RESET}")
    os.system(f"php -S 0.0.0.0:8080 -t {path}")

def mk_hotspot_active(): # Menu 2
    creds = get_credentials("mikrotik")
    if not creds:
        print(f"{RED}[!] Profile MikroTik belum aktif.{RESET}")
        return
    
    print(f"\n{CYAN}=== DAFTAR USER HOTSPOT AKTIF ==={RESET}")
    try:
        connection = routeros_api.RouterOsApiPool(
            creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True
        )
        api = connection.get_api()
        active_users = api.get_resource('/ip/hotspot/active').get()
        
        print(f"{MAGENTA}------------------------------------------------------------{RESET}")
        print(f"{WHITE}{'USER':<20} {'ADDRESS':<15} {'UPTIME':<10}{RESET}")
        print(f"{MAGENTA}------------------------------------------------------------{RESET}")
        
        for u in active_users:
            print(f"{GREEN}{u.get('user'):<20} {WHITE}{u.get('address'):<15} {CYAN}{u.get('uptime'):<10}{RESET}")
            
        print(f"{MAGENTA}------------------------------------------------------------{RESET}")
        print(f"{WHITE}Total Aktif: {YELLOW}{len(active_users)} User{RESET}")
        connection.disconnect()
    except Exception as e:
        print(f"{RED}[!] Error: {e}{RESET}")

def cek_dhcp_rogue(): # Menu 3
    creds = get_credentials("mikrotik")
    if not creds: return
    print(f"\n{CYAN}=== DHCP ALERT / ROGUE DETECTOR ==={RESET}")
    try:
        connection = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = connection.get_api()
        alerts = api.get_resource('/ip/dhcp-server/alert').get()
        if not alerts:
            print(f"{GREEN}[✓] Aman. Tidak ada DHCP Rogue terdeteksi.{RESET}")
        else:
            for a in alerts:
                print(f"{RED}[!!] DETEKSI: {a.get('unknown-mac')} di Interface {a.get('interface')}{RESET}")
        connection.disconnect()
    except Exception as e:
        print(f"{RED}[!] Error: {e}{RESET}")

def hapus_laporan_mikhmon(): # Menu 4
    print(f"\n{CYAN}=== CLEANUP MIKHMON SCRIPT ==={RESET}")
    confirm = input(f"{YELLOW}Hapus semua file laporan/log Mikhmon? (y/n): {RESET}")
    if confirm.lower() == 'y':
        os.system("rm -rf mikhmon/log/*.txt && rm -rf mikhmon/report/*.txt")
        print(f"{GREEN}[✓] Laporan berhasil dibersihkan.{RESET}")

def bandwidth_usage_report(): # Menu 5
    creds = get_credentials("mikrotik")
    if not creds: return
    interface = input(f"{WHITE}Input Nama Interface (misal ether1): {RESET}").strip()
    try:
        connection = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = connection.get_api()
        print(f"\n{YELLOW}[*] Monitoring {interface}... Tekan Ctrl+C untuk stop.{RESET}")
        resource = api.get_resource('/interface')
        while True:
            data = resource.get(name=interface)
            for d in data:
                tx = int(d.get('tx-byte', 0)) / 1024 / 1024
                rx = int(d.get('rx-byte', 0)) / 1024 / 1024
                print(f"\r{CYAN}TX: {WHITE}{tx:.2f} Mbps | {CYAN}RX: {WHITE}{rx:.2f} Mbps   ", end="")
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{GREEN}[✓] Monitoring Selesai.{RESET}")
    except Exception as e:
        print(f"\n{RED}[!] Error: {e}{RESET}")

def backup_restore_mikrotik(): # Menu 6
    creds = get_credentials("mikrotik")
    if not creds: return
    print(f"\n{CYAN}=== MIKROTIK BACKUP & RESTORE ==={RESET}")
    print(" 1. Buat Backup Baru (.backup)")
    print(" 2. Buat Export Baru (.rsc)")
    opt = input(f"\n{YELLOW}Pilih: {RESET}")
    
    filename = f"Backup_{creds['ip']}_{datetime.now().strftime('%Y%m%d')}"
    try:
        connection = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = connection.get_api()
        if opt == '1':
            api.get_binary_resource('/').call('system/backup/save', {'name': filename})
            print(f"{GREEN}[✓] Backup disimpan dengan nama: {filename}.backup{RESET}")
        elif opt == '2':
            api.get_binary_resource('/').call('export', {'file': filename})
            print(f"{GREEN}[✓] Export disimpan dengan nama: {filename}.rsc{RESET}")
        connection.disconnect()
    except Exception as e:
        print(f"{RED}[!] Gagal: {e}{RESET}")

def snmp_monitoring(): # Menu 7
    creds = get_credentials("mikrotik")
    if not creds: return
    print(f"\n{CYAN}=== SNMP & RESOURCE MONITOR ==={RESET}")
    try:
        connection = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = connection.get_api()
        res = api.get_resource('/system/resource').get()[0]
        print(f"{WHITE}CPU Load: {GREEN}{res.get('cpu-load')}%{RESET}")
        print(f"{WHITE}Uptime:   {GREEN}{res.get('uptime')}{RESET}")
        print(f"{WHITE}Free RAM: {GREEN}{int(res.get('free-memory'))/1048576:.1f} MB{RESET}")
        print(f"{WHITE}Board:    {GREEN}{res.get('board-name')}{RESET}")
        connection.disconnect()
    except Exception as e:
        print(f"{RED}[!] Error: {e}{RESET}")

def log_viewer_mikrotik(): # Menu 8
    creds = get_credentials("mikrotik")
    if not creds: return
    print(f"\n{CYAN}=== MIKROTIK LOG VIEWER (Last 20) ==={RESET}")
    try:
        connection = routeros_api.RouterOsApiPool(creds['ip'], username=creds['user'], password=creds['pass'], plaintext_login=True)
        api = connection.get_api()
        logs = api.get_resource('/log').get()
        for l in logs[-20:]:
            color = WHITE
            if "error" in l.get('topics') or "critical" in l.get('topics'): color = RED
            print(f"{CYAN}{l.get('time')} {color}{l.get('message')}{RESET}")
        connection.disconnect()
    except Exception as e:
        print(f"{RED}[!] Error: {e}{RESET}")

# --- CORE TELNET ENGINE FOR OLT ---
def telnet_olt_execute(creds, cmds):
    try:
        tn = telnetlib.Telnet(creds['ip'], timeout=10)
        tn.read_until(b"Username:", timeout=5)
        tn.write(creds['user'].encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(creds['pass'].encode('ascii') + b"\n")
        
        output = ""
        for cmd in cmds:
            tn.write(cmd.encode('ascii') + b"\n")
            time.sleep(1) # Memberi waktu OLT memproses buffer
            output += tn.read_until(b"#", timeout=10).decode('ascii')
            
        tn.write(b"exit\n")
        tn.close()
        return output
    except Exception as e:
        print(f"{RED}[!] Telnet OLT Error: {e}{RESET}")
        return None

# --- OLT MANAGEMENT TOOLS ---

def list_onu(): # Menu 9
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum aktif.{RESET}")
        return
        
    p = input(f"{WHITE}Masukkan Port PON (contoh 1/1/1): {RESET}").strip()
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}[*] Menarik data ONU dari OLT {brand.upper()}...{RESET}")
    if brand == 'zte':
        cmds = ["terminal length 0", "enable", f"show pon onu information gpon-olt_{p}"]
    else:
        cmds = ["terminal length 0", f"show onu status port {p}"]
        
    output = telnet_olt_execute(creds, cmds)
    
    print(f"\n{WHITE}==== DAFTAR ONU TERDAFTAR (PORT {p}) ===={RESET}")
    print(f"{MAGENTA}----------------------------------------------------------------------{RESET}")
    if output:
        lines = output.splitlines()
        found_data = False
        for line in lines:
            l_strip = line.strip()
            # Alice Fix: Filter sampah prompt tapi tetap menampilkan baris data
            if not l_strip or any(k in l_strip for k in ["ZXAN", "terminal length", "show pon", "password is not strong"]):
                continue
            print(f"{WHITE}{l_strip}{RESET}")
            found_data = True
        
        if not found_data:
            print(f"{YELLOW}[!] Tidak ada data ONU ditemukan di port tersebut.{RESET}")
    else:
        print(f"{RED}[!] Gagal mendapatkan respon dari OLT.{RESET}")
    print(f"{MAGENTA}----------------------------------------------------------------------{RESET}")

def config_onu_logic(): # Menu 10
    creds = get_credentials("olt")
    if not creds: return
    
    brand = creds.get('brand', 'zte').lower()
    found_sn = "" # Variable penampung SN hasil scan
    
    print(f"\n{CYAN}=== ONU CONFIGURATION (AUTO-SCAN & REGIS) ==={RESET}")
    p = input(f"{WHITE}Lokasi Port PON (contoh 1/1/1): {RESET}").strip()

    # 1. Tahap Auto-Scan Unconfigured
    print(f"{CYAN}[*] Mencari ONU Unconfigured di port {p}...{RESET}")
    if brand == 'zte':
        cmd_scan = ["terminal length 0", "enable", "show gpon onu uncfg"]
    else:
        cmd_scan = ["terminal length 0", f"show onu unconfigured port {p}"]
        
    res_unconfig = telnet_olt_execute(creds, cmd_scan)
    if res_unconfig:
        # Tampilkan hasil scan yang sudah difilter
        print(f"\n{YELLOW}HASIL SCAN ONU BARU:{RESET}")
        for line in res_unconfig.splitlines():
            if any(x in line.upper() for x in ["FHTT", "ZTEG", "SN", "ONUINDEX"]):
                print(f"{WHITE}{line.strip()}{RESET}")
                # Otomatis ambil SN pertama yang ditemukan
                sn_match = re.search(r'(FHTT|ZTEG)[0-9A-Z]{8,}', line.upper())
                if sn_match and not found_sn:
                    found_sn = sn_match.group(0)

    # 2. Menu Tindakan Konfigurasi
    while True:
        print(f"\n{MAGENTA}--- TINDAKAN PORT {p} ---{RESET}")
        print(f" 1. {YELLOW}Cek ID Kosong (Auto-Analyze){RESET}")
        print(f" 2. ZTE - Hotspot Only")
        print(f" 3. ZTE - Hotspot + PPPoE")
        print(f" 4. FH  - Hotspot Only")
        print(f" 5. FH  - Hotspot + PPPoE")
        print(f" 6. Cek Power Optik (Temporary Bind)")
        print(f" 0. Kembali")
        
        opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()
        if opt == '0' or not opt: break

        if opt == '1':
            print(f"[*] Menganalisa ID yang sudah terpakai...")
            cmd_check = ["terminal length 0", f"show gpon onu state gpon-olt_{p}"] if brand == 'zte' else [f"show onu status port {p}"]
            res_list = telnet_olt_execute(creds, cmd_check)
            if res_list:
                # Alice Fix: Regex lebih fleksibel untuk menangkap :1, : 1, atau ID murni
                ids_found = re.findall(r'[:](\d{1,3})', res_list)
                ids_int = sorted(list(set([int(x) for x in ids_found if int(x) < 129])))
                
                if not ids_int:
                    print(f"{GREEN}[✓] Port kosong. Rekomendasi ID: 1{RESET}")
                else:
                    max_id = max(ids_int)
                    missing = [x for x in range(1, max_id + 1) if x not in ids_int]
                    if missing:
                        print(f"{YELLOW}[!] ID Terlewat (Kosong): {', '.join(map(str, missing))}{RESET}")
                    print(f"{GREEN}[✓] Rekomendasi ID Berikutnya: {max_id + 1}{RESET}")
            continue

        # Logika registrasi (Opsi 2-5)
        if opt in ['2', '3', '4', '5']:
            onu_id = input(f"{WHITE}Masukkan ID ONU: {RESET}").strip()
            sn = input(f"{WHITE}Masukkan SN [{found_sn}]: {RESET}").strip() or found_sn
            name = input(f"{WHITE}Nama Pelanggan: {RESET}").strip().replace(" ", "_")
            
            # Logic ZTE Hotspot (Opsi 2)
            if opt == '2':
                vlan = input("VLAN Hotspot: ").strip()
                prof = input("Tcont Profile (UP-100M): ").strip()
                cmds = [
                    "conf t", f"interface gpon-olt_{p}", f"onu {onu_id} type ALL sn {sn}", "exit",
                    f"interface gpon-onu_{p}:{onu_id}", f"name {name}", f"tcont 1 profile {prof}",
                    "gemport 1 tcont 1", f"service-port 1 vport 1 user-vlan {vlan} vlan {vlan}", "exit",
                    f"pon-onu-mng gpon-onu_{p}:{onu_id}", f"service 1 gemport 1 vlan {vlan}",
                    f"vlan port wifi_0/1 mode tag vlan {vlan}", "end", "write"
                ]
            
            # (Note: Opsi 3,4,5 menyusul polanya sama sesuai kebutuhan config kamu)
            print(f"{CYAN}[*] Mengirim perintah konfigurasi...{RESET}")
            telnet_olt_execute(creds, cmds)
            print(f"{GREEN}[✓] ONU {name} Berhasil Diregistrasi!{RESET}")

def restart_onu(): # Menu 11
    creds = get_credentials("olt")
    if not creds: return
    brand = creds.get('brand', 'zte').lower()
    port = input("Port (1/1/1): ")
    onu_id = input("ID ONU: ")
    print(f"[*] Rebooting ONU {port}:{onu_id}...")
    cmds = [f"pon-onu-mng gpon-onu_{port}:{onu_id}", "reboot", "yes"] if brand == 'zte' else [f"reboot onu port {port} onu {onu_id}", "y"]
    telnet_olt_execute(creds, cmds)
    print(f"{GREEN}[✓] Perintah reboot telah dikirim.{RESET}")

def reset_onu(): # Menu 12
    creds = get_credentials("olt")
    if not creds: return
    port = input("Port: "); id_onu = input("ID ONU: ")
    confirm = input(f"{RED}Hapus ONU {id_onu} di port {port}? (y/n): {RESET}")
    if confirm.lower() == 'y':
        cmds = ["conf t", f"interface gpon-olt_{port}", f"no onu {id_onu}", "end", "write"]
        telnet_olt_execute(creds, cmds)
        print(f"{GREEN}[✓] ONU Berhasil dihapus.{RESET}")

def check_optical_power_fast(): # Menu 13
    creds = get_credentials("olt")
    if not creds: return
    brand = creds.get('brand', 'zte').lower()
    port = input("Port: "); id_onu = input("ID ONU: ")
    cmds = [f"show pon power attenuation gpon-onu_{port}:{id_onu}"] if brand == 'zte' else [f"show onu optical-power {port} {id_onu}"]
    output = telnet_olt_execute(creds, cmds)
    print(f"\n{WHITE}HASIL POWER OPTIK:{RESET}\n{CYAN}{output}{RESET}")

def port_vlan(): # Menu 14
    print(f"{YELLOW}[!] Fitur Port & VLAN Config sedang dalam pengembangan.{RESET}")

def alarm_event_viewer(): # Menu 15
    creds = get_credentials("olt")
    if not creds: return
    brand = creds.get('brand', 'zte').lower()
    cmds = ["show alarm current severity critical"] if brand == 'zte' else ["show alarm active"]
    print(telnet_olt_execute(creds, cmds))

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


def traffic_report_pon(): # Menu 17
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum aktif.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}=== TRAFFIC REPORT PER PON PORT ==={RESET}")
    port = input(f"{WHITE}Masukkan Port PON (contoh 1/1/1): {RESET}").strip()
    
    print(f"\n{CYAN}[*] Mengambil data statistik trafik...{RESET}")
    
    if brand == 'zte':
        cmds = [
            "terminal length 0", 
            "enable", 
            f"show interface gpon-olt_{port}"
        ]
    else:
        cmds = ["terminal length 0", f"show interface pon {port}"]

    output = telnet_olt_execute(creds, cmds)
    
    print(f"\n{WHITE}LAPORAN TRAFIK PORT {port}:{RESET}")
    print(f"{MAGENTA}----------------------------------------------------------------------{RESET}")
    
    if output:
        lines = output.splitlines()
        found = False
        for line in lines:
            l_low = line.lower()
            if any(x in l_low for x in ["input rate", "output rate", "bits/sec", "throughput"]):
                print(f"{GREEN}{line.strip()}{RESET}")
                found = True
            elif "description" in l_low or "state" in l_low:
                print(f"{WHITE}{line.strip()}{RESET}")
        
        if not found:
            print(f"{WHITE}{output}{RESET}")
    else:
        print(f"{YELLOW}[!] Gagal mengambil data trafik.{RESET}")
        
    print(f"{MAGENTA}-----------------------------------------------------------------------{RESET}")


def auto_audit_olt(): # Menu 18
    creds = get_credentials("olt")
    if not creds: 
        print(f"{YELLOW}[!] Profile OLT belum aktif.{RESET}")
        return
    
    brand = creds.get('brand', 'zte').lower()
    
    print(f"\n{CYAN}=== AUTO AUDIT OLT SYSTEM ==={RESET}")
    print(f"{WHITE}[*] Memulai audit kesehatan jaringan...{RESET}")
    
    if brand == 'zte':
        cmds = [
            "terminal length 0",
            "enable",
            "show pon power attenuation gpon-olt_1/1/1", # Default audit port
            "show alarm current severity critical"
        ]
    else:
        cmds = ["show card", "show port state", "show pon power attenuation"]

    output = telnet_olt_execute(creds, cmds)
    
    print(f"\n{WHITE}HASIL AUDIT OTOMATIS:{RESET}")
    print(f"{MAGENTA}-------------------------------------------------------------------------------{RESET}")
    
    if output:
        lines = output.splitlines()
        for line in lines:
            l_low = line.lower()
            
            # Deteksi Sinyal Lemah
            if "dbm" in l_low:
                try:
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

# --- NETWORK TOOLS (Menu 19-25) ---

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
        # Panggil fungsi get_brand yang ada di Sesi 1
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
        os.system(f"traceroute {target} 2>/dev/null || mtr -rw {target}")
    else:
        return


def dns_tools(): # Menu 25
    print(f"\n{CYAN}=== DNS LOOKUP TOOLS ==={RESET}")
    domain = input(f"{WHITE}Domain (contoh google.com): {RESET}").strip()
    if not domain: return

    print(f"\n{MAGENTA}--- PILIH INFORMASI DNS ---{RESET}")
    print(" 1. A Record | 2. NS Record | 3. All Records")
    opt = input(f"\n{YELLOW}Pilih Opsi: {RESET}").strip()
    
    type_map = {'1': 1, '2': 2, '3': 255}
    record_type = type_map.get(opt, 1)

    try:
        url = f"https://dns.google/resolve?name={domain}&type={record_type}"
        resp = requests.get(url, timeout=10).json()
        if "Answer" in resp:
            print(f"\n{GREEN}HASIL LOOKUP ({domain}):{RESET}")
            for ans in resp['Answer']:
                print(f" {YELLOW}[Type-{ans['type']}]{RESET} {ans['data']}")
        else:
            print(f"{RED}[!] Record tidak ditemukan.{RESET}")
    except Exception as e:
        print(f"{RED}[!] Error: {e}{RESET}")


# --- PROFILE SETTING & UPDATER ---

def manage_profiles(): # Menu 99
    v = load_vault()
    print(f"\n{CYAN}=== PROFILE MANAGEMENT ==={RESET}")
    print(f"Current Profile: {GREEN}{v.get('active_profile')}{RESET}")
    print("1. Tambah/Edit Profile")
    print("2. Ganti Profile Aktif")
    opt = input("\nPilih: ")
    
    if opt == '1':
        name = input("Nama Profile: ").strip()
        if name not in v["profiles"]: v["profiles"][name] = {}
        
        # Mikrotik
        v["profiles"][name]["mikrotik"] = {
            "ip": input("IP Mikrotik: "),
            "user": input("User: "),
            "pass": input("Pass: ")
        }
        # OLT
        v["profiles"][name]["olt"] = {
            "ip": input("IP OLT: "),
            "user": input("User: "),
            "pass": input("Pass: "),
            "brand": input("Brand (zte/fh): ").lower()
        }
        save_vault(v)
        print(f"{GREEN}[✓] Profile {name} disimpan.{RESET}")
    elif opt == '2':
        new_prof = input("Masukkan Nama Profile: ")
        if new_prof in v["profiles"]:
            v["active_profile"] = new_prof
            save_vault(v)
            print(f"{GREEN}[✓] Berhasil pindah ke {new_prof}{RESET}")

def update_tools_auto(): # Menu 26
    print(f"\n{CYAN}=== UPDATE TOOLS (FORCE SYNC) ==={RESET}")
    print(f"{WHITE}[*] Membersihkan cache git lokal...{RESET}")
    os.system("git fetch --all && git reset --hard origin/main")
    print(f"{GREEN}[✓] Selesai.{RESET}")


# --- UI & MAIN LOOP ---

def show_menu():
    v = load_vault(); prof = v.get("active_profile", "Ucenk")
    os.system('clear')
    os.system('echo "==================================================================" | lolcat 2>/dev/null')
    os.system('figlet -f slant "Ucenk D-Tech" | lolcat 2>/dev/null')
    os.system('echo "         Premium Network Management System - Author: Ucenk" | lolcat 2>/dev/null')
    os.system('echo "==================================================================" | lolcat 2>/dev/null')
    print(f"\n{WHITE}                PROFILE ACTIVE: {GREEN}{prof}{RESET}")
    os.system('echo "============================ NOC TOOLS ===========================" | lolcat 2>/dev/null')
    
    print(f"\n{YELLOW}=== MIKROTIK TOOLS ==={RESET}")
    print(f"{CYAN} 1. Mikhmon Server        5. Live Traffic Monitoring")
    print(f" 2. Active Users Hotspot  6. MikroTik Backup & Restore")
    print(f" 3. DHCP Alert (Rogue)    7. SNMP Monitoring")
    print(f" 4. Remove Mikhmon Script 8. MikroTik Log Viewer{RESET}")

    print(f"\n{YELLOW}=== OLT TOOLS ==={RESET}")
    print(f"{CYAN} 9. View Registered ONU   14. Port & VLAN Config")
    print(f" 10. ONU Config (ZTE/FH)  15. Alarm & Event Viewer")
    print(f" 11. Restart ONU          16. Backup & Restore OLT")
    print(f" 12. Reset/Delete ONU     17. Traffic Report per PON")
    print(f" 13. Check Optical Power  18. Auto Audit Script{RESET}")

    print(f"\n{YELLOW}=== NETWORK TOOLS ==={RESET}")
    print(f"{CYAN} 19. Speedtest            23. WhatMyIP")
    print(f" 20. Nmap                 24. Ping & Traceroute")
    print(f" 21. MAC Lookup           25. DNS Checker")
    print(f" 22. Port Scanner         26. Update-Tools{RESET}")
    
    print(f"\n{GREEN} 99. Profile Setting{RESET}  {YELLOW} 0. Exit{RESET}")
    os.system('echo "======================= github.com/UceNk-Tech =====================" | lolcat 2>/dev/null')

def main():
    while True:
        try:
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
        except KeyboardInterrupt:
            print(f"\n{RED}[!] Program dihentikan paksa.{RESET}")
            break

if __name__ == "__main__":
    main()
