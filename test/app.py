from dotenv import load_dotenv
load_dotenv()

# app.py

import os
import json
import json
from datetime import date, timedelta
import calendar
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps

from models import db, User, Sale, Cost, RolePermissions, CostCategory, SafeTransaction, Product, Dish, RecipeItem
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
from sqlalchemy import event
from sqlalchemy.orm.attributes import get_history
from models import AuditLog
from flask import session

# --- AUDIT LOG EVENT LISTENERS ---
def register_audit_listeners():
    def after_insert(mapper, connection, target):
        try:
            user_id = session.get('user_id')
        except:
            user_id = None
        connection.execute(AuditLog.__table__.insert().values(
            user_id=user_id, action='create', object_type=mapper.class_.__name__, object_id=target.id, details=None
        ))

    def after_update(mapper, connection, target):
        try:
            user_id = session.get('user_id')
        except:
            user_id = None
        diffs = {}
        for attr in mapper.column_attrs:
            hist = get_history(target, attr.key)
            if hist.has_changes():
                old = hist.deleted[0] if hist.deleted else None
                new = hist.added[0] if hist.added else None
                diffs[attr.key] = {'old': old, 'new': new}
        connection.execute(AuditLog.__table__.insert().values(
            user_id=user_id,
            action='update',
            object_type=mapper.class_.__name__,
            object_id=target.id,
            details=json.dumps(diffs)
        ))
    def after_delete(mapper, connection, target):
        try:
            user_id = session.get('user_id')
        except:
            user_id = None
        connection.execute(AuditLog.__table__.insert().values(
            user_id=user_id, action='delete', object_type=mapper.class_.__name__, object_id=target.id, details=None
        ))

    for cls in [User, Sale, Cost, SafeTransaction, CostCategory, RolePermissions]:
        event.listen(cls, 'after_insert', after_insert)
        event.listen(cls, 'after_update', after_update)
        event.listen(cls, 'after_delete', after_delete)

register_audit_listeners()
# --- END AUDIT LOG SETUP ---


# Konfiguracja bazy:
#  - Jeśli używasz PostgreSQL na Renderze: 
#      os.environ.get('DATABASE_URL') 
#    w przeciwnym wypadku lokalnie (SQLite) np. 'sqlite:///pizzeria.db'
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pizzeria.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Klucz sesji
app.secret_key = os.environ.get('SECRET_KEY', 'super-secret-key')

db.init_app(app)

# Dekorator wymuszający zalogowanie
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Uprawnienia w zależności od roli
PERMISSIONS = {
    "Administrator": ["manage_users", "add_cost", "view_reports", "add_sale"],
    "Manager": ["add_cost", "view_reports", "add_sale"],
    "Pracownik": ["add_cost"]
}

