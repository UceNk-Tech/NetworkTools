#!/usr/bin/env python3
# ==========================================
# NetworkTools Full Menu (Ucenk-D-Tech) v3.0
# ==========================================
import os, time, telnetlib, sys

# Warna ANSI
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

# KONFIGURASI OLT
OLT_IP = "192.168.80.100"
OLT_USER = "zte"
OLT_PASS = "zte"

def header():
    os.system('clear')
    print(f"{MAGENTA}======================================================{RESET}")
    os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    print(f"{WHITE}      Author: Ucenk  |  Premium Network Management System{RESET}")
    print(f"{MAGENTA}======================================================{RESET}")

def pause():
    input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

def _run_telnet(cmds):
    try:
        tn = telnetlib.Telnet(OLT_IP, 23, timeout=10)
        tn.read_until(b"Username:", timeout=5)
        tn.write(OLT_USER.encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(OLT_PASS.encode('ascii') + b"\n")
        
        idx, _, _ = tn.expect([b"ZXAN#", b"Login invalid"], timeout=5)
        if idx != 0: return f"{RED}Gagal Login OLT! Cek User/Pass.{RESET}"
        
        tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")
        
        result = ""
        for c in cmds:
            tn.write(c.encode('ascii') + b"\n")
            res = tn.read_until(b"ZXAN#", timeout=15)
            result += res.decode('ascii')
            
        tn.write(b"exit\n")
        return result
    except Exception as e:
        return f"{RED}Error Koneksi: {e}{RESET}"

# ---------- FUNGSI OLT SPESIFIK ----------

def menu_15_list_onu():
    header()
    print(f"{YELLOW}--- LIHAT SEMUA ONU PER SLOT ---{RESET}")
    slot = input(f"{WHITE}Masukkan Nomor Slot (Contoh 2 untuk 1/2/1): {RESET}").strip()
    if slot:
        full_path = f"gpon-olt_1/{slot}/1"
        print(f"\n{CYAN}Menjalankan: show pon onu information {full_path}...{RESET}")
        print(_run_telnet([f"show pon onu information {full_path}"]))
    pause()

def menu_25_hapus_onu():
    header()
    print(f"{RED}--- HAPUS ONU (INTERAKTIF) ---{RESET}")
    slot = input("Masukkan Slot (Contoh: 2): ").strip()
    onu_id = input("Masukkan Nomor ONU ID: ").strip()
    if slot and onu_id:
        iface = f"gpon-olt_1/{slot}/1"
        confirm = input(f"{YELLOW}Yakin hapus ONU {onu_id} di {iface}? (y/n): {RESET}")
        if confirm.lower() == 'y':
            cmds = ["conf t", f"interface {iface}", f"no onu {onu_id}", "exit", "write"]
            print(_run_telnet(cmds))
            print(f"{GREEN}Selesai!{RESET}")
    pause()

# ---------- MAIN MENU ----------

def main():
    while True:
        header()
        print(f"{GREEN} 1. Monitor Traffic Interface   {CYAN} 2. User Aktif Hotspot")
        print(f"{YELLOW} 3. Hapus Voucher Expired       {RED} 4. Cek DHCP Alert")
        print(f"{MAGENTA} 5. Speedtest CLI               {BLUE} 6. Nmap Scan")
        print(f"{WHITE} 7. Cek Neighbor (LLDP)         {GREEN} 8. Backup Config")
        print("-" * 54)
        print(f"{CYAN} 14. Update/Repair Environment")
        print(f"{MAGENTA} 15. OLT: List ONU Aktif (per Slot)")
        print(f"{BLUE} 16. OLT: Optical Power (RX/TX)")
        print(f"{YELLOW} 17. OLT: Reset/Reboot ONU")
        print(f"{GREEN} 18. OLT: Cek Vlan Port")
        print("-" * 54)
        print(f"{MAGENTA} 23. OLT: Cek ONU Unconfigured")
        print(f"{BLUE} 24. OLT: Show ONU Info by Port")
        print(f"{RED} 25. OLT: Hapus ONU (Interactive)")
        print(f"{WHITE} 88. Fix Permission Mikhmon")
        print(f"{RED}  0. Keluar")
        
        choice = input(f"\n{WHITE}Pilih Menu (0-88): {RESET}").strip()

        if choice == '15': menu_15_list_onu()
        elif choice == '23': 
            header()
            print(_run_telnet(["show gpon onu uncfg"]))
            pause()
        elif choice == '24':
            header()
            p = input("Masukkan Port Lengkap (misal 1/2/1): ")
            print(_run_telnet([f"show pon onu information gpon-olt_{p}"]))
            pause()
        elif choice == '25': menu_25_hapus_onu()
        elif choice == '88':
            os.system("chmod -R 755 $HOME/mikhmon && echo 'Izin Mikhmon diperbaiki!'")
            time.sleep(2)
        elif choice == '14':
            os.system("pkg update && pkg install python-pip -y && pip install routeros-api lolcat --break-system-packages")
            pause()
        elif choice == '0':
            print("Sampai jumpa, Ucenk!"); break
        elif choice == '': continue
        else:
            print(f"{YELLOW}Menu {choice} masih dalam tahap sinkronisasi API...{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    main()
