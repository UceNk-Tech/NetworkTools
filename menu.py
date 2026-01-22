#!/usr/bin/env python3
# ==========================================
# NetworkTools Menu (Ucenk-D-Tech) v2.0
# ==========================================

import os, time, sys, csv
from datetime import datetime

# Dependensi Python
try:
    import routeros_api
except Exception:
    print("RouterOS API belum terpasang. Jalankan: pip install routeros-api")
    sys.exit(1)

try:
    import paramiko
except Exception:
    print("Paramiko belum terpasang. Jalankan: pip install paramiko")
    sys.exit(1)

# ANSI Colors
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"
RESET   = "\033[0m"

# Cache kredensial MikroTik (valid 5 menit)
MT_CREDS = {"host": None, "user": None, "pw": None, "ts": 0}

# Cache profil perangkat (MikroTik & OLT)
DEVICE_PROFILES = {
    "mikrotik": [],
    "olt": []
}

# ---------- UI ----------
def header():
    os.system('clear')
    os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    print(" Author: Ucenk | Premium Network Management System")
    os.system("neofetch --ascii_distro ubuntu")
    print("-" * 70)

def pause(msg="Tekan Enter..."):
    try:
        input(msg)
    except KeyboardInterrupt:
        pass

# ---------- Helper ----------
def safe_int(v, default=0):
    try:
        return int(v)
    except Exception:
        return default

def write_csv(path, rows, header_row=None):
    try:
        with open(path, 'w', newline='') as f:
            w = csv.writer(f)
            if header_row: w.writerow(header_row)
            w.writerows(rows)
        return True
    except Exception as e:
        print(f"{RED}Gagal menulis CSV: {e}{RESET}")
        return False

# ---------- MikroTik ----------
def get_mt_api():
    global MT_CREDS
    now = time.time()
    if (MT_CREDS["host"] is None) or (now - MT_CREDS["ts"] > 300):
        header()
        print("\n[Login MikroTik] (valid 5 menit)")
        MT_CREDS["host"] = input("IP MikroTik : ") or "10.30.0.1"
        MT_CREDS["user"] = input("Username    : ") or "admin"
        MT_CREDS["pw"]   = input("Password    : ") or ""
        MT_CREDS["ts"]   = time.time()
    try:
        pool = routeros_api.RouterOsApiPool(
            MT_CREDS["host"],
            username=MT_CREDS["user"],
            password=MT_CREDS["pw"],
            plaintext_login=True,
            timeout=10
        )
        return pool.get_api(), pool
    except Exception as e:
        print(f"{RED}[X] Gagal koneksi MikroTik: {e}{RESET}")
        MT_CREDS["host"] = None
        time.sleep(2)
        return None, None

def monitor_traffic_realtime():
    api, pool = get_mt_api()
    if not api: return
    iface = input("Interface (default: bridge1-Hotspot): ") or "bridge1-Hotspot"
    try:
        while True:
            data = api.get_resource('/interface').call('monitor-traffic', {'interface': iface, 'once': 'true'})
            tx = safe_int(data[0].get('tx-bits-per-second', 0)) / 1e6
            rx = safe_int(data[0].get('rx-bits-per-second', 0)) / 1e6
            header()
            print(f"{CYAN}[{datetime.now().strftime('%H:%M:%S')}] {iface}{RESET}")
            print(f"{GREEN}TX: {tx:.2f} Mbps{RESET} | {YELLOW}RX: {rx:.2f} Mbps{RESET}")
            print("Ctrl+C untuk berhenti.")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        pool.disconnect()

def hotspot_active_realtime():
    api, pool = get_mt_api()
    if not api: return
    try:
        while True:
            active = api.get_resource('/ip/hotspot/active').get()
            header()
            print(f"{MAGENTA}TOTAL USER AKTIF: {len(active)} USER{RESET}")
            print("-" * 70)
            for u in active:
                print(f"{GREEN}{u.get('user','?'):15}{RESET} | {CYAN}{u.get('address','?'):15}{RESET} | {YELLOW}{u.get('uptime','0')}{RESET}")
            print("-" * 70)
            print("Refresh tiap 5 detik — Ctrl+C untuk berhenti.")
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        pool.disconnect()

def remove_expired_voucher():
    api, pool = get_mt_api()
    if not api: return
    try:
        kw = input("Keyword komentar (filter): ").strip()
        users = api.get_resource('/ip/hotspot/user')
        data = users.get()
        expired = [u for u in data
                   if kw in (u.get('comment',''))
                   and u.get('uptime') == u.get('limit-uptime')]
        header()
        print(f"{RED}Ditemukan {len(expired)} voucher expired.{RESET}")
        if expired and input("Hapus semua? (y/n): ").lower() == 'y':
            for u in expired:
                users.remove(id=u['id'])
            print(f"{GREEN}Selesai menghapus.{RESET}")
        pause()
    finally:
        pool.disconnect()

