import requests
from bs4 import BeautifulSoup


web = requests.get("https://books.toscrape.com/")

print(web)

soup = BeautifulSoup(web.content,"html.parser")

# print(soup)

lines = soup.find_all("a")

for l in lines:
    print(l.text)

# print(lines)