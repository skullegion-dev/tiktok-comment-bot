import requests

def get_trending_memecoins():
    url = "https://api.coingecko.com/api/v3/search/trending"
    response = requests.get(url)
    data = response.json()
    coins = data["coins"][:3]  # Top 3 trending coins
    return [coin["item"]["name"] for coin in coins]

def get_crypto_news():
    url = "https://min-api.cryptocompare.com/data/v2/news/?lang=EN"
    response = requests.get(url)
    data = response.json()
    headlines = [article["title"] for article in data["Data"][:2]]  # Top 2 news
    return headlines

if __name__ == "__main__":
    print("Trending Memecoins:", get_trending_memecoins())
    print("Latest Crypto News:", get_crypto_news())