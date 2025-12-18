import asyncio
import json
from playwright.async_api import async_playwright

CHANNELS_FILE = "channels.json"

def load_channels(path=CHANNELS_FILE):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

async def main():
    print("\n=== Playlist Builder – JSON Driven ===\n")

    channels = load_channels()
    playlist_entries = []

    for ch in channels:
        url = ch.get("url")
        if not url:
            continue

        entry = (
            f'#EXTINF:-1 group-title="Israel Sports",{ch["name"]}\n'
            f'#EXTVLCOPT:http-user-agent={ch["headers"]["User-Agent"]}\n'
            f'{url}'
        )
        playlist_entries.append(entry)

    if not playlist_entries:
        print("❌ לא נמצאו ערוצים תקינים")
        return

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("\n".join(playlist_entries))

    print("🏆 playlist.m3u נוצר בהצלחה")

if __name__ == "__main__":
    asyncio.run(main())
