import os
import requests
from bs4 import BeautifulSoup
import re

def get_ip_list(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    text = response.text.strip()

    ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
    
    # 纯文本格式
    if text.count('\n') > 0 and re.match(ip_pattern, text.split('\n')[0]):
        return [line.strip() for line in text.split('\n') if re.match(ip_pattern, line.strip())]

    # HTML 格式
    soup = BeautifulSoup(text, 'html.parser')

    if 'uouin.com' in url:
        return [div.text.strip() for div in soup.find_all('div', class_='ip') if re.match(ip_pattern, div.text.strip())]

    # 默认抓取 li 和 p
    elements = soup.find_all(['li', 'p'])
    return [el.text.strip() for el in elements if re.match(ip_pattern, el.text.strip())]

def get_cloudflare_zone(api_token):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get('https://api.cloudflare.com/client/v4/zones', headers=headers)
    response.raise_for_status()
    zones = response.json().get('result', [])
    if not zones:
        raise Exception("No zones found")
    return zones[0]['id'], zones[0]['name']

def delete_existing_dns_records(api_token, zone_id, subdomain, domain):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    while True:
        response = requests.get(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?type=A&name={record_name}',
            headers=headers
        )
        response.raise_for_status()
        records = response.json().get('result', [])
        if not records:
            break
        for record in records:
            delete_response = requests.delete(
                f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record["id"]}',
                headers=headers
            )
            delete_response.raise_for_status()
            print(f"Del {subdomain}:{record['id']}")

def update_cloudflare_dns(ip_list, api_token, zone_id, subdomain, domain):
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'
    for ip in ip_list:
        data = {
            "type": "A",
            "name": record_name,
            "content": ip,
            "ttl": 1,
            "proxied": False
        }
        response = requests.post(
            f'https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records',
            json=data,
            headers=headers
        )
        if response.status_code == 200:
            print(f"Add {subdomain}:{ip}")
        else:
            print(f"Failed to add A record for IP {ip} to subdomain {subdomain}: {response.status_code} {response.text}")

if __name__ == "__main__":
    api_token = os.getenv('CF_API_TOKEN')

    subdomain_ip_mapping = {
        'bestcf': 'https://ipdb.030101.xyz/api/bestcf.txt',
        'api': 'https://raw.githubusercontent.com/idwip/yxym/refs/heads/main/ip.txt',
        'stock': 'https://stock.hostmonit.com/CloudFlareYes',
        'cf090227': 'https://cf.090227.xyz/api/best.txt',
        'uouin': 'https://api.uouin.com/cloudflare.html',
    }

    try:
        zone_id, domain = get_cloudflare_zone(api_token)
        
        for subdomain, url in subdomain_ip_mapping.items():
            print(f"\nProcessing {subdomain} from {url}")
            ip_list = get_ip_list(url)
            if not ip_list:
                print(f"No IPs found for {subdomain}, skipping...")
                continue

            delete_existing_dns_records(api_token, zone_id, subdomain, domain)
            update_cloudflare_dns(ip_list, api_token, zone_id, subdomain, domain)

    except Exception as e:
        print(f"Error: {e}")
