from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
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
    wait = WebDriverWait(driver, 10)  # Wait up to 10 seconds for elements
    
    try:
        # Wait for and click the "Log in" button
        login_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Log in') or contains(., 'Login')]"))
        )
        login_button.click()
        time.sleep(2)

        # Enter username
        username_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@name='username' or @placeholder='Email or Username']"))
        )
        username_field.send_keys(USERNAME)

        # Enter password
        password_field = wait.until(
            EC.presence_of_element_located((By.XPATH, "//input[@type='password']"))
        )
        password_field.send_keys(PASSWORD)

        # Submit login form
        submit_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' or contains(., 'Log in')]"))
        )
        submit_button.click()
        time.sleep(5)  # Wait for login to complete
    except TimeoutException:
        print("Login elements not found. TikTok UI may have changed. Check the page manually.")
        raise  # Raise exception to trigger retry in main()

def find_trending_videos(driver):
    driver.get("https://www.tiktok.com/trending")
    time.sleep(5)  # Wait for page to load
    # Scroll to load more videos
    for _ in range(3):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
    # Find video links
    video_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/video/')]")
    video_urls = [elem.get_attribute("href") for elem in video_elements][:5]  # Top 5 videos
    return video_urls

def comment_on_video(driver, video_url, comment):
    driver.get(video_url)
    wait = WebDriverWait(driver, 10)
    try:
        # Find and interact with the comment box
        comment_box = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//div[@contenteditable='true']"))
        )
        comment_box.click()
        comment_box.send_keys(comment)
        # Post comment
        post_button = wait.until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'Post')]"))
        )
        post_button.click()
        time.sleep(2)
    except TimeoutException:
        print(f"Couldn’t comment on {video_url}. Skipping.")

def generate_comment(coins, news):
    # Large pool of comment templates
    comment_templates = [
        "Yo, {coin1} is popping off! Create your own at memecoinscreator.fun! 🚀 #memecoin",
        "This vid slaps! {coin2} and {coin3} are trending – memecoinscreator.fun has the goods! #crypto",
        "Insane energy here! {coin1} is mooning – check memecoinscreator.fun! 🌙 #memecoin",
        "Wow, {coin2} is 🔥 right now! Make yours at memecoinscreator.fun! #cryptohype",
        "Big vibes! Trending: {coin3} – memecoinscreator.fun for more! #memecoinmania",
        "Loving this! {coin1} and {coin2} are hot – memecoinscreator.fun! 🚀 #crypto",
        "Can’t stop watching! {coin3} is trending – memecoinscreator.fun! #memecoinlife",
        "This is wild! {coin1} is pumping – memecoinscreator.fun has it all! #cryptocraze",
        "Epic! {coin2} is trending – create yours at memecoinscreator.fun! �火星 #memecoin",
        "Too good! {coin3} is on fire – memecoinscreator.fun! 🔥 #cryptotrends",
        "Crypto alert: {news1}! More at memecoinscreator.fun! #cryptocurrency",
        "This bangs! News: {news2} – memecoinscreator.fun for updates! #crypto",
        "Huge vibes! {news1} just dropped – memecoinscreator.fun! #cryptonews",
        "Mind blown! {news2} is big – check memecoinscreator.fun! #cryptohype",
        "This is it! {news1} is trending – memecoinscreator.fun has more! #cryptoalert",
        "Sick vid! {news2} is hot – memecoinscreator.fun! 🔥 #cryptocurrency",
        "Wowza! {news1} news – memecoinscreator.fun for the scoop! #cryptotrends",
        "LFG! {news2} just hit – memecoinscreator.fun! 🚀 #crypto",
        "Next level! {news1} is buzzing – memecoinscreator.fun! #cryptolife",
        "Can’t get enough! {news2} – memecoinscreator.fun for more! #cryptoupdate",
        "This rocks! {coin1} is trending + {news1}! memecoinscreator.fun! #memecoin",
        "Vibes! {coin2} is up & {news2} is huge – memecoinscreator.fun! #crypto",
        "Holy cow! {coin3} + {news1} = 🔥 – memecoinscreator.fun! #cryptocurrency",
        "Obsessed! {coin1} is hot & {news2} is big – memecoinscreator.fun! #memecoin",
        "Yesss! {coin2} trending + {news1} news – memecoinscreator.fun! 🚀 #crypto",
        "Unreal! {coin3} is pumping, {news2} is out – memecoinscreator.fun! #cryptohype",
        "Banger! {coin1} + {news1} = win – memecoinscreator.fun! #memecoinlife",
        "Lit! {coin2} is trending & {news2} is fire – memecoinscreator.fun! #crypto",
        "Can’t believe it! {coin3} + {news1} – memecoinscreator.fun! 🌙 #cryptotrends",
        "Top tier! {coin1} is up, {news2} is hot – memecoinscreator.fun! #memecoinmania",
        "This is everything! Make your own coin at memecoinscreator.fun! #crypto",
        "Straight fire! memecoinscreator.fun for the best memecoins! 🚀 #memecoin",
        "Obsessed with this! memecoinscreator.fun has the crypto sauce! #cryptocurrency",
        "Too lit! Check memecoinscreator.fun for memecoin magic! 🔥 #crypto",
        "Viral vibes! memecoinscreator.fun is the spot! #memecoinlife",
        "This hits! memecoinscreator.fun for all things crypto! #cryptohype",
        "No cap, memecoinscreator.fun is where it’s at! 🚀 #memecoin",
        "Energy! memecoinscreator.fun for the win! #cryptotrends",
        "Slaps hard! memecoinscreator.fun is the move! #crypto",
        "Legendary! memecoinscreator.fun has it all! 🌙 #memecoinmania",
    ]

    # Randomly pick a template
    template = random.choice(comment_templates)

    # Fill in placeholders with data
    coin1, coin2, coin3 = coins[0], coins[1], coins[2] if len(coins) >= 3 else coins[0]
    news1, news2 = news[0][:50], news[1][:50] if len(news) >= 2 else news[0][:50]  # Truncate for brevity
    comment = template.format(coin1=coin1, coin2=coin2, coin3=coin3, news1=news1, news2=news2)

    # Randomly add an extra emoji for more variety
    extra_emojis = ["💥", "✨", "💰", "🌟", "🤑", "🎉", "🔥", "🚀", "🌙", "⚡️"]
    if random.random() > 0.5:  # 50% chance to add an emoji
        comment += " " + random.choice(extra_emojis)

    # Ensure comment fits TikTok's 150-character limit
    return comment[:150]

def main():
    # Configure Chrome options for Heroku (headless mode)
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    while True:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        try:
            login_to_tiktok(driver)
            video_urls = find_trending_videos(driver)
            coins = get_trending_memecoins()
            news = get_crypto_news()

            # Comment on trending videos
            for url in video_urls:
                comment = generate_comment(coins, news)
                comment_on_video(driver, url, comment)
                print(f"Commented on {url}: {comment}")
                time.sleep(random.randint(10, 30))  # Random delay between comments
            print("Cycle complete. Waiting 1 hour before next run...")
            time.sleep(3600)  # Wait 1 hour before next cycle
        except Exception as e:
            print(f"Error occurred: {e}. Restarting in 5 minutes...")
            time.sleep(300)  # Wait 5 minutes before retrying
        finally:
            driver.quit()

if __name__ == "__main__":
    main()