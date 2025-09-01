# scrape_and_push.py (VERSION WITH BUG FIX)
# -*- coding: utf-8 -*-
import os
import sys
import json
import time
import shutil
import subprocess
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

from seleniumwire import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- Configuration ---
GITHUB_USER = "Oren1978"
GITHUB_REPO = "sportstream-auto"
GITHUB_BRANCH = "main"
REPO_DIR = os.path.join(os.path.expanduser("~"), "sportstream-auto_repo")
CHANNELS_JSON_PATH = os.path.join(REPO_DIR, "channels.json")

CHANNELS = [
    {"id": 1, "name": "ספורט 1", "page_url": "https://www.freeshot.live/live-tv/yes-sport-1-israel/168", "image": "sport1", "stream_key": "SPORT1IL"},
    {"id": 2, "name": "ספורט 2", "page_url": "https://www.freeshot.live/live-tv/yes-sport-2-israel/169", "image": "sport2", "stream_key": "SPORT2IL"},
    {"id": 3, "name": "ספורט 3", "page_url": "https://www.freeshot.live/live-tv/yes-sport-3-israel/170", "image": "sport3", "stream_key": "SPORT3IL"},
    {"id": 4, "name": "ספורט 4", "page_url": "https://www.freeshot.live/live-tv/yes-sport-4-israel/171", "image": "sport4", "stream_key": "SPORT4IL"},
    {"id": 5, "name": "ספורט 5", "page_url": "https://www.freeshot.live/live-tv/yes-sport-5-israel/172", "image": "sport5", "stream_key": "SPORT5IL"},
    {"id": 6, "name": "ספורט 5 פלוס", "page_url": "https://www.freeshot.live/live-tv/sport-5-plus-israel/173", "image": "sport5plus", "stream_key": "SPORT5PLUS"},
    {"id": 7, "name": "ספורט 5 לייב", "page_url": "https://www.freeshot.live/live-tv/sport-5-live-israel/174", "image": "sport5live", "stream_key": "SPORT5LIVE"},
    {"id": 8, "name": "ספורט 5 סטארס", "page_url": "https://www.freeshot.live/live-tv/sport-5-stars-israel/175", "image": "sport5stars", "stream_key": "SPORT5STARS"},
    {"id": 9, "name": "ספורט 5 גולד", "page_url": "https://www.freeshot.live/live-tv/sport-5-gold-israel/176", "image": "sport5gold", "stream_key": "SPORT5GOLD"},
]

# --- Helper Functions ---
def log(msg):
    sys.stdout.write(msg + "\n")
    sys.stdout.flush()

def run(cmd, cwd=None, check=True):
    log(f"$ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, encoding='utf-8')
    if proc.stdout and proc.returncode == 0: log(proc.stdout.strip())
    if proc.stderr: log(proc.stderr.strip())
    if check and proc.returncode != 0: raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return proc
    
def ensure_repo_cloned_and_ready():
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise RuntimeError("GITHUB_TOKEN env var is not set. Please set a PAT with 'repo' scope.")
    remote_url = f"https://{token}@github.com/{GITHUB_USER}/{GITHUB_REPO}.git"
    if not os.path.isdir(REPO_DIR) or not os.path.isdir(os.path.join(REPO_DIR, ".git")):
        if os.path.isdir(REPO_DIR): shutil.rmtree(REPO_DIR, ignore_errors=True)
        log(f"Cloning repo into: {REPO_DIR}")
        run(["git", "clone", "--branch", GITHUB_BRANCH, remote_url, REPO_DIR])
    run(["git", "remote", "set-url", "origin", remote_url], cwd=REPO_DIR, check=False)
    run(["git", "fetch", "origin", GITHUB_BRANCH], cwd=REPO_DIR, check=False)
    run(["git", "checkout", GITHUB_BRANCH], cwd=REPO_DIR)
    run(["git", "pull", "origin", GITHUB_BRANCH], cwd=REPO_DIR, check=False)
    run(["git", "config", "user.email", "automation@local"], cwd=REPO_DIR, check=False)
    run(["git", "config", "user.name", "automation"], cwd=REPO_DIR, check=False)

def get_token_from_url(url):
    try:
        return parse_qs(urlparse(url).query)['token'][0]
    except (KeyError, IndexError):
        return None

# THIS FUNCTION WAS MISSING. I'VE ADDED IT BACK.
def extract_header_value(req, header_name):
    try:
        return req.headers.get(header_name)
    except Exception:
        return None

def derive_headers_for_url(m3u8_url, stream_key, ua_from_req=None):
    token = get_token_from_url(m3u8_url)
    if not token: return None
    p = urlparse(m3u8_url)
    referer_path = f"/{stream_key}/embed.html"
    referer_query = urlencode({'token': token, 'remote': 'no_check_ip'})
    referer_parts = (p.scheme, p.netloc, referer_path, '', referer_query, '')
    referer = urlunparse(referer_parts)
    headers = {
        "accept": "*/*", "referer": referer, "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin"
    }
    headers["user-agent"] = ua_from_req or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
    return headers

def collect_m3u8_url(driver, page_url):
    try: del driver.requests
    except Exception: pass
    driver.get(page_url)
    try:
        req = driver.wait_for_request(r'.*index\.fmp4\.m3u8.*', timeout=20)
        return req.url, extract_header_value(req, 'User-Agent')
    except Exception as e:
        log(f"--> Could not find m3u8 request: {e}")
        return None, None

def write_channels_json_to_repo(output_items):
    os.makedirs(REPO_DIR, exist_ok=True)
    with open(CHANNELS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(output_items, f, indent=2, ensure_ascii=False)
    log(f"Wrote {CHANNELS_JSON_PATH}")

def git_commit_and_push():
    run(["git", "add", "channels.json"], cwd=REPO_DIR)
    commit_proc = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=REPO_DIR)
    if commit_proc.returncode == 0:
        log("No changes to commit (channels.json unchanged).")
        return
    run(["git", "commit", "-m", "update channels"], cwd=REPO_DIR)
    run(["git", "push", "origin", GITHUB_BRANCH], cwd=REPO_DIR)
    
# --- Main Execution ---
def main():
    log("Step 1: Ensuring local git repo is ready...")
    ensure_repo_cloned_and_ready()
    log("Step 2: Launching headless Chrome (selenium-wire)...")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    output = []
    try:
        for ch in CHANNELS:
            name, page, image, key = ch["name"], ch["page_url"], ch["image"], ch["stream_key"]
            log(f"\n--- Scraping: {name} ---")
            m3u8_url, user_agent = collect_m3u8_url(driver, page)
            if m3u8_url:
                headers = derive_headers_for_url(m3u8_url, key, user_agent)
                if headers:
                    log(f"--> Found stream for {name}")
                    item = {"id": ch["id"], "name": name, "url": m3u8_url, "image": image, "headers": headers}
                    output.append(item)
                else:
                    log(f"--> X Found URL but could not derive headers for {name}")
            else:
                log(f"--> X No stream found for {name}")
    finally:
        try: driver.quit()
        except Exception: pass
    log("\nStep 3: Writing channels.json to local repo...")
    write_channels_json_to_repo(output)
    log("\nStep 4: Committing and pushing to GitHub...")
    try:
        git_commit_and_push()
        log("\n--- Pushed to GitHub successfully! ---")
    except Exception as e:
        log(f"--> X Git push failed: {e}")

if __name__ == "__main__":
    main()