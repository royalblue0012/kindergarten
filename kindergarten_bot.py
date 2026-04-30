import requests
import feedparser
import os
import time

# 配置資訊
SEARCH_KEYWORDS = ['幼稚園+開放日', '幼稚園+入學+2027', '幼稚園+報名']
CACHE_FILE = 'seen_links.txt'

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
            # 去重核心邏輯：不在舊紀錄中，且不在本次循環已處理的紀錄中
            if entry.link not in seen_links and entry.link not in current_iteration_links:
                msg = f"🔔 *發現新幼稚園資訊*\n\n標題: {entry.title}\n[點擊查看文章]({entry.link})"
                new_updates.append(msg)
                current_iteration_links.add(entry.link)

    # 3. 發送新資訊並更新紀錄
    if new_updates:
        for update in new_updates:
            send_telegram_msg(update)
            time.sleep(1) # 防頻控
        
        # 將新的連結與舊紀錄合併，只保留最新的 1000 條避免檔案過大
        updated_links = list(current_iteration_links.union(seen_links))[-1000:]
        with open(CACHE_FILE, 'w') as f:
            f.write('\n'.join(updated_links))
        print(f"成功推送 {len(new_updates)} 條新資訊。")
    else:
        print("沒有發現新資訊。")

if __name__ == "__main__":
    monitor_kindergarten()