# Dekorator sprawdzający uprawnienia
def role_required(permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            user_role = session.get("user_role")
            user_id = session.get("user_id")
            if not user_role or not user_id:
                return redirect(url_for("login"))

            # Najpierw sprawdź user-specific permission
            user_permission = RolePermissions.query.filter_by(user_id=user_id, permission=permission).first()
            if user_permission:
                return func(*args, **kwargs)

            # Potem sprawdź role-based permission
            role_permission = RolePermissions.query.filter_by(role=user_role, permission=permission).first()
            if role_permission:
                return func(*args, **kwargs)
            
            # Brak pozwolenia
            return redirect(url_for("index"))
        return wrapper
    return decorator

# Lista kategorii w pamięci (opcjonalnie)
global_categories = ['Food Oclock', 'Piter Company', 'Utilities', 'Office Supplies']

#
# ======================
#  Inicjalizacja bazy
# ======================
#
with app.app_context():
    db.create_all()
    from sqlalchemy import text
    db.session.execute(text("ALTER TABLE IF EXISTS cost ADD COLUMN IF NOT EXISTS category VARCHAR(100);"))
    db.session.execute(text("ALTER TABLE IF EXISTS cost_category ADD COLUMN IF NOT EXISTS parent_id INTEGER;"))
    db.session.commit()

    # Upewnij się, że mamy użytkownika Administrator (jeśli nie, twórz)
    admin_user = User.query.filter_by(role='Administrator').first()
    if not admin_user:
        admin = User(username='admin', role='Administrator')
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()
        print("Utworzono użytkownika Administrator: login=admin, hasło=admin123")

    # Wstaw domyślne uprawnienia (jeśli nie istnieją)
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
# ======================
#  ROUTES
# ======================
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

            # Wczytanie user-specific permissions do sesji (opcjonalne)
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
    return render_template('sales.html')  # updated to new template
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
    if request.method == 'POST':
        cost_date = request.form['date']
        main_id = request.form['main_category']
        sub_id = request.form['subcategory']
        description = request.form['description']
        amount = float(request.form['amount'] or 0)
        payment_method = request.form['payment_method']
        main = CostCategory.query.get(main_id)
        sub = CostCategory.query.get(sub_id)
        category = f"{main.name} / {sub.name}" if main and sub else ''
        new_cost = Cost(
            date=cost_date,
            category=category,
            description=description,
            amount=amount,
            payment_method=payment_method,
            user_id=session.get('user_id')
        )
        db.session.add(new_cost)
        db.session.commit()
        return redirect(url_for('costs_list'))
    # GET request
    main_categories = CostCategory.query.filter_by(parent_id=None).order_by(CostCategory.name).all()
    return render_template('add_cost.html', main_categories=main_categories)

@app.route('/costs')
@login_required
def costs_list():
    """Filtrowana lista kosztów"""
    q = Cost.query
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    if date_from: q = q.filter(Cost.date >= date_from)
    if date_to: q = q.filter(Cost.date <= date_to)
    cat = request.args.get('category')
    if cat: q = q.filter(Cost.category.ilike(f'%{cat}%'))
    cash = request.args.get('cash'); transfer = request.args.get('transfer')
    if cash and not transfer: q = q.filter(Cost.payment_method=='Gotówka')
    if transfer and not cash: q = q.filter(Cost.payment_method=='Przelew')
    costs = q.order_by(Cost.date.desc()).all()
    return render_template('costs_list.html', costs=costs)


@app.route('/edit_cost/<int:cost_id>', methods=['GET', 'POST'])
@login_required
def edit_cost(cost_id):
    cost = Cost.query.get_or_404(cost_id)
    if request.method == 'POST':
        cost.date = request.form['date']
        main_id = request.form['main_category']
        sub_id = request.form['subcategory']
        main = CostCategory.query.get(main_id)
        sub = CostCategory.query.get(sub_id)
        cost.category = f"{main.name} / {sub.name}" if main and sub else ''
        cost.description = request.form['description']
        cost.amount = float(request.form['amount'] or 0)
        cost.payment_method = request.form['payment_method']
        db.session.commit()
        return redirect(url_for('costs_list'))
    # GET request
    main_categories = CostCategory.query.filter_by(parent_id=None).order_by(CostCategory.name).all()
    selected_main_id = None
    selected_sub_id = None
    if cost.category and ' / ' in cost.category:
        mn, sn = cost.category.split(' / ', 1)
        main = CostCategory.query.filter_by(name=mn, parent_id=None).first()
        if main:
            selected_main_id = main.id
            sub = CostCategory.query.filter_by(name=sn, parent_id=main.id).first()
            if sub:
                selected_sub_id = sub.id
    return render_template('edit_cost.html', cost=cost, main_categories=main_categories, selected_main_id=selected_main_id, selected_sub_id=selected_sub_id)
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
# Podsumowanie kosztów wg kategorii
# ---------------------------
@app.route('/cost_summary', methods=['GET'])
@login_required
def cost_summary():
    today = date.today()
    current_year = today.year
    current_month = today.month

    selected_year = request.args.get('year', current_year, type=int)
    selected_month = request.args.get('month', current_month, type=int)
    selected_year_month = f"{selected_year}-{selected_month:02d}"

    costs = Cost.query.filter(Cost.date.startswith(selected_year_month)).all()
    summary = {}
    for cost in costs:
        cat = cost.category
        summary[cat] = summary.get(cat, 0) + cost.amount

    return render_template(
        'cost_summary.html',
        summary=summary,
        selected_year=selected_year,
        selected_month=selected_month
    )

# ---------------------------
# Zarządzanie kategoriami (settings)
# ---------------------------
@app.route('/manage_users', methods=['GET', 'POST'])
@login_required
@role_required('manage_users')
def manage_users():
    if request.method == 'POST':
        # Aktualizacja uprawnień user-specific
        for user in User.query.all():
            RolePermissions.query.filter_by(user_id=user.id).delete()

            permissions = request.form.getlist(f"permissions_{user.id}")
            for permission in permissions:
                new_perm = RolePermissions(user_id=user.id, permission=permission, role=None)
                db.session.add(new_perm)
        
        db.session.commit()
        flash("Zaktualizowano uprawnienia użytkowników.")

    users = User.query.all()
    for u in users:
        u.permissions = [perm.permission for perm in RolePermissions.query.filter_by(user_id=u.id).all()]

    return render_template('manage_users.html', users=users)

# ---------------------------
# SEJF / SALDO (z filtrowaniem dat, domyślnie ostatnie 7 dni)
# ---------------------------
@app.route('/sejf_saldo', methods=['GET', 'POST'])
@login_required
def sejf_saldo():
    """Wyświetla i obsługuje stan sejfu (gotówka),
       rejestruje wpłaty/wypłaty do/z bankomatu,
       pokazuje listę transakcji (z możliwością filtrowania zakresu dat)."""

    # 1. Dodawanie nowej transakcji (POST)
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        transaction_type = request.form.get('type')  # "wpłata" / "wypłata"

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

    # 2. Filtrowanie zakresu dat (GET)
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    # Domyślnie: od 1 stycznia 2025 do dziś
    if not start_date_str and not end_date_str:
        start_date_str = date(2025, 1, 1).strftime("%Y-%m-%d")
        end_date_str   = date.today().strftime("%Y-%m-%d")

    # Zapamiętujemy wybrane daty, by wyświetlić je w formularzu
    selected_start_date = start_date_str
    selected_end_date = end_date_str

    # 3. Pobieramy z bazy transakcje z wybranego zakresu dat
    sales = Sale.query.filter(Sale.date >= start_date_str, Sale.date <= end_date_str).all()
    costs = Cost.query.filter(
        Cost.date >= start_date_str,
        Cost.date <= end_date_str,
        Cost.payment_method == 'Gotówka'
    ).all()
    safe_transactions = SafeTransaction.query.filter(
        SafeTransaction.date >= start_date_str,
        SafeTransaction.date <= end_date_str
    ).all()

    transactions = []

    # Sprzedaż
    for sale in sales:
        username = sale.user.username if sale.user else "Nieznany"
        transactions.append({
            "date": sale.date,
            "type": "Sprzedaż",
            "amount": sale.gotowka,
            "user": username,
        })

    # Koszty
    for cost in costs:
        username = cost.user.username if cost.user else "Nieznany"
        transactions.append({
            "date": cost.date,
            "type": "Wydatek",
            "amount": -cost.amount,
            "user": username,
        })

    # Transakcje sejfu
    for st in safe_transactions:
        username = st.user.username if st.user else "Nieznany"
        delta = st.amount if st.type == "wypłata" else -st.amount
        transactions.append({
            "date": st.date,
            "type": st.type,
            "amount": delta,
            "user": username,
        })

    # 4. Sortujemy rosnąco po dacie -> liczymy narastająco "balance_after"
    transactions.sort(key=lambda x: x["date"])

    running_balance = 0
    for t in transactions:
        running_balance += t["amount"]
        t["balance_after"] = running_balance

    # Opcjonalnie odwracamy, żeby najnowsze były na górze
    transactions.reverse()

    current_safe_balance = running_balance if transactions else 0

    return render_template(
        'sejf_saldo.html',
        current_safe_balance=current_safe_balance,
        transactions=transactions,
        start_date=selected_start_date,
        end_date=selected_end_date
    )


# === AJAX API for Categories ===
@app.route('/api/categories', methods=['GET'])
@login_required
def api_get_categories():
    mains = CostCategory.query.filter_by(parent_id=None).order_by(CostCategory.name).all()
    data = [{'id': mc.id, 'name': mc.name,
             'subcategories': [{'id': sc.id, 'name': sc.name} for sc in mc.subcategories]}
            for mc in mains]
    return jsonify(data)

@app.route('/api/categories', methods=['POST'])
@login_required
def api_add_main():
    data = request.get_json() or {}
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'error': 'Name required'}), 400
    if CostCategory.query.filter_by(name=name, parent_id=None).first():
        return jsonify({'error': 'Exists'}), 400
    main = CostCategory(name=name)
    db.session.add(main)
    db.session.commit()
    return jsonify({'id': main.id, 'name': main.name}), 201

