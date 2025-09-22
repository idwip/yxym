import requests
from bs4 import BeautifulSoup
import re
import os

# 目标URL列表
urls = [
    'https://ip.164746.xyz/ipTop10.html',
    'https://cf.090227.xyz',
    'https://api.uouin.com/cloudflare.html',
    'https://www.wetest.vip/page/cloudflare/address_v4.html',
    'https://stock.hostmonit.com/CloudFlareYes',
    'https://ipdb.030101.xyz/bestcfv4/'  # 新增的URL
]

# 模拟浏览器请求
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 更严格的IP正则
ip_pattern = r'(?:\d{1,3}\.){3}\d{1,3}'

all_ips = set()
source_ip_count = {}

for url in urls:
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        print(f"正在抓取 {url}, 状态码: {response.status_code}")

        ip_matches = set()

        # 纯文本格式
        if url == 'https://stock.hostmonit.com/CloudFlareYes':
            ip_matches = set(re.findall(ip_pattern, response.text))

        # 解析 ipdb.030101.xyz/bestcfv4/
        elif url == 'https://ipdb.030101.xyz/bestcfv4/':
            soup = BeautifulSoup(response.text, 'html.parser')
            rows = soup.find_all('tr')  # 找到所有表格行
            for row in rows:
                cols = row.find_all('td')
                if cols:
                    ip_text = cols[0].get_text().strip()  # 第一列是IP
                    if re.match(ip_pattern, ip_text):
                        ip_matches.add(ip_text)

        # 其他 HTML 格式
        else:
            soup = BeautifulSoup(response.text, 'html.parser')
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

        # 更新总集合和统计
        all_ips.update(ip_matches)
        source_ip_count[url] = len(ip_matches)

    except Exception as e:
        print(f"处理 {url} 时出错：{e}")
        source_ip_count[url] = 0

# 输出每个源抓取数量
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
