import re
import random
import time
from bs4 import BeautifulSoup
from requests_html import HTMLSession

# 目标URL列表
urls = [
    'https://ip.164746.xyz/ipTop10.html',
    'https://cf.090227.xyz',
    'https://api.uouin.com/cloudflare.html',
    'https://www.wetest.vip/page/cloudflare/address_v4.html',
    'https://stock.hostmonit.com/CloudFlareYes',
    'https://ipdb.030101.xyz/bestcfv4/'
]

# 模拟浏览器请求头
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36"
}

# 更严格的IP正则
ip_pattern = r'(?:\d{1,3}\.){3}\d{1,3}'

# 可选代理（示例格式，可替换为你的代理）
proxies_list = [
    # "http://127.0.0.1:1080",
    # "http://127.0.0.1:1081",
]

all_ips = set()
source_ip_count = {}

session = HTMLSession()

for url in urls:
    try:
        # 随机延时 1~3 秒
        time.sleep(random.uniform(1, 3))

        # 随机选代理，如果列表为空则不使用
        proxies = {"http": random.choice(proxies_list), "https": random.choice(proxies_list)} if proxies_list else None

        print(f"正在抓取 {url} ...")
        r = session.get(url, headers=headers, timeout=15, proxies=proxies)

        # 动态渲染页面
        if url == 'https://ipdb.030101.xyz/bestcfv4/':
            r.html.render(timeout=20)

        text = r.text
        ip_matches = set()

        # 纯文本格式
        if url == 'https://stock.hostmonit.com/CloudFlareYes':
            ip_matches = set(re.findall(ip_pattern, text))

        # 解析 ipdb.030101.xyz/bestcfv4/
        elif url == 'https://ipdb.030101.xyz/bestcfv4/':
            soup = BeautifulSoup(r.html.html, 'html.parser')
            rows = soup.find_all('tr')
            for row in rows:
                cols = row.find_all('td')
                if cols:
                    ip_text = cols[0].get_text().strip()
                    if re.match(ip_pattern, ip_text):
                        ip_matches.add(ip_text)

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
