import os
import time
import random
import numpy as np
from PIL import Image
from io import BytesIO
from fake_useragent import UserAgent
from urllib.parse import urljoin
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import requests
import streamlit as st
import re

# ===== Streamlit UI =====
st.set_page_config(page_title="書法字下載器", layout="centered")
st.title("🖋 書法字體圖像下載工具")

# 使用者輸入字句，會自動分解為單一中文字
search_words_input = st.text_input("請輸入要搜尋的文字句子（會自動分解成單一字）", "")
cleaned_input = re.sub(r"[^\w\u4e00-\u9fff]", "", search_words_input)
search_words = list(cleaned_input)

# 書體對應表
style_map = {
    "章草": "1",
    "篆書": "3",
    "簡牘": "4",
    "魏碑": "5",
    "隸書": "6",
    "草書": "7",
    "行書": "8",
    "楷書": "9"
}
style_display = st.selectbox("請選擇書體", list(style_map.keys()))
style_value = style_map[style_display]

# 每個字最多下載幾張
download_limit = st.number_input("每個字最多下載幾張圖？", min_value=1, max_value=50, value=10)

# 存檔路徑
save_base_dir = os.path.join("downloads", style_display)

# 開始按鈕
start_download = st.button("開始下載")

# ===== 主程式邏輯 =====
if start_download:
    os.makedirs(save_base_dir, exist_ok=True)
    st.write("🚀 開始下載...")
    error_list = []
	
	# 產生 header
	try:
		ua = UserAgent()
		user_agent = ua.chrome
	except:
		user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

	headers = {
		'User-Agent': user_agent
	}
	options.add_argument(f"user-agent={user_agent}")

    # 設定瀏覽器
    options = Options()
	options.add_argument("--disable-gpu")
	options.add_argument("--no-sandbox")
	options.add_argument("--headless")
	options.add_argument("--incognito")
	options.add_argument("--disable-dev-shm-usage")
	options.add_argument("--disable-extensions")
	options.add_experimental_option("excludeSwitches", ["enable-automation"])
	options.add_experimental_option("useAutomationExtension", False)
	options.add_argument(f"user-agent={headers['User-Agent']}")

	from shutil import which
	chrome_path = which("chromium-browser") or which("chromium")
	if chrome_path:
		options.binary_location = chrome_path

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
        """
    })

    base_url = "https://www.shufazidian.com/s.php"

    for word in search_words:
        st.write(f"🔍 處理字：{word}")
        save_dir = os.path.join(save_base_dir, f"{word}_{style_display}")
        os.makedirs(save_dir, exist_ok=True)

        driver.get(base_url)
        time.sleep(random.uniform(1, 2))

        search_input = driver.find_element(By.ID, "wd")
        search_input.clear()
        search_input.send_keys(word)

        select = Select(driver.find_element(By.ID, "sort"))
        select.select_by_value(style_value)

        submit_button = driver.find_element(By.XPATH, "//form[@name='form1']//button[@type='submit']")
        submit_button.click()
        time.sleep(random.uniform(2, 3))

        img_elements = driver.find_elements(By.CSS_SELECTOR, ".woo-pcont.woo-masned.my-pic img")
        if not img_elements:
            st.warning(f"❌ 找不到字 {word} 的圖片")
            continue

        for idx, img_elem in enumerate(img_elements[1:]):
            if idx >= download_limit:
                break
            src = img_elem.get_attribute("src")
            if not src:
                continue
            img_url = urljoin(base_url, src)
            try:
                img_data = requests.get(img_url, headers=headers, timeout=10).content
                img_name = os.path.join(save_dir, f"{word}_{idx + 1}.jpg")
                with open(img_name, "wb") as f:
                    f.write(img_data)
                time.sleep(random.uniform(1, 3))
            except Exception as e:
                error_list.append((word, img_url, str(e)))

    driver.quit()

    st.success("✅ 所有字處理完畢！")
    if error_list:
        st.error("⚠️ 以下圖片下載失敗：")
        for word, url, msg in error_list:
            st.write(f"{word}: {url}")
