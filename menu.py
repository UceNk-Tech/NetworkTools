#!/usr/bin/env python3
# ==========================================
# NetworkTools Menu (Ucenk-D-Tech)
# ==========================================

import os, time, subprocess, sys
from datetime import datetime
try:
    import routeros_api
except Exception as e:
    print("RouterOS API belum terpasang. Jalankan: pip install routeros-api")
    sys.exit(1)

# Cache kredensial MikroTik (valid 5 menit)
CREDS = {"host": None, "user": None, "pw": None, "ts": 0}

# ---------- UI ----------
def header():
    os.system('clear')
    os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    print(" Author: Ucenk | Premium Network Management System")
    os.system("neofetch --ascii_distro ubuntu")
    print("-" * 60)

def pause(msg="Tekan Enter..."):
    try:
        input(msg)
    except KeyboardInterrupt:
        pass

# ---------- MikroTik ----------
def get_api():
    global CREDS
    now = time.time()
    if (CREDS["host"] is None) or (now - CREDS["ts"] > 300):
        header()
        print("\n[Login MikroTik] (valid 5 menit)")
        CREDS["host"] = input("IP MikroTik : ") or "10.30.0.1"
        CREDS["user"] = input("Username    : ") or "admin"
        CREDS["pw"]   = input("Password    : ") or ""
        CREDS["ts"]   = time.time()
    try:
        pool = routeros_api.RouterOsApiPool(
            CREDS["host"],
            username=CREDS["user"],
            password=CREDS["pw"],
            plaintext_login=True,
            timeout=10
        )
        return pool.get_api(), pool
    except Exception as e:
        print(f"[X] Gagal koneksi: {e}")
        CREDS["host"] = None
        time.sleep(2)
        return None, None

# ---------- Tools ----------
def monitor_traffic_realtime():
    api, pool = get_api()
    if not api: return
    iface = input("Interface (default: bridge1-Hotspot): ") or "bridge1-Hotspot"
    try:
        while True:
            data = api.get_resource('/interface').call('monitor-traffic', {'interface': iface, 'once': 'true'})
            tx = int(data[0].get('tx-bits-per-second', 0)) / 1e6
            rx = int(data[0].get('rx-bits-per-second', 0)) / 1e6
            header()
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {iface} | TX: {tx:.2f} Mbps | RX: {rx:.2f} Mbps")
            print("Ctrl+C untuk berhenti.")
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        pool.disconnect()

def hotspot_active_realtime():
    api, pool = get_api()
    if not api: return
    try:
        while True:
            active = api.get_resource('/ip/hotspot/active').get()
            header()
            print(f"TOTAL USER AKTIF: {len(active)} USER")
            print("-" * 60)
            for u in active:
                print(f"- {u.get('user','?'):15} | {u.get('address','?'):15} | {u.get('uptime','0')}")
            print("-" * 60)
            print("Refresh tiap 5 detik — Ctrl+C untuk berhenti.")
            time.sleep(5)
    except KeyboardInterrupt:
        pass
    finally:
        pool.disconnect()

def remove_expired_voucher():
    api, pool = get_api()
    if not api: return
    try:
        kw = input("Keyword komentar (filter): ").strip()
        users = api.get_resource('/ip/hotspot/user')
        data = users.get()
        expired = [u for u in data
                   if kw in (u.get('comment',''))
                   and u.get('uptime') == u.get('limit-uptime')]
        header()
        print(f"Ditemukan {len(expired)} voucher expired.")
        if expired and input("Hapus semua? (y/n): ").lower() == 'y':
            for u in expired:
                users.remove(id=u['id'])
            print("Selesai menghapus.")
        pause()
    finally:
        pool.disconnect()

def dhcp_alert_check():
    api, pool = get_api()
    if not api: return
    try:
        alerts = api.get_resource('/ip/dhcp-server/alert').get()
        header()
        if alerts:
            print("[!] Rogue DHCP terdeteksi:")
            for a in alerts:
                print(f"- {a.get('unknown-server','?')} | on {a.get('interface','?')}")
        else:
            print("Aman—tidak ada Rogue DHCP.")
        pause()
    finally:
        pool.disconnect()

def speedtest_realtime():
    header()
    # Menjalankan speedtest-cli apa adanya agar progress realtime tampil
    os.system("speedtest-cli")
    pause()

def nmap_scan():
    header()
    target = input("Target IP/Domain: ").strip()
    if not target:
        print("Target kosong.")
        pause()
        return
    # -A untuk OS/service detection; progress realtime dari nmap
    os.system(f"nmap -A {target}")
    pause()

def mac_lookup():
    header()
    mac = input("Masukkan MAC (format 00:11:22:33:44:55): ").strip()
    if not mac:
        print("MAC kosong.")
        pause()
        return
    os.system(f"curl -s https://api.macvendors.com/{mac}")
    print()
    pause()

# ---------- Menu ----------
def main():
    while True:
        header()
        print(" Silakan pilih menu:")
        print(" 1. Monitor Traffic Interface (Realtime)")
        print(" 2. Total User Aktif Hotspot (Realtime)")
        print(" 3. Hapus Voucher Expired")
        print(" 4. Cek DHCP Alert (Rogue DHCP)")
        print(" 5. Speedtest CLI (Realtime Progress)")
        print(" 6. Nmap Scan")
        print(" 7. MAC Lookup")
        print(" 8. Keluar")
        choice = input("\nPilih Menu (1-8): ").strip()

        if choice == '1':
            monitor_traffic_realtime()
        elif choice == '2':
            hotspot_active_realtime()
        elif choice == '3':
            remove_expired_voucher()
        elif choice == '4':
            dhcp_alert_check()
        elif choice == '5':
            speedtest_realtime()
        elif choice == '6':
            nmap_scan()
        elif choice == '7':
            mac_lookup()
        elif choice == '8':
            break
        else:
            print("Pilihan tidak valid.")
            time.sleep(1)

if __name__ == "__main__":
    main()
