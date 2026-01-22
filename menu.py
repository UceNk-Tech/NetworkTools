#!/usr/bin/env python3
# ==========================================
# NetworkTools Menu (Ucenk-D-Tech) v2.2
# ==========================================

import os, time, sys, csv, getpass
from datetime import datetime

# Verifikasi Dependensi
try:
    import routeros_api
    import paramiko
except ImportError:
    print("Error: Library belum lengkap. Jalankan install.sh kembali.")
    sys.exit(1)

# ANSI Colors
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

# Global State
MT_CREDS = {"host": None, "user": None, "pw": None, "ts": 0}
DEVICE_PROFILES = {"mikrotik": [], "olt": []}

# ---------- UI & Helper ----------
def header():
    os.system('clear')
    os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    print(" Author: Ucenk | Premium Network Management System")
    os.system("neofetch --ascii_distro ubuntu")
    print("-" * 75)

def pause():
    input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

def safe_int(v, default=0):
    try: return int(v)
    except: return default

# ---------- SSH & API Core ----------
def get_mt_api():
    global MT_CREDS
    now = time.time()
    if (MT_CREDS["host"] is None) or (now - MT_CREDS["ts"] > 300):
        header()
        print("\n[Login MikroTik]")
        MT_CREDS["host"] = input("IP MikroTik : ") or "10.30.0.1"
        MT_CREDS["user"] = input("Username    : ") or "admin"
        MT_CREDS["pw"] = getpass.getpass("Password    : ")
        MT_CREDS["ts"] = time.time()
    try:
        pool = routeros_api.RouterOsApiPool(MT_CREDS["host"], username=MT_CREDS["user"], password=MT_CREDS["pw"], plaintext_login=True, timeout=10)
        return pool.get_api(), pool
    except Exception as e:
        print(f"{RED}Gagal koneksi MikroTik: {e}{RESET}")
        MT_CREDS["host"] = None
        time.sleep(2)
        return None, None

def _ssh_run(ip, user, pw, port, commands):
    out = []
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(ip, port=port, username=user, password=pw, timeout=10)
        for cmd in commands:
            stdin, stdout, stderr = client.exec_command(cmd)
            out.append(stdout.read().decode(errors='ignore'))
        client.close()
    except Exception as e:
        out.append(f"ERROR: {e}")
    return "\n".join(out)

def _pick_olt_profile():
    if not DEVICE_PROFILES["olt"]:
        print(f"{RED}Belum ada profil OLT. Tambahkan di menu 14.{RESET}")
        pause(); return None
    header()
    print(f"{CYAN}Daftar OLT:{RESET}")
    for i, p in enumerate(DEVICE_PROFILES["olt"], 1):
        print(f"{i}. {p['ip']} ({p['user']})")
    idx = safe_int(input("Pilih OLT (nomor): ")) - 1
    if 0 <= idx < len(DEVICE_PROFILES["olt"]):
        return DEVICE_PROFILES["olt"][idx]
    return None

# ---------- MikroTik Functions (1-13) ----------
def monitor_traffic_realtime():
    api, pool = get_mt_api()
    if not api: return
    iface = input("Interface: ") or "bridge1-Hotspot"
    try:
        while True:
            data = api.get_resource('/interface').call('monitor-traffic', {'interface': iface, 'once': 'true'})
            tx, rx = safe_int(data[0].get('tx-bits-per-second', 0))/1e6, safe_int(data[0].get('rx-bits-per-second', 0))/1e6
            header()
            print(f"{CYAN}Traffic {iface} - Ctrl+C untuk stop{RESET}")
            print(f"{GREEN}TX: {tx:.2f} Mbps | RX: {rx:.2f} Mbps{RESET}")
            time.sleep(1)
    except KeyboardInterrupt: pass
    finally: pool.disconnect()

def hotspot_active_realtime():
    api, pool = get_mt_api()
    if not api: return
    try:
        while True:
            active = api.get_resource('/ip/hotspot/active').get()
            header()
            print(f"{MAGENTA}User Aktif: {len(active)}{RESET}\n" + "-"*40)
            for u in active: print(f"{u.get('user','?'):15} | {u.get('address','?'):15} | {u.get('uptime','?')}")
            time.sleep(5)
    except KeyboardInterrupt: pass
    finally: pool.disconnect()

def remove_expired_voucher():
    api, pool = get_mt_api()
    if not api: return
    try:
        kw = input("Keyword Komentar: ")
        users = api.get_resource('/ip/hotspot/user')
        expired = [u for u in users.get() if kw in u.get('comment','') and u.get('uptime') == u.get('limit-uptime')]
        print(f"Ditemukan {len(expired)} voucher."); 
        if expired and input("Hapus? (y/n): ").lower() == 'y':
            for u in expired: users.remove(id=u['id'])
    finally: pool.disconnect(); pause()

