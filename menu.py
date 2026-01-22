def run_mt_api(menu_type):
    try:
        import routeros_api
    except ImportError:
        print(f"{RED}Error: Library 'routeros-api' tidak ditemukan!{RESET}")
        return

    creds = get_credentials("mikrotik")
    
    try:
        connection = routeros_api.RouterOsApiPool(
            creds['ip'], username=creds['user'], password=creds['pass'], port=8728, plaintext_login=True
        )
        api = connection.get_api()
        
        # --- LOGIKA MENU 3 (HAPUS LAPORAN) ---
        if menu_type == '3':
            print(f"{CYAN}Scanning Script Laporan Mikhmon...{RESET}")
            script_res = api.get_resource('/system/script')
            # Mencari script yang berawalan 'log-'
            to_delete = [s for s in script_res.get() if s.get('name', '').startswith('log-')]
            
            if not to_delete:
                print(f"{YELLOW}Tidak ditemukan script laporan (log-) untuk dihapus.{RESET}")
            else:
                print(f"{WHITE}Ditemukan {len(to_delete)} script laporan:{RESET}")
                for s in to_delete:
                    print(f" - {s.get('name')}")
                
                # Meminta konfirmasi Ucenk
                confirm = input(f"\n{RED}Hapus semua script di atas? (y/n): {RESET}").lower()
                if confirm == 'y':
                    count = 0
                    for s in to_delete:
                        script_res.remove(id=s.get('id'))
                        count += 1
                    # Kosongkan System Note
                    try:
                        api.get_resource('/system/note').set(note="")
                    except: pass
                    print(f"{GREEN}Berhasil menghapus {count} script laporan.{RESET}")
                else:
                    print(f"{YELLOW}Penghapusan dibatalkan.{RESET}")
        
        # --- LOGIKA MENU LAINNYA ---
        elif menu_type == '1':
            res = api.get_resource('/interface').get()
            for i in res: print(f"[{i.get('name')}] Running: {i.get('running')}")
        elif menu_type == '2':
            active = api.get_resource('/ip/hotspot/active').get()
            print(f"\n{GREEN}Total Hotspot Aktif: {len(active)}{RESET}")
            for u in active: print(f"User: {u.get('user'):<15} IP: {u.get('address'):<15}")
        elif menu_type == '4':
            alerts = api.get_resource('/ip/dhcp-server/alert').get()
            print(alerts if alerts else f"{YELLOW}Aman. Tidak ada Rogue DHCP.{RESET}")

        connection.disconnect()
    except Exception as e:
        print(f"{RED}Mikrotik API Error: {e}{RESET}")
            
