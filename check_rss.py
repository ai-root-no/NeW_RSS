import json
import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

DATA_FILE = 'data/sources.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 确保 data 文件夹存在
os.makedirs('data', exist_ok=True)

# 1. 尝试读取已有数据
rss_list = []
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            rss_list = json.load(f)
            # 如果读取出来不是列表，强行变为空列表
            if not isinstance(rss_list, list):
                rss_list = []
    except Exception:
        rss_list = []

# 安全提取已有的 URL
existing_urls = set()
for item in rss_list:
    if isinstance(item, dict) and 'url' in item:
        existing_urls.add(item['url'].strip().lower())

def discover_rss_from_homepage(homepage_url):
    discovered = []
    try:
        res = requests.get(homepage_url, headers=HEADERS, timeout=10, allow_redirects=True)
        if res.status_code != 200: return discovered
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 寻找标准的 link 标签
        feed_links = soup.find_all('link', rel=re.compile(r'alternate', re.I), type=re.compile(r'(rss|atom|xml)', re.I))
        for link in feed_links:
            href = link.get('href')
            if href: discovered.append(urljoin(homepage_url, href))
                
        # 扫描普通 A 标签
        a_tags = soup.find_all('a', href=True)
        for a in a_tags:
            href = a['href']
            if any(p in href.lower() for p in ['/feed', '/rss.xml', 'atom.xml', '/rss', '/index.xml']):
                discovered.append(urljoin(homepage_url, href))
    except Exception:
        pass
    return list(set(discovered))

def verify_and_format_rss(rss_url, default_category="tech"):
    rss_url_clean = rss_url.strip()
    if rss_url_clean.lower() in existing_urls:
        return None
        
    try:
        res = requests.get(rss_url_clean, headers=HEADERS, timeout=8)
        if res.status_code == 200 and ('xml' in res.headers.get('Content-Type', '').lower() or '<rss' in res.text[:300].lower() or '<feed' in res.text[:300].lower()):
            title_match = re.search(r'<title>(.*?)</title>', res.text)
            name = title_match.group(1) if title_match else urlparse(rss_url_clean).netloc
            name = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', name).strip()
            
            # 全局去重检测
            existing_urls.add(rss_url_clean.lower())
            print(f"✨ 成功挖出新源: {name} -> {rss_url_clean}")
            return {
                "name": name,
                "name_en": urlparse(rss_url_clean).netloc,
                "url": rss_url_clean,
                "category": default_category,
                "status": "active"
            }
    except Exception:
        pass
    return None

def check_existing_link(item):
    if not isinstance(item, dict) or 'url' not in item: return None
    try:
        res = requests.get(item['url'], headers=HEADERS, timeout=8)
        item['status'] = 'active' if res.status_code == 200 else 'dead'
    except Exception:
        item['status'] = 'dead'
    return item

if __name__ == "__main__":
    print("➡️ 开始体检存量数据...")
    if rss_list:
        with ThreadPoolExecutor(max_workers=10) as executor:
            rss_list = [r for r in executor.map(check_existing_link, rss_list) if r is not None]

    print("\n➡️ 启动智能雷达挖新源...")
    # 丰富种子网站，给它更多目标去抓取新数据
    target_homepages = [
        "https://ruanyifeng.com",
        "https://meituan.com",
        "https://sspai.com",
        "https://36kr.com",
        "https://ifanr.com",
        "https://hellogithub.com"
    ]
    
    all_potential_rss = []
    for homepage in target_homepages:
        all_potential_rss.extend(discover_rss_from_homepage(homepage))
    
    new_valid_feeds = []
    if all_potential_rss:
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(verify_and_format_rss, all_potential_rss)
            new_valid_feeds = [r for r in results if r is not None]
            
    if new_valid_feeds:
        rss_list.extend(new_valid_feeds)
        print(f"🎉 本次自动追加了 {len(new_valid_feeds)} 个全新的 RSS 订阅源！")
    else:
        print("未发现未录入的新源。")

    # 最终严格进行数据去重清洗
    unique_list = []
    seen_urls = set()
    for item in rss_list:
        u = item['url'].strip().lower()
        if u not in seen_urls:
            seen_urls.add(u)
            unique_list.append(item)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=2)
    print("💾 数据处理成功并安全写回 sources.json。")
