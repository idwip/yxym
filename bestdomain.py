import os
import requests
import ipaddress

def is_valid_ip(ip):
    """检查IP地址是否有效"""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False

def get_ip_list(url):
    """从URL获取IP列表，并过滤无效IP"""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        ips = response.text.strip().split('\n')
        return [ip.strip() for ip in ips if is_valid_ip(ip.strip())]
    except Exception as e:
        print(f"Failed to fetch IPs from {url}: {e}")
        return []

def get_cloudflare_zone(api_token, target_domain=None):
    """获取Cloudflare的Zone ID"""
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    response = requests.get('https://api.cloudflare.com/client/v4/zones', headers=headers)
    response.raise_for_status()
    zones = response.json().get('result', [])
    if not zones:
        raise Exception("No zones found")

    if target_domain:
        for zone in zones:
            if zone['name'] == target_domain:
                return zone['id'], zone['name']
        raise Exception(f"Domain {target_domain} not found")

    return zones[0]['id'], zones[0]['name']

def delete_existing_dns_records(api_token, zone_id, subdomain, domain):
    """删除指定子域名下的所有A记录"""
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
    """添加新的A记录，最多200条"""
    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json',
    }
    record_name = domain if subdomain == '@' else f'{subdomain}.{domain}'

    # 将限制提高到200条
    max_records = 200
    ip_list = ip_list[:max_records]
    
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
            json=data, headers=headers
        )
        if response.status_code == 200:
            print(f"Add {subdomain}:{ip}")
        else:
            print(f"Failed to add A record for IP {ip} to subdomain {subdomain}: {response.status_code} {response.text}")

if __name__ == "__main__":
    # 读取环境变量中的Cloudflare API Token
    api_token = os.getenv('CF_API_TOKEN')
    
    # 子域名与对应IP列表的URL映射
    subdomain_ip_mapping = {
        '*': 'https://raw.githubusercontent.com/idwip/yxym/refs/heads/main/ip.txt',
    }
    
    try:
        # 获取Cloudflare的Zone ID和域名
        zone_id, domain = get_cloudflare_zone(api_token)
        
        for subdomain, url in subdomain_ip_mapping.items():
            # 获取并验证IP列表
            ip_list = get_ip_list(url)
            print(f"Found {len(ip_list)} valid IPs for {subdomain}")
            
            # 删除旧的DNS记录
            delete_existing_dns_records(api_token, zone_id, subdomain, domain)
            
            # 添加新的DNS记录（最多200条）
            update_cloudflare_dns(ip_list, api_token, zone_id, subdomain, domain)
            
    except Exception as e:
        print(f"Error: {e}")
