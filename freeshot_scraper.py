import asyncio
import json
from playwright.async_api import async_playwright

# --- רשימת הערוצים ---
channels = [
    {"id": 1, "name": "Sport 1", "image": "sport1",
     "page_url": "https://www.freeshot.live/live-tv/yes-sport-1-israel/168"},
    {"id": 2, "name": "Sport 2", "image": "sport2",
     "page_url": "https://www.freeshot.live/live-tv/yes-sport-2-israel/169"},
    {"id": 3, "name": "Sport 3", "image": "sport3",
     "page_url": "https://www.freeshot.live/live-tv/yes-sport-3-israel/170"},
    {"id": 4, "name": "Sport 4", "image": "sport4",
     "page_url": "https://www.freeshot.live/live-tv/yes-sport-4-israel/171"},
    {"id": 5, "name": "Sport 5", "image": "sport5",
     "page_url": "https://www.freeshot.live/live-tv/yes-sport-5-israel/172"},
    {"id": 6, "name": "Sport 5 Plus", "image": "sport5plus",
     "page_url": "https://www.freeshot.live/live-tv/sport-5-plus-israel/173"},
    {"id": 7, "name": "Sport 5 Live", "image": "sport5live",
     "page_url": "https://www.freeshot.live/live-tv/sport-5-live-israel/174"},
    {"id": 8, "name": "Sport 5 Stars", "image": "sport5stars",
     "page_url": "https://www.freeshot.live/live-tv/sport-5-stars-israel/175"},
    {"id": 9, "name": "Sport 5 Gold", "image": "sport5gold",
     "page_url": "https://www.freeshot.live/live-tv/sport-5-gold-israel/176"},
]

# --- Headers קבועים ---
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://www.freeshot.live/",
    "Origin": "https://www.freeshot.live"
}

async def construct_m3u8_from_embed(embed_url):
    """
    מרכיב את הלינק הסופי לפי התבנית המוכחת שעובדת
    """
    if "embed.html" not in embed_url:
        return None

    base_part = embed_url.split("embed.html")[0]
    query_part = embed_url.split("embed.html")[1]

    template = "tracks-v1/index.fmp4.m3u8"

    final_url = f"{base_part}{template}{query_part}"
    print(f"      ✔ לינק הורכב: {final_url[:60]}...")
    return final_url


async def scrape_channel(playwright, channel):
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-setuid-sandbox']
    )

    context = await browser.new_context(
        user_agent=DEFAULT_HEADERS["User-Agent"]
    )
    page = await context.new_page()

    print(f"\n🏁 ערוץ: {channel['name']}")

    try:
        await page.goto(channel["page_url"], timeout=30000, wait_until="domcontentloaded")

        target_embed_url = None

        # לולאה שמחפשת את ה-iframe הנכון
        for _ in range(10):
            for frame in page.frames:
                if ("embed.html" in frame.url or "beautifulpeople" in frame.url) and "token" in frame.url:
                    target_embed_url = frame.url
                    break

            if target_embed_url:
                break

            await page.wait_for_timeout(800)

        if target_embed_url:
            return await construct_m3u8_from_embed(target_embed_url)
        else:
            print("      ⚠ iframe לא נמצא")
            return None

    except Exception as e:
        print(f"      ❌ שגיאה: {str(e)[:100]}")
        return None

    finally:
        await browser.close()


async def main():
    print("\n=== FreeShot JSON Builder v1 ===\n")
    results = []

    async with async_playwright() as playwright:
        for ch in channels:
            url = await scrape_channel(playwright, ch)

            if url:
                results.append({
                    "id": ch["id"],
                    "name": ch["name"],
                    "url": url,
                    "image": ch["image"],
                    "headers": DEFAULT_HEADERS
                })

    # כתיבה לקובץ JSON
    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n🎉 channels.json נוצר בהצלחה!")
    print("📂 מוכן לשימוש באפליקציה שלך.")


if __name__ == "__main__":
    asyncio.run(main())
