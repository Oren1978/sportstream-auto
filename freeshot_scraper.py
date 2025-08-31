import json, time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By

channels = [
    {
        "id": 1,
        "name": "ספורט 1",
        "page_url": "https://www.freeshot.live/live-tv/yes-sport-1-israel/168",
        "image": "sport1"
    },
    {
        "id": 2,
        "name": "ספורט 2",
        "page_url": "https://www.freeshot.live/live-tv/yes-sport-2-israel/169",
        "image": "sport2"
    },
    {
        "id": 3,
        "name": "ספורט 3",
        "page_url": "https://www.freeshot.live/live-tv/yes-sport-3-israel/170",
        "image": "sport3"
    },
]

def get_m3u8(driver, url):
    driver.get(url)
    time.sleep(10)
    logs = driver.get_log("performance")
    for log in logs:
        message = log["message"]
        if ".m3u8" in message and "url" in message:
            try:
                start = message.index("https")
                end = message.index(".m3u8") + 5
                return message[start:end]
            except:
                continue
    return None

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

    driver = webdriver.Chrome(options=chrome_options)
    result = []

    for ch in channels:
        print(f"⏳ Scraping: {ch['name']}")
        stream_url = get_m3u8(driver, ch["page_url"])
        if stream_url:
            print(f"✅ Found stream: {stream_url}")
            result.append({
                "id": ch["id"],
                "name": ch["name"],
                "url": stream_url,
                "image": ch["image"],
                "headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                    "Referer": ch["page_url"],
                    "Origin": "https://www.freeshot.live"
                }
            })

    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    driver.quit()

if __name__ == "__main__":
    main()
