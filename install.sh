#!/usr/bin/env python3
import os, time, sys, getpass, telnetlib

# ANSI Colors
RED, GREEN, YELLOW, BLUE, MAGENTA, CYAN, WHITE, RESET = (
    "\033[31m", "\033[32m", "\033[33m", "\033[34m", 
    "\033[35m", "\033[36m", "\033[37m", "\033[0m"
)

# Penyimpanan Profil OLT (Agar tidak isi IP terus-menerus)
# Anda bisa isi manual di sini atau via menu 14
DEVICE_PROFILES = {
    "olt": [
        {"ip": "192.168.80.100", "user": "zte", "pw": "zte"} # Sesuaikan pass-nya
    ]
}

def header():
    os.system('clear')
    os.system("figlet -f slant 'Ucenk D-Tech' | lolcat")
    print(f"{WHITE} Author: Ucenk | Premium Network Management System{RESET}")
    print("-" * 60)

def pause():
    input(f"\n{YELLOW}Tekan Enter untuk kembali...{RESET}")

# ---------- ENGINE TELNET ZTE ----------
def _telnet_zte_run(ip, user, pw, commands):
    try:
        print(f"{CYAN}Menghubungkan ke {ip}...{RESET}")
        tn = telnetlib.Telnet(ip, port=23, timeout=10)
        
        # Menunggu prompt Username
        tn.read_until(b"Username:", timeout=5)
        tn.write(user.encode('ascii') + b"\n")
        
        # Menunggu prompt Password
        tn.read_until(b"Password:", timeout=5)
        tn.write(pw.encode('ascii') + b"\n")
        
        # Cek apakah login berhasil (menunggu prompt ZXAN#)
        idx, obj, res = tn.expect([b"ZXAN#", b"Login invalid"], timeout=5)
        if idx == 1:
            return f"{RED}Login Gagal: Username/Password salah.{RESET}"
        
        output = ""
        # Matikan pagination agar teks tidak terpotong (penting di C320)
        tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#", timeout=2)

        for cmd in commands:
            print(f"{BLUE}Mengirim perintah: {cmd}{RESET}")
            tn.write(cmd.encode('ascii') + b"\n")
            # Tunggu sampai prompt muncul kembali menandakan perintah selesai
            res = tn.read_until(b"ZXAN#", timeout=10)
            output += res.decode('ascii')
            
        tn.write(b"exit\n")
        tn.close()
        return output
    except Exception as e:
        return f"{RED}Error Telnet: {e}{RESET}"

def _pick_olt():
    if not DEVICE_PROFILES["olt"]:
        print(f"{RED}Belum ada profil OLT. Tambahkan di menu 14.{RESET}")
        pause(); return None
    return DEVICE_PROFILES["olt"][0] # Ambil profil pertama (192.168.80.100)

# ---------- FUNGSI MENU OLT (23, 24, 25) ----------

def olt_check_unconfigured():
    p = _pick_olt()
    if p:
        header()
        res = _telnet_zte_run(p['ip'], p['user'], p['pw'], ["show gpon onu uncfg"])
        print(f"\n{GREEN}--- HASIL UNCONFIGURED ---{RESET}")
        print(res)
    pause()

def olt_show_onu_info_port():
    p = _pick_olt()
    if p:
        header()
        print(f"{WHITE}Contoh format: gpon-olt_1/1/1{RESET}")
        port = input("Masukkan Port OLT: ").strip()
        if port:
            res = _telnet_zte_run(p['ip'], p['user'], p['pw'], [f"show pon onu information {port}"])
            print(f"\n{GREEN}--- INFORMASI ONU {port} ---{RESET}")
            print(res)
    pause()

def olt_delete_onu_interactive():
    p = _pick_olt()
    if p:
        header()
        print(f"{RED}=== HAPUS ONU DARI OLT ==={RESET}")
        iface = input("Masukkan Interface (Contoh gpon-olt_1/1/1): ").strip()
        onu_id = input("Masukkan Nomor ONU (Contoh 1): ").strip()
        
        if iface and onu_id:
            print(f"\n{YELLOW}PERINGATAN: Akan menghapus ONU {onu_id} di {iface}{RESET}")
            confirm = input("Apakah Anda yakin? (y/n): ").lower()
            if confirm == 'y':
                cmds = [
                    "configure terminal",
                    f"interface {iface}",
                    f"no onu {onu_id}",
                    "exit",
                    "write"
                ]
                res = _telnet_zte_run(p['ip'], p['user'], p['pw'], cmds)
                print(res)
                print(f"{GREEN}Selesai.{RESET}")
            else:
                print("Dibatalkan.")
    pause()

# ---------- MAIN MENU ----------
def main():
    while True:
        header()
        print(f"{WHITE} 23. OLT: Cek ONU Unconfigured")
        print(f"{WHITE} 24. OLT: Show ONU Info by Port")
        print(f"{RED} 25. OLT: Hapus ONU (Interactive)")
        print(f"{WHITE}  0. Keluar")
        
        choice = input("\nPilih Menu (0-25): ").strip()

        if choice == '23': olt_check_unconfigured()
        elif choice == '24': olt_show_onu_info_port()
        elif choice == '25': olt_delete_onu_interactive()
        elif choice == '0': break
        else:
            print("Menu belum diimplementasi atau salah pilih."); time.sleep(1)

if __name__ == "__main__":
    main()
