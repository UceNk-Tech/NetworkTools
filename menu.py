#!/usr/bin/env python3
import os, time, telnetlib, sys, subprocess

# Warna ANSI
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

def header():
    os.system('clear')
    print(f"{MAGENTA}======================================================{RESET}")
    # Menggunakan try-except jika figlet/lolcat belum terinstall
    try:
        os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    except:
        print(f"{GREEN}      UCENK D-TECH NETWORK TOOLS{RESET}")
    print(f"{WHITE}      Author: Ucenk  |  Premium Network Management System{RESET}")
    print(f"{MAGENTA}======================================================{RESET}")

# --- SISTEM KEAMANAN KONFIGURASI ---
try:
    import config
    OLT_IP = config.OLT_IP
    OLT_USER = config.OLT_USER
    OLT_PASS = config.OLT_PASS
except ImportError:
    header()
    print(f"{YELLOW}INFO: Konfigurasi OLT tidak ditemukan di config.py{RESET}")
    OLT_IP = input(" Masukkan IP OLT (ex: 192.168.80.100): ").strip()
    OLT_USER = input(" Masukkan Username OLT: ").strip()
    import getpass
    OLT_PASS = getpass.getpass(" Masukkan Password OLT: ").strip()

# Konfigurasi Mikrotik (Optional)
MT_IP = "192.168.88.1"
MT_USER = "admin"
MT_PASS = ""

def pause():
    input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

# ---------- ENGINE KONEKSI OLT (TELNET) ----------

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

# ---------- FUNGSI MENU MIKROTIK (1-8) ----------

def menu_mt(choice):
    header()
    # Menggunakan SSH CLI sederhana (Membutuhkan sshpass)
    ssh_base = f"sshpass -p '{MT_PASS}' ssh -o StrictHostKeyChecking=no {MT_USER}@{MT_IP}"
    
    if choice == '1': 
        os.system(f"{ssh_base} '/interface monitor-traffic [find] once'")
    elif choice == '2': 
        os.system(f"{ssh_base} '/ip hotspot active print'")
    elif choice == '3': 
        os.system(f"{ssh_base} '/ip hotspot user remove [find where comment~\"vc-\" and uptime=limit-uptime]'")
        print(f"{GREEN}Proses pembersihan voucher expired selesai.{RESET}")
    elif choice == '4': 
        os.system(f"{ssh_base} '/ip dhcp-server alert print'")
    elif choice == '5': 
        os.system("speedtest-cli")
    elif choice == '6': 
        target = input("Masukkan IP Target Scan: "); os.system(f"nmap -F {target}")
    elif choice == '7': 
        os.system(f"{ssh_base} '/routing protocols lldp neighbor print'")
    elif choice == '8': 
        os.system(f"{ssh_base} '/system backup save name=backup_ucenk; /export file=config_ucenk'")
        print(f"{GREEN}Backup tersimpan di Mikrotik (backup_ucenk & config_ucenk).{RESET}")
    pause()

# ---------- FUNGSI MENU OLT (15-25) ----------

def menu_olt(choice):
    header()
    if choice == '15':
        slot = input("Masukkan Nomor Slot (Contoh 2 untuk 1/2/1): ")
        if slot: print(_run_olt([f"show pon onu information gpon-olt_1/{slot}/1"]))
    elif choice == '16':
        slot = input("Slot: "); onu = input("ONU ID: ")
        if slot and onu: print(_run_olt([f"show pon onu rx-power gpon-onu_1/{slot}/1:{onu}"]))
    elif choice == '17':
        slot = input("Slot: "); onu = input("ONU ID: ")
        if slot and onu:
            confirm = input(f"Reset ONU {onu} di 1/{slot}/1? (y/n): ")
            if confirm.lower() == 'y': print(_run_olt([f"pon-onu-mng gpon-onu_1/{slot}/1:{onu}", "reboot", "exit"]))
    elif choice == '18':
        slot = input("Slot: ")
        if slot: print(_run_olt([f"show vlan bridge interface gpon-olt_1/{slot}/1"]))
    elif choice == '23':
        print(_run_olt(["show gpon onu uncfg"]))
    elif choice == '24':
        p = input("Masukkan Port Lengkap (misal 1/2/1): ")
        if p: print(_run_olt([f"show pon onu information gpon-olt_{p}"]))
    elif choice == '25':
        slot = input("Masukkan Slot: "); onu = input("Masukkan ONU ID: ")
        if slot and onu:
            confirm = input(f"Yakin hapus ONU {onu} di Slot {slot}? (y/n): ")
            if confirm.lower() == 'y':
                print(_run_olt(["conf t", f"interface gpon-olt_1/{slot}/1", f"no onu {onu}", "exit", "write"]))
    pause()

# ---------- MAIN INTERFACE ----------

def main():
    while True:
        header()
        print(f"{GREEN} 1. Monitor Traffic Interface   {CYAN} 2. User Aktif Hotspot")
        print(f"{YELLOW} 3. Hapus Voucher Expired       {RED} 4. Cek DHCP Alert")
        print(f"{MAGENTA} 5. Speedtest CLI               {BLUE} 6. Nmap Scan")
        print(f"{WHITE} 7. Cek Neighbor (LLDP)         {GREEN} 8. Backup Config")
        print(f"{MAGENTA}------------------------------------------------------")
        print(f"{WHITE} 14. Update/Repair Environment")
        print(f"{MAGENTA} 15. OLT: List ONU Aktif (Slot) {BLUE} 16. OLT: Optical Power")
        print(f"{YELLOW} 17. OLT: Reset/Reboot ONU      {GREEN} 18. OLT: Cek Vlan Port")
        print(f"{MAGENTA}------------------------------------------------------")
        print(f"{CYAN} 23. OLT: Cek ONU Unconfigured  {WHITE} 24. OLT: Show ONU Info")
        print(f"{RED} 25. OLT: Hapus ONU (Interactive){CYAN} 88. Fix Permission Mikhmon")
        print(f"{RED}  0. Keluar")
        
        c = input(f"\n{WHITE}Pilih Menu (0-88): {RESET}").strip()

        if c in ['1','2','3','4','5','6','7','8']: menu_mt(c)
        elif c in ['15','16','17','18','23','24','25']: menu_olt(c)
        elif c == '14':
            os.system("pkg update && pkg install sshpass nmap figlet -y")
            os.system("pip install speedtest-cli lolcat --break-system-packages")
            print(f"{GREEN}Environment diperbarui.{RESET}")
            pause()
        elif c == '88':
            os.system("chmod -R 755 $HOME/mikhmon")
            print(f"{GREEN}Izin folder Mikhmon telah diperbaiki.{RESET}")
            time.sleep(1)
        elif c == '0':
            print(f"{CYAN}Sampai jumpa, Ucenk!{RESET}"); break
        elif c == '': continue
        else:
            print(f"{RED}Pilihan tidak ada!{RESET}")
            time.sleep(1)

if __name__ == "__main__":
    main()
