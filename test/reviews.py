from flask import render_template, Blueprint
import requests
from bs4 import BeautifulSoup

reviews_bp = Blueprint('reviews', __name__)

# POBIERANIE OPINII Z PYSZNE.PL
def get_pyszne_reviews():
    url = "https://www.pyszne.pl/menu/joker-pizza-burger"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Przykładowe szukanie oceny
        average_rating = "Brak danych"
        rating_el = soup.find("span", class_="rating-score")
        if rating_el:
            average_rating = rating_el.get_text(strip=True)

        reviews = []
        review_elements = soup.select('.review, .rating-comment')
        for review in review_elements[:20]:
            text = review.get_text(strip=True)
            if text:
                reviews.append(text)

        return {
            "average": average_rating,
            "reviews": reviews
        }
    except Exception as e:
        return {"average": "Błąd", "reviews": [f"Błąd pobierania: {e}"]}

# STRONA /OCENY
@reviews_bp.route("/oceny")
def show_reviews():
    pyszne_data = get_pyszne_reviews()
    google_data = {
        "average": "4.6",
        "reviews": [
            "Bardzo dobre jedzenie, polecam!",
            "Obsługa miła, ale czas oczekiwania długi.",
            "Pizza smaczna jak zawsze."
        ]
    }
    return render_template("reviews.html", pyszne=pyszne_data, google=google_data)
