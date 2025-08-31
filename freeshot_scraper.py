import json
import time
from seleniumwire import webdriver  # ⚠️ שים לב - לא selenium רגיל
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

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
    try:
        driver.get(url)
        time.sleep(10)

        for request in driver.requests:
            if request.response and ".m3u8" in request.url:
                return request.url

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
    chrome_options.binary_location = "/usr/bin/google-chrome"

    seleniumwire_options = {
        'verify_ssl': False
    }

    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=chrome_options, seleniumwire_options=seleniumwire_options)

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
