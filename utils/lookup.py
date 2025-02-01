import socket
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

def lookup_domains(domains_by_category, output_file):
    """
    Mengunjungi tiap domain yang diberikan, mengambil setiap request yang terjadi,
    melakukan pengecekan whois untuk memastikan domain sesuai dengan kategori,
    dan mengambil IP address dari domain tersebut.
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
                                try:
                                    w = whois.whois(base_url)
                                except Exception as whois_err:
                                    print(f"[ERROR] Gagal mengambil whois untuk {base_url}: {whois_err}")
                                    continue

                                # Pengecekan sederhana apakah kategori (misalnya 'tiktok' atau 'reddit')
                                # terdapat pada hasil whois (dapat disesuaikan dengan kebutuhan)
                                if category.lower() in str(w).lower():
                                    print(f"[INFO] Mendapatkan IP untuk {base_url}")
                                    try:
                                        ip_address = socket.gethostbyname(base_url)
                                        ip_addresses[base_url] = ip_address
                                    except socket.gaierror as ip_err:
                                        print(f"[ERROR] Gagal resolusi IP untuk {base_url}: {ip_err}")
                                else:
                                    print(f"[INFO] WHOIS untuk {base_url} tidak mengandung kategori '{category}'")
                except Exception as e:
                    print(f"[ERROR] Terjadi error saat mengakses {domain}: {e}")
    finally:
        driver.quit()

    save_ip_addresses(ip_addresses, output_file)

if __name__ == "__main__":
    yaml_file = "utils/custom.yaml"  # Path ke file YAML Anda
    output_file = "data/custom.txt"  # Pastikan ekstensi file sesuai, misal .txt
    domains_by_category = load_domains_from_yaml(yaml_file)
    lookup_domains(domains_by_category, output_file)