def dhcp_alert_check():
    api, pool = get_mt_api()
    if not api: return
    try:
        alerts = api.get_resource('/ip/dhcp-server/alert').get()
        header()
        if alerts:
            print(f"{RED}[!] Rogue DHCP terdeteksi:{RESET}")
            for a in alerts:
                print(f"- {a.get('unknown-server','?')} | on {a.get('interface','?')}")
        else:
            print(f"{GREEN}Aman—tidak ada Rogue DHCP.{RESET}")
        pause()
    finally:
        pool.disconnect()

def speedtest_realtime():
    header()
    os.system("speedtest-cli")
    pause()

def nmap_scan():
    header()
    target = input("Target IP/Domain: ").strip()
    if not target:
        print("Target kosong."); pause(); return
    os.system(f"nmap -A {target}")
    pause()

def mac_lookup():
    header()
    mac = input("Masukkan MAC (00:11:22:33:44:55): ").strip()
    if not mac:
        print("MAC kosong."); pause(); return
    os.system(f"curl -s https://api.macvendors.com/{mac}")
    print()
    pause()

def ping_traceroute():
    header()
    host = input("Host/IP: ").strip()
    if not host:
        print("Host kosong."); pause(); return
    print(f"{CYAN}Ping ke {host}{RESET}")
    os.system(f"ping -c 4 {host}")
    print(f"\n{YELLOW}Traceroute ke {host}{RESET}")
    os.system(f"traceroute {host}")
    pause()

def dns_tools():
    header()
    domain = input("Domain: ").strip()
    if not domain:
        print("Domain kosong."); pause(); return
    print(f"{CYAN}nslookup {domain}{RESET}")
    os.system(f"nslookup {domain}")
    print(f"\n{YELLOW}dig {domain}{RESET}")
    os.system(f"dig {domain}")
    pause()

def bandwidth_report_csv():
    api, pool = get_mt_api()
    if not api: return
    try:
        iface = input("Interface (default: bridge1-Hotspot): ") or "bridge1-Hotspot"
        duration = safe_int(input("Durasi (detik, default 10): ") or "10", 10)
        interval = safe_int(input("Interval (detik, default 1): ") or "1", 1)
        rows = []
        start = time.time()
        while time.time() - start < duration:
            data = api.get_resource('/interface').call('monitor-traffic', {'interface': iface, 'once': 'true'})
            tx = safe_int(data[0].get('tx-bits-per-second', 0))
            rx = safe_int(data[0].get('rx-bits-per-second', 0))
            rows.append([datetime.now().isoformat(), tx, rx])
            time.sleep(interval)
        path = os.path.join(os.path.expanduser("~"), f"bandwidth_{iface}.csv")
        ok = write_csv(path, rows, header_row=["timestamp","tx_bps","rx_bps"])
        header()
        if ok:
            print(f"{GREEN}Report tersimpan: {path}{RESET}")
        else:
            print(f"{RED}Gagal menyimpan report.{RESET}")
        pause()
    finally:
        pool.disconnect()

def backup_restore_mikrotik():
    api, pool = get_mt_api()
    if not api: return
    try:
        header()
        print(" 1) Backup konfigurasi")
        print(" 2) Restore konfigurasi (.rsc)")
        ch = input("Pilih (1/2): ").strip()
        if ch == '1':
            # Backup via export file
            fname = input("Nama file (tanpa ekstensi): ").strip() or "backup"
            cmd = f"/export file={fname}"
            api.get_resource('/').call('execute', {'command': cmd})
            print(f"{GREEN}Perintah backup dikirim. File akan tersimpan di router.{RESET}")
        elif ch == '2':
            path = input("Path file .rsc di router (mis: backup.rsc): ").strip()
            if not path:
                print("Path kosong.")
            else:
                cmd = f"/import file-name={path}"
                api.get_resource('/').call('execute', {'command': cmd})
                print(f"{GREEN}Perintah restore dikirim.{RESET}")
        else:
            print("Pilihan tidak valid.")
        pause()
    except Exception as e:
        print(f"{RED}Operasi gagal: {e}{RESET}"); pause()
    finally:
        pool.disconnect()

def snmp_monitor():
    header()
    print("SNMP Monitoring (placeholder aman)")
    print("Untuk produksi, gunakan pysnmp dengan OID perangkat target.")
    pause()

