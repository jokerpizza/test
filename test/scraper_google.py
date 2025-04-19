from playwright.sync_api import sync_playwright
import time

def get_google_reviews():
    url = "https://www.google.pl/maps/place/Joker+-+Food+%26+Friends"
    result = {"average": "Brak", "reviews": []}
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(url, timeout=60000)
            page.wait_for_timeout(7000)

            try:
                page.locator('button[jsaction*="pane.reviewChart.moreReviews"]').click()
                page.wait_for_timeout(3000)
            except:
                pass

            scroll_container = page.locator('div[aria-label*="Lista recenzji"]')
            for _ in range(5):
                scroll_container.evaluate("e => e.scrollBy(0, 1000)")
                page.wait_for_timeout(1000)

            try:
                rating = page.locator('div[class*="F7nice"]').first.inner_text()
                result["average"] = rating.strip()
            except:
                result["average"] = "Brak"

            texts = page.locator('span[jscontroller][jsaction*="reviewText"]')
            for i in range(min(20, texts.count())):
                txt = texts.nth(i).inner_text().strip()
                if txt:
                    result["reviews"].append(txt)

            browser.close()
    except Exception as e:
        result["reviews"].append(f"Błąd: {e}")
    return result
