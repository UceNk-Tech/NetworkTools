# --- FUNGSI OLT (NOMOR 9 - REVISI SLOT INPUT) ---
def run_olt_telnet_onu():
    creds = get_credentials("olt")
    try:
        print(f"\n{MAGENTA}==== OLT ONU SCANNER ===={RESET}")
        # Ucenk masukkan angka tengah (Slot), misal: 2
        slot = input(f"{CYAN} Masukkan Nomor Slot (contoh: 2): {RESET}").strip()
        
        if not slot:
            print(f"{RED}Slot tidak boleh kosong!{RESET}")
            return

        # Meminta Port (angka terakhir), misal: 1
        pon = input(f"{CYAN} Masukkan Nomor PON (contoh: 1): {RESET}").strip()
        
        if not pon:
            print(f"{RED}PON tidak boleh kosong!{RESET}")
            return

        # Koordinat lengkap menjadi 1/slot/pon, misal: 1/2/1
        full_port = f"gpon-olt_1/{slot}/{pon}"
        
        tn = telnetlib.Telnet(creds['ip'], 23, timeout=10)
        tn.read_until(b"Username:"); tn.write(creds['user'].encode() + b"\n")
        tn.read_until(b"Password:"); tn.write(creds['pass'].encode() + b"\n")
        time.sleep(1)
        
        tn.write(b"terminal length 0\n")
        tn.read_until(b"ZXAN#")
        
        print(f"{YELLOW}[*] Menarik data ONU Aktif di {full_port}...{RESET}")
        
        # Eksekusi perintah sesuai format OLT ZTE
        command = f"show pon onu information {full_port}\n"
        tn.write(command.encode())
        time.sleep(2)
        
        result = tn.read_very_eager().decode()
        
        # Tampilkan hasil
        print(f"\n{WHITE}{result}{RESET}")
        
        tn.write(b"exit\n")
        tn.close()
    except Exception as e:
        print(f"{RED}Error OLT: {e}{RESET}")

# --- UPDATE DI DALAM MAIN() ---
def main():
    while True:
        show_sticky_header()
        c = input(f"{CYAN}Pilih Nomor: {RESET}").strip()
        
        if c == '1':
            # Logika Mikhmon Anti-Lock tetap dipertahankan
            mikhmon_dir = os.path.expanduser("~/mikhmonv3")
            tmp_dir = os.path.expanduser("~/tmp")
            sess_dir = os.path.expanduser("~/session_mikhmon")
            if not os.path.exists(mikhmon_dir):
                os.system(f"git clone https://github.com/laksa19/mikhmonv3.git {mikhmon_dir}")
            os.system(f"mkdir -p {tmp_dir} {sess_dir}")
            with open(os.path.join(tmp_dir, "custom.ini"), "w") as f:
                f.write("opcache.enable=0\n")
                f.write(f'session.save_path="{sess_dir}"\n')
            os.system("fuser -k 8080/tcp > /dev/null 2>&1")
            os.system(f'export PHP_INI_SCAN_DIR={tmp_dir}; php -S 127.0.0.1:8080 -t {mikhmon_dir}')
            
        elif c in ['2', '3', '4']:
            run_mt(c) # Menu Mikrotik aman
            
        elif c == '9':
            run_olt_telnet_onu() # Menu OLT dengan input Slot
            
        elif c == '22':
            # Update & Auto-Refresh tetap sinkron
            os.system('cd $HOME/NetworkTools && git reset --hard && git pull origin main && bash install.sh && exec zsh')
            break
            
        elif c == '0': break
        input(f"\n{YELLOW}Tekan Enter untuk kembali ke Menu Utama...{RESET}")