@app.route('/api/categories/<int:cid>', methods=['PUT', 'DELETE'])
@login_required
def api_main_detail(cid):
    main = CostCategory.query.get_or_404(cid)
    if request.method == 'PUT':
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error': 'Name required'}), 400
        main.name = name
        db.session.commit()
        return jsonify({'id': main.id, 'name': main.name})
    else:
        db.session.delete(main)
        db.session.commit()
        return jsonify({'result':'ok'})

@app.route('/api/subcategories', methods=['POST'])
@login_required
def api_add_sub():
    data = request.get_json() or {}
    parent_id = data.get('parent_id')
    name = data.get('name', '').strip()
    parent = CostCategory.query.get(parent_id)
    if not parent or not name:
        return jsonify({'error':'Invalid data'}), 400
    if CostCategory.query.filter_by(name=name, parent_id=parent.id).first():
        return jsonify({'error':'Exists'}), 400
    sub = CostCategory(name=name, parent_id=parent.id)
    db.session.add(sub)
    db.session.commit()
    return jsonify({'id': sub.id, 'name': sub.name, 'parent_id': parent.id}), 201

@app.route('/api/subcategories/<int:sid>', methods=['PUT', 'DELETE'])
@login_required
def api_sub_detail(sid):
    sub = CostCategory.query.get_or_404(sid)
    if request.method == 'PUT':
        data = request.get_json() or {}
        name = data.get('name', '').strip()
        if not name:
            return jsonify({'error':'Name required'}), 400
        sub.name = name
        db.session.commit()
        return jsonify({'id': sub.id, 'name': sub.name})
    else:
        db.session.delete(sub)
        db.session.commit()
        return jsonify({'result':'ok'})


