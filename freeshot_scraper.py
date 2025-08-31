import json
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By

channels = [
    {
        "id": 1,
        "name": "ספורט 1",
        "page_url": "https://www.freeshot.live/live-tv/yes-sport-1-israel/168",
        "image": "sport1"
    },
    # המשך הערוצים כרגיל...
]

def get_m3u8(driver, url):
    requests = []

    def log_request(request):
        if ".m3u8" in request['request']['url']:
            requests.append(request['request']['url'])

    try:
        driver.execute_cdp_cmd("Network.enable", {})
        driver.request_interceptor = log_request
        driver.get(url)
        time.sleep(12)

        # נשלוף את כל הבקשות ברשת
        logs = driver.execute_cdp_cmd("Network.getResponseBody", {})
        for req in requests:
            if ".m3u8" in req:
                return req
    except Exception as e:
        print(f"⚠️  Failed to fetch m3u8 for {url}: {e}")

    return None

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    )
    chrome_options.binary_location = "/usr/bin/google-chrome"
    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    output = []

    for ch in channels:
        print(f"⏳ Scraping: {ch['name']}")
        stream_url = get_m3u8(driver, ch["page_url"])
        if stream_url:
            print(f"✅ Found stream: {stream_url}")
            output.append({
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
        else:
            print(f"❌ No stream found for {ch['name']}")

    driver.quit()

    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print("✅ channels.json saved")

if __name__ == "__main__":
    main()
