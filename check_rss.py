import json
import requests
import re
import os
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

DATA_FILE = 'data/sources.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

os.makedirs('data', exist_ok=True)

# 1. 加载已有 RSS 数据（去重用）
rss_list = []
if os.path.exists(DATA_FILE):
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            rss_list = json.load(f)
            if not isinstance(rss_list, list): rss_list = []
    except Exception:
        rss_list = []

existing_urls = {item['url'].strip().lower() for item in rss_list if isinstance(item, dict) and 'url' in item}

# 2. 核心功能：顺藤摸瓜 —— 从已有网页中“捕获”新的友情链接网站
def harvest_new_homepages(seed_url):
    new_seeds = set()
    try:
        res = requests.get(seed_url, headers=HEADERS, timeout=8, allow_redirects=True)
        if res.status_code != 200: return new_seeds
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 扫描页面上所有的超级链接 <a> 标签
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            # 策略：抓取属于独立的 http/https 的外部完整网址 (排除当前种子站自身的外链、GitHub 或推特等社交大厂外链)
            if href.startswith('http') and urlparse(seed_url).netloc != urlparse(href).netloc:
                if not any(domain in href.lower() for domain in ['github.com', 'twitter.com', 'google.com', 'baidu.com', 'apple.com', 'v2ex.com']):
                    # 格式化为干净的首页路径：例如 https://example.com
                    parsed = urlparse(href)
                    clean_homepage = f"{parsed.scheme}://{parsed.netloc}/"
                    new_seeds.add(clean_homepage)
    except Exception:
        pass
    return new_seeds

# 3. 在目标站点中嗅探 RSS
def discover_rss_from_homepage(homepage_url):
    discovered = []
    try:
        res = requests.get(homepage_url, headers=HEADERS, timeout=8, allow_redirects=True)
        if res.status_code != 200: return discovered
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 寻找标准的 link 标签
        feed_links = soup.find_all('link', rel=re.compile(r'alternate', re.I), type=re.compile(r'(rss|atom|xml)', re.I))
        for link in feed_links:
            href = link.get('href')
            if href: discovered.append(urljoin(homepage_url, href))
                
        # 扫描普通 A 标签路径
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(p in href.lower() for p in ['/feed', '/rss.xml', 'atom.xml', '/rss', '/index.xml']):
                discovered.append(urljoin(homepage_url, href))
    except Exception:
        pass
    return list(set(discovered))

# 4. 验证 RSS 合法性
def verify_and_format_rss(rss_url):
    rss_url_clean = rss_url.strip()
    if rss_url_clean.lower() in existing_urls: return None
    try:
        res = requests.get(rss_url_clean, headers=HEADERS, timeout=6)
        if res.status_code == 200 and ('xml' in res.headers.get('Content-Type', '').lower() or '<rss' in res.text[:300].lower() or '<feed' in res.text[:300].lower()):
            title_match = re.search(r'<title>(.*?)</title>', res.text)
            name = title_match.group(1) if title_match else urlparse(rss_url_clean).netloc
            name = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', name).strip()
            
            existing_urls.add(rss_url_clean.lower())
            print(f"✨ 发现活体新源: {name} -> {rss_url_clean}")
            return {"name": name, "name_en": urlparse(rss_url_clean).netloc, "url": rss_url_clean, "category": "tech", "status": "active"}
    except Exception:
        pass
    return None

def check_existing_link(item):
    if not isinstance(item, dict) or 'url' not in item: return None
    try:
        res = requests.get(item['url'], headers=HEADERS, timeout=6)
        item['status'] = 'active' if res.status_code == 200 else 'dead'
    except Exception: item['status'] = 'dead'
    return item

if __name__ == "__main__":
    print("➡️ 第一步：例行旧数据健康体检...")
    if rss_list:
        with ThreadPoolExecutor(max_workers=10) as executor:
            rss_list = [r for r in executor.map(check_existing_link, rss_list) if r is not None]

    # === 【降维打击核心：target_homepages 种子站全自动滚雪球分裂】 ===
    print("\n➡️ 第二步：雷达种子站正在进行全网“友情链接”无线蔓延挖掘...")
    
    # 你的初始母体种子（用来当做挖掘源头的元老级站点）
    base_seeds = [
        "https://meituan.com",
        "https://www.ruanyifeng.com/blog/",
        "https://hellogithub.com"
    ]
    
    # 自动把母体站里的所有博客外链、友链提取出来，变成一个庞大的自动化线索库！
    dynamic_target_homepages = set(base_seeds)
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(harvest_new_homepages, base_seeds)
        for h_set in results:
            dynamic_target_homepages.update(h_set)
            
    print(f"📡 繁衍成功！种子站线索库已由最初的 {len(base_seeds)} 个，全自动扩充为了 {len(dynamic_target_homepages)} 个巡逻基地！")
    # ===================================================================

    print("\n➡️ 第三步：派驻机器人去这数百个新基地疯狂抽洗 RSS 链接...")
    all_potential_rss = []
    # 限制遍历前 50 个高权重扩充地址，防止 Actions 运行超时
    for homepage in list(dynamic_target_homepages)[:50]:
        all_potential_rss.extend(discover_rss_from_homepage(homepage))
    
    new_valid_feeds = []
    if all_potential_rss:
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(verify_and_format_rss, all_potential_rss)
            new_valid_feeds = [r for r in results if r is not None]
            
    if new_valid_feeds:
        rss_list.extend(new_valid_feeds)
        print(f"🎉 成果丰硕：本次自动化战役追加了 {len(new_valid_feeds)} 个全新的 RSS 订阅卡片！")
    else:
        print("暂无新发现。")

    # 去重清洗并存盘
    unique_list = []
    seen_urls = set()
    for item in rss_list:
        if isinstance(item, dict) and 'url' in item:
            u = item['url'].strip().lower()
            if u not in seen_urls:
                seen_urls.add(u); unique_list.append(item)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=2)
    print(f"💾 数据库落盘完毕。当前总池规模：{len(unique_list)} 个源。")
