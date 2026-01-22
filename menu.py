#!/usr/bin/env python3
import os, time, telnetlib

# Warna ANSI
RED, GREEN, YELLOW, BLUE, CYAN, WHITE, RESET = "\033[31m", "\033[32m", "\033[33m", "\033[34m", "\033[36m", "\033[37m", "\033[0m"

# KONFIGURASI OLT (Ucenk D-Tech)
OLT_IP = "192.168.80.100"
OLT_USER = "zte"
OLT_PASS = "zte"

def header():
    os.system('clear')
    print(f"{CYAN}======================================================{RESET}")
    print(f"{GREEN}   Ucenk D-Tech - OLT Management System (ZTE C320)   {RESET}")
    print(f"{CYAN}======================================================{RESET}")

def _run_command(cmds):
    try:
        tn = telnetlib.Telnet(OLT_IP, 23, timeout=10)
        tn.read_until(b"Username:", timeout=5)
        tn.write(OLT_USER.encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=5)
        tn.write(OLT_PASS.encode('ascii') + b"\n")
        
        idx, _, _ = tn.expect([b"ZXAN#", b"Login invalid"], timeout=5)
        if idx != 0: return f"{RED}Gagal Login OLT!{RESET}"
        
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

# --- FUNGSI MENU 15 (REVISI SLOT) ---
def menu_15_list_onu():
    header()
    print(f"{YELLOW}MENU 15: LIHAT SEMUA ONU PER SLOT{RESET}")
    slot = input(f"{WHITE}Masukkan Nomor Slot (Contoh 2 untuk 1/2/1): {RESET}").strip()
    
    if slot:
        full_path = f"gpon-olt_1/{slot}/1"
        print(f"\n{CYAN}Menjalankan: show pon onu information {full_path}...{RESET}")
        print(_run_command([f"show pon onu information {full_path}"]))
    pause()

def pause():
    input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

def main():
    while True:
        header()
        print(f" 15. OLT: List ONU per Slot (1/Slot/1)")
        print(f" 23. OLT: Cek ONU Unconfigured")
        print(f" 88. Fix Permission Mikhmon")
        print(f"  0. Keluar")
        
        pilih = input(f"\n{WHITE}Pilih menu: {RESET}")
        
        if pilih == '15':
            menu_15_list_onu()
        elif pilih == '23':
            header()
            print(_run_command(["show gpon onu uncfg"]))
            pause()
        elif pilih == '88':
            os.system("chmod -R 755 $HOME/mikhmon && echo 'Izin Mikhmon diperbaiki!'")
            time.sleep(2)
        elif pilih == '0':
            break

if __name__ == "__main__":
    main()