@app.route('/settings')
@login_required

def settings():

    # Render settings SPA page

    return render_template('settings.html')


# === AJAX API for Sales ===
from datetime import date, timedelta
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
@app.route('/api/sales', methods=['GET'])
@login_required
def api_get_sales():
    sales = Sale.query.order_by(Sale.date.desc()).all()
    data = []
    for s in sales:
        total = s.gotowka + s.przelew + s.zaplacono
        data.append({
            'id': s.id,
            'date': s.date,
            'gotowka': s.gotowka,
            'przelew': s.przelew,
            'zaplacono': s.zaplacono,
            'sum': total
        })
    return jsonify(data)

@app.route('/api/sales', methods=['POST'])
@login_required
def api_add_sale():
    data = request.get_json() or {}
    date_str = data.get('date')
    got = float(data.get('gotowka', 0))
    prz = float(data.get('przelew', 0))
    zap = float(data.get('zaplacono', 0))
    if not date_str:
        return jsonify({'error':'Date required'}), 400
    s = Sale(date=date_str, gotowka=got, przelew=prz, zaplacono=zap, user_id=session.get('user_id'))
    db.session.add(s)
    db.session.commit()
    return jsonify({'id': s.id}), 201

@app.route('/api/sales/<int:sid>', methods=['PUT','DELETE'])
@login_required
def api_sale_detail(sid):
    s = Sale.query.get_or_404(sid)
    if request.method == 'PUT':
        data = request.get_json() or {}
        s.date = data.get('date', s.date)
        s.gotowka = float(data.get('gotowka', s.gotowka))
        s.przelew = float(data.get('przelew', s.przelew))
        s.zaplacono = float(data.get('zaplacono', s.zaplacono))
        db.session.commit()
        return jsonify({'result':'ok'})
    else:
        db.session.delete(s)
        db.session.commit()
        return jsonify({'result':'ok'})

@app.route('/api/sales/metrics', methods=['GET'])
@login_required
def api_sales_metrics():
    today = date.today()
    week_ago = today - timedelta(days=6)
    sales = Sale.query.all()
    daily = sum((s.gotowka + s.przelew + s.zaplacono) for s in sales if s.date == today.strftime('%Y-%m-%d'))
    weekly = sum((s.gotowka + s.przelew + s.zaplacono) for s in sales if week_ago.strftime('%Y-%m-%d') <= s.date <= today.strftime('%Y-%m-%d'))
    monthly = sum((s.gotowka + s.przelew + s.zaplacono) for s in sales if s.date.startswith(today.strftime('%Y-%m')))
    return jsonify({'daily': daily, 'weekly': weekly, 'monthly': monthly})

def parse_date(s):
    return date.fromisoformat(s)