def dhcp_alert_check():
    api, pool = get_mt_api()
    if not api: return
    try:
        alerts = api.get_resource('/ip/dhcp-server/alert').get()
        header()
        if alerts:
            print(f"{RED}Rogue DHCP Terdeteksi!{RESET}")
            for a in alerts: print(f"- {a.get('unknown-server')} on {a.get('interface')}")
        else: print(f"{GREEN}Aman—tidak ada Rogue DHCP.{RESET}")
    finally: pool.disconnect(); pause()

def speedtest_realtime(): header(); os.system("speedtest-cli"); pause()
def nmap_scan(): header(); t = input("Target: "); os.system(f"nmap -A {t}"); pause()
def mac_lookup(): header(); m = input("MAC: "); os.system(f"curl -s https://api.macvendors.com/{m}"); print(); pause()
def ping_traceroute(): header(); h = input("Host: "); os.system(f"ping -c 4 {h} && traceroute {h}"); pause()
def dns_tools(): header(); d = input("Domain: "); os.system(f"nslookup {d} && dig {d}"); pause()

def bandwidth_report_csv():
    api, pool = get_mt_api()
    if not api: return
    try:
        iface = input("Interface: ") or "bridge1-Hotspot"
        rows = []
        header()
        print(f"Mengambil data 10 detik ke depan...")
        for _ in range(10):
            data = api.get_resource('/interface').call('monitor-traffic', {'interface': iface, 'once': 'true'})
            rows.append([datetime.now().isoformat(), data[0].get('tx-bits-per-second'), data[0].get('rx-bits-per-second')])
            time.sleep(1)
        path = f"{os.path.expanduser('~')}/bandwidth_{iface}.csv"
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            w.writerow(["timestamp","tx_bps","rx_bps"])
            w.writerows(rows)
        print(f"{GREEN}Saved: {path}{RESET}")
    finally: pool.disconnect(); pause()

def backup_restore_mikrotik():
    api, pool = get_mt_api()
    if not api: return
    try:
        n = input("Nama File (tanpa .rsc): ") or "backup"
        api.get_resource('/').call('execute', {'command': f'/export file={n}'})
        print(f"{GREEN}Backup {n}.rsc sedang diproses di router.{RESET}")
    finally: pool.disconnect(); pause()

def log_viewer_mikrotik():
    api, pool = get_mt_api()
    if not api: return
    try:
        header()
        for l in api.get_resource('/log').get()[-25:]: 
            print(f"- {l.get('time')} {l.get('topics')} {l.get('message')}")
    finally: pool.disconnect(); pause()

def multi_device_manager():
    header()
    print("1. Tambah OLT Profile")
    print("2. Lihat Profile")
    print("3. Hapus Profile OLT Terakhir")
    c = input("Pilih: ")
    if c == '1':
        ip = input("IP OLT: ")
        u = input("User: ")
        p = getpass.getpass("Pass: ")
        DEVICE_PROFILES["olt"].append({"ip":ip, "user":u, "pw":p, "port":22})
        print(f"{GREEN}Profile ditambahkan.{RESET}")
    elif c == '2':
        print(DEVICE_PROFILES["olt"])
    elif c == '3' and DEVICE_PROFILES["olt"]:
        DEVICE_PROFILES["olt"].pop()
        print("Profile terakhir dihapus.")
    pause()

# ---------- OLT ZTE Functions (15-25) ----------
def olt_list_onu():
    p = _pick_olt_profile()
    if p: print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], ["enable", "show onu-information all"]))
    pause()

def olt_optical_power():
    p = _pick_olt_profile()
    if p:
        pon = input("PON (misal 1/1): ") or "1/1"
        print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], ["enable", f"show optical-power pon {pon}"]))
    pause()

def olt_reset_onu():
    p = _pick_olt_profile()
    if p:
        onu = input("ONU ID: ")
        print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], ["enable", f"reset onu {onu}"]))
    pause()

def olt_port_vlan_config():
    p = _pick_olt_profile()
    if p:
        v, pt = input("VLAN ID: "), input("Port OLT: ")
        cmds = ["enable", "conf t", f"interface {pt}", f"switchport access vlan {v}", "end", "write"]
        print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], cmds))
    pause()

def olt_alarm_event_viewer():
    p = _pick_olt_profile()
    if p: print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], ["enable", "show alarm current"]))
    pause()

def olt_backup_restore():
    p = _pick_olt_profile()
    if p:
        print("Saving configuration...")
        print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], ["enable", "write"]))
    pause()

def olt_traffic_report_pon():
    p = _pick_olt_profile()
    if p:
        pon = input("PON Port: ")
        print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], ["enable", f"show traffic pon {pon}"]))
    pause()

def olt_auto_audit():
    p = _pick_olt_profile()
    if p:
        cmds = ["enable", "show alarm current", "show onu-information all", "show version"]
        print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], cmds))
    pause()

def olt_check_unconfigured():
    p = _pick_olt_profile()
    if p: 
        header()
        print(f"{CYAN}Checking: show gpon onu uncfg...{RESET}")
        print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], ["enable", "show gpon onu uncfg"]))
    pause()

