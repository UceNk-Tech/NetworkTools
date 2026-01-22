import os, time, subprocess, routeros_api

creds = {"host": None, "user": None, "pw": None, "time": 0}

def tampilkan_atribut():
    os.system('clear')
    os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    print(" Author: Ucenk | Premium Network Management System")
    os.system("neofetch --ascii_distro ubuntu")
    print("-" * 54)

def get_api():
    global creds
    current_time = time.time()
    if not creds["host"] or (current_time - creds["time"] > 300):
        tampilkan_atribut()
        print("\n[!] Login MikroTik (valid 5 menit)")
        creds["host"] = input("IP MikroTik : ") or "10.30.0.1"
        creds["user"] = input("Username    : ")
        creds["pw"]   = input("Password    : ")
        creds["time"] = time.time()
    try:
        conn = routeros_api.RouterOsApiPool(
            creds["host"], username=creds["user"], password=creds["pw"],
            plaintext_login=True, timeout=10
        )
        return conn.get_api(), conn
    except Exception as e:
        print(f"[X] Gagal koneksi: {e}")
        creds["host"] = None
        time.sleep(2)
        return None, None

def main_menu():
    while True:
        tampilkan_atribut()
        print(" Silakan pilih menu:")
        print(" 1. OLT Management (Telnet)")
        print(" 2. Monitor Traffic Interface")
        print(" 3. Lihat User Aktif Hotspot")
        print(" 4. Hapus Voucher Expired")
        print(" 5. Cek DHCP Alert (Rogue DHCP)")
        print(" 6. Speedtest CLI")
        print(" 7. Nmap Scan")
        print(" 8. MAC Lookup")
        print(" 9. Keluar")

        p = input("\nPilih Menu (1-9): ")

        if p == '1':
            ip = input("Masukkan IP OLT: ")
            if ip: subprocess.run(["telnet", ip])

        elif p in ['2','3','4','5']:
            api, conn = get_api()
            if api:
                try:
                    if p == '2':
                        eth = input("Interface: ") or "bridge1-Hotspot"
                        while True:
                            d = api.get_resource('/interface').call('monitor-traffic', {'interface': eth, 'once':'true'})
                            tx = int(d[0].get('tx-bits-per-second',0))/1e6
                            rx = int(d[0].get('rx-bits-per-second',0))/1e6
                            print(f"{eth} | TX: {tx:.2f} Mbps | RX: {rx:.2f} Mbps")
                            time.sleep(1)
                    elif p == '3':
                        active = api.get_resource('/ip/hotspot/active').get()
                        print(f"User Aktif: {len(active)}")
                        for u in active: print(f"- {u.get('user')} | {u.get('address')} | {u.get('uptime')}")
                        input("Enter...")
                    elif p == '4':
                        kw = input("Keyword Komentar: ")
                        u_res = api.get_resource('/ip/hotspot/user')
                        expired = [u for u in u_res.get() if kw in u.get('comment','') and u.get('uptime')==u.get('limit-uptime','')]
                        print(f"{len(expired)} voucher expired.")
                        if expired and input("Hapus? (y/n): ").lower()=='y':
                            for u in expired: u_res.remove(id=u['id'])
                    elif p == '5':
                        alerts = api.get_resource('/ip/dhcp-server/alert').get()
                        if alerts: 
                            for a in alerts: print(f"[!] Rogue: {a.get('unknown-server')}")
                        else: print("Aman, tidak ada Rogue DHCP.")
                        input("Enter...")
                finally: conn.disconnect()

        elif p == '6':
            os.system("speedtest-cli --simple"); input("Enter...")

        elif p == '7':
            target = input("Target IP/Domain: ")
            os.system(f"nmap -A {target}"); input("Enter...")

        elif p == '8':
            mac = input("Masukkan MAC: ")
            os.system(f"curl -s https://api.macvendors.com/{mac}")

        elif p == '9':
            break

if __name__ == "__main__":
    main_menu()
