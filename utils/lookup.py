import re
import socket
import whois
import yaml
from seleniumwire import webdriver
from urllib.parse import urlparse

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

def extract_domain_from_url(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc

def lookup_domains(domains_by_category, file_path):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')

    driver = webdriver.Chrome(options=options)

    ip_addresses = {}
    base_urls = []

    for category, domains in domains_by_category.items():
        print(f"Looking up domains for category '{category}'...")
        for domain in domains:
            try:
                print(f"Sending request to {domain}")
                driver.get(domain)

                print(f"Checking each request for {domain}:")
                for request in driver.requests:
                    if request.response:
                        base_url = extract_domain_from_url(request.url)
                        if base_url and base_url not in base_urls:
                            base_urls.append(base_url)
                            print(f"Checking domain org for {base_url}")
                            w = whois.whois(base_url)
                            if category.lower() in str(w).lower():
                                print(f"Getting the IP address for {base_url}")
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
