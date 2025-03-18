# -*- coding: utf-8 -*-
import os
import random
import time
import logging
from selenium_stealth import stealth
import undetected_chromedriver as uc  # Use undetected_chromedriver for SadCaptcha
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from tiktok_captcha_solver import SeleniumSolver  # SadCaptcha solver

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# TikTok credentials
USERNAME = os.getenv("TIKTOK_USERNAME", "user81453494537828")
PASSWORD = os.getenv("TIKTOK_PASSWORD", "Chevrolet2868!")

# SadCaptcha API key
SADCAPTCHA_API_KEY = "f4bc1352255db03144ecce57474fdb98"  # Replace with your actual key

def login_to_tiktok(driver):
    driver.get("https://www.tiktok.com/login/phone-or-email/email")
    wait = WebDriverWait(driver, 40)
    
    logging.info(f"Page loaded. Title: {driver.title}, URL: {driver.current_url}")
    time.sleep(random.uniform(2, 5))

    # Handle cookie banner
    try:
        cookie_accept = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Allow all')]")))
        cookie_accept.click()
        logging.info("Cookie banner accepted")
        time.sleep(random.uniform(1, 3))
    except TimeoutException:
        logging.info("No cookie banner detected")

    # Enter username
    try:
        username_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@name='username']")))
        logging.info("Found username field")
        username_field.clear()
        for char in USERNAME:
            username_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(random.uniform(1, 3))
    except TimeoutException:
        logging.error("Username field not found. Dumping page source.")
        driver.save_screenshot("username_failure.png")
        full_source = driver.page_source
        for i in range(0, len(full_source), 1000):
            logging.info(f"Page source chunk: {full_source[i:i+1000]}")
        raise Exception("Username field not found")

    # Enter password
    try:
        password_field = wait.until(EC.presence_of_element_located((By.XPATH, "//input[@type='password']")))
        logging.info("Found password field")
        password_field.clear()
        for char in PASSWORD:
            password_field.send_keys(char)
            time.sleep(random.uniform(0.05, 0.15))
        time.sleep(random.uniform(1, 3))
    except TimeoutException:
        logging.error("Password field not found. Dumping page source.")
        driver.save_screenshot("password_failure.png")
        full_source = driver.page_source
        for i in range(0, len(full_source), 1000):
            logging.info(f"Page source chunk: {full_source[i:i+1000]}")
        raise Exception("Password field not found")

    # Click login button
    login_button = None
    for xpath in [
        "//button[@type='submit' and contains(., 'Log in')]",
        "//button[@data-e2e='login-button']",
        "//button[contains(., 'Log')]"
    ]:
        try:
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            logging.info(f"Found login button with XPath '{xpath}': {login_button.text}")
            break
        except TimeoutException:
            logging.warning(f"XPath '{xpath}' failed")
    
    if not login_button:
        logging.error("No login button found. Dumping page source.")
        driver.save_screenshot("login_button_failure.png")
        full_source = driver.page_source
        for i in range(0, len(full_source), 1000):
            logging.info(f"Page source chunk: {full_source[i:i+1000]}")
        raise TimeoutException("No login button found")

    login_button.click()
    time.sleep(random.uniform(5, 10))

    # Initialize SadCaptcha solver
    sadcaptcha = SeleniumSolver(driver, SADCAPTCHA_API_KEY)

    # Handle CAPTCHA with SadCaptcha
    if "captcha" in driver.page_source.lower() or "verify" in driver.current_url.lower():
        logging.info("CAPTCHA detected. Attempting to solve with SadCaptcha.")
        driver.save_screenshot("captcha_detected.png")
        try:
            sadcaptcha.solve_captcha_if_present()  # Solves rotate, puzzle, 3D shapes, etc.
            logging.info("SadCaptcha successfully solved the CAPTCHA")
            time.sleep(random.uniform(3, 5))
        except Exception as e:
            logging.error(f"SadCaptcha failed: {str(e)}. Dumping page source.")
            driver.save_screenshot("captcha_solve_failure.png")
            full_source = driver.page_source
            for i in range(0, len(full_source), 1000):
                logging.info(f"Page source chunk: {full_source[i:i+1000]}")
            raise Exception("SadCaptcha solving failed")

    # Verify login success
    try:
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'For You')]")))
        logging.info("Login successful")
    except TimeoutException:
        logging.error("Login failed (no 'For You' found). Dumping page source.")
        driver.save_screenshot("login_verification_failure.png")
        full_source = driver.page_source
        for i in range(0, len(full_source), 1000):
            logging.info(f"Page source chunk: {full_source[i:i+1000]}")
        raise Exception("Login verification failed")

