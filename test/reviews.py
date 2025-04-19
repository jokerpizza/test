
from flask import render_template, Blueprint, redirect, url_for, request
import json
import os
from scrape_reviews import scrape_and_save

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

@reviews_bp.route("/odswiez-opinie", methods=["POST"])
def refresh_reviews():
    scrape_and_save()
    return redirect(url_for("reviews.show_reviews"))