def olt_show_onu_info_port():
    p = _pick_olt_profile()
    if p:
        header()
        port = input("Port OLT (gpon-olt_1/3/1): ").strip()
        if port:
            print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], ["enable", f"show pon onu information {port}"]))
    pause()

def olt_delete_onu_interactive():
    p = _pick_olt_profile()
    if p:
        header()
        print(f"{RED}=== DELETE ONU INTERACTIVE ==={RESET}")
        iface = input("Interface OLT (misal gpon-olt_1/1/1): ")
        onu_id = input("Nomor ONU (misal 1): ")
        if iface and onu_id:
            confirm = input(f"Yakin hapus ONU {onu_id} di {iface}? (y/n): ")
            if confirm.lower() == 'y':
                cmds = ["enable", "conf t", f"interface {iface}", f"no onu {onu_id}", "end", "write"]
                print(_ssh_run(p['ip'], p['user'], p['pw'], p['port'], cmds))
                print(f"{GREEN}Proses Delete & Write Selesai.{RESET}")
    pause()

# ---------- Main Menu ----------
def main():
    while True:
        try:
            header()
            print(WHITE + " Silakan pilih menu:" + RESET)
            # MikroTik & umum (1-14)
            print(GREEN   + "  1. Monitor Traffic Interface (Realtime)" + RESET)
            print(CYAN    + "  2. Total User Aktif Hotspot (Realtime)" + RESET)
            print(YELLOW  + "  3. Hapus Voucher Expired" + RESET)
            print(RED     + "  4. Cek DHCP Alert (Rogue DHCP)" + RESET)
            print(MAGENTA + "  5. Speedtest CLI (Realtime Progress)" + RESET)
            print(BLUE    + "  6. Nmap Scan" + RESET)
            print(CYAN    + "  7. MAC Lookup" + RESET)
            print(GREEN   + "  8. Ping & Traceroute" + RESET)
            print(YELLOW  + "  9. DNS Tools (Lookup / Reverse)" + RESET)
            print(MAGENTA + " 10. Bandwidth Usage Report (CSV)" + RESET)
            print(BLUE    + " 11. Backup & Export Config MikroTik" + RESET)
            print(CYAN    + " 12. SNMP Monitoring (placeholder)" + RESET)
            print(GREEN   + " 13. Log Viewer MikroTik" + RESET)
            print(YELLOW  + " 14. Multi-Device Manager (profiles)" + RESET)
            print("-" * 75)
            # OLT ZTE (15-25)
            print(MAGENTA + " 15. OLT: List ONU Aktif" + RESET)
            print(BLUE    + " 16. OLT: Monitor Optical Power" + RESET)
            print(CYAN    + " 17. OLT: Reset ONU" + RESET)
            print(GREEN   + " 18. OLT: Port & VLAN Config" + RESET)
            print(YELLOW  + " 19. OLT: Alarm & Event Viewer" + RESET)
            print(MAGENTA + " 20. OLT: Write/Save Config" + RESET)
            print(BLUE    + " 21. OLT: Traffic Report per PON" + RESET)
            print(CYAN    + " 22. OLT: Auto Audit Script" + RESET)
            print(MAGENTA + " 23. OLT: Cek ONU Unconfigured" + RESET)
            print(BLUE    + " 24. OLT: Show ONU Info by Port" + RESET)
            print(RED     + " 25. OLT: Hapus ONU (Interactive)" + RESET)
            print(RESET   + "  0. Keluar")

            choice = input("\nPilih Menu (0-25): ").strip()

            if choice == '1':  monitor_traffic_realtime()
            elif choice == '2': hotspot_active_realtime()
            elif choice == '3': remove_expired_voucher()
            elif choice == '4': dhcp_alert_check()
            elif choice == '5': speedtest_realtime()
            elif choice == '6': nmap_scan()
            elif choice == '7': mac_lookup()
            elif choice == '8': ping_traceroute()
            elif choice == '9': dns_tools()
            elif choice == '10': bandwidth_report_csv()
            elif choice == '11': backup_restore_mikrotik()
            elif choice == '13': log_viewer_mikrotik()
            elif choice == '14': multi_device_manager()
            elif choice == '15': olt_list_onu()
            elif choice == '16': olt_optical_power()
            elif choice == '17': olt_reset_onu()
            elif choice == '18': olt_port_vlan_config()
            elif choice == '19': olt_alarm_event_viewer()
            elif choice == '20': olt_backup_restore()
            elif choice == '21': olt_traffic_report_pon()
            elif choice == '22': olt_auto_audit()
            elif choice == '23': olt_check_unconfigured()
            elif choice == '24': olt_show_onu_info_port()
            elif choice == '25': olt_delete_onu_interactive()
            elif choice == '0': break
            else: print("Pilihan tidak valid."); time.sleep(1)
        except KeyboardInterrupt:
            print("\nKeluar..."); break

if __name__ == "__main__":
    main()
