#!/usr/bin/env python3
import os
import json
from models import db, CostCategory
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pizzeria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def seed_categories():
    mapping_path = os.path.join(os.path.dirname(__file__), 'categories.json')
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    with app.app_context():
        for main_name, subs in mapping.items():
            main = CostCategory.query.filter_by(name=main_name, parent_id=None).first()
            if not main:
                main = CostCategory(name=main_name)
                db.session.add(main)
                db.session.flush()
            for sub_name in subs:
                exists = CostCategory.query.filter_by(name=sub_name, parent_id=main.id).first()
                if not exists:
                    db.session.add(CostCategory(name=sub_name, parent_id=main.id))
        db.session.commit()
        print("Seed completed.")

if __name__ == '__main__':
    seed_categories()
