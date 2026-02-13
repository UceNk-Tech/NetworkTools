def tanya_alice():
    # --- PENTING: MASUKKAN API KEY BARU KAMU DI SINI ---
    API_KEY = "AIzaSyArLs7KtWTwb7p02OUhZtNLDTx1YPvtdlM" 
    
    # Setting Model
    MODEL = "gemini-1.5-flash"
    URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
    
    # Warna Termux
    RED = '\033[0;31m'; CYAN = '\033[0;36m'; MAGENTA = '\033[0;35m'; YELLOW = '\033[0;33m'; RESET = '\033[0m'
    
    print(f"\n{MAGENTA}[✨ Alice Gemini 1.5 Flash]{RESET} {CYAN}Halo Ucenk! Aku siap pantau Mikrotik & OLT kamu.{RESET}")
    print(f"{YELLOW}(Ketik '0' untuk kembali ke menu utama){RESET}")

    while True:
        try:
            user_input = input(f"{YELLOW}Ucenk [90]: {RESET}").strip()
            
            if user_input.lower() in ['0', 'keluar', 'exit']: 
                print(f"{CYAN}Alice istirahat dulu ya. Bye!{RESET}")
                break
            
            if not user_input: continue

            output_eksekusi = "Tidak ada data sistem tambahan."
            
            # --- LOGIKA IMPORT FUNGSI DARI MAIN MENU ---
            # Kita menggunakan trik mengintip namespace global atau file main
            import __main__ 
            
            # Cek User Hotspot
            if any(key in user_input.lower() for key in ["user aktif", "hotspot", "mikrotik"]):
                print(f"{CYAN}(Bentar Cenk, aku intip Mikrotik dulu...){RESET}")
                f = io.StringIO()
                with redirect_stdout(f):
                    try:
                        # Mencoba akses fungsi yang ada di menu.py (file utama)
                        if hasattr(__main__, 'mk_hotspot_active'):
                            __main__.mk_hotspot_active()
                        else:
                            print("Info: Fungsi mk_hotspot_active tidak ditemukan di menu utama.")
                    except Exception as e:
                        print(f"Error fungsi: {e}")
                output_eksekusi = f.getvalue()

            # Cek ONU/OLT
            elif any(key in user_input.lower() for key in ["list onu", "onu", "olt"]):
                print(f"{CYAN}(Sabar ya, aku cek daftar ONU dulu...){RESET}")
                f = io.StringIO()
                with redirect_stdout(f):
                    try:
                        if hasattr(__main__, 'list_onu'):
                            __main__.list_onu()
                        else:
                            print("Info: Fungsi list_onu tidak ditemukan di menu utama.")
                    except Exception as e:
                        print(f"Error fungsi: {e}")
                output_eksekusi = f.getvalue()

            # --- KIRIM KE AI ---
            headers = {
                'Content-Type': 'application/json',
                'x-goog-api-key': API_KEY
            }
            
            prompt_system = f"""
            Kamu adalah Alice, asisten teknisi jaringan D-Tech (Ucenk).
            Data dari sistem (Mikrotik/OLT):
            {output_eksekusi}
            
            Jawab pertanyaan Ucenk berdasarkan data di atas (jika ada) atau pengetahuan umum teknisi.
            """

            payload = {
                "contents": [{
                    "parts": [{"text": f"{prompt_system}\n\nUcenk bertanya: {user_input}"}]
                }],
                "generationConfig": {
                    "temperature": 0.7,
                    "maxOutputTokens": 800
                }
            }

            response = requests.post(URL, headers=headers, json=payload)
            
            if response.status_code == 200:
                res_json = response.json()
                try:
                    jawaban = res_json['candidates'][0]['content']['parts'][0]['text']
                    # Bersihkan format bold markdown (**) biar rapi
                    jawaban = jawaban.replace("**", "")
                    print(f"\n{MAGENTA}Alice: {RESET}{jawaban}\n")
                except:
                    print(f"\n{RED}[!] Alice bingung.{RESET}")
            else:
                print(f"\n{RED}[!] Gagal connect Google.{RESET}")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\n{RED}[!] Error: {e}{RESET}")
