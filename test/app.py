# app.py

import os
from datetime import date, timedelta
import calendar
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Sale, Cost, CostCategory, CostSubcategory, SafeTransaction, RolePermissions
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Konfiguracja bazy:
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pizzeria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key')

db.init_app(app)

#
# Dekoratory i role
#

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

PERMISSIONS = {
    "Administrator": ["manage_users", "add_cost", "view_reports", "add_sale"],
    "Manager": ["add_cost", "view_reports", "add_sale"],
    "Pracownik": ["add_cost"]
}

def role_required(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = session.get("user_role")
            user_id = session.get("user_id")
            if not user_role or not user_id:
                return redirect(url_for("login"))

            user_perm = RolePermissions.query.filter_by(user_id=user_id, permission=permission).first()
            if user_perm:
                return func(*args, **kwargs)

            role_perm = RolePermissions.query.filter_by(role=user_role, permission=permission).first()
            if role_perm:
                return func(*args, **kwargs)
            
            return redirect(url_for("index"))
        return wrapper
    return decorator

#
# Inicjalizacja bazy
#

with app.app_context():
    db.create_all()

    admin_user = User.query.filter_by(role='Administrator').first()
    if not admin_user:
        admin = User(username='admin', role='Administrator')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    default_permissions = [
        ("Administrator", "manage_users"),
        ("Administrator", "add_cost"),
        ("Administrator", "add_sale"),
        ("Manager", "add_cost"),
        ("Manager", "add_sale"),
        ("Pracownik", "add_cost")
    ]
    for role, permission in default_permissions:
        if not RolePermissions.query.filter_by(role=role, permission=permission).first():
            db.session.add(RolePermissions(role=role, permission=permission))
    db.session.commit()

#
# ROUTES
#

@app.route('/')
def index():
    return render_template('index.html')

# ---------------------------
# Rejestracja / Logowanie / Wylogowanie
# ---------------------------
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return "Taki użytkownik już istnieje!"

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['user_role'] = user.role

            user_permissions = [
                perm.permission for perm in RolePermissions.query.filter_by(user_id=user.id).all()
            ]
            session['user_permissions'] = user_permissions

            return redirect(url_for('index'))
        else:
            return "Nieprawidłowe dane logowania!"
    else:
        return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------------------------
# Sprzedaż
# ---------------------------
@app.route('/add_sale', methods=['GET','POST'])
@login_required
@role_required('add_sale')
def add_sale():
    if request.method == 'POST':
        sale_date = request.form['date']
        gotowka = float(request.form['dine_in'] or 0)
        przelew = float(request.form['delivery'] or 0)
        zaplacono = float(request.form['other'] or 0)

        new_sale = Sale(
            date=sale_date,
            gotowka=gotowka,
            przelew=przelew,
            zaplacono=zaplacono,
            user_id=session.get('user_id')
        )
        db.session.add(new_sale)
        db.session.commit()

        return redirect(url_for('sales_list'))
    else:
        return render_template('add_sale.html')

@app.route('/sales')
@login_required
def sales_list():
    sales = Sale.query.order_by(Sale.date.desc()).all()
    return render_template('sales_list.html', sales=sales)

@app.route('/edit_sale/<int:sale_id>', methods=['GET', 'POST'])
@login_required
def edit_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    if request.method == 'POST':
        sale.date = request.form['date']
        sale.gotowka = float(request.form['dine_in'] or 0)
        sale.przelew = float(request.form['delivery'] or 0)
        sale.zaplacono = float(request.form['other'] or 0)
        db.session.commit()
        return redirect(url_for('sales_list'))
    return render_template('edit_sale.html', sale=sale)

@app.route('/delete_sale/<int:sale_id>', methods=['POST'])
@login_required
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    return redirect(url_for('sales_list'))

# ---------------------------
# Koszty
# ---------------------------
@app.route('/add_cost', methods=['GET', 'POST'])
@login_required
@role_required('add_cost')
def add_cost():
    """
    Dodawanie kosztu z wyborem kategorii i podkategorii (z bazy).
    """
    if request.method == 'POST':
        cost_date = request.form['date']
        category_id = request.form.get('category_id')
        subcategory_id = request.form.get('subcategory_id')
        description = request.form['description']
        amount = float(request.form['amount'] or 0)
        payment_method = request.form['payment_method']

        # Utwórz nowy koszt, zapisz subcategory_id
        new_cost = Cost(
            date=cost_date,
            description=description,
            amount=amount,
            payment_method=payment_method,
            subcategory_id=subcategory_id,
            user_id=session.get('user_id')
        )
        db.session.add(new_cost)
        db.session.commit()

        return redirect(url_for('costs_list'))

    # GET -> pobieramy listę kategorii, a w szablonie przez JS filtry do subkategorii
    categories = CostCategory.query.order_by(CostCategory.name).all()
    subcategories = CostSubcategory.query.order_by(CostSubcategory.name).all()

    return render_template('add_cost.html',
                           categories=categories,
                           subcategories=subcategories)

@app.route('/costs')
@login_required
def costs_list():
    costs = Cost.query.order_by(Cost.date.desc()).all()
    return render_template('costs_list.html', costs=costs)

@app.route('/edit_cost/<int:cost_id>', methods=['GET', 'POST'])
@login_required
def edit_cost(cost_id):
    cost = Cost.query.get_or_404(cost_id)
    if request.method == 'POST':
        cost.date = request.form['date']
        cost.description = request.form['description']
        cost.amount = float(request.form['amount'] or 0)
        cost.payment_method = request.form['payment_method']
        cost.subcategory_id = request.form.get('subcategory_id')
        db.session.commit()
        return redirect(url_for('costs_list'))

    # Potrzebne do dropdownów
    categories = CostCategory.query.order_by(CostCategory.name).all()
    subcategories = CostSubcategory.query.order_by(CostSubcategory.name).all()

    return render_template('edit_cost.html', cost=cost,
                           categories=categories,
                           subcategories=subcategories)

@app.route('/delete_cost/<int:cost_id>', methods=['POST'])
@login_required
def delete_cost(cost_id):
    cost = Cost.query.get_or_404(cost_id)
    db.session.delete(cost)
    db.session.commit()
    return redirect(url_for('costs_list'))

# ---------------------------
# Status Finansowy + Prognoza
# ---------------------------
@app.route('/finance_status', methods=['GET'])
@login_required
def finance_status():
    today = date.today()
    current_year = today.year
    current_month = today.month

    selected_year = request.args.get('year', current_year, type=int)
    selected_month = request.args.get('month', current_month, type=int)
    selected_year_month = f"{selected_year}-{selected_month:02d}"

    sales = Sale.query.all()
    costs = Cost.query.all()

    monthly_sales = 0
    monthly_costs = 0

    for s in sales:
        if s.date and s.date.startswith(selected_year_month):
            monthly_sales += (s.gotowka + s.przelew + s.zaplacono)

    for c in costs:
        if c.date and c.date.startswith(selected_year_month):
            monthly_costs += c.amount

    current_profit = monthly_sales - monthly_costs

    _, num_days_in_month = calendar.monthrange(selected_year, selected_month)
    day_of_month = today.day if (selected_month == current_month and selected_year == current_year) else num_days_in_month

    if day_of_month > 0:
        average_daily_profit = current_profit / day_of_month
        projected_month_end = average_daily_profit * num_days_in_month
    else:
        average_daily_profit = 0
        projected_month_end = 0

    return render_template(
        "finance_status.html",
        current_profit=current_profit,
        average_daily_profit=average_daily_profit,
        projected_month_end=projected_month_end,
        selected_year=selected_year,
        selected_month=selected_month,
    )

# ---------------------------
# Dashboard (wykresy)
# ---------------------------
@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    today = date.today()
    current_year = today.year
    current_month = today.month

    selected_year = request.args.get('year', current_year, type=int)
    selected_month = request.args.get('month', current_month, type=int)
    selected_year_month = f"{selected_year}-{selected_month:02d}"

    _, num_days_in_month = calendar.monthrange(selected_year, selected_month)
    daily_sales = [0.0] * num_days_in_month
    daily_costs = [0.0] * num_days_in_month

    sales = Sale.query.all()
    costs = Cost.query.all()

    for s in sales:
        if s.date and s.date.startswith(selected_year_month):
            day_str = s.date[8:10]
            try:
                day_int = int(day_str)
                daily_sales[day_int - 1] += (s.gotowka + s.przelew + s.zaplacono)
            except:
                pass

    for c in costs:
        if c.date and c.date.startswith(selected_year_month):
            day_str = c.date[8:10]
            try:
                day_int = int(day_str)
                daily_costs[day_int - 1] += c.amount
            except:
                pass

    labels = list(range(1, num_days_in_month + 1))

    return render_template(
        'dashboard.html',
        labels=labels,
        daily_sales=daily_sales,
        daily_costs=daily_costs,
        selected_year=selected_year,
        selected_month=selected_month,
    )

# ---------------------------
# Podsumowanie kosztów wg kategorii i podkategorii
# ---------------------------
@app.route('/cost_summary', methods=['GET'])
@login_required
def cost_summary():
    """
    Grupowanie kosztów wg (Kategoria -> Podkategoria).
    """
    today = date.today()
    current_year = today.year
    current_month = today.month

    selected_year = request.args.get('year', current_year, type=int)
    selected_month = request.args.get('month', current_month, type=int)
    selected_year_month = f"{selected_year}-{selected_month:02d}"

    # Pobieramy koszty tylko z wybranego miesiąca
    costs = Cost.query.filter(Cost.date.startswith(selected_year_month)).all()

    # Struktura: { category_id: { "name": "Food", "total": X, "subcats": { subcat_id: {...} } } }
    summary = {}

    for cost in costs:
        subcat = cost.subcategory
        if not subcat:
            # np. stare rekordy bez subcat
            continue
        cat = subcat.category

        if cat.id not in summary:
            summary[cat.id] = {
                "name": cat.name,
                "total": 0,
                "subcats": {}
            }

        if subcat.id not in summary[cat.id]["subcats"]:
            summary[cat.id]["subcats"][subcat.id] = {
                "name": subcat.name,
                "total": 0
            }
        
        # Dodajemy kwotę do kategorii i do podkategorii
        summary[cat.id]["total"] += cost.amount
        summary[cat.id]["subcats"][subcat.id]["total"] += cost.amount

    return render_template(
        'cost_summary.html',
        summary=summary,
        selected_year=selected_year,
        selected_month=selected_month
    )

# ---------------------------
# Zarządzanie kategoriami i podkategoriami (settings)
# ---------------------------
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """
    Dodawanie kategorii i podkategorii do bazy.
    """
    if request.method == 'POST':
        # Obsługa dodania nowej kategorii
        if "new_category" in request.form:
            new_cat_name = request.form.get('category_name')
            if new_cat_name:
                # Sprawdź, czy nie istnieje
                existing = CostCategory.query.filter_by(name=new_cat_name).first()
                if not existing:
                    db.session.add(CostCategory(name=new_cat_name))
                    db.session.commit()

        # Obsługa dodania nowej podkategorii
        if "new_subcategory" in request.form:
            parent_category_id = request.form.get('parent_category_id')
            subcat_name = request.form.get('subcategory_name')
            if parent_category_id and subcat_name:
                parent_category = CostCategory.query.get(parent_category_id)
                if parent_category:
                    # Sprawdź, czy taka podkategoria nie istnieje w tej kategorii
                    already = CostSubcategory.query.filter_by(name=subcat_name, category_id=parent_category.id).first()
                    if not already:
                        new_sub = CostSubcategory(name=subcat_name, category_id=parent_category.id)
                        db.session.add(new_sub)
                        db.session.commit()

    # Po obsłudze POST wyświetlamy to samo: listę kategorii i podkategorii
    categories = CostCategory.query.order_by(CostCategory.name).all()
    return render_template('settings.html', categories=categories)

# ---------------------------
# SEJF / SALDO
# ---------------------------
@app.route('/sejf_saldo', methods=['GET', 'POST'])
@login_required
def sejf_saldo():
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        transaction_type = request.form.get('type')

        if amount > 0:
            new_transaction = SafeTransaction(
                date=date.today().strftime("%Y-%m-%d"),
                type=transaction_type,
                amount=amount,
                user_id=session.get('user_id')
            )
            db.session.add(new_transaction)
            db.session.commit()
        return redirect(url_for('sejf_saldo'))

    # Filtrowanie zakresu dat (domyślnie ostatnie 7 dni)
    from_date = request.args.get('start_date')
    to_date = request.args.get('end_date')
    if not from_date or not to_date:
        from_date = (date.today() - timedelta(days=7)).strftime("%Y-%m-%d")
        to_date = date.today().strftime("%Y-%m-%d")

    sales = Sale.query.filter(Sale.date >= from_date, Sale.date <= to_date).all()
    costs = Cost.query.filter(Cost.date >= from_date, Cost.date <= to_date).all()
    safe_tx = SafeTransaction.query.filter(SafeTransaction.date >= from_date, SafeTransaction.date <= to_date).all()

    transactions = []

    for s in sales:
        username = s.user.username if s.user else "Nieznany"
        transactions.append({
            "date": s.date,
            "type": "Sprzedaż",
            "amount": s.gotowka,
            "user": username
        })
    for c in costs:
        username = c.user.username if c.user else "Nieznany"
        transactions.append({
            "date": c.date,
            "type": "Wydatek",
            "amount": -c.amount,
            "user": username
        })
    for st in safe_tx:
        username = st.user.username if st.user else "Nieznany"
        delta = st.amount if st.type == 'wypłata' else -st.amount
        transactions.append({
            "date": st.date,
            "type": st.type,
            "amount": delta,
            "user": username
        })

    transactions.sort(key=lambda x: x["date"])
    running_balance = 0
    for t in transactions:
        running_balance += t["amount"]
        t["balance_after"] = running_balance

    transactions.reverse()
    current_safe_balance = running_balance if transactions else 0

    return render_template(
        'sejf_saldo.html',
        current_safe_balance=current_safe_balance,
        transactions=transactions,
        start_date=from_date,
        end_date=to_date
    )

if __name__ == '__main__':
    app.run(debug=True)
