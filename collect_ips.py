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
    'https://stock.hostmonit.com/CloudFlareYes'
]

# 模拟浏览器请求，防止被拦截
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# 更严格的IP正则表达式
ip_pattern = r'(?:\d{1,3}\.){3}\d{1,3}'

# 存储所有IP，避免重复
all_ips = set()

# 存储每个源抓取数量
source_ip_count = {}

for url in urls:
    try:
        # 请求网页内容
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        print(f"正在抓取 {url}, 状态码: {response.status_code}")

        ip_matches = set()

        # 特殊情况：纯文本格式
        if url == 'https://stock.hostmonit.com/CloudFlareYes':
            ip_matches = set(re.findall(ip_pattern, response.text))
        else:
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')

            # 根据不同网站结构选择标签
            if url in ['https://ip.164746.xyz/ipTop10.html', 'https://cf.090227.xyz']:
                elements = soup.find_all('tr')
            elif url == 'https://api.uouin.com/cloudflare.html':
                elements = soup.find_all('div', class_='ip')
            elif url == 'https://www.wetest.vip/page/cloudflare/address_v4.html':
                elements = soup.find_all('p')
            else:
                elements = soup.find_all('li')

            # 从标签中提取IP
            for element in elements:
                ip_matches.update(re.findall(ip_pattern, element.get_text()))

        # 更新总集合和源统计
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
