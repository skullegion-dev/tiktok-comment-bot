# -*- coding: utf-8 -*-
import os
import random
import time
import logging
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# TikTok credentials from environment variables
USERNAME = os.getenv("TIKTOK_USERNAME")
PASSWORD = os.getenv("TIKTOK_PASSWORD")

def login_to_tiktok(driver):
    driver.get("https://www.tiktok.com/login")
    wait = WebDriverWait(driver, 40)  # Increased timeout
    
    try:
        logging.info(f"Page loaded. HTML title: {driver.title}")
        time.sleep(5)  # Wait for JS load
        
        # Step 1: Click "Use phone / email / username"
        try:
            email_login_option = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Use phone / email / username')]"))
            )
            email_login_option.click()
            logging.info("Clicked 'Use phone / email / username' option")
            time.sleep(3)
        except TimeoutException:
            logging.info("No 'Use phone / email / username' option found, assuming form is directly available")

        # Step 2: Enter username
        try:
            username_field = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@name='username' or @placeholder[contains(., 'Email') or contains(., 'Username') or contains(., 'Phone')]]")
                )
            )
            logging.info("Found username field")
            username_field.clear()
            for char in USERNAME:
                username_field.send_keys(char)
                time.sleep(0.1)
            time.sleep(2)  # Extra delay after username
        except TimeoutException:
            raise Exception("Username field not found")

        # Step 3: Enter password (broader selector)
        try:
            password_field = wait.until(
                EC.presence_of_element_located(
                    (By.XPATH, "//input[@type='password' or @placeholder[contains(., 'Password')] or @name='password' or contains(@class, 'pass')]")
                )
            )
            logging.info("Found password field")
            password_field.clear()
            for char in PASSWORD:
                password_field.send_keys(char)
                time.sleep(0.1)
        except TimeoutException:
            raise Exception("Password field not found")

        # Step 4: Click "Log in" button
        login_button = None
        for xpath in [
            "//button[@data-e2e='login-button']",
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in')]",
            "//button[@type='submit']",
            "//button[contains(., 'Log')]",
            "//button"
        ]:
            try:
                login_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                logging.info(f"Found login button with XPath '{xpath}': {login_button.text}")
                break
            except TimeoutException:
                logging.warning(f"XPath '{xpath}' failed to find login button")
        
        if not login_button:
            raise TimeoutException("No login button found with any XPath")
        
        login_button.click()
        time.sleep(10)

        # Step 5: Check login success
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'For You')]")))
        logging.info("Login successful")
    except Exception as e:
        logging.error(f"Login failed: {str(e)}. TikTok UI may have changed or CAPTCHA detected.")
        logging.info(f"Current URL: {driver.current_url}")
        logging.info(f"Page source snippet on failure: {driver.page_source[:2000]}")
        with open("page_source_on_failure.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        logging.info("Full page source saved to 'page_source_on_failure.html'")
        raise

def find_trending_videos(driver):
    driver.get("https://www.tiktok.com/trending")
    time.sleep(5)
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    video_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
    video_urls = [elem.get_attribute("href") for elem in video_elements][:5]
    logging.info(f"Found {len(video_urls)} trending video URLs")
    return video_urls

def comment_on_video(driver, video_url, comment):
    driver.get(video_url)
    wait = WebDriverWait(driver, 10)
    try:
        comment_box = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true']"))
        )
        comment_box.click()
        comment_box.send_keys(comment)
        post_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Post')]"))
        )
        post_button.click()
        time.sleep(2)
        logging.info(f"Commented on {video_url}: {comment}")
    except TimeoutException:
        logging.warning(f"Couldn’t comment on {video_url}. Skipping.")

def generate_comment(coins, news):
    comment_templates = [
        "Yo, {coin1} is popping off! Create your own at memecoinscreator.fun! 🚀 #memecoin",
        "This vid slaps! {coin2} and {coin3} are trending – memecoinscreator.fun has the goods! #crypto",
        "Insane energy here! {coin1} is mooning – check memecoinscreator.fun! 🌙 #memecoin",
        "Wow, {coin2} is 🔥 right now! Make yours at memecoinscreator.fun! #cryptohype",
        "Big vibes! Trending: {coin3} – memecoinscreator.fun for more! #memecoinmania",
    ]
    template = random.choice(comment_templates)
    coin1, coin2, coin3 = coins[0], coins[1], coins[2] if len(coins) >= 3 else coins[0]
    comment = template.format(coin1=coin1, coin2=coin2, coin3=coin3)
    extra_emojis = ["💥", "✨", "💰", "🌟", "🤑", "🎉", "🔥", "🚀", "🌙", "⚡️"]
    if random.random() > 0.5:
        comment += " " + random.choice(extra_emojis)
    return comment[:150]

def main():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    chrome_options.binary_location = os.getenv("GOOGLE_CHROME_BIN", "/app/.chrome-for-testing/chrome-linux64/chrome")
    chromedriver_path = os.getenv("CHROMEDRIVER_PATH", "/app/.chrome-for-testing/chromedriver-linux64/chromedriver")

    while True:
        try:
            driver = webdriver.Chrome(
                service=Service(executable_path=chromedriver_path),
                options=chrome_options
            )
            try:
                login_to_tiktok(driver)
                video_urls = find_trending_videos(driver)
                coins = get_trending_memecoins()
                news = get_crypto_news()
                for url in video_urls:
                    comment = generate_comment(coins, news)
                    comment_on_video(driver, url, comment)
                    time.sleep(random.randint(10, 30))
                logging.info("Cycle complete. Waiting 1 hour before next run...")
                time.sleep(3600)
            except Exception as e:
                logging.error(f"Error occurred: {e}. Restarting in 5 minutes...")
                time.sleep(300)
            finally:
                driver.quit()
        except WebDriverException as e:
            logging.error(f"WebDriver failed to initialize: {e}. Retrying in 5 minutes...")
            time.sleep(300)

if __name__ == "__main__":
    main()