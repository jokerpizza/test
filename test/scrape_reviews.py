import json
from scraper_pyszne import get_pyszne_reviews
from scraper_google import get_google_reviews

def scrape_and_save():
    google = get_google_reviews()
    pyszne = get_pyszne_reviews()

    data = {
        "google": google,
        "pyszne": pyszne
    }

    with open("reviews.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    scrape_and_save()
    print("Opinie zapisane do reviews.json")
