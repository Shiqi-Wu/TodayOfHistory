#!/usr/bin/env python3
"""
Auto-post Weibo (TodayOfHistory)

Features:
- Read runtime configuration from `config.json` (or --config)
- Scan folders named with timestamp prefix (YYYY-MM-DD_HH-MM-SS_text)
- For matched "today" folders, create posts:
  - each video file -> one video post
  - all images in folder -> one multi-image post
- Upload files and attempt to click the publish button with multiple strategies

Note: This script uses Selenium + webdriver-manager. Ensure `selenium` and
`webdriver-manager` are installed in your Python environment.
"""

import time
import datetime
import os
import re
import json
import argparse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


def load_config(path: Path):
    if not path.exists():
        raise SystemExit(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def build_posts(base_dir: str, template: str, image_exts, video_exts):
    today = datetime.date.today()
    today_mmdd = today.strftime("%m-%d")
    print(f"🧭 Checking memories for {today_mmdd}...")

    date_pattern = re.compile(r"^(\d{4})-(\d{2})-(\d{2})_")
    posts_to_send = []

    if not os.path.isdir(base_dir):
        raise SystemExit(f"base_dir does not exist or is not a directory: {base_dir}")

    for folder in os.listdir(base_dir):
        match = date_pattern.search(folder)
        if not match:
            continue
        year, month, day = match.groups()

        if f"{month}-{day}" == today_mmdd:
            folder_path = os.path.join(base_dir, folder)
            if not os.path.isdir(folder_path):
                continue

            # extract trailing text after the timestamp (used as hashtags/text part)
            match_text = re.search(r"\d{4}-\d{2}-\d{2}_[\d-]+_(.*)", folder)
            if match_text:
                hashtags = match_text.group(1).strip()
            else:
                hashtags = ""
            hashtags = re.sub(r"@(?!\s)", "@ ", hashtags)

            files = sorted(os.listdir(folder_path))
            video_files = [f for f in files if os.path.splitext(f)[1].lower() in video_exts]
            image_files = [f for f in files if os.path.splitext(f)[1].lower() in image_exts]

            text = template.format(year=year, month=month, day=day, hashtags=hashtags)

            for v in video_files:
                video_path = os.path.join(folder_path, v)
                posts_to_send.append({"type": "video", "text": text, "paths": [video_path]})

            if image_files:
                image_paths = [os.path.join(folder_path, img) for img in image_files]
                posts_to_send.append({"type": "images", "text": text, "paths": image_paths})

    return posts_to_send


def start_browser(detach: bool, maximize: bool):
    chrome_options = webdriver.ChromeOptions()
    if detach:
        chrome_options.add_experimental_option("detach", True)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    if maximize:
        try:
            driver.maximize_window()
        except Exception:
            pass
    return driver


def find_and_click_publish(driver):
    post_button = None
    xpaths = [
        "//button[contains(text(),'发送') or contains(text(),'发布') or contains(text(),'发表') or contains(text(),'发布微博') ]",
        "//button[@type='submit']",
        "//div[contains(@class,'publish') or contains(@class,'send')]/button",
    ]
    for xp in xpaths:
        try:
            buttons = driver.find_elements(By.XPATH, xp)
            if not buttons:
                continue
            for b in buttons:
                try:
                    if b.is_displayed() and b.is_enabled():
                        post_button = b
                        break
                except Exception:
                    continue
            if post_button:
                break
        except Exception:
            continue

    if post_button:
        try:
            driver.execute_script("arguments[0].click();", post_button)
            return True
        except Exception:
            try:
                post_button.click()
                return True
            except Exception:
                return False
    return False


def main():
    parser = argparse.ArgumentParser(description="Auto post Weibo - TodayOfHistory")
    parser.add_argument("--config", help="Path to config JSON (defaults to same dir/config.json)")
    args = parser.parse_args()

    base_path = Path(__file__).parent
    config_path = Path(args.config) if args.config else base_path / "config.json"
    cfg = load_config(config_path)

    BASE_DIR = cfg.get("base_dir")
    TEMPLATE = cfg.get("template")
    LOGIN_WAIT = cfg.get("login_wait", 30)
    UPLOAD_WAIT = cfg.get("upload_wait", 25)
    CHROME_DETACH = cfg.get("chrome_detach", True)
    MAXIMIZE = cfg.get("browser_maximize", True)
    IMAGE_EXTS = cfg.get("image_extensions", [".jpg", ".jpeg", ".png", ".gif"]) 
    VIDEO_EXTS = cfg.get("video_extensions", [".mp4", ".mov"]) 

    posts_to_send = build_posts(BASE_DIR, TEMPLATE, IMAGE_EXTS, VIDEO_EXTS)
    if not posts_to_send:
        print("No 'On This Day' posts today.")
        return

    driver = start_browser(CHROME_DETACH, MAXIMIZE)
    driver.get("https://weibo.com/")
    print("🌐 Waiting for login (if not already logged in)...")
    time.sleep(LOGIN_WAIT)

    for post in posts_to_send:
        post_text = post.get("text")
        paths = post.get("paths", [])
        print(f"🚀 Posting: {post_text}")
        driver.get("https://weibo.com/")
        time.sleep(6)

        try:
            textarea = driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='有什么新鲜事']")
            textarea.click()
            time.sleep(1)
            textarea.send_keys(post_text)
            time.sleep(1)
        except Exception as e:
            print("❌ 找不到发微博输入框:", e)
            continue

        if paths:
            try:
                upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
                if isinstance(paths, list) and len(paths) > 1:
                    upload_value = "\n".join(paths)
                elif isinstance(paths, list) and len(paths) == 1:
                    upload_value = paths[0]
                else:
                    upload_value = str(paths)

                upload_input.send_keys(upload_value)
                print(f"🎬 Uploading: {upload_value}")
                time.sleep(UPLOAD_WAIT)
            except Exception as e:
                print("⚠️ 上传失败:", e)

        clicked = find_and_click_publish(driver)
        if clicked:
            print("✅ Posted successfully.")
        else:
            print("❌ 未找到或无法点击发布按钮，请手动检查页面。")

        # short pause between posts
        time.sleep(5)

    print("🎉 All done. Browser will remain open.")
    input("✅ Press Enter to exit the script (browser stays open)...")


if __name__ == "__main__":
    main()
