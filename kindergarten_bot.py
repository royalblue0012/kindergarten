import requests
import feedparser
import os
import time

# --- 配置資訊 ---
SEARCH_KEYWORDS = ['幼稚園+開放日', '幼稚園+入學+2027', '幼稚園+報名']
CACHE_FILE = 'seen_links.txt'

# 定義排除地區
EXCLUDED_AREAS = [
    '屯門', '上水', '粉嶺', '元朗', '天水圍', '大埔', 
    '荃灣', '葵涌', '青衣', '馬鞍山', '沙田'
]

def send_telegram_msg(message):
    # 從 GitHub Secrets 獲取 Token
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not token or not chat_id:
        print("❌ 錯誤: 找不到 TELEGRAM_TOKEN 或 TELEGRAM_CHAT_ID，請檢查 GitHub Secrets 設定。")
        return False
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id, 
        "text": message, 
        "parse_mode": "Markdown",
        "disable_web_page_preview": False
    }
    
    try:
        r = requests.post(url, json=payload)
        r.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ 發送 Telegram 失敗: {e}")
        if r.text:
            print(f"   API 回傳內容: {r.text}")
        return False

def monitor_kindergarten():
    # 1. 讀取已讀紀錄
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            seen_links = set(f.read().splitlines())
    else:
        seen_links = set()

    new_updates = []
    current_iteration_links = set()

    # 2. 抓取資訊
    print("📡 正在抓取 Google News 資訊...")
    for kw in SEARCH_KEYWORDS:
        rss_url = f"https://news.google.com/rss/search?q={kw}+when:7d&hl=zh-HK&gl=HK&ceid=HK:zh-Hant"
        feed = feedparser.parse(rss_url)
        
        print(f"🔍 關鍵字 [{kw}] 找到 {len(feed.entries)} 條原始資訊")

        for entry in feed.entries:
            title = entry.title
            link = entry.link

            # 去重與過濾邏輯
            if link not in seen_links and link not in current_iteration_links:
                is_excluded = any(area in title for area in EXCLUDED_AREAS)
                
                # 將軍澳白名單
                if "將軍澳" in title:
                    is_excluded = False

                if not is_excluded:
                    msg = f"🔔 *發現相關幼稚園資訊*\n\n標題: {title}\n\n[點擊查看文章]({link})"
                    new_updates.append(msg)
                    current_iteration_links.add(link)

    # 3. 發送新資訊
    if new_updates:
        success_count = 0
        for update in new_updates:
            if send_telegram_msg(update):
                success_count += 1
            time.sleep(1) # 防頻控
        
        # 4. 更新已讀紀錄
        updated_links = list(current_iteration_links.union(seen_links))[-1000:]
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_links))
        print(f"✅ 成功推送 {success_count} 條資訊。")
    else:
        print("ℹ️ 沒有發現符合地區要求的新資訊。")

if __name__ == "__main__":
    # 執行主程式
    monitor_kindergarten()
