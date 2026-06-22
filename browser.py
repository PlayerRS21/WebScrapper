from selenium import webdriver
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from butyfulsup import main
import time
import tempfile
from pathlib import Path

query = input("Enter a product you want to search...\n>> ")

pages_max = input("Enter the number of pages you want to collect data from...\n>> ")

temp_obj = tempfile.TemporaryDirectory()
temp_path = Path(temp_obj.name)
print(temp_path)

# Setup Firefox driver
browser = webdriver.Firefox()
file = 1
for i in range(0,int(pages_max)):
    browser.get(f"https://www.amazon.in/s?k={query}&page={i+1}&xpid=buxCJGuEk7_r2&crid=SJ3HWJVPMJ7S&qid=1781022751&sprefix=laptop%2Caps%2C622&ref=sr_pg_{i}")
    elem = browser.find_elements(By.CLASS_NAME, "puis-card-container")
    for item in elem:
        html = item.get_attribute("outerHTML")
        with open(f"{temp_path}/file_{file}","w") as f:
            htm = BeautifulSoup(html, "html.parser")
            f.write(htm.prettify())
            file +=1
browser.close()

main(temp_path,file,query)

if __name__ == "__main__":
    main()