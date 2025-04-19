#!/usr/bin/env python3
"""Idempotent seed script for CostCategory.

- Ensures categories are created once.
- If a category exists with a different parent_id, the parent_id is updated.
"""

import os
import json
from models import db, CostCategory
from flask import Flask

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pizzeria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

def get_or_create(name: str, parent_id: int | None = None) -> CostCategory:
    """Return existing CostCategory or create a new one.

    If the category exists but has a different parent_id, update it.
    """
    cat = CostCategory.query.filter_by(name=name).first()
    if cat is None:
        cat = CostCategory(name=name, parent_id=parent_id)
        db.session.add(cat)
        db.session.flush()  # we need the id for sub‑categories
    elif cat.parent_id != parent_id:
        cat.parent_id = parent_id
    return cat

def seed_categories() -> None:
    mapping_path = os.path.join(os.path.dirname(__file__), 'categories.json')
    with open(mapping_path, 'r', encoding='utf-8') as f:
        mapping = json.load(f)

    with app.app_context():
        for main_name, subs in mapping.items():
            main = get_or_create(main_name, None)
            for sub_name in subs:
                get_or_create(sub_name, main.id)
        db.session.commit()
        print('Seed completed (idempotent).')

if __name__ == '__main__':
    seed_categories()
