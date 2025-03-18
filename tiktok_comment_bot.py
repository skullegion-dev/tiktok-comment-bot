from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import random
import os
from crypto_data import get_trending_memecoins, get_crypto_news

# TikTok login credentials from environment variables
USERNAME = os.getenv("TIKTOK_USERNAME")
PASSWORD = os.getenv("TIKTOK_PASSWORD")

def login_to_tiktok(driver):
    driver.get("https://www.tiktok.com/login")
    wait = WebDriverWait(driver, 20)
    
    try:
        print("Page loaded. HTML title:", driver.title)
        time.sleep(5)  # Wait for JavaScript
        print("Page source snippet after wait:", driver.page_source[:2000])  # More context

        # Try multiple strategies to find the "Log in" button
        login_button = None
        for xpath in [
            "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in') or contains(., 'Login')]",
            "//button[contains(., 'Log')]",
            "//*[contains(@class, 'login') or contains(@class, 'Login')]/button",
            "//button[@data-e2e='login-button']",  # TikTok-specific data attribute
            "//button"  # Last resort
        ]:
            try:
                login_button = wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
                print(f"Found login button with XPath '{xpath}': {login_button.text}")
                break
            except TimeoutException:
                print(f"XPath '{xpath}' failed to find login button")
        
        if not login_button:
            raise TimeoutException("No login button found with any XPath")
        
        login_button.click()
        time.sleep(2)

        # Enter username
        username_field = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@name='username' or @placeholder[contains(., 'Email') or contains(., 'Username') or contains(., 'Phone')]]")
            )
        )
        print("Found username field")
        username_field.send_keys(USERNAME)

        # Enter password
        password_field = wait.until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@type='password' or @placeholder[contains(., 'Password')]]")
            )
        )
        print("Found password field")
        password_field.send_keys(PASSWORD)

        # Submit login form
        submit_button = wait.until(
            EC.element_to_be_clickable(
                (By.XPATH, "//button[@type='submit' or contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), 'log in')]")
            )
        )
        print("Found submit button:", submit_button.text)
        submit_button.click()
        time.sleep(5)

        # Check if login succeeded
        wait.until(EC.presence_of_element_located((By.XPATH, "//*[contains(., 'For You')]")))
        print("Login successful")
    except TimeoutException as e:
        print(f"Login failed: {str(e)}. TikTok UI may have changed.")
        print("Current URL:", driver.current_url)
        with open("page_source_on_failure.html", "w", encoding="utf-8") as f:
            f.write(driver.page_source)  # Save full source locally
        print("Full page source saved to 'page_source_on_failure.html' (check Heroku filesystem)")
        raise

def find_trending_videos(driver):
    driver.get("https://www.tiktok.com/trending")
    time.sleep(5)
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    video_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
    video_urls = [elem.get_attribute("href") for elem in video_elements][:5]
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
    except TimeoutException:
        print(f"Couldn’t comment on {video_url}. Skipping.")

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
    news1, news2 = news[0][:50], news[1][:50] if len(news) >= 2 else news[0][:50]
    comment = template.format(coin1=coin1, coin2=coin2, coin3=coin3, news1=news1, news2=news2)
    extra_emojis = ["💥", "✨", "💰", "🌟", "🤑", "🎉", "🔥", "🚀", "🌙", "⚡️"]
    if random.random() > 0.5:
        comment += " " + random.choice(extra_emojis)
    return comment[:150]

def main():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.binary_location = "/app/.chrome-for-testing/chrome-linux64/chrome"
    chromedriver_path = "/app/.chrome-for-testing/chromedriver-linux64/chromedriver"

    while True:
        try:
            driver = webdriver.Chrome(
                service=Service(chromedriver_path),
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
                    print(f"Commented on {url}: {comment}")
                    time.sleep(random.randint(10, 30))
                print("Cycle complete. Waiting 1 hour before next run...")
                time.sleep(3600)
            except Exception as e:
                print(f"Error occurred: {e}. Restarting in 5 minutes...")
                time.sleep(300)
            finally:
                driver.quit()
        except Exception as e:
            print(f"Failed to initialize WebDriver: {e}. Retrying in 5 minutes...")
            time.sleep(300)

if __name__ == "__main__":
    main()