def log_viewer_mikrotik():
    api, pool = get_mt_api()
    if not api: return
    try:
        logs = api.get_resource('/log').get()
        header()
        print(f"{CYAN}System Log (terbaru 50){RESET}")
        for l in logs[-50:]:
            print(f"- {l.get('time','')} {l.get('topics','')} {l.get('message','')}")
        pause()
    finally:
        pool.disconnect()

def multi_device_manager():
    header()
    print(" 1) Tambah profil MikroTik")
    print(" 2) Tambah profil OLT")
    print(" 3) Lihat profil")
    print(" 4) Hapus profil")
    ch = input("Pilih (1-4): ").strip()
    if ch == '1':
        ip = input("IP: "); user = input("User: "); pw = input("Pass: ")
        DEVICE_PROFILES["mikrotik"].append({"ip": ip, "user": user, "pw": pw})
        print(f"{GREEN}Profil MikroTik ditambahkan.{RESET}")
    elif ch == '2':
        ip = input("IP: "); user = input("User: "); pw = input("Pass: "); port = input("Port SSH (default 22): ") or "22"
        DEVICE_PROFILES["olt"].append({"ip": ip, "user": user, "pw": pw, "port": int(port)})
        print(f"{GREEN}Profil OLT ditambahkan.{RESET}")
    elif ch == '3':
        print(f"{CYAN}MikroTik:{RESET} {DEVICE_PROFILES['mikrotik']}")
        print(f"{CYAN}OLT:{RESET} {DEVICE_PROFILES['olt']}")
    elif ch == '4':
        which = input("Hapus (mt/olt): ").strip()
        if which == 'mt' and DEVICE_PROFILES["mikrotik"]:
            DEVICE_PROFILES["mikrotik"].pop()
            print(f"{YELLOW}Profil MikroTik terakhir dihapus.{RESET}")
        elif which == 'olt' and DEVICE_PROFILES["olt"]:
            DEVICE_PROFILES["olt"].pop()
            print(f"{YELLOW}Profil OLT terakhir dihapus.{RESET}")
        else:
            print("Tidak ada profil untuk dihapus.")
    else:
        print("Pilihan tidak valid.")
    pause()

# ---------- OLT ZTE (via SSH Paramiko, aman dengan try/except) ----------
def _ssh_run(ip, user, pw, port, commands):
    """Jalankan daftar perintah CLI di OLT via SSH, kembalikan output gabungan."""
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
    header()
    if not DEVICE_PROFILES["olt"]:
        print("Belum ada profil OLT. Tambahkan di Multi-Device Manager.")
        pause(); return None
    print(f"{CYAN}Daftar OLT:{RESET}")
    for i, p in enumerate(DEVICE_PROFILES["olt"], 1):
        print(f"{i}. {p['ip']} (user: {p['user']}, port: {p['port']})")
    idx = input("Pilih OLT (nomor): ").strip()
    try:
        i = int(idx) - 1
        return DEVICE_PROFILES["olt"][i]
    except Exception:
        print("Pilihan tidak valid."); pause(); return None

def olt_list_onu():
    prof = _pick_olt_profile()
    if not prof: return
    header()
    print(f"{CYAN}Mengambil daftar ONU dari OLT {prof['ip']}{RESET}")
    # Perintah contoh; sesuaikan dengan CLI OLT ZTE yang kamu pakai
    cmds = ["enable", "show onu-information all"]
    out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], cmds)
    print(out)
    pause()

def olt_optical_power():
    prof = _pick_olt_profile()
    if not prof: return
    header()
    pon = input("PON port (mis: 1/1): ").strip() or "1/1"
    print(f"{CYAN}Monitor optical power PON {pon}{RESET}")
    cmds = ["enable", f"show optical-power pon {pon}"]
    out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], cmds)
    print(out)
    pause()

def olt_reset_onu():
    prof = _pick_olt_profile()
    if not prof: return
    header()
    onu_id = input("ONU ID: ").strip()
    if not onu_id:
        print("ONU ID kosong."); pause(); return
    print(f"{YELLOW}Reset ONU {onu_id}{RESET}")
    cmds = ["enable", f"reset onu {onu_id}"]
    out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], cmds)
    print(out)
    pause()

def olt_port_vlan_config():
    prof = _pick_olt_profile()
    if not prof: return
    header()
    print(" 1) Lihat VLAN aktif")
    print(" 2) Tambah VLAN ke port")
    ch = input("Pilih (1/2): ").strip()
    if ch == '1':
        cmds = ["enable", "show vlan all"]
        out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], cmds)
        print(out)
    elif ch == '2':
        vlan = input("VLAN ID: ").strip()
        port = input("Port (mis: ge-1/1/1): ").strip()
        if not vlan or not port:
            print("VLAN/Port kosong.")
        else:
            cmds = ["enable", f"configure terminal", f"interface {port}", f"switchport access vlan {vlan}", "end", "write"]
            out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], cmds)
            print(out)
    else:
        print("Pilihan tidak valid.")
    pause()

