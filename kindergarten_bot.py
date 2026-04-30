import requests
import feedparser
import os
import time

# --- 配置資訊 ---
SEARCH_KEYWORDS = ['幼稚園+開放日', '幼稚園+入學+2027', '幼稚園+報名']
CACHE_FILE = 'seen_links.txt'

# 定義排除地區（新界區，但不包括將軍澳）
# 這裡加入常見的新界地名關鍵字
EXCLUDED_AREAS = [
    '屯門', '上水', '粉嶺', '元朗', '天水圍', '大埔', 
    '荃灣', '葵涌', '青衣', '馬鞍山', '沙田' # 沙田可視個人需求保留或刪除
]

def send_telegram_msg(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    requests.post(url, json=payload)

def monitor_kindergarten():
    # 1. 讀取已讀紀錄
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r') as f:
            seen_links = set(f.read().splitlines())
    else:
        seen_links = set()

    new_updates = []
    current_iteration_links = set()

    # 2. 抓取資訊
    for kw in SEARCH_KEYWORDS:
        rss_url = f"https://news.google.com/rss/search?q={kw}+when:7d&hl=zh-HK&gl=HK&ceid=HK:zh-Hant"
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            title = entry.title
            link = entry.link

            # 去重邏輯
            if link not in seen_links and link not in current_iteration_links:
                
                # 地區過濾邏輯：
                # 檢查標題是否包含排除名單中的地區
                is_excluded = any(area in title for area in EXCLUDED_AREAS)
                
                # 特別檢查：如果是將軍澳，則強制不排除 (雖然 EXCLUDED_AREAS 沒寫將軍澳，但這是雙重保險)
                if "將軍澳" in title:
                    is_excluded = False

                if not is_excluded:
                    msg = f"🔔 *發現相關幼稚園資訊*\n\n標題: {title}\n[點擊查看文章]({link})"
                    new_updates.append(msg)
                    current_iteration_links.add(link)

    # 3. 發送新資訊並更新紀錄
    if new_updates:
        for update in new_updates:
            send_telegram_msg(update)
            time.sleep(1) # 防頻控
        
        updated_links = list(current_iteration_links.union(seen_links))[-1000:]
        with open(CACHE_FILE, 'w') as f:
            f.write('\n'.join(updated_links))
        print(f"成功推送 {len(new_updates)} 條相關資訊。")
    else:
        print("沒有發現符合地區要求的新資訊。")

if __name__ == "__main__":
    monitor_kindergarten()
