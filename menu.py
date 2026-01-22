        elif menu_type == '3':
            print(f"{CYAN}Scanning Script Laporan Mikhmon...{RESET}")
            # Akses ke System Script (Bukan User Hotspot)
            script_res = api.get_resource('/system/script')
            
            # Filter ketat: Hanya yang berawalan 'log-' (Format laporan Mikhmon)
            to_delete = [s for s in script_res.get() if s.get('name', '').startswith('log-')]
            
            if not to_delete:
                print(f"{YELLOW}Tidak ditemukan script laporan (log-) di System Script.{RESET}")
                print(f"{GREEN}User dan Voucher aman, tidak ada yang perlu dihapus.{RESET}")
            else:
                print(f"{WHITE}Ditemukan {len(to_delete)} script laporan mikhmon:{RESET}")
                for s in to_delete:
                    print(f" - {s.get('name')}")
                
                # Konfirmasi manual oleh Ucenk
                print(f"\n{RED}PERINGATAN: Ini hanya menghapus LOG LAPORAN di System Script.{RESET}")
                confirm = input(f"{YELLOW}Hapus semua LOG ini? (y/n): {RESET}").lower()
                
                if confirm == 'y':
                    count = 0
                    for s in to_delete:
                        script_res.remove(id=s.get('id'))
                        count += 1
                    
                    # Kosongkan System Note (Tempat simpan totalan sementara Mikhmon)
                    try:
                        api.get_resource('/system/note').set(note="")
                        print(f"{GREEN}System Note dikosongkan.{RESET}")
                    except:
                        pass
                        
                    print(f"{GREEN}Selesai! {count} script laporan dihapus. User/Voucher tetap utuh.{RESET}")
                else:
                    print(f"{BLUE}Dibatalkan. Tidak ada data yang dihapus.{RESET}")
                    
