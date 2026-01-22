#!/usr/bin/env python3
import os, time, telnetlib, sys, subprocess

# Warna ANSI
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

# --- KONFIGURASI PERANGKAT ---
OLT_IP = "192.168.80.100"
OLT_USER = "zte"
OLT_PASS = "zte"

# Konfigurasi Mikrotik (Silakan sesuaikan)
MT_IP = "192.168.88.1"
MT_USER = "admin"
MT_PASS = ""

def header():
    os.system('clear')
    print(f"{MAGENTA}======================================================{RESET}")
    os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    print(f"{WHITE}      Author: Ucenk  |  Premium Network Management System{RESET}")
    print(f"{MAGENTA}======================================================{RESET}")

def pause():
    input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

# ---------- ENGINE KONEKSI ----------

def _run_olt(cmds):
    try:
        tn = telnetlib.Telnet(OLT_IP, 23, timeout=10)
        tn.read_until(b"Username:", timeout=5); tn.write(OLT_USER.encode('ascii') + b"\n")
        tn.read_until(b"Password:", timeout=5); tn.write(OLT_PASS.encode('ascii') + b"\n")
        idx, _, _ = tn.expect([b"ZXAN#", b"Login invalid"], timeout=5)
        if idx != 0: return f"{RED}Gagal Login OLT!{RESET}"
        tn.write(b"terminal length 0\n"); tn.read_until(b"ZXAN#")
        res_full = ""
        for c in cmds:
            tn.write(c.encode('ascii') + b"\n")
            res_full += tn.read_until(b"ZXAN#", timeout=15).decode('ascii')
        tn.write(b"exit\n"); return res_full
    except Exception as e: return f"{RED}Error OLT: {e}{RESET}"

def _run_mt(cmd):
    # Menggunakan SSH CLI untuk Mikrotik agar lebih simpel di Termux
    ssh_cmd = f"sshpass -p '{MT_PASS}' ssh -o StrictHostKeyChecking=no {MT_USER}@{MT_IP} '{cmd}'"
    try:
        return subprocess.check_output(ssh_cmd, shell=True).decode()
    except:
        return f"{RED}Gagal konek Mikrotik. Pastikan sshpass terinstall dan service SSH Mikrotik aktif.{RESET}"

# ---------- FUNGSI MENU MIKROTIK (1-8) ----------

def menu_mt(choice):
    header()
    if choice == '1': print(_run_mt("/interface monitor-traffic [find] once"))
    elif choice == '2': print(_run_mt("/ip hotspot active print"))
    elif choice == '3': print(_run_mt("/ip hotspot user remove [find where comment~\"vc-\" and uptime=limit-uptime]"))
    elif choice == '4': print(_run_mt("/ip dhcp-server alert print"))
    elif choice == '5': os.system("speedtest-cli")
    elif choice == '6': 
        ip = input("Masukkan IP Target Scan: "); os.system(f"nmap -F {ip}")
    elif choice == '7': print(_run_mt("/routing protocols lldp neighbor print"))
    elif choice == '8': print(_run_mt("/system backup save name=backup_ucenk; /export file=config_ucenk"))
    pause()

# ---------- FUNGSI MENU OLT (15-25) ----------

def menu_olt(choice):
    header()
    if choice == '15':
        slot = input("Masukkan Slot (Contoh 2): ")
        print(_run_olt([f"show pon onu information gpon-olt_1/{slot}/1"]))
    elif choice == '16':
        slot = input("Slot: "); onu = input("ONU ID: ")
        print(_run_olt([f"show pon onu rx-power gpon-onu_1/{slot}/1:{onu}"]))
    elif choice == '17':
        slot = input("Slot: "); onu = input("ONU ID: ")
        print(_run_olt([f"pon-onu-mng gpon-onu_1/{slot}/1:{onu}", "reboot", "exit"]))
    elif choice == '18':
        slot = input("Slot: ")
        print(_run_olt([f"show vlan bridge interface gpon-olt_1/{slot}/1"]))
    elif choice == '23':
        print(_run_olt(["show gpon onu uncfg"]))
    elif choice == '24':
        p = input("Masukkan Port (misal 1/2/1): ")
        print(_run_olt([f"show pon onu information gpon-olt_{p}"]))
    elif choice == '25':
        slot = input("Slot: "); onu = input("ONU ID: ")
        confirm = input(f"Hapus ONU {onu} di 1/{slot}/1? (y/n): ")
        if confirm.lower() == 'y':
            print(_run_olt(["conf t", f"interface gpon-olt_1/{slot}/1", f"no onu {onu}", "exit", "write"]))
    pause()

# ---------- MAIN ----------

def main():
    while True:
        header()
        print(f"{GREEN} 1. Monitor Traffic Interface   {CYAN} 2. User Aktif Hotspot")
        print(f"{YELLOW} 3. Hapus Voucher Expired       {RED} 4. Cek DHCP Alert")
        print(f"{MAGENTA} 5. Speedtest CLI               {BLUE} 6. Nmap Scan")
        print(f"{WHITE} 7. Cek Neighbor (LLDP)         {GREEN} 8. Backup Config")
        print(f"{MAGENTA}------------------------------------------------------")
        print(f"{WHITE} 14. Update/Repair Environment")
        print(f"{MAGENTA} 15. OLT: List ONU Aktif        {BLUE} 16. OLT: Optical Power")
        print(f"{YELLOW} 17. OLT: Reset/Reboot ONU      {GREEN} 18. OLT: Cek Vlan Port")
        print(f"{MAGENTA}------------------------------------------------------")
        print(f"{CYAN} 23. OLT: Cek ONU Unconfigured  {WHITE} 24. OLT: Show ONU Info")
        print(f"{RED} 25. OLT: Hapus ONU (Interactive){CYAN} 88. Fix Permission Mikhmon")
        print(f"{RED}  0. Keluar")
        
        c = input(f"\n{WHITE}Pilih Menu: {RESET}").strip()

        if c in ['1','2','3','4','5','6','7','8']: menu_mt(c)
        elif c in ['15','16','17','18','23','24','25']: menu_olt(c)
        elif c == '14':
            os.system("pkg update && pkg install sshpass nmap -y")
            os.system("pip install speedtest-cli lolcat --break-system-packages")
            pause()
        elif c == '88':
            os.system("chmod -R 755 $HOME/mikhmon && echo 'Izin diperbaiki!'")
            time.sleep(1)
        elif c == '0': break
        else: print(f"{RED}Input Salah!{RESET}"); time.sleep(1)

if __name__ == "__main__":
    main()
