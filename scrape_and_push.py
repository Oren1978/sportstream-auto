import asyncio
import re
from playwright.async_api import async_playwright

# --- רשימת הערוצים ---
channels = [
    {"id": 1, "name": "Sport 1", "page_url": "https://www.freeshot.live/live-tv/yes-sport-1-israel/168"},
    {"id": 2, "name": "Sport 2", "page_url": "https://www.freeshot.live/live-tv/yes-sport-2-israel/169"},
    {"id": 3, "name": "Sport 3", "page_url": "https://www.freeshot.live/live-tv/yes-sport-3-israel/170"},
    {"id": 4, "name": "Sport 4", "page_url": "https://www.freeshot.live/live-tv/yes-sport-4-israel/171"},
    {"id": 5, "name": "Sport 5", "page_url": "https://www.freeshot.live/live-tv/yes-sport-5-israel/172"},
    {"id": 6, "name": "Sport 5 Plus", "page_url": "https://www.freeshot.live/live-tv/sport-5-plus-israel/173"},
    {"id": 7, "name": "Sport 5 Live", "page_url": "https://www.freeshot.live/live-tv/sport-5-live-israel/174"},
    {"id": 8, "name": "Sport 5 Stars", "page_url": "https://www.freeshot.live/live-tv/sport-5-stars-israel/175"},
    {"id": 9, "name": "Sport 5 Gold", "page_url": "https://www.freeshot.live/live-tv/sport-5-gold-israel/176"},
]

async def construct_m3u8_from_embed(embed_url):
    """
    מרכיב את הלינק הסופי לפי התבנית המנצחת ללא בדיקות מיותרות
    """
    if "embed.html" not in embed_url: return None
        
    base_part = embed_url.split("embed.html")[0]
    query_part = embed_url.split("embed.html")[1]
    
    # התבנית שנמצאה בקבצי הלוג כעובדת
    template = "tracks-v1/index.fmp4.m3u8"
    
    target_url = f"{base_part}{template}{query_part}"
    print(f"      ✅ לינק חולץ והורכב: {target_url[:50]}...")
    return target_url

async def scrape_channel(playwright, channel):
    # דפדפן מהיר ויעיל
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )
    
    context = await browser.new_context(
        user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36'
    )
    page = await context.new_page()
    
    print(f"\n📡 ערוץ: {channel['name']}")

    try:
        await page.goto(channel["page_url"], timeout=30000, wait_until="domcontentloaded")
        
        target_embed_url = None
        # חיפוש זריז של ה-iframe
        for i in range(10):
            for frame in page.frames:
                if "beautifulpeople" in frame.url and "token" in frame.url:
                    target_embed_url = frame.url
                    break
                if "embed.html" in frame.url and "token" in frame.url:
                    target_embed_url = frame.url
                    break
            if target_embed_url: break
            await page.wait_for_timeout(1000)

        if target_embed_url:
            return await construct_m3u8_from_embed(target_embed_url)
        else:
            print("      ⚠️ לא נמצא iframe (דלג).")

    except Exception as e:
        print(f"      ❌ שגיאה: {str(e)[:50]}")
    finally:
        await browser.close()
    
    return None

async def main():
    print("--- FreeShot Scraper v22: The Final Cut ---")
    results = []
    
    async with async_playwright() as playwright:
        for ch in channels:
            url = await scrape_channel(playwright, ch)
            if url:
                # הוספת כותרות ל-VLC שיעזרו בניגון
                entry = f'#EXTINF:-1 group-title="Israel Sports",{ch["name"]}\n'
                entry += '#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36\n'
                entry += f'{url}'
                results.append(entry)

    if results:
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            f.write("\n".join(results))
        print("\n🏆 בוצע! הקובץ playlist.m3u מוכן.")
        print("💡 גרור את הקובץ ל-VLC כדי לצפות.")
    else:
        print("\n❌ לא נמצאו לינקים.")

if __name__ == "__main__":
    asyncio.run(main())
