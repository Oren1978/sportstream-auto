# -*- coding: utf-8 -*-
import json
import time
import sys
from urllib.parse import urlparse
from collections import defaultdict

# ⚠️ חשוב: seleniumwire (לא selenium)
from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

###############################################################################
# רשימת הערוצים (תוכל לשנות/להרחיב כאן בלבד)
###############################################################################
CHANNELS = [
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

###############################################################################
# הגדרות דפדפן (כרום) + seleniumwire
###############################################################################
chrome_options = Options()
chrome_options.add_argument("--headless=new")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--lang=en-US")

# הורדת רעש רשת (לא חובה)
seleniumwire_options = {
    'verify_ssl': True,
    'connection_timeout': None,  # נשתמש בטיים-אאוטים שלנו
}

driver = None

###############################################################################
# פונקציות עזר
###############################################################################

def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def wait_for_iframes(max_wait=15):
    try:
        WebDriverWait(driver, max_wait).until(EC.presence_of_element_located((By.TAG_NAME, "iframe")))
        # ניסוי קצר לעבור ל־iframe הראשון אם צריך
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        if iframes:
            driver.switch_to.frame(iframes[0])
            time.sleep(1)
            driver.switch_to.default_content()
    except Exception:
        pass

def clear_network():
    # ננקה בקשות שנאספו עד כה לפני ערוץ חדש
    try:
        driver.requests.clear()
    except Exception:
        pass

def host_base(url: str) -> str:
    p = urlparse(url)
    return f"{p.scheme}://{p.netloc}"

def best_m3u8_choice(m3u8_urls):
    """
    נותן עדיפות ל־master/variant מקובלים:
    - מכיל 'index' ו/או 'tracks'
    - מסתיים ב-.m3u8 (לא קובץ מקומי משני)
    """
    # ניקוי כפילויות ושמירה על סדר הופעה
    seen = set()
    unique = []
    for u in m3u8_urls:
        if u not in seen:
            seen.add(u)
            unique.append(u)

    # סידור עדיפות
    def score(u):
        s = 0
        lu = u.lower()
        if "index" in lu: s += 3
        if "tracks" in lu: s += 2
        if lu.endswith(".m3u8"): s += 1
        return s

    unique.sort(key=score, reverse=True)
    return unique

def extract_cookie_from_request(req):
    try:
        # cookie שדפדפן שלח בפועל בבקשת ה-m3u8
        hdr = req.headers
        if not hdr:
            return None
        cookie = hdr.get('Cookie') or hdr.get('cookie')
        return cookie
    except Exception:
        return None

def extract_ua_from_request(req):
    try:
        hdr = req.headers
        if not hdr:
            return None
        ua = hdr.get('User-Agent') or hdr.get('user-agent')
        return ua
    except Exception:
        return None

def derive_headers_for_url(m3u8_url, page_url, cookie_from_req=None, ua_from_req=None):
    """
    כותרות HLS בטוחות לאפליקציה:
    - Accept ל-HLS
    - Origin/Referer לפי דומיין ה-m3u8 (הכי בטוח מול CDN)
    - Host מפורש
    - UA מהבקשה בפועל אם יש; אחרת UA דפדפן גנרי
    - Cookie מהבקשה בפועל אם יש
    """
    p = urlparse(m3u8_url)
    base = f"{p.scheme}://{p.netloc}"
    headers = {
        "Accept": "application/x-mpegURL, application/vnd.apple.mpegurl, */*",
        "Origin": base,
        "Referer": base + "/",
        "Host": p.netloc,
        "Accept-Language": "en-US,en;q=0.9",
    }
    if ua_from_req:
        headers["User-Agent"] = ua_from_req
    else:
        headers["User-Agent"] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"

    if cookie_from_req:
        headers["Cookie"] = cookie_from_req

    return headers

def collect_m3u8_candidates(channel_name, page_url, keyword_hint=None, idle_wait=10, total_wait=20):
    """
    טוען את עמוד הערוץ, ממתין לטעינת iframes/נגן, אוסף כל בקשות ה-m3u8,
    מחזיר עד 3 כתובות ממויינות + הכותרות המתאימות לראשונה (primary).
    """
    clear_network()
    driver.get("about:blank")
    clear_network()

    driver.get(page_url)
    wait_for_iframes(max_wait=15)

    # נחכה קצת לתעבורה; בד"כ 6-10 שניות מספיק
    t0 = time.time()
    time.sleep(idle_wait)

    # אם מעט מדי בקשות, נמתין עוד (עד total_wait)
    while time.time() - t0 < total_wait:
        # האם ראינו בכלל m3u8?
        m3u8_count = sum(1 for r in driver.requests if r.response and r.url.endswith(".m3u8"))
        if m3u8_count >= 1:
            break
        time.sleep(1)

    # סינון m3u8ים ובדיקת מילת מפתח אם נתונה
    candidates = []
    for req in driver.requests:
        try:
            if not req.response:
                continue
            url = req.url
            if ".m3u8" not in url.lower():
                continue
            if keyword_hint and keyword_hint.lower() not in url.lower():
                # אם יש רמז (שם תמונה/ערוץ), ננסה לצמצם לפיו – אם אין התאמה, נדלג
                continue
            candidates.append(req)
        except Exception:
            continue

    # fallback: אם לא נמצאו לפי hint, ניקח כל m3u8
    if not candidates:
        for req in driver.requests:
            try:
                if req.response and ".m3u8" in req.url.lower():
                    candidates.append(req)
            except Exception:
                continue

    if not candidates:
        return None, None, []

    # סדר עדיפות URLים
    urls_sorted = best_m3u8_choice([r.url for r in candidates])

    # התאמת ה־request לאותו URL (כדי לשלוף Cookie/UA)
    req_by_url = {r.url: r for r in candidates}

    # נבחר primary
    primary_url = urls_sorted[0]
    primary_req = req_by_url.get(primary_url)

    cookie_val = extract_cookie_from_request(primary_req)
    ua_val     = extract_ua_from_request(primary_req)

    headers = derive_headers_for_url(primary_url, page_url, cookie_from_req=cookie_val, ua_from_req=ua_val)

    # נבנה alts עד 2 נוספים (סה״כ 3 מקורות)
    alts = []
    for alt in urls_sorted[1:]:
        if len(alts) >= 2:
            break
        # אל תוסיף פעמיים את אותו ה-host+path עם query אחר אם זה זהה ממש
        alts.append(alt)

    return primary_url, headers, alts

###############################################################################
# הפעלת הסקרייפר
###############################################################################

def main():
    global driver
    log("🚀 Starting headless Chrome with selenium-wire...")
    driver = webdriver.Chrome(options=chrome_options, seleniumwire_options=seleniumwire_options)

    output = []

    try:
        for ch in CHANNELS:
            name = ch["name"]
            page = ch["page_url"]
            image = ch["image"]
            log(f"⏳ Scraping: {name}")

            primary_url, headers, alts = collect_m3u8_candidates(
                channel_name=name,
                page_url=page,
                keyword_hint=image,     # נשתמש בשם התמונה כרמז (sport1/sport2...)
                idle_wait=8,
                total_wait=20
            )

            if primary_url:
                log(f"✅ Found stream for {name}: {primary_url}")

                # התאמת Referer/Origin ל־host של ה־m3u8 עדיפה על פני page_url
                # (במקרה שתצטרך freeshot כ-Referer, האפליקציה שלך כבר תנסה ALT_ORIGIN)
                p = urlparse(primary_url)
                headers["Origin"]  = f"{p.scheme}://{p.netloc}"
                headers["Referer"] = f"{p.scheme}://{p.netloc}/"
                headers["Host"]    = p.netloc
                # ודא Accept נכון
                headers["Accept"]  = "application/x-mpegURL, application/vnd.apple.mpegurl, */*"
                # השאר UA כפי שנלכד (או ברירת מחדל כבר בפנים)

                item = {
                    "id": ch["id"],
                    "name": name,
                    "url": primary_url,
                    "image": image,
                    "headers": headers
                }

                # הוסף alts אם קיימים
                if alts:
                    # דילול כפילויות בסיסיות בין primary ל-alts
                    dedup = []
                    seen = set([primary_url])
                    for alt in alts:
                        if alt not in seen:
                            dedup.append(alt)
                            seen.add(alt)
                    if dedup:
                        item["alts"] = dedup[:3]  # עד 3 בסה״כ

                output.append(item)
            else:
                log(f"❌ No stream found for {name}")
                # עדיין נכניס רשומה עם דגל?
                # אפשר לדלג; כאן נבחר לדלג כדי לא לזהם את הקובץ.

    finally:
        try:
            driver.quit()
        except Exception:
            pass

    # כתיבה ל-channels.json
    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    log("✅ channels.json saved")


if __name__ == "__main__":
    main()
