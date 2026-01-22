#!/usr/bin/env python3
# ==========================================
# NetworkTools Menu (Ucenk-D-Tech) v2.6
# ==========================================

import os, time, sys, getpass, telnetlib, csv
from datetime import datetime

# Warna ANSI
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

# Profil Default OLT (Sesuaikan IP/User/Pass Anda di sini)
DEVICE_PROFILES = {
    "olt": [{"ip": "192.168.80.100", "user": "zte", "pw": "zte"}],
    "mikrotik": []
}

def header():
    os.system('clear')
    # --- TAMPILAN BANNER TETAP (Sesuai Permintaan) ---
    print(MAGENTA + "======================================================" + RESET)
    os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    print(WHITE + "      Author: Ucenk  |  Premium Network Management System" + RESET)
    print(MAGENTA + "======================================================" + RESET)
    print(CYAN + f" Welcome back, Ucenk D-Tech! | {datetime.now().strftime('%d-%m-%Y %H:%M')}" + RESET)
    print("-" * 54)

def pause():
    input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

# ---------- FUNGSI AUTO REPAIR / UPDATE (Permintaan Anda) ----------
def run_system_update():
    header()
    print(f"{CYAN}Menjalankan Pemeliharaan Lingkungan Termux...{RESET}")
    # Perintah yang Anda minta digabung jadi satu eksekusi
    cmds = [
        "pkg update && pkg upgrade -y",
        "pkg install python-pip python-cryptography -y",
        "pip install routeros-api lolcat --break-system-packages"
    ]
    for cmd in cmds:
        print(f"{YELLOW}Executing: {cmd}{RESET}")
        os.system(cmd)
    print(f"\n{GREEN}Update & Repair Selesai!{RESET}")
    pause()

# ---------- ENGINE TELNET ZTE (ZXAN C320) ----------
def _telnet_run(ip, user, pw, commands):
    try:
        print(f"{CYAN}Connecting Telnet to {ip}...{RESET}")
        tn = telnetlib.Telnet(ip, 23, timeout=10)
        
        tn.read_until(b"Username:", timeout=5)
        tn.write(user.encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(pw.encode('ascii') + b"\n")
        
        idx, obj, res = tn.expect([b"ZXAN#", b"Login invalid"], timeout=5)
        if idx == 1: return f"{RED}Login Gagal! Cek User/Pass di menu.py{RESET}"
        
        output = ""
        tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#", timeout=2)

        for cmd in commands:
            tn.write(cmd.encode('ascii') + b"\n")
            res = tn.read_until(b"ZXAN#", timeout=15)
            output += res.decode('ascii')
            
        tn.write(b"exit\n")
        return output
    except Exception as e:
        return f"{RED}Koneksi Telnet Gagal: {e}{RESET}"

# ---------- FUNGSI MENU OLT (15-25) ----------

def olt_check_unconfigured():
    p = DEVICE_PROFILES["olt"][0]
    header()
    print(f"{GREEN}Mencari ONU Belum Config di OLT {p['ip']}...{RESET}")
    print(_telnet_run(p['ip'], p['user'], p['pw'], ["show gpon onu uncfg"]))
    pause()

def olt_show_onu_info_port():
    p = DEVICE_PROFILES["olt"][0]
    header()
    print(f"{WHITE}Contoh: gpon-olt_1/1/1{RESET}")
    port = input("Masukkan Interface: ").strip()
    if port:
        print(_telnet_run(p['ip'], p['user'], p['pw'], [f"show pon onu information {port}"]))
    pause()

def olt_delete_onu_interactive():
    p = DEVICE_PROFILES["olt"][0]
    header()
    print(f"{RED}--- MENU HAPUS ONU (ZXAN C320) ---{RESET}")
    iface = input("Masukkan Interface (misal gpon-olt_1/1/1): ").strip()
    onu_id = input("Masukkan Nomor ONU (misal 1): ").strip()
    
    if iface and onu_id:
        print(f"\n{YELLOW}KONFIRMASI: Hapus ONU {onu_id} pada port {iface}?{RESET}")
        confirm = input("Ketik 'y' untuk eksekusi: ").lower()
        if confirm == 'y':
            cmds = ["conf t", f"interface {iface}", f"no onu {onu_id}", "exit", "write"]
            print(_telnet_run(p['ip'], p['user'], p['pw'], cmds))
            print(f"{GREEN}Proses Penghapusan Selesai.{RESET}")
        else:
            print("Pembatalan dilakukan.")
    pause()

# ---------- MAIN MENU ----------
def main():
    while True:
        header()
        print(WHITE + " Silakan pilih menu:" + RESET)
        print(GREEN + "  1. Monitor Traffic Interface      " + CYAN + " 2. User Aktif Hotspot")
        print(YELLOW + "  3. Hapus Voucher Expired          " + RED + " 4. Cek DHCP Alert")
        print(MAGENTA + "  5. Speedtest CLI                  " + BLUE + " 6. Nmap Scan")
        print("-" * 54)
        print(CYAN + " 14. Update/Repair Environment (PKG & PIP)")
        print("-" * 54)
        print(MAGENTA + " 15. OLT: List ONU Aktif            " + BLUE + " 16. OLT: Optical Power")
        print(CYAN + " 17. OLT: Reset ONU                 " + GREEN + " 18. OLT: Port & VLAN")
        print(MAGENTA + " 23. OLT: Cek ONU Unconfigured")
        print(BLUE + " 24. OLT: Show ONU Info by Port")
        print(RED + " 25. OLT: Hapus ONU (Interactive)")
        print(RESET + "  0. Keluar")
        
        choice = input("\nPilih Menu (0-25): ").strip()

        if choice == '14': run_system_update()
        elif choice == '23': olt_check_unconfigured()
        elif choice == '24': olt_show_onu_info_port()
        elif choice == '25': olt_delete_onu_interactive()
        elif choice == '0': break
        else:
            print(f"{YELLOW}Menu {choice} dipilih (Dalam Pengembangan / Demo).{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    main()
