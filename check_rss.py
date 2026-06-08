if __name__ == "__main__":
    print("➡️ 开始体检存量数据...")
    if rss_list:
        with ThreadPoolExecutor(max_workers=10) as executor:
            rss_list = [r for r in executor.map(check_existing_link, rss_list) if r is not None]

    # === 【降维打击：全网白嫖合并大厂/优质开源 RSS 列表】 ===
    print("\n➡️ 正在远程同步全网优质开源 RSS 列表（扩充数据规模）...")
    awesome_lists = [
        # 这里你可以放入任何互联网上公开的公开 JSON 格式或文本格式的优质 RSS 列表
        "https://githubusercontent.com" # 例如：把原项目的历史积累直接作为你起步的底座！
    ]
    
    for remote_url in awesome_lists:
        try:
            print(f"正在吸纳整合: {remote_url}")
            res = requests.get(remote_url, timeout=10)
            if res.status_code == 200:
                remote_data = res.json()
                for item in remote_data:
                    # 自动过滤、规范格式并吸纳
                    u = item.get('url', '').strip()
                    if u and u.lower() not in existing_urls:
                        rss_list.append({
                            "name": item.get('name', '未命名源'),
                            "name_en": urlparse(u).netloc,
                            "url": u,
                            "category": item.get('category', 'tech'), # 继承分类
                            "status": "active"
                        })
                        existing_urls.add(u.lower())
        except Exception as e:
            print(f"读取远程列表失败（跳过）: {str(e)}")
    # ========================================================

    print("\n➡️ 启动智能雷达，继续挖掘新源...")
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
        print(f"🎉 本次雷达自动追加了 {len(new_valid_feeds)} 个全新的 RSS 订阅源！")

    # 最终严格进行数据去重清洗并保存
    unique_list = []
    seen_urls = set()
    for item in rss_list:
        if isinstance(item, dict) and 'url' in item:
            u = item['url'].strip().lower()
            if u not in seen_urls:
                seen_urls.add(u)
                unique_list.append(item)

    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique_list, f, ensure_ascii=False, indent=2)
    print(f"💾 扩充成功！当前总计拥有高质量 RSS 源：{len(unique_list)} 个！")
