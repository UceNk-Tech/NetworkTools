#!/usr/bin/env python3
# ==========================================
# NetworkTools Menu (Ucenk-D-Tech) v2.0
# ==========================================

import os, time, sys, csv, getpass
from datetime import datetime

# Verifikasi Dependensi
def check_deps():
    needed = ['routeros_api', 'paramiko']
    for dep in needed:
        try:
            __import__(dep)
        except ImportError:
            print(f"\033[31m[!] Error: Modul {dep} tidak ditemukan. Jalankan install.sh ulang.\033[0m")
            sys.exit(1)

check_deps()
import routeros_api
import paramiko

# ANSI Colors
RED     = "\033[31m"
GREEN   = "\033[32m"
YELLOW  = "\033[33m"
BLUE    = "\033[34m"
MAGENTA = "\033[35m"
CYAN    = "\033[36m"
WHITE   = "\033[37m"
RESET   = "\033[0m"

# State & Cache
MT_CREDS = {"host": None, "user": None, "pw": None, "ts": 0}
DEVICE_PROFILES = {"mikrotik": [], "olt": []}

# ---------- UI (Tampilan Tetap) ----------
def header():
    os.system('clear')
    os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    print(" Author: Ucenk | Premium Network Management System")
    os.system("neofetch --ascii_distro ubuntu")
    print("-" * 70)

def pause(msg="Tekan Enter untuk kembali..."):
    try:
        input(f"\n{YELLOW}{msg}{RESET}")
    except KeyboardInterrupt:
        pass

# ---------- Helper ----------
def safe_int(v, default=0):
    try:
        return int(v)
    except:
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

# ---------- MikroTik Logic ----------
def get_mt_api():
    global MT_CREDS
    now = time.time()
    if (MT_CREDS["host"] is None) or (now - MT_CREDS["ts"] > 300):
        header()
        print("\n[Login MikroTik] (Sesi 5 Menit)")
        MT_CREDS["host"] = input("IP MikroTik : ") or "10.30.0.1"
        MT_CREDS["user"] = input("Username    : ") or "admin"
        MT_CREDS["pw"]   = getpass.getpass("Password    : ") # Lebih aman
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
        MT_CREDS["host"] = None # Reset cache jika gagal
        time.sleep(2)
        return None, None

def monitor_traffic_realtime():
    api, pool = get_mt_api()
    if not api: return
    iface = input("Interface (contoh: ether1): ") or "bridge1-Hotspot"
    try:
        while True:
            data = api.get_resource('/interface').call('monitor-traffic', {'interface': iface, 'once': 'true'})
            tx = safe_int(data[0].get('tx-bits-per-second', 0)) / 1e6
            rx = safe_int(data[0].get('rx-bits-per-second', 0)) / 1e6
            header()
            print(f"{CYAN}Monitoring Interface: {iface}{RESET}")
            print(f"{GREEN}TX: {tx:.2f} Mbps{RESET} | {YELLOW}RX: {rx:.2f} Mbps{RESET}")
            print("\nCtrl+C untuk kembali ke menu.")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        pool.disconnect()

# ... (Fungsi lain tetap sama, pastikan pemanggilan pool.disconnect() selalu ada)

def olt_traffic_report_pon():
    prof = _pick_olt_profile()
    if not prof: return
    header()
    pon = input("PON port (mis: 1/1): ").strip() or "1/1"
    duration = safe_int(input("Durasi (detik): "), 10)
    interval = safe_int(input("Interval (detik): "), 1)
    rows = []
    start = time.time()
    try:
        while time.time() - start < duration:
            out = _ssh_run(prof['ip'], prof['user'], prof['pw'], prof['port'], [f"show traffic pon {pon}"])
            ts = datetime.now().isoformat()
            rows.append([ts, out.strip()])
            header()
            print(f"{CYAN}[{ts}] Traffic PON {pon}{RESET}")
            print(out)
            time.sleep(interval)
        
        path = os.path.join(os.path.expanduser("~"), f"olt_traffic_{pon.replace('/','-')}.csv")
        if write_csv(path, rows, ["timestamp", "raw_output"]):
            print(f"\n{GREEN}Berhasil disimpan di: {path}{RESET}")
    except KeyboardInterrupt:
        pass
    pause()

# ---------- Main Menu (Tetap) ----------
def main():
    while True:
        try:
            header()
            print(WHITE + " Silakan pilih menu:" + RESET)
            # MikroTik
            print(GREEN   + "  1. Monitor Traffic Interface (Realtime)" + RESET)
            print(CYAN    + "  2. Total User Aktif Hotspot (Realtime)" + RESET)
            print(YELLOW  + "  3. Hapus Voucher Expired" + RESET)
            print(RED     + "  4. Cek DHCP Alert (Rogue DHCP)" + RESET)
            print(MAGENTA + "  5. Speedtest CLI" + RESET)
            # ... (Lanjutkan sesuai daftar menu Anda)
            print(BLUE    + " 21. OLT: Traffic Report per PON (CSV)" + RESET)
            print(CYAN    + " 22. OLT: Auto Audit Script" + RESET)
            print(RESET   + "  0. Keluar")
            
            choice = input("\nPilih Menu (0-22): ").strip()

            if choice == '1': monitor_traffic_realtime()
            elif choice == '2': hotspot_active_realtime()
            # ... (mapping function lainnya)
            elif choice == '21': olt_traffic_report_pon()
            elif choice == '0': sys.exit()
            else:
                print("Pilihan tidak tersedia."); time.sleep(1)
        except KeyboardInterrupt:
            print("\nGunakan menu 0 untuk keluar."); time.sleep(1)

if __name__ == "__main__":
    main()
