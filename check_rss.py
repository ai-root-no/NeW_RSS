import json
import requests
from concurrent.futures import ThreadPoolExecutor

# 读取数据
with open('data/sources.json', 'r', encoding='utf-8') as f:
    rss_list = json.load(f)

def check_link(item):
    url = item['url']
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        # 设置 10 秒超时，允许重定向
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code == 200:
            item['status'] = 'active'
            print(f"✅ {item['name']} - 在线")
        else:
            item['status'] = 'dead'
            print(f"❌ {item['name']} - 状态码错误: {response.status_code}")
    except Exception as e:
        item['status'] = 'dead'
        print(f"❌ {item['name']} - 连接超时或失败: {str(e)}")
    return item

# 使用线程池并发检测，大幅提升速度
print("开始检测 RSS 源状态...")
with ThreadPoolExecutor(max_workers=10) as executor:
    updated_list = list(executor.map(check_link, rss_list))

# 将更新后的状态写回 JSON 文件
with open('data/sources.json', 'w', encoding='utf-8') as f:
    json.dump(updated_list, f, ensure_ascii=False, indent=2)
print("检测完成，数据已更新！")

