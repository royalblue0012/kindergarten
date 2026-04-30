import requests
from bs4 import BeautifulSoup
import os
import time
import feedparser # 需要 pip install feedparser

# 配置資訊
# 關鍵字：幼稚園 開放日, 幼稚園 報名, 優質幼稚園 (可自行增加)
SEARCH_KEYWORDS = ['幼稚園+開放日', '幼稚園+入學+2027', '幼稚園+報名']

def send_telegram_msg(message):
    token = os.environ.get('TELEGRAM_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    if not token or not chat_id:
        print("Error: Missing Telegram Config")
        return
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Telegram Send Error: {e}")

def monitor_kindergarten_news():
    seen_links_file = 'seen_links.txt'
    
    # 讀取已發送過的連結，避免重複通知
    if os.path.exists(seen_links_file):
        with open(seen_links_file, 'r') as f:
            seen_links = set(f.read().splitlines())
    else:
        seen_links = set()

    new_updates = []

    for kw in SEARCH_KEYWORDS:
        # 使用 Google News RSS 監控關鍵字
        rss_url = f"https://news.google.com/rss/search?q={kw}+when:7d&hl=zh-HK&gl=HK&ceid=HK:zh-Hant"
        feed = feedparser.parse(rss_url)

        for entry in feed.entries:
            if entry.link not in seen_links:
                # 簡單過濾：確保標題包含關鍵字（減少雜訊）
                msg = f"🔔 *發現新幼稚園資訊*\n\n標題: {entry.title}\n時間: {entry.published}\n\n[點擊查看文章]({entry.link})"
                new_updates.append(msg)
                seen_links.add(entry.link)

    # 發送通知並更新已讀清單
    if new_updates:
        for update in new_updates:
            send_telegram_msg(update)
            time.sleep(1) # 避免觸發 TG API 頻率限制
            
        with open(seen_links_file, 'w') as f:
            f.write('\n'.join(list(seen_links)[-500:])) # 只保留最後 500 條記錄避免檔案過大
    else:
        print("今日暫無新資訊。")

if __name__ == "__main__":
    monitor_kindergarten_news()
