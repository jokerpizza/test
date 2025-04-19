from playwright.sync_api import sync_playwright

def get_pyszne_reviews():
    url = "https://www.pyszne.pl/menu/joker-pizza-burger"
    result = {"average": "Brak", "reviews": []}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_timeout(5000)

            try:
                rating = page.locator('span[data-testid="restaurant-rating"]').first.inner_text()
                result["average"] = rating.strip()
            except:
                result["average"] = "Brak"

            comments = page.locator('p[data-testid="review-comment"]')
            count = comments.count()
            for i in range(min(20, count)):
                text = comments.nth(i).inner_text().strip()
                if text:
                    result["reviews"].append(text)

            browser.close()
    except Exception as e:
        result["reviews"].append(f"Błąd: {e}")
    return result