def olt_alarm_event_viewer():
    prof = _pick_olt_profile()
    if not prof: return
    header()
    print(f"{CYAN}Ambil alarm & event OLT{RESET}")
    cmds = ["enable", "show alarm current"]
    out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], cmds)
    print(out)
    pause()

def olt_backup_restore():
    prof = _pick_olt_profile()
    if not prof: return
    header()
    print(" 1) Backup konfigurasi")
    print(" 2) Restore konfigurasi")
    ch = input("Pilih (1/2): ").strip()
    if ch == '1':
        cmds = ["enable", "copy running-config startup-config"]
        out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], cmds)
        print(out)
    elif ch == '2':
        src = input("Nama file backup di OLT: ").strip()
        if not src:
            print("Nama file kosong.")
        else:
            cmds = ["enable", f"copy {src} startup-config", "reload"]
            out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], cmds)
            print(out)
    else:
        print("Pilihan tidak valid.")
    pause()

def olt_traffic_report_pon():
    prof = _pick_olt_profile()
    if not prof: return
    header()
    pon = input("PON port (mis: 1/1): ").strip() or "1/1"
    duration = int(input("Durasi (detik, default 10): ") or "10")
    interval = int(input("Interval (detik, default 1): ") or "1")
    rows = []
    start = time.time()
    while time.time() - start < duration:
        out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], ["enable", f"show traffic pon {pon}"])
        ts = datetime.now().isoformat()
        rows.append([ts, out.strip()])
        header()
        print(f"{CYAN}[{ts}] Traffic PON {pon}{RESET}")
        print(out)
        time.sleep(interval)
    path = os.path.join(os.path.expanduser("~"), f"olt_traffic_pon_{pon}.csv")
    ok = write_csv(path, rows, header_row=["timestamp","raw_output"])
    print(f"\n{GREEN}Report tersimpan: {path}{RESET}")
    pause()

def olt_auto_audit():
    prof = _pick_olt_profile()
    if not prof: return
    header()
    print(f"{CYAN}Menjalankan audit harian OLT {prof['ip']}{RESET}")
    cmds = [
        "enable",
        "show alarm current",
        "show onu-information all",
        "show optical-power pon 1/1"
    ]
    out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], cmds)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    path = os.path.join(os.path.expanduser("~"), f"olt_audit_{ts}.log")
    try:
        with open(path, 'w') as f:
            f.write(out)
        print(f"{GREEN}Audit log tersimpan: {path}{RESET}")
    except Exception as e:
        print(f"{RED}Gagal simpan audit: {e}{RESET}")
    pause()

# ---------- Menu ----------
def main():
    while True:
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
        print(BLUE    + " 11. Backup & Restore Config MikroTik" + RESET)
        print(CYAN    + " 12. SNMP Monitoring (placeholder)" + RESET)
        print(GREEN   + " 13. Log Viewer MikroTik" + RESET)
        print(YELLOW  + " 14. Multi-Device Manager (profiles)" + RESET)
        # OLT ZTE (15-22)
        print(MAGENTA + " 15. OLT: List ONU Aktif" + RESET)
        print(BLUE    + " 16. OLT: Monitor Optical Power" + RESET)
        print(CYAN    + " 17. OLT: Reset ONU" + RESET)
        print(GREEN   + " 18. OLT: Port & VLAN Config" + RESET)
        print(YELLOW  + " 19. OLT: Alarm & Event Viewer" + RESET)
        print(MAGENTA + " 20. OLT: Backup & Restore Config" + RESET)
        print(BLUE    + " 21. OLT: Traffic Report per PON (CSV)" + RESET)
        print(CYAN    + " 22. OLT: Auto Audit Script (daily)" + RESET)
        print(RESET   + "  0. Keluar")
        choice = input("\nPilih Menu (0-22): ").strip()

        # MikroTik & umum
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
        elif choice == '12': snmp_monitor()
        elif choice == '13': log_viewer_mikrotik()
        elif choice == '14': multi_device_manager()
        # OLT ZTE
        elif choice == '15': olt_list_onu()
        elif choice == '16': olt_optical_power()
        elif choice == '17': olt_reset_onu()
        elif choice == '18': olt_port_vlan_config()
        elif choice == '19': olt_alarm_event_viewer()
        elif choice == '20': olt_backup_restore()
        elif choice == '21': olt_traffic_report_pon()
        elif choice == '22': olt_auto_audit()
        elif choice == '0': break
        else:
            print("Pilihan tidak valid."); time.sleep(1)

if __name__ == "__main__":
    main()