@app.route('/api/costs/summary')
@login_required
def api_costs_summary():
    start = request.args.get('start')
    end = request.args.get('end')
    cmp_start = request.args.get('cmp_start')
    cmp_end = request.args.get('cmp_end')

    def get_data(s, e):
        # parse dates
        costs = Cost.query.filter(Cost.date >= s, Cost.date <= e).all()
        total = sum(c.amount for c in costs)
        cats = {}
        for c in costs:
            parts = (c.category or 'Inne').split(' / ')
            main = parts[0]
            sub = parts[1] if len(parts) > 1 else 'Inne'
            if main not in cats:
                cats[main] = {'name': main, 'amount': 0, 'sub': {}}
            cats[main]['amount'] += c.amount
            cats[main]['sub'].setdefault(sub, 0)
            cats[main]['sub'][sub] += c.amount
        result = []
        for info in cats.values():
            result.append({
                'name': info['name'],
                'amount': info['amount'],
                'sub': [{'name': k, 'amount': v} for k, v in info['sub'].items()]
            })
        return {'total': total, 'categories': result}

    dataA = get_data(start, end)
    if cmp_start and cmp_end:
        dataB = get_data(cmp_start, cmp_end)
    else:
        # fallback to previous same-length period
        from datetime import timedelta
        from datetime import date
        delta = None
        try:
            start_date = date.fromisoformat(start)
            end_date = date.fromisoformat(end)
            delta = end_date - start_date
        except:
            delta = None
        if delta:
            prev_start = (date.fromisoformat(start) - delta - timedelta(days=1)).isoformat()
            prev_end   = (date.fromisoformat(end) - timedelta(days=1)).isoformat()
            dataB = get_data(prev_start, prev_end)
        else:
            dataB = {'total': 0, 'categories': []}

    return jsonify({'periodA': dataA, 'periodB': dataB})


@app.route('/logi')
@login_required
def logi():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    query = AuditLog.query
    if start_date_str:
        from datetime import datetime
        start = datetime.strptime(start_date_str, '%Y-%m-%d')
        query = query.filter(AuditLog.timestamp >= start)
    if end_date_str:
        from datetime import datetime
        end = datetime.strptime(end_date_str, '%Y-%m-%d')
        query = query.filter(AuditLog.timestamp <= end)
    page = int(request.args.get('page', 1))
    per_page = 50
    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=per_page, error_out=False)
    return render_template('logi.html', logs=pagination.items, pagination=pagination, start_date=start_date_str, end_date=end_date_str)


# --- Food Cost feature routes ---
@app.route('/foodcost')
@login_required
def foodcost():
    # Tab selection
    tab = request.args.get('tab', 'products')
    products = Product.query.all()
    dishes = Dish.query.all()
    # For analysis tab, compute food cost
    analysis = []
    if tab == 'analysis':
        for dish in dishes:
            total_cost = sum(item.weight_kg * item.product.price_per_kg for item in dish.recipe_items)
            pct = (total_cost / dish.sale_price * 100) if dish.sale_price else 0
            analysis.append({'dish': dish.name, 'cost': total_cost, 'pct': pct})
    return render_template('foodcost.html',
                           tab=tab,
                           products=products,
                           dishes=dishes,
                           analysis=analysis)


# --- Food Cost add endpoints ---
@app.route('/add_product', methods=['POST'])
@login_required
def add_product():
    name = request.form.get('name', '').strip()
    price = request.form.get('price_per_kg', '').strip()
    try:
        price = float(price)
    except:
        flash('Nieprawidłowa cena', 'danger')
        return redirect(url_for('foodcost', tab='products'))
    if not name or price < 0:
        flash('Wszystkie pola wymagane', 'danger')
        return redirect(url_for('foodcost', tab='products'))
    prod = Product(name=name, price_per_kg=price)
    db.session.add(prod)
    db.session.commit()
    flash('Produkt dodany', 'success')
    return redirect(url_for('foodcost', tab='products'))

@app.route('/add_dish', methods=['POST'])
@login_required
def add_dish():
    name = request.form.get('name', '').strip()
    sale_price = request.form.get('sale_price', '').strip()
    try:
        sale_price = float(sale_price)
    except:
        flash('Nieprawidłowa cena sprzedaży', 'danger')
        return redirect(url_for('foodcost', tab='dishes'))
    if not name or sale_price < 0:
        flash('Wszystkie pola wymagane', 'danger')
        return redirect(url_for('foodcost', tab='dishes'))
    dish = Dish(name=name, sale_price=sale_price)
    db.session.add(dish)
    db.session.flush()
    # gather recipe items
    for key, value in request.form.items():
        if key.startswith('product_id_'):
            idx = key.split('product_id_')[1]
            prod_id = int(value)
            weight = request.form.get(f'weight_kg_{idx}', '').strip()
            try:
                w = float(weight)
            except:
                continue
            if w > 0:
                ri = RecipeItem(dish_id=dish.id, product_id=prod_id, weight_kg=w)
                db.session.add(ri)
    db.session.commit()
    flash('Danie dodane', 'success')
    return redirect(url_for('foodcost', tab='dishes'))

if __name__ == '__main__':

    app.run(debug=True)
