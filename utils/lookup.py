import socket
import time
import whois
import yaml
from seleniumwire import webdriver
from urllib.parse import urlparse

def load_domains_from_yaml(yaml_file):
    """
    Memuat daftar domain berdasarkan kategori dari file YAML.
    """
    with open(yaml_file, 'r') as f:
        domains_by_category = yaml.safe_load(f)
    return domains_by_category

def save_ip_addresses(ip_addresses, file_path):
    """
    Menyimpan pasangan domain dan IP address ke file.
    """
    with open(file_path, 'w') as f:
        for domain, ip_address in ip_addresses.items():
            if ip_address:
                f.write(f"{ip_address}\t{domain}\n")
                print(f"[INFO] IP address untuk '{domain}' adalah '{ip_address}', disimpan ke '{file_path}'")
            else:
                print(f"[WARN] Tidak dapat menyelesaikan IP untuk '{domain}'")

def extract_domain_from_url(url):
    """
    Mengekstrak hostname dari URL.
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc

def get_whois_info(domain, retries=3, delay=2):
    """
    Mencoba mengambil informasi whois dengan mekanisme retry.
    Jika gagal setelah sejumlah percobaan, mengembalikan None.
    """
    for attempt in range(1, retries + 1):
        try:
            print(f"[INFO] Mencoba mengambil whois untuk {domain} (percobaan {attempt}/{retries})...")
            w = whois.whois(domain)
            return w
        except Exception as e:
            print(f"[ERROR] Gagal mengambil whois untuk {domain} (percobaan {attempt}/{retries}): {e}")
            time.sleep(delay)
    return None

def lookup_domains(domains_by_category, output_file, bypass_whois=False):
    """
    Mengunjungi tiap domain yang diberikan, mengambil setiap request yang terjadi,
    melakukan pengecekan whois untuk memastikan domain sesuai dengan kategori (jika tidak dibypass),
    dan mengambil IP address dari domain tersebut.
    
    Parameter:
      - bypass_whois: jika True, maka proses akan melanjutkan resolusi IP meskipun gagal mendapatkan whois.
    """
    # Inisialisasi Selenium Wire dengan opsi headless
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome(options=options)

    ip_addresses = {}
    seen_domains = set()  # Gunakan set untuk menyimpan domain yang sudah diperiksa

    try:
        for category, domains in domains_by_category.items():
            print(f"\n[INFO] Melakukan lookup untuk kategori '{category}'...")
            for domain in domains:
                try:
                    print(f"[INFO] Mengirim request ke: {domain}")
                    driver.get(domain)

                    # Iterasi setiap request yang terekam oleh selenium-wire
                    for request in driver.requests:
                        if request.response:
                            base_url = extract_domain_from_url(request.url)
                            if base_url and base_url not in seen_domains:
                                seen_domains.add(base_url)
                                print(f"[INFO] Mengecek informasi WHOIS untuk: {base_url}")
                                
                                # Coba ambil informasi whois dengan retry
                                w = get_whois_info(base_url, retries=3, delay=2)
                                
                                if w is None:
                                    if bypass_whois:
                                        print(f"[WARN] WHOIS gagal untuk {base_url}. Melanjutkan proses resolusi IP karena bypass_whois=True")
                                    else:
                                        print(f"[WARN] WHOIS gagal untuk {base_url}. Lewati domain ini.")
                                        continue  # Lewati domain ini jika whois tidak berhasil dan bypass_whois False
                                
                                # Jika tidak bypass, cek apakah kategori terdapat dalam informasi whois
                                if not bypass_whois:
                                    if category.lower() not in str(w).lower():
                                        print(f"[INFO] WHOIS untuk {base_url} tidak mengandung kategori '{category}'")
                                        continue

                                print(f"[INFO] Mendapatkan IP untuk {base_url}")
                                try:
                                    ip_address = socket.gethostbyname(base_url)
                                    ip_addresses[base_url] = ip_address
                                except socket.gaierror as ip_err:
                                    print(f"[ERROR] Gagal resolusi IP untuk {base_url}: {ip_err}")
                except Exception as e:
                    print(f"[ERROR] Terjadi error saat mengakses {domain}: {e}")
    finally:
        driver.quit()

    save_ip_addresses(ip_addresses, output_file)

if __name__ == "__main__":
    yaml_file = "utils/custom.yaml"  # Path ke file YAML Anda
    output_file = "data/custom.txt"  # Pastikan ekstensi file sesuai, misal .txt
    domains_by_category = load_domains_from_yaml(yaml_file)
    
    # Ubah bypass_whois ke True jika Anda ingin tetap melanjutkan resolusi IP meskipun WHOIS gagal
    lookup_domains(domains_by_category, output_file, bypass_whois=True)
