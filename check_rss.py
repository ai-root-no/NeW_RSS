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

# 1. 终极底座：把原仓库 README 里所有活着的、优质的源全部打包死磕在这里
raw_imported_feeds = [
  {"name": "知乎每日精选", "url": "https://zhihu.com", "category": "news"},
  {"name": "阮一峰的网络日志", "url": "https://ruanyifeng.com", "category": "tech"},
  {"name": "少数派", "url": "https://sspai.com/feed", "category": "news"},
  {"name": "美团技术团队", "url": "https://meituan.com", "category": "tech"},
  {"name": "V2EX", "url": "https://v2ex.com", "category": "tech"},
  {"name": "酷壳 – CoolShell", "url": "http://coolshell.cn", "category": "tech"},
  {"name": "爱范儿", "url": "https://ifanr.com", "category": "news"},
  {"name": "知乎热榜", "url": "https://rsshub.app", "category": "news"},
  {"name": "南方周末-新闻", "url": "https://rsshub.app", "category": "news"},
  {"name": "机核", "url": "https://gcores.com", "category": "news"},
  {"name": "热榜 - 煎蛋", "url": "https://rsshub.app", "category": "news"},
  {"name": "云风的 BLOG", "url": "http://codingnow.com", "category": "blog"},
  {"name": "知乎日报", "url": "https://rsshub.app", "category": "news"},
  {"name": "小众软件", "url": "https://appinn.com", "category": "tech"},
  {"name": "虎嗅网", "url": "https://huxiu.com", "category": "news"},
  {"name": "36氪", "url": "https://36kr.com", "category": "news"},
  {"name": "异次元软件世界", "url": "https://iplaysoft.com", "category": "tech"},
  {"name": "DIYGod", "url": "https://diygod.me", "category": "blog"},
  {"name": "王垠的博客", "url": "https://rsshub.app", "category": "blog"},
  {"name": "微博热搜榜", "url": "https://rsshub.app", "category": "news"},
  {"name": "码农周刊", "url": "https://rsshub.app", "category": "tech"},
  {"name": "潮流周刊", "url": "https://tw93.fun", "category": "tech"},
  {"name": "HelloGitHub 月刊", "url": "http://hellogithub.com", "category": "tech"},
  {"name": "游戏研究社", "url": "https://yystv.cn", "category": "news"},
  {"name": "Anyway.FM 设计杂谈", "url": "https://anyway.fm", "category": "blog"},
  {"name": "Anthony Fu", "url": "https://antfu.me", "category": "blog"},
  {"name": "稚晖君的bilibili动态", "url": "https://rsshub.app", "category": "tech"}
]

# 2. 读取或合并
rss_list = raw_imported_feeds

# 给所有源打上英文名和初始在线状态
for item in rss_list:
    item["name_en"] = urlparse(item["url"]).netloc
    item["status"] = "active"

existing_urls = {item['url'].strip().lower() for item in rss_list}

# 3. 体检函数
def check_existing_link(item):
    try:
        res = requests.get(item['url'], headers=HEADERS, timeout=5)
        item['status'] = 'active' if res.status_code == 200 else 'dead'
    except Exception:
        item['status'] = 'dead'
    return item

# 4. 自动繁衍种子站
def harvest_new_homepages(seed_url):
    new_seeds = set()
    try:
        res = requests.get(seed_url, headers=HEADERS, timeout=5)
        if res.status_code != 200: return new_seeds
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if href.startswith('http') and urlparse(seed_url).netloc != urlparse(href).netloc:
                if not any(d in href.lower() for d in ['github.com', 'twitter.com', 'google.com', 'baidu.com']):
                    parsed = urlparse(href)
                    new_seeds.add(f"{parsed.scheme}://{parsed.netloc}/")
    except Exception: pass
    return new_seeds

def discover_rss_from_homepage(homepage_url):
    discovered = []
    try:
        res = requests.get(homepage_url, headers=HEADERS, timeout=5)
        if res.status_code != 200: return discovered
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a', href=True):
            href = a['href']
            if any(p in href.lower() for p in ['/feed', '/rss.xml', 'atom.xml', '/rss', '/index.xml']):
                discovered.append(urljoin(homepage_url, href))
    except Exception: pass
    return list(set(discovered))

def verify_and_format_rss(rss_url):
    if rss_url.strip().lower() in existing_urls: return None
    try:
        res = requests.get(rss_url, headers=HEADERS, timeout=5)
        if res.status_code == 200 and ('xml' in res.headers.get('Content-Type', '').lower() or '<rss' in res.text[:200].lower()):
            existing_urls.add(rss_url.strip().lower())
            return {"name": urlparse(rss_url).netloc, "name_en": urlparse(rss_url).netloc, "url": rss_url, "category": "tech", "status": "active"}
    except Exception: pass
    return None

if __name__ == "__main__":
    print("➡️ 开始并发体检刚才导入的全部优质源...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        rss_list = [r for r in executor.map(check_existing_link, rss_list) if r is not None]

    print("\n➡️ 启动雪球繁殖机制...")
    base_seeds = ["https://meituan.com", "https://ruanyifeng.com"]
    dynamic_seeds = set(base_seeds)
    with ThreadPoolExecutor(max_workers=5) as executor:
        for h_set in executor.map(harvest_new_homepages, base_seeds):
            dynamic_seeds.update(h_set)

    all_potential = []
    for hp in list(dynamic_seeds)[:15]:
        all_potential.extend(discover_rss_from_homepage(hp))

    if all_potential:
        with ThreadPoolExecutor(max_workers=5) as executor:
            new_feeds = [r for r in executor.map(verify_and_format_rss, all_potential) if r is not None]
            rss_list.extend(new_feeds)

    # 彻底去重
    unique_list = []
    seen = set()
    for item in rss_list:
        u = item['url'].strip().lower()
        if u not in seen:
            seen.add(u)
            unique_list.append(item)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=2)
    print(f"💾 导入+体检+繁衍全部结束！当前累计生成源数量：{len(unique_list)}")
