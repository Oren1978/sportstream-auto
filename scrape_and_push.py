import json
import time
import random
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- רשימת הערוצים ---
channels = [
    {"id": 1, "name": "ספורט 1", "page_url": "https://www.freeshot.live/live-tv/yes-sport-1-israel/168", "image": "sport1"},
    {"id": 2, "name": "ספורט 2", "page_url": "https://www.freeshot.live/live-tv/yes-sport-2-israel/169", "image": "sport2"},
    {"id": 3, "name": "ספורט 3", "page_url": "https://www.freeshot.live/live-tv/yes-sport-3-israel/170", "image": "sport3"},
    {"id": 4, "name": "ספורט 4", "page_url": "https://www.freeshot.live/live-tv/yes-sport-4-israel/171", "image": "sport4"},
    {"id": 5, "name": "ספורט 5", "page_url": "https://www.freeshot.live/live-tv/yes-sport-5-israel/172", "image": "sport5"},
    {"id": 6, "name": "ספורט 5 פלוס", "page_url": "https://www.freeshot.live/live-tv/sport-5-plus-israel/173", "image": "sport5plus"},
    {"id": 7, "name": "ספורט 5 לייב", "page_url": "https://www.freeshot.live/live-tv/sport-5-live-israel/174", "image": "sport5live"},
    {"id": 8, "name": "ספורט 5 סטארס", "page_url": "https://www.freeshot.live/live-tv/sport-5-stars-israel/175", "image": "sport5stars"},
    {"id": 9, "name": "ספורט 5 גולד", "page_url": "https://www.freeshot.live/live-tv/sport-5-gold-israel/176", "image": "sport5gold"},
]

# --- פונקציה להגדרת דפדפן "חמקן" ---
def get_stealth_driver():
    chrome_options = Options()
    
    # 1. מצב Headless משופר (פחות ניתן לגילוי)
    chrome_options.add_argument("--headless=new") 

    # 2. הסתרת העובדה שזה אוטומציה (קריטי!)
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # 3. User Agent אמין וקבוע (כרום על ווינדוס 10)
    # שימוש בזה עדיף לפעמים על רנדומלי כדי למנוע יצירת UA לא הגיוני
    fake_ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    chrome_options.add_argument(f'user-agent={fake_ua}')

    # 4. ביטול הגבלות ושיפור ביצועים
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--ignore-certificate-errors")
    
    # יצירת הדרייבר
    driver = webdriver.Chrome(options=chrome_options)

    # טריק נוסף: שינוי מאפייני Navigator ב-JavaScript כדי להסתיר את ה-Webdriver
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver

# --- הפונקציה שמושכת את הלינק ---
def get_stream_data(driver, url, channel_keyword):
    print(f"   >>> נכנס לכתובת: {url}")
    try:
        # ניקוי היסטוריה קודמת
        driver.get("about:blank")
        del driver.requests  # ניקוי בקשות קודמות מהזיכרון של selenium-wire

        driver.get(url)

        # המתנה לטעינת הנגן (עד 20 שניות)
        try:
            WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.TAG_NAME, "iframe"))
            )
        except:
            print("   ⚠️ לא נמצא iframe, ממשיך בכל זאת...")

        # המתנה נוספת כדי לוודא שהווידאו התחיל לנגן
        time.sleep(8) 

        stream_url = None
        # חיפוש הבקשה הנכונה בתעבורה
        for request in driver.requests:
            if request.response:
                # בדיקה אם זה קובץ m3u8 וגם מכיל את השם של הערוץ
                if ".m3u8" in request.url and channel_keyword.lower() in request.url.lower():
                    if "index" in request.url: # מעדיפים את ה-index
                        stream_url = request.url
                        break
        
        # אם לא מצאנו index, ניקח כל m3u8 שקשור לערוץ
        if not stream_url:
            for request in driver.requests:
                if request.response and ".m3u8" in request.url and channel_keyword.lower() in request.url.lower():
                    stream_url = request.url
                    break
        
        # חילוץ העוגיות (Cookies) מהדפדפן
        cookies_list = driver.get_cookies()
        cookies_string = ""
        for cookie in cookies_list:
            cookies_string += f"{cookie['name']}={cookie['value']}; "

        return stream_url, cookies_string.strip()

    except Exception as e:
        print(f"⚠️ שגיאה בטעינת הערוץ: {e}")
        return None, None

# --- התכנית הראשית ---
def main():
    print("--- מתחיל סריקה עם מצב חמקן (Stealth Mode) ---")
    driver = get_stealth_driver()
    output = []

    try:
        for ch in channels:
            print(f"\n📺 סורק את: {ch['name']}...")
            stream_url, cookies = get_stream_data(driver, ch["page_url"], ch["image"])

            if stream_url:
                print(f"   ✅ הצלחה! נמצא לינק.")
                # הוספה לרשימה הסופית
                output.append({
                    "id": ch["id"],
                    "name": ch["name"],
                    "url": stream_url,
                    "image": ch["image"],
                    "headers": {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Referer": ch["page_url"],
                        "Origin": "https://www.freeshot.live",
                        "Cookie": cookies
                    }
                })
            else:
                print(f"   ❌ נכשל. לא נמצא לינק או שהאתר חסם.")
                
    finally:
        print("\nסוגר דפדפן...")
        driver.quit()

    # שמירה לקובץ
    if output:
        with open("channels.json", "w", encoding="utf-8") as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
        print(f"\n✨ הסתיים בהצלחה! נשמרו {len(output)} ערוצים לקובץ channels.json")
    else:
        print("\n❌ לא נמצאו ערוצים בכלל. ייתכן שיש חסימה חזקה יותר.")

if __name__ == "__main__":
    main()
