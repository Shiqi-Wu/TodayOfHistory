import time
import datetime
import os
import re
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys

# =============== 基础配置 ===============
BASE_DIR = "/Users/shiqi/Documents/Personal-Code-Tools/douyin-downloader/Downloaded/孙亦航."
TEMPLATE = "#孙亦航[超话]#\n\n那年今日（{year}{month}{day}）dy更新\n\n“{hashtags}”\n\n@孙亦航mew "

today = datetime.date.today()
# today = datetime.date(2025, 11, 5)
today_mmdd = today.strftime("%m-%d")

print(f"🧭 Checking memories for {today_mmdd}...")

date_pattern = re.compile(r"^(\d{4})-(\d{2})-(\d{2})_")
posts_to_send = []

for folder in os.listdir(BASE_DIR):
    match = date_pattern.search(folder)
    if not match:
        continue
    year, month, day = match.groups()

    if f"{month}-{day}" == today_mmdd:
        folder_path = os.path.join(BASE_DIR, folder)
        if not os.path.isdir(folder_path):
            continue
        # 剩余内容：把日期前缀去掉后的所有文字
        match = re.search(r"\d{4}-\d{2}-\d{2}_[\d-]+_(.*)", folder)
        if match:
            hashtags = match.group(1).strip()
        else:
            hashtags = ""
        hashtags = re.sub(r"@(?!\s)", "@ ", hashtags)
        
        mp4_files = [f for f in os.listdir(folder_path) if f.endswith(".mp4")]
        for mp4 in mp4_files:
            video_path = os.path.join(folder_path, mp4)
            text = TEMPLATE.format(year=year, month=month, day=day, hashtags=hashtags)
            posts_to_send.append((text, video_path))

if not posts_to_send:
    print("No 'On This Day' videos today.")
    exit(0)

# =============== 启动浏览器（保持打开） ===============
chrome_options = webdriver.ChromeOptions()
chrome_options.add_experimental_option("detach", True)  # ✅ 让浏览器不随脚本关闭

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
driver.maximize_window()
driver.get("https://weibo.com/")

print("🌐 Waiting for login (if not already logged in)...")
time.sleep(30)  # 登录等待时间（可根据情况调整）

# =============== 发微博 ===============
for post_text, video_path in posts_to_send:
    print(f"🚀 Posting: {post_text}")
    driver.get("https://weibo.com/")
    time.sleep(6)

    # 点击输入框
    try:
        textarea = driver.find_element(By.CSS_SELECTOR, "textarea[placeholder*='有什么新鲜事']")
        textarea.click()
        time.sleep(1)
        textarea.send_keys(post_text)
        time.sleep(2)
    except Exception as e:
        print("❌ 找不到发微博输入框:", e)
        continue

    # 上传视频
    try:
        upload_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        upload_input.send_keys(video_path)
        print(f"🎬 Uploading {video_path}")
        time.sleep(25)  # 等待视频上传（可视情况调整）
    except Exception as e:
        print("⚠️ 上传失败:", e)
        continue

    # # 点击发布按钮
    # try:
    #     buttons = driver.find_elements(By.XPATH, "//button[contains(text(),'发送') or contains(text(),'发布')]")
    #     if buttons:
    #         post_button = buttons[0]
    #         driver.execute_script("arguments[0].click();", post_button)
    #         print("✅ Posted successfully.")
    #     else:
    #         print("❌ 未找到发布按钮")
    #     time.sleep(10)
    # except Exception as e:
    #     print("⚠️ 找不到发布按钮:", e)
    #     continue

print("🎉 All done. Browser will remain open.")
input("✅ Press Enter to exit the script (browser stays open)...")
