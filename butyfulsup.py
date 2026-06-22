import os
import sqlite3
from bs4 import BeautifulSoup

def process_and_insert_item(file_index, cursor, path):
    file_path = f"{path}/file_{file_index}"
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    except FileNotFoundError:
        print(f"[-] File {file_index} not found. Skipping.")
        return

    # Anti-bot check
    if "api-services-support@amazon.com" in html_content or "sorry, we just need to make sure you're not a robot" in html_content.lower():
        print(f"[-] File {file_index} was blocked by Amazon Automated Bot Detection (CAPTCHA).")
        return

    soup = BeautifulSoup(html_content, "html.parser")

    # 1. Parse Title / H2
    h2_tag = soup.h2
    if not h2_tag:
        print(f"[-] File {file_index}: Missing H2 tag (No product title found).")
        return
    
    item_name_spec = [g.strip() for g in h2_tag.text.split(",") if g.strip()]
    if not item_name_spec:
        print(f"[-] File {file_index}: H2 tag contains no valid text parsing options.")
        return
    
    item_name = item_name_spec[0]
    item_spec = ",".join(item_name_spec[1:])

    # 2. Parse Price (With fallbacks for variations/OOS structures)
    price_tag = soup.find("span", class_="a-price-whole")
    
    # Fallback 1: Check offscreen accessibility price text (e.g. "$15.99")
    if not price_tag:
        price_tag = soup.find("span", class_="a-offscreen")
        
    # Fallback 2: Check standard alternative price containers
    if not price_tag:
        price_tag = soup.find("span", id="priceblock_ourprice") or soup.find("span", id="priceblock_dealprice")

    if not price_tag:
        # Check if explicitly Out of Stock
        oos_div = soup.find(id="availability")
        if oos_div and "currently unavailable" in oos_div.text.lower():
            print(f"[!] File {file_index}: Item is explicitly Out of Stock (No price tag available).")
        else:
            print(f"[!] File {file_index}: No structural price tag found (Layout changed or Variation listing).")
        return
    
    # Clean price string for SQLite REAL mapping
    # Extract only digits, periods, and remove commas or currency symbols
    raw_price = price_tag.text.strip().replace(",", "").replace("$", "").replace("₹", "")
    
    try:
        item_price = float(raw_price)
    except ValueError:
        # Sometimes a-offscreen pulls the full string like "$15.99". We extract just the float portion.
        try:
            import re
            cleaned = re.findall(r"[-+]?\d*\.\d+|\d+", raw_price)
            if cleaned:
                item_price = float(cleaned[0])
            else:
                raise ValueError
        except ValueError:
            print(f"[-] File {file_index}: Failed to convert raw price text '{raw_price}' to float.")
            return

    # 3. Database Write Execution
    cursor.execute(
        "INSERT INTO products (name, price, specifications) VALUES (?, ?, ?)", 
        (item_name, item_price, item_spec)
    )
    print(f"[+] File {file_index}: Successfully processed and inserted into DB.")

def main(path,pages,query):
    # Ensure data directory context exists
    if not os.path.exists("data"):
        print("[-] 'data' directory does not exist in the current working directory.")
        return

    # Database Initialization
    conn = sqlite3.connect(f"{query}_database.db")
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specifications TEXT NOT NULL,
        price REAL NOT NULL
    )
    """)
    conn.commit()

    print("[*] Starting batch processing of HTML files...")
    
    # Run loops
    for i in range(1, pages):
        process_and_insert_item(i, cur, path)

    # Single final transaction commit
    conn.commit()
    cur.close()
    conn.close()
    print("[*] Processing complete. Database connections closed.")
    input(f"Check Location {path}")
