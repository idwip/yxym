import requests
from bs4 import BeautifulSoup
import re
import json
import time
import random

# 目标URL列表
urls = [
    'https://ip.164746.xyz/ipTop10.html',
    'https://cf.090227.xyz',
    'https://api.uouin.com/cloudflare.html',
    'https://www.wetest.vip/page/cloudflare/address_v4.html',
    'https://stock.hostmonit.com/CloudFlareYes',
    'https://ipdb.030101.xyz/bestcfv4/'  # 静态抓取优化
]

# 模拟浏览器请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

# IP正则
ip_pattern = r'(?:\d{1,3}\.){3}\d{1,3}'

all_ips = set()
source_ip_count = {}

for url in urls:
    try:
        # 随机延时 1~3 秒
        time.sleep(random.uniform(1, 3))

        print(f"正在抓取 {url} ...")
        r = requests.get(url, headers=headers, timeout=15)
        r.encoding = 'utf-8'
        text = r.text

        ip_matches = set()

        # 纯文本页面
        if url == 'https://stock.hostmonit.com/CloudFlareYes':
            ip_matches = set(re.findall(ip_pattern, text))

        # 静态解析 ipdb.030101.xyz/bestcfv4/
        elif url == 'https://ipdb.030101.xyz/bestcfv4/':
            soup = BeautifulSoup(text, 'html.parser')
            # 尝试从表格抓
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if cols:
                    ip_text = cols[0].get_text().strip()
                    if re.match(ip_pattern, ip_text):
                        ip_matches.add(ip_text)
            # 尝试从 script/json 中抓
            scripts = soup.find_all('script')
            for script in scripts:
                data = script.string
                if data:
                    ips_in_script = re.findall(ip_pattern, data)
                    ip_matches.update(ips_in_script)

        # 其他 HTML 页面
        else:
            soup = BeautifulSoup(text, 'html.parser')
            if url in ['https://ip.164746.xyz/ipTop10.html', 'https://cf.090227.xyz']:
                elements = soup.find_all('tr')
            elif url == 'https://api.uouin.com/cloudflare.html':
                elements = soup.find_all('div', class_='ip')
            elif url == 'https://www.wetest.vip/page/cloudflare/address_v4.html':
                elements = soup.find_all('p')
            else:
                elements = soup.find_all('li')

            for element in elements:
                ip_matches.update(re.findall(ip_pattern, element.get_text()))

        all_ips.update(ip_matches)
        source_ip_count[url] = len(ip_matches)
        print(f"源 {url} 共抓取 {len(ip_matches)} 个 IP 地址")

    except Exception as e:
        print(f"处理 {url} 时出错：{e}")
        source_ip_count[url] = 0

# 输出抓取统计
for url, count in source_ip_count.items():
    print(f"源 {url} 共抓取 {count} 个 IP 地址")

# 保存到 ip.txt
if all_ips:
    with open('ip.txt', 'w') as file:
        for ip in sorted(all_ips):
            file.write(ip + '\n')
    print(f"共抓取到 {len(all_ips)} 个 IP，已保存到 ip.txt")
else:
    print("未抓取到任何 IP，请检查网络或网页结构。")
