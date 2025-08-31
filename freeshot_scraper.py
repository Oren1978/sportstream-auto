import json
import time
from seleniumwire import webdriver  # ⚠️ שים לב: seleniumwire
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchFrameException, TimeoutException

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
    {
        "id": 4,
        "name": "ספורט 4",
        "page_url": "https://www.freeshot.live/live-tv/yes-sport-4-israel/171",
        "image": "sport4"
    },
    {
        "id": 5,
        "name": "ספורט 5",
        "page_url": "https://www.freeshot.live/live-tv/yes-sport-5-israel/172",
        "image": "sport5"
    },
    {
        "id": 6,
        "name": "ספורט 5 פלוס",
        "page_url": "https://www.freeshot.live/live-tv/sport-5-plus-israel/173",
        "image": "sport5plus"
    },
    {
        "id": 7,
        "name": "ספורט 5 לייב",
        "page_url": "https://www.freeshot.live/live-tv/sport-5-live-israel/174",
        "image": "sport5live"
    },
    {
        "id": 8,
        "name": "ספורט 5 סטארס",
        "page_url": "https://www.freeshot.live/live-tv/sport-5-stars-israel/175",
        "image": "sport5stars"
    },
    {
        "id": 9,
        "name": "ספורט 5 גולד",
        "page_url": "https://www.freeshot.live/live-tv/sport-5-gold-israel/176",
        "image": "sport5gold"
    },
]

def get_m3u8(driver, url):
    try:
        driver.get(url)
        time.sleep(12)  # זמן לטעינת JS והנגן

        # נסה להיכנס ל-iframe אם קיים
        try:
            iframe = driver.find_element(By.TAG_NAME, "iframe")
            driver.switch_to.frame(iframe)
            time.sleep(5)
        except NoSuchFrameException:
            pass

        # חיפוש בבקשות רשת דרך seleniumwire
        for request in driver.requests:
            if request.response and ".m3u8" in request.url:
                return request.url

    except Exception as e:
        print(f"⚠️  Failed to fetch m3u8 for {url}: {e}")
    return None

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.binary_location = "/usr/bin/google-chrome"

    seleniumwire_options = {
        'verify_ssl': False,
        'request_storage': 'memory',
        'disable_encoding': True
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
