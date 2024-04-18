import re
import socket

import whois
import yaml
from seleniumwire import webdriver


def load_domains_from_yaml(yaml_file):
    with open(yaml_file, 'r') as f:
        domains_by_category = yaml.safe_load(f)
    return domains_by_category

def save_ip_addresses(ip_addresses, file_path):
    with open(file_path, 'w') as f:
        for domain, ip_address in ip_addresses.items():
            if ip_address:
                f.write(f"{ip_address}\t{domain}\n")
                print(f"IP address for '{domain}' is '{ip_address}', saved to '{file_path}'")
            else:
                print(f"Could not resolve the IP address for '{domain}'")

def lookup_domains(domains_by_category, file_path):
    pattern = r"https?://(?:www\.)?([^/]+)"

    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)

    ip_addresses = {}
    base_urls = []
    for category, domains in domains_by_category.items():
        print(f"Looking up domains for category '{category}'...")
        for domain in domains:
            try:
                print("sending request")
                driver.get(domain)

                print(f"checking each requests for {domain}:")
                for request in driver.requests:
                    if request.response:
                        match = re.match(pattern, request.url)
                        base_url = match.group(1) if match else None
                        if base_url not in base_urls:
                            base_urls.append(base_url)
                            print(f"checking domain org for {request.url}")
                            w = whois.whois(base_url)
                            if category in str(w).lower():
                                print(f"getting the ip address for {base_url}")
                                ip_address = socket.gethostbyname(base_url)
                                ip_addresses[base_url] = ip_address

            except Exception as e:
                print(f"{domain} error: {e}")
    save_ip_addresses(ip_addresses, file_path)
    driver.quit()

# Example usage:
yaml_file = "utils/custom.yaml"
domains_by_category = load_domains_from_yaml(yaml_file)
file_path = "data/custom"
lookup_domains(domains_by_category, file_path)

