import json
import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor

# 1. 基础配置
DATA_FILE = 'data/sources.json'
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

# 2. 读取当前已有的 RSS 数据库，建立“已存在网址集合”用于去重
try:
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        rss_list = json.load(f)
except Exception:
    rss_list = []
existing_urls = {item['url'].strip().lower() for item in rss_list}

# 3. 核心探测函数：输入一个普通网站首页，自动找出隐藏的 RSS
def discover_rss_from_homepage(homepage_url):
    discovered = []
    try:
        res = requests.get(homepage_url, headers=HEADERS, timeout=8, allow_redirects=True)
        if res.status_code != 200: return discovered
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 策略 A：寻找标准的 <link rel="alternate" type="application/rss+xml"> 标签
        feed_links = soup.find_all('link', rel=re.compile(r'alternate', re.I), type=re.compile(r'(rss|atom|xml)', re.I))
        for link in feed_links:
            href = link.get('href')
            if href:
                discovered.append(urljoin(homepage_url, href))
                
        # 策略 B：由于部分博主不用标准的 link 标签，额外扫描页面中带有 /feed 或 /rss 字样的普通 A 标签
        a_tags = soup.find_all('a', href=True)
        for a in a_tags:
            href = a['href']
            if any(pattern in href.lower() for pattern in ['/feed', '/rss.xml', 'atom.xml', '/rss']):
                discovered.append(urljoin(homepage_url, href))
    except Exception:
        pass
    return list(set(discovered)) # 去重返回

# 4. 验证寻找出来的 RSS 链接是否真实可用
def verify_and_format_rss(rss_url, default_category="tech"):
    rss_url_clean = rss_url.strip()
    if rss_url_clean.lower() in existing_urls:
        return None # 已经存在的，不要重复添加
        
    try:
        res = requests.get(rss_url_clean, headers=HEADERS, timeout=5)
        if res.status_code == 200 and ('xml' in res.headers.get('Content-Type', '').lower() or '<rss' in res.text[:200].lower() or '<feed' in res.text[:200].lower()):
            # 自动提取 XML 中的博客名字
            title_match = re.search(r'<title>(.*?)</title>', res.text)
            name = title_match.group(1) if title_match else urlparse(rss_url_clean).netloc
            name = re.sub(r'<!\[CDATA\[(.*?)\]\]>', r'\1', name) # 清理 CDATA 标签
            
            print(f"✨ 发现并验证通过了新 RSS 源: {name} -> {rss_url_clean}")
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

# 5. 原有的“存量死链体检”逻辑（保持原先功能）
def check_existing_link(item):
    try:
        res = requests.get(item['url'], headers=HEADERS, timeout=8)
        item['status'] = 'active' if res.status_code == 200 else 'dead'
    except Exception:
        item['status'] = 'dead'
    return item

# 主运行流程
if __name__ == "__main__":
    print("➡️ 第一步：开始对已有的本地 RSS 数据进行例行健康体检...")
    if rss_list:
        with ThreadPoolExecutor(max_workers=10) as executor:
            rss_list = list(executor.map(check_existing_link, rss_list))

    print("\n➡️ 第二步：启动智能雷达，去目标站点抓取新源...")
    # 你可以在这个列表里加入你希望脚本每天盯着和挖掘的博客导航站、技术大厂首页或聚合站
    target_homepages = [
        "https://ruanyifeng.com",
        "https://meituan.com",
        "https://sspai.com",
        "https://36kr.com"
    ]
    
    all_potential_rss = []
    for homepage in target_homepages:
        all_potential_rss.extend(discover_rss_from_homepage(homepage))
    
    # 过滤掉重复和验证不通过的
    new_valid_feeds = []
    if all_potential_rss:
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = executor.map(verify_and_format_rss, all_potential_rss)
            new_valid_feeds = [r for r in results if r is not None]
            
    # 追加并保存
    if new_valid_feeds:
        rss_list.extend(new_valid_feeds)
        print(f"🎉 成功自动追加了 {len(new_valid_feeds)} 个全新的 RSS 订阅源！")
    else:
        print("查无新源，或发现的新源之前已存在。")

    # 写回文件
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(rss_list, f, ensure_ascii=False, indent=2)
    print("💾 数据保存完成。")
