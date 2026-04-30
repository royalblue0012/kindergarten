import requests
import feedparser
import os
import time

# --- 配置資訊 ---
# 針對你目前的居住地加強搜尋關鍵字
SEARCH_KEYWORDS = [
    '幼稚園+開放日', 
    '幼稚園+報名',
    '將軍澳+幼稚園+入學', 
    '九龍灣+幼稚園', 
    '中西區+幼稚園+報名', # 西環屬於中西區
    '西環+幼稚園'
]
CACHE_FILE = 'seen_links.txt'

# 修改排除地區：將你「不」住的遠程地區列入排除
EXCLUDED_AREAS = [
    '屯門', '上水', '粉嶺', '元朗', '天水圍', '大埔', 
    '荃灣', '葵涌', '青衣', '馬鞍山', '沙田', '東涌',
    '南區', '貝沙灣', '數碼港', '香港仔', '鴨脷洲' # 移除舊住址相關地區
]

# 增加無關內容過濾
EXCLUDED_TERMS = ['地產', '成交', '二手', '商場', '繪畫比賽', '著數']

def send_telegram_msg(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ 錯誤: 找不到配置。")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    try:
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ 發送失敗: {e}")
        return False

def monitor_kindergarten():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            seen_links = set(f.read().splitlines())
    else:
        seen_links = set()

    new_updates = []
    current_iteration_links = set()

    print(f"📡 正在為您搜尋 [{', '.join(['將軍澳', '九龍灣', '西環'])}] 附近的幼稚園資訊...")
    
    for kw in SEARCH_KEYWORDS:
        rss_url = f"https://news.google.com/rss/search?q={kw}+when:7d&hl=zh-HK&gl=HK&ceid=HK:zh-Hant"
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries:
            title = entry.title
            link = entry.link

            if link not in seen_links and link not in current_iteration_links:
                # 1. 檢查是否在排除地區
                is_excluded = any(area in title for area in EXCLUDED_AREAS)
                
                # 2. 檢查是否包含垃圾關鍵字
                is_excluded = is_excluded or any(term in title for term in EXCLUDED_TERMS)
                
                # 3. 強制白名單（即便包含排除字眼，只要有以下地名就保留）
                # 加入你的三個居住地作為絕對優先
                whitelist = ["將軍澳", "九龍灣", "西環", "西營盤", "堅尼地城", "中西區"]
                if any(target in title for target in whitelist):
                    is_excluded = False

                if not is_excluded:
                    msg = f"🔔 *發現相關幼稚園資訊*\n\n*標題*: {title}\n\n🔗 [點擊查看文章]({link})"
                    new_updates.append(msg)
                    current_iteration_links.add(link)

    if new_updates:
        success_count = 0
        for update in new_updates:
            if send_telegram_msg(update):
                success_count += 1
            time.sleep(1)
        
        updated_links = list(current_iteration_links.union(seen_links))[-1000:]
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_links))
        print(f"✅ 推送完畢，共 {success_count} 條資訊。")
    else:
        print("ℹ️ 暫時沒有符合地區要求的新資訊。")

if __name__ == "__main__":
    monitor_kindergarten()