def find_trending_videos(driver):
    driver.get("https://www.tiktok.com/trending")
    wait = WebDriverWait(driver, 20)
    time.sleep(random.uniform(3, 6))
    logging.info(f"Loaded trending page. URL: {driver.current_url}")

    # Scroll to load videos
    for _ in range(10):
        driver.execute_script("window.scrollBy(0, 1500);")
        time.sleep(random.uniform(1, 2))
    
    # Find video links
    video_elements = []
    for xpath in [
        "//a[contains(@href, '/video/') and @data-e2e='video-feed-item-link']",
        "//a[contains(@href, '/video/')]",
        "//div[contains(@data-e2e, 'video-feed-item')]//a"
    ]:
        try:
            video_elements = driver.find_elements(By.XPATH, xpath)
            if video_elements:
                logging.info(f"Found {len(video_elements)} video elements with XPath: {xpath}")
                break
        except Exception as e:
            logging.warning(f"XPath {xpath} failed: {str(e)}")
    
    if not video_elements:
        logging.error("No video elements found. Dumping page source.")
        driver.save_screenshot("trending_videos_failure.png")
        full_source = driver.page_source
        for i in range(0, len(full_source), 1000):
            logging.info(f"Page source chunk: {full_source[i:i+1000]}")
        return []

    video_urls = list(set([elem.get_attribute("href") for elem in video_elements if elem.get_attribute("href")]))[:5]
    logging.info(f"Collected {len(video_urls)} unique trending video URLs: {video_urls}")
    return video_urls

def comment_on_video(driver, video_url, comment):
    driver.get(video_url)
    wait = WebDriverWait(driver, 15)
    time.sleep(random.uniform(2, 5))
    
    try:
        comment_box = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true' and contains(@data-e2e, 'comment-input')]")))
        comment_box.click()
        for char in comment:
            comment_box.send_keys(char)
            time.sleep(random.uniform(0.05, 0.1))
        
        post_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@data-e2e='comment-post']")))
        post_button.click()
        time.sleep(random.uniform(1, 3))
        logging.info(f"Commented on {video_url}: {comment}")
    except TimeoutException as e:
        logging.warning(f"Couldn’t comment on {video_url}: {str(e)}. Skipping.")
        driver.save_screenshot(f"comment_failure_{video_url.split('/')[-1]}.png")

def generate_comment(coins, news):
    comment_templates = [
        "Yo, {coin1} is popping off! Create your own at memecoinscreator.fun! 🚀 #memecoin",
        "This vid slaps! {coin2} and {coin3} are trending – memecoinscreator.fun has the goods! #crypto",
        "Check out {coin1} vibes! Get in on memecoinscreator.fun! #bullrun",
    ]
    template = random.choice(comment_templates)
    coin1, coin2, coin3 = coins[0], coins[1], coins[2] if len(coins) >= 3 else (coins[0], coins[1], coins[0])
    comment = template.format(coin1=coin1, coin2=coin2, coin3=coin3)
    extra_emojis = ["💥", "✨", "💰", "🌟", "🤑", "🎉", "🔥", "🚀", "🌙", "⚡️"]
    if random.random() > 0.5:
        comment += " " + random.choice(extra_emojis)
    return comment[:150]

def main():
    chrome_options = uc.ChromeOptions()
    # chrome_options.add_argument("--headless")  # Uncomment for production
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36")
    chrome_options.add_argument("--window-size=1920,1080")

    while True:
        try:
            # Force ChromeDriver to match Chrome 133
            driver = uc.Chrome(options=chrome_options, version_main=133)
            # Apply stealth settings to avoid detection
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True)
            try:
                login_to_tiktok(driver)
                video_urls = find_trending_videos(driver)
                coins = ["CoinA", "CoinB", "CoinC"]
                news = "Crypto is booming!"
                for url in video_urls:
                    comment = generate_comment(coins, news)
                    comment_on_video(driver, url, comment)
                    time.sleep(random.uniform(10, 30))
                logging.info("Cycle complete. Waiting 1 hour before next run...")
                time.sleep(3600)
            except Exception as e:
                logging.error(f"Error in cycle: {str(e)}. Restarting in 5 minutes...")
                time.sleep(300)
            finally:
                driver.quit()
        except WebDriverException as e:
            logging.error(f"WebDriver failed: {str(e)}. Retrying in 5 minutes...")
            time.sleep(300)

if __name__ == "__main__":
    main()