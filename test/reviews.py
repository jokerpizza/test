from flask import render_template, Blueprint
import json
import os

reviews_bp = Blueprint('reviews', __name__)

@reviews_bp.route("/oceny")
def show_reviews():
    try:
        with open("reviews.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            google = data.get("google", {})
            pyszne = data.get("pyszne", {})
    except Exception as e:
        google = {"average": "Błąd", "reviews": [f"Błąd: {e}"]}
        pyszne = {"average": "Błąd", "reviews": [f"Błąd: {e}"]}
    return render_template("reviews.html", google=google, pyszne=pyszne)
