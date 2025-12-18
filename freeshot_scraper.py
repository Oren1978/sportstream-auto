import asyncio
import json
from playwright.async_api import async_playwright

CHANNELS_FILE = "channels.json"

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Referer": "https://www.freeshot.live/",
    "Origin": "https://www.freeshot.live"
}

def load_channels(path=CHANNELS_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

async def construct_m3u8_from_embed(embed_url):
    if not embed_url or "embed.html" not in embed_url:
        return None

    base_part = embed_url.split("embed.html")[0]
    query_part = embed_url.split("embed.html")[1]
    return f"{base_part}tracks-v1/index.fmp4.m3u8{query_part}"

async def scrape_channel(playwright, channel):
    browser = await playwright.chromium.launch(
        headless=True,
        args=["--no-sandbox", "--disable-setuid-sandbox"]
    )

    context = await browser.new_context(
        user_agent=DEFAULT_HEADERS["User-Agent"]
    )
    page = await context.new_page()

    print(f"\n📡 ערוץ: {channel['name']}")

    try:
        await page.goto(channel["page_url"], timeout=30000, wait_until="domcontentloaded")

        embed_url = None
        for _ in range(10):
            for frame in page.frames:
                if "embed.html" in frame.url and "token" in frame.url:
                    embed_url = frame.url
                    break
            if embed_url:
                break
            await page.wait_for_timeout(800)

        if not embed_url:
            print("      ⚠️ iframe לא נמצא")
            return None

        final_url = await construct_m3u8_from_embed(embed_url)
        print("      ✅ לינק הופק")
        return final_url

    except Exception as e:
        print(f"      ❌ שגיאה: {e}")
        return None

    finally:
        await browser.close()

async def main():
    print("\n=== FreeShot Scraper – JSON Driven ===\n")

    channels = load_channels()
    results = []

    async with async_playwright() as playwright:
        for ch in channels:
            if "page_url" not in ch:
                continue

            url = await scrape_channel(playwright, ch)
            if url:
                results.append({
                    "id": ch["id"],
                    "name": ch["name"],
                    "url": url,
                    "image": ch.get("image", ""),
                    "headers": DEFAULT_HEADERS
                })

    with open("channels.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print("\n🏆 channels.json עודכן בהצלחה")

if __name__ == "__main__":
    asyncio.run(main())
