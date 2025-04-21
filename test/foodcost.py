from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required
from models import db, Product, Dish, RecipeItem

foodcost_bp = Blueprint('foodcost', __name__, template_folder='templates/foodcost', url_prefix='/foodcost')

@foodcost_bp.route('/', methods=['GET'])
@login_required
def index():
    tab = request.args.get('tab', 'products')
    if tab == 'products':
        products = Product.query.order_by(Product.name).all()
        return render_template('foodcost/products.html', products=products)
    elif tab == 'dishes':
        dishes = Dish.query.order_by(Dish.name).all()
        return render_template('foodcost/dishes.html', dishes=dishes, products=Product.query.all())
    else:
        dishes = Dish.query.all()
        analysis = []
        for dish in dishes:
            total = sum(item.weight_kg * item.product.price_per_kg for item in dish.recipe_items)
            pct = (total / dish.sale_price * 100) if dish.sale_price else 0
            analysis.append({'dish': dish.name, 'cost': total, 'pct': pct})
        return render_template('foodcost/analysis.html', analysis=analysis)
        
@foodcost_bp.route('/api/products', methods=['POST'])
@login_required
def api_add_product():
    data = request.get_json()
    prod = Product(name=data['name'], price_per_kg=data['price_per_kg'])
    db.session.add(prod); db.session.commit()
    return jsonify(id=prod.id, name=prod.name, price_per_kg=prod.price_per_kg)

@foodcost_bp.route('/api/products/<int:id>', methods=['PUT'])
@login_required
def api_update_product(id):
    prod = Product.query.get_or_404(id)
    data = request.get_json()
    prod.price_per_kg = data['price_per_kg']; db.session.commit()
    return jsonify(success=True)

@foodcost_bp.route('/api/dishes', methods=['POST'])
@login_required
def api_add_dish():
    data = request.get_json()
    dish = Dish(name=data['name'], sale_price=data['sale_price'])
    db.session.add(dish); db.session.flush()
    for item in data.get('recipe', []):
        ri = RecipeItem(dish_id=dish.id, product_id=item['product_id'], weight_kg=item['weight_kg'])
        db.session.add(ri)
    db.session.commit()
    return jsonify(id=dish.id, name=dish.name, sale_price=dish.sale_price)
