import requests
import feedparser
import os
import time

# --- 配置資訊 ---
# 1. 強化搜尋參數：hl=zh-HK, gl=HK, ceid=HK:zh-Hant 是指定香港區的關鍵
# 2. 在關鍵字後加上 "香港" 二字，進一步縮小範圍
SEARCH_KEYWORDS = [
    '香港+幼稚園+開放日', 
    '香港+幼稚園+報名',
    '將軍澳+幼稚園', 
    '九龍灣+幼稚園', 
    '西環+幼稚園',
    '中西區+幼稚園+入學'
]
CACHE_FILE = 'seen_links.txt'

# 排除地區（排除新界遠程地區及台灣常見地名）
EXCLUDED_AREAS = [
    '屯門', '上水', '粉嶺', '元朗', '天水圍', '大埔', 
    '荃灣', '葵涌', '青衣', '馬鞍山', '沙田', '東涌',
    '南區', '貝沙灣', '數碼港',
    # 新增台灣地名排除，防止台灣新聞誤入
    '台北', '台中', '台南', '高雄', '新北', '桃園', '新竹'
]

# 排除無關關鍵字
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

    print(f"📡 正在搜尋 [香港 - 將軍澳/九龍灣/西環] 幼稚園資訊...")
    
    for kw in SEARCH_KEYWORDS:
        # 強制指定香港區域碼
        rss_url = f"https://news.google.com/rss/search?q={kw}+when:7d&hl=zh-HK&gl=HK&ceid=HK:zh-Hant"
        feed = feedparser.parse(rss_url)
        
        for entry in feed.entries:
            title = entry.title
            link = entry.link

            # 排除非香港來源的連結（例如 .tw 結尾的網址）
            if ".tw" in link or "udn.com" in link or "ltn.com.tw" in link:
                continue

            if link not in seen_links and link not in current_iteration_links:
                # 檢查排除地區
                is_excluded = any(area in title for area in EXCLUDED_AREAS)
                # 檢查排除字眼
                is_excluded = is_excluded or any(term in title for term in EXCLUDED_TERMS)
                
                # 香港在地化白名單：確保目標地區不被誤殺
                whitelist = ["將軍澳", "九龍灣", "西環", "西營盤", "堅尼地城", "中西區"]
                if any(target in title for target in whitelist):
                    is_excluded = False

                # 最終確認：標題必須含有「香港」或白名單地名，才視為香港新聞
                # 或者是來源不含有台灣新聞常用的後綴
                if not is_excluded:
                    msg = f"🔔 *發現香港幼稚園資訊*\n\n*標題*: {title}\n\n🔗 [點擊查看文章]({link})"
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
        print(f"✅ 香港資訊推送完畢，共 {success_count} 條。")
    else:
        print("ℹ️ 暫時沒有符合要求的香港新資訊。")

if __name__ == "__main__":
    monitor_kindergarten()
