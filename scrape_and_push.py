import asyncio
import json
import os
from playwright.async_api import async_playwright

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

# User-Agent קבוע ואמין
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"

async def construct_m3u8_from_embed(embed_url):
    """מרכיב את הלינק הסופי לפי התבנית המנצחת"""
    if "embed.html" not in embed_url: return None
    base_part = embed_url.split("embed.html")[0]
    query_part = embed_url.split("embed.html")[1]
    # התבנית שנמצאה כעובדת
    template = "tracks-v1/index.fmp4.m3u8"
    target_url = f"{base_part}{template}{query_part}"
    print(f"      ✅ לינק חולץ: {target_url[:60]}...")
    return target_url

async def scrape_channel(playwright, channel):
    # דפדפן מהיר
    browser = await playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
    context = await browser.new_context(user_agent=USER_AGENT)
    page = await context.new_page()
    
    print(f"\n📡 ערוץ: {channel['name']}")
    try:
        await page.goto(channel["page_url"], timeout=40000, wait_until="domcontentloaded")
        
        target_embed_url = None
        # חיפוש ה-iframe הנכון (עד 15 שניות)
        for i in range(15):
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
    print("--- SportStream Auto Update (Playwright) ---")
    json_output = []
    m3u_lines = ["#EXTM3U"]
    
    async with async_playwright() as playwright:
        for ch in channels:
            url = await scrape_channel(playwright, ch)
            if url:
                # 1. יצירת רשומה ל-JSON (מותאם לאפליקציה שלך)
                # הלינקים האלה עובדים לרוב בלי Headers מיוחדים, אבל הוספתי ליתר ביטחון
                json_item = {
                    "id": ch["id"],
                    "name": ch["name"],
                    "url": url,
                    "image": ch["image"],
                    "headers": {
                        "User-Agent": USER_AGENT,
                        "Referer": "https://www.freeshot.live/",
                        "Origin": "https://www.freeshot.live"
                    }
                }
                json_output.append(json_item)

                # 2. יצירת רשומה ל-M3U (עבור VLC/TiviMate)
                m3u_lines.append(f'#EXTINF:-1 group-title="Israel Sports" tvg-id="{ch["image"]}" tvg-logo="{ch["image"]}",{ch["name"]}')
                m3u_lines.append(f'#EXTVLCOPT:http-user-agent={USER_AGENT}')
                m3u_lines.append(url)

    # שמירת קבצים
    if json_output:
        with open("channels.json", "w", encoding="utf-8") as f:
            json.dump(json_output, f, indent=2, ensure_ascii=False)
        print("\n✅ channels.json עודכן בהצלחה.")
        
        with open("playlist.m3u", "w", encoding="utf-8") as f:
            f.write("\n".join(m3u_lines))
        print("✅ playlist.m3u עודכן בהצלחה.")
    else:
        print("\n❌ לא נמצאו לינקים, הקבצים לא עודכנו.")

if __name__ == "__main__":
    asyncio.run(main())
