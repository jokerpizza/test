
PERMISSIONS = {
    "Administrator": ["manage_users", "add_cost", "view_reports"],
    "Manager": ["add_cost", "view_reports"],
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

            # Check user-specific permissions
            user_permission = RolePermissions.query.filter_by(user_id=user_id, permission=permission).first()
            if user_permission:
                return func(*args, **kwargs)

            # Check role-based permissions if no user-specific permission exists
            role_permission = RolePermissions.query.filter_by(role=user_role, permission=permission).first()
            if role_permission:
                return func(*args, **kwargs)
            
            return redirect(url_for("index"))
        return wrapper
    return decorator



# Global list of categories for costs
global_categories = ['Food Oclock', 'Piter Company', 'Utilities', 'Office Supplies']


import os
from datetime import date
import calendar

from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Sale, Cost, RolePermissions, CostCategory
from models import SafeTransaction
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////data/pizzeria.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Klucz do sesji – w produkcji trzymaj go w bezpiecznym miejscu (np. zmienna środowiskowa)
app.secret_key = 'super-secret-key'

db.init_app(app)

with app.app_context():
    db.create_all()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

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

            # Load user permissions into the session
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
# Formularze i listy Sprzedaży
# ---------------------------
@app.route('/add_sale', methods=['GET','POST'])
@login_required
def add_sale():
    if request.method == 'POST':
        sale_date = request.form['date']
        gotowka = float(request.form['dine_in'] or 0)
        przelew = float(request.form['delivery'] or 0)
        zaplacono = float(request.form['other'] or 0)

        new_sale = Sale(date=sale_date, gotowka=gotowka, przelew=przelew, zaplacono=zaplacono)
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

# ---------------------------
# Formularze i listy Kosztów
# ---------------------------
@app.route('/add_cost', methods=['GET', 'POST'])
@login_required
@role_required('add_cost')
def add_cost():
    if request.method == 'POST':
        cost_date = request.form['date']
        category = request.form['category']
        description = request.form['description']
        amount = float(request.form['amount'] or 0)
        payment_method = request.form['payment_method']

        new_cost = Cost(date=cost_date, category=category, description=description, amount=amount, payment_method=payment_method)
        db.session.add(new_cost)
        db.session.commit()

        return redirect(url_for('costs_list'))
    return render_template('add_cost.html', categories=global_categories)

    return render_template('add_cost.html', categories=global_categories)

@app.route('/costs')
@login_required
def costs_list():
    costs = Cost.query.order_by(Cost.date.desc()).all()
    return render_template('costs_list.html', costs=costs)

# ---------------------------
# Status Finansowy + Prognoza
# ---------------------------

@app.route('/finance_status', methods=['GET'])
@login_required
def finance_status():
    # Pobranie parametrów month i year z GET (domyślnie bieżący miesiąc i rok)
    today = date.today()
    current_year = today.year
    current_month = today.month

    selected_year = request.args.get('year', current_year, type=int)
    selected_month = request.args.get('month', current_month, type=int)
    
    # Sformatuj wybrany rok i miesiąc
    selected_year_month = f"{selected_year}-{selected_month:02d}"

    # Zliczamy sprzedaż i koszty dla wybranego miesiąca
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

    # Obliczenia dla prognozy
    _, num_days_in_month = calendar.monthrange(selected_year, selected_month)
    day_of_month = today.day if selected_month == current_month and selected_year == current_year else num_days_in_month

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

@login_required
def finance_status():
    # Określ bieżący rok-miesiąc (np. "2025-01")
    today = date.today()
    current_year_month = today.strftime("%Y-%m")

    # Zliczamy sprzedaż i koszty w tym miesiącu
    sales = Sale.query.all()
    costs = Cost.query.all()

    monthly_sales = 0
    monthly_costs = 0

    for s in sales:
        if s.date and s.date.startswith(current_year_month):
            monthly_sales += (s.gotowka + s.przelew + s.zaplacono)

    for c in costs:
        if c.date and c.date.startswith(current_year_month):
            monthly_costs += c.amount

    current_profit = monthly_sales - monthly_costs

    day_of_month = today.day
    _, num_days_in_month = calendar.monthrange(today.year, today.month)

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
        current_year_month=current_year_month
    )

# ---------------------------
# DASHBOARD Z WYKRESAMI (Chart.js)
# ---------------------------

@app.route('/dashboard', methods=['GET'])
@login_required
def dashboard():
    # Pobranie parametrów month i year z GET (domyślnie bieżący miesiąc i rok)
    today = date.today()
    current_year = today.year
    current_month = today.month

    selected_year = request.args.get('year', current_year, type=int)
    selected_month = request.args.get('month', current_month, type=int)
    
    # Sformatuj wybrany rok i miesiąc
    selected_year_month = f"{selected_year}-{selected_month:02d}"

    # Ile dni w wybranym miesiącu
    _, num_days_in_month = calendar.monthrange(selected_year, selected_month)
    daily_sales = [0.0] * num_days_in_month
    daily_costs = [0.0] * num_days_in_month

    sales = Sale.query.all()
    costs = Cost.query.all()

    for s in sales:
        if s.date and s.date.startswith(selected_year_month):
            day_str = s.date[8:10]  # np. '05'
            try:
                day_int = int(day_str)
                daily_sales[day_int - 1] += (s.gotowka + s.przelew + s.zaplacono)
            except ValueError:
                pass

    for c in costs:
        if c.date and c.date.startswith(selected_year_month):
            day_str = c.date[8:10]
            try:
                day_int = int(day_str)
                daily_costs[day_int - 1] += c.amount
            except ValueError:
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

@login_required
def dashboard():
    """
    Strona z wykresami:
    - Pobieramy sprzedaż i koszty z bieżącego miesiąca
    - Grupujemy je day -> sales_sum, day -> cost_sum
    - Wyświetlamy wykres w dashboard.html
    """
    today = date.today()
    current_year_month = today.strftime("%Y-%m")
    # Ile dni w obecnym miesiącu
    _, num_days_in_month = calendar.monthrange(today.year, today.month)

    daily_sales = [0.0] * num_days_in_month
    daily_costs = [0.0] * num_days_in_month

    sales = Sale.query.all()
    costs = Cost.query.all()

    for s in sales:
        if s.date and s.date.startswith(current_year_month):
            day_str = s.date[8:10]  # np. '05'
            try:
                day_int = int(day_str)
                daily_sales[day_int - 1] += (s.gotowka + s.przelew + s.zaplacono)
            except:
                pass

    for c in costs:
        if c.date and c.date.startswith(current_year_month):
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
        current_year_month=current_year_month
    )


if __name__ == '__main__':
    app.run(debug=True)

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
    return render_template('edit_sale.html', sale=sale)

@app.route('/edit_cost/<int:cost_id>', methods=['GET', 'POST'])
@login_required
def edit_cost(cost_id):
    cost = Cost.query.get_or_404(cost_id)
    if request.method == 'POST':
        cost.date = request.form['date']
        cost.category = request.form['category']
        cost.description = request.form['description']
        cost.amount = float(request.form['amount'] or 0)
        cost.payment_method = request.form['payment_method']
        db.session.commit()
        return redirect(url_for('costs_list'))
    return render_template('edit_cost.html', cost=cost)
    return render_template('edit_cost.html', cost=cost)

@app.route('/delete_cost/<int:cost_id>', methods=['POST'])
@login_required
def delete_cost(cost_id):
    cost = Cost.query.get_or_404(cost_id)
    db.session.delete(cost)
    db.session.commit()
    return redirect(url_for('costs_list'))

@app.route('/delete_sale/<int:sale_id>', methods=['POST'])
@login_required
def delete_sale(sale_id):
    sale = Sale.query.get_or_404(sale_id)
    db.session.delete(sale)
    db.session.commit()
    return redirect(url_for('sales_list'))

@app.route('/cost_summary', methods=['GET'])
@login_required
def cost_summary():
    # Pobranie parametrów month i year z GET (domyślnie bieżący miesiąc i rok)
    today = date.today()
    current_year = today.year
    current_month = today.month

    selected_year = request.args.get('year', current_year, type=int)
    selected_month = request.args.get('month', current_month, type=int)
    
    # Sformatuj wybrany rok i miesiąc
    selected_year_month = f"{selected_year}-{selected_month:02d}"

    # Grupowanie kosztów według kategorii dla wybranego miesiąca
    costs = Cost.query.filter(Cost.date.startswith(selected_year_month)).all()
    summary = {}
    for cost in costs:
        category = cost.category
        summary[category] = summary.get(category, 0) + cost.amount

    return render_template(
        'cost_summary.html',
        summary=summary,
        selected_year=selected_year,
        selected_month=selected_month
    )


@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        # Add a new category
        new_category = request.form.get('category_name')
        if new_category and new_category not in global_categories:
            global_categories.append(new_category)

        # Remove a category
        category_to_remove = request.form.get('delete_category_name')
        if category_to_remove in global_categories:
            global_categories.remove(category_to_remove)

    return render_template('settings.html', categories=global_categories)



@app.route('/manage_users', methods=['GET', 'POST'])
@login_required
@role_required('manage_users')
def manage_users():
    if request.method == 'POST':
        # Handle updating permissions
        for user in User.query.all():
            # Remove existing user-specific permissions
            RolePermissions.query.filter_by(user_id=user.id).delete()

            # Add new permissions based on submitted checkboxes
            permissions = request.form.getlist(f"permissions_{user.id}")
            for permission in permissions:
                new_permission = RolePermissions(user_id=user.id, permission=permission, role=None)
                db.session.add(new_permission)
        
        db.session.commit()
        # Debugging: Print the current RolePermissions table
        all_permissions = RolePermissions.query.all()
        print("Aktualne dane w tabeli RolePermissions:")
        for perm in all_permissions:
            print(f"User ID: {perm.user_id}, Permission: {perm.permission}, Role: {perm.role}")

    # Fetch users and their permissions
    users = User.query.all()
    for user in users:
        user.permissions = [
            perm.permission for perm in RolePermissions.query.filter_by(user_id=user.id).all()
        ]

    return render_template('manage_users.html', users=users)



with app.app_context():
    # Check if an admin exists
    admin_user = User.query.filter_by(role='Administrator').first()
    if not admin_user:
        # Create an admin user if none exists
        admin = User(username='admin', role='Administrator')
        admin.set_password('admin123')  # Default password
        db.session.add(admin)
        db.session.commit()
        print("Utworzono użytkownika Administrator: login=admin, hasło=admin123")



with app.app_context():
    db.create_all()
    # Ensure default permissions exist
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

@app.route('/safe', methods=['GET'])
@login_required
def safe():
    # Pobranie wszystkich transakcji sprzedaży i kosztów
    sales = Sale.query.all()
    costs = Cost.query.filter_by(payment_method="Gotówka").all()

    # Obliczenie aktualnego stanu gotówki w sejfie
    total_cash_in = sum(s.gotowka for s in sales)  # Wszystkie wpłaty gotówkowe ze sprzedaży
    total_cash_out = sum(c.amount for c in costs)  # Wszystkie wypłaty gotówkowe z kosztów

    current_safe_balance = total_cash_in - total_cash_out  # Aktualny stan sejfu

    # Pobranie ostatnich transakcji wpływających na sejf (np. 10 ostatnich operacji)
    recent_transactions = (
        [(s.date, "Sprzedaż", s.gotowka) for s in sales if s.gotowka > 0] +
        [(c.date, "Koszt", -c.amount) for c in costs]
    )
    recent_transactions.sort(reverse=True, key=lambda x: x[0])  # Sortowanie według daty malejąco
    recent_transactions = recent_transactions[:10]  # Ograniczenie do 10 ostatnich wpisów

    return render_template(
        'safe.html',
        current_safe_balance=current_safe_balance,
        recent_transactions=recent_transactions
    )


    # Obliczanie salda przelewów
    total_transfer_in = db.session.query(db.func.sum(Sale.przelew)).scalar() or 0
    total_transfer_out = db.session.query(db.func.sum(Cost.amount)
                                          .filter(Cost.payment_method == "Przelew")).scalar() or 0
    saldo_przelewow = total_transfer_in - total_transfer_out

    # Obsługa formularza wpłat/wypłat do/z bankomatu
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        transaction_type = request.form.get('type')

        if transaction_type == 'wpłata':  # Wpłata do bankomatu (zmniejsza sejf, zwiększa przelew)
            current_safe_balance -= amount
            saldo_przelewow += amount
        elif transaction_type == 'wypłata':  # Wypłata z bankomatu (zwiększa sejf, zmniejsza przelew)
            current_safe_balance += amount
            saldo_przelewow -= amount

        # Dodanie transakcji do bazy danych
        new_transaction = SafeTransaction(date=date.today().strftime("%Y-%m-%d"),
                                          type=transaction_type, amount=amount)
        db.session.add(new_transaction)
        db.session.commit()

        return redirect(url_for('sejf_saldo'))

    # Pobranie ostatnich transakcji sejf <-> bankomat
    transactions = SafeTransaction.query.order_by(SafeTransaction.date.desc()).limit(10).all()

    return render_template('sejf_saldo.html', 
                           current_safe_balance=current_safe_balance, 
                           saldo_przelewow=saldo_przelewow, 
                           transactions=transactions)


    # Obliczanie salda przelewów
    total_transfer_in = db.session.query(db.func.sum(Sale.przelew)).scalar() or 0
    total_transfer_out = db.session.query(db.func.sum(Cost.amount)
                                          .filter(Cost.payment_method == "Przelew")).scalar() or 0
    saldo_przelewow = total_transfer_in - total_transfer_out

    # Obsługa formularza wpłat/wypłat do/z bankomatu
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        transaction_type = request.form.get('type')

        if amount > 0:  # Tylko jeśli kwota jest dodatnia
            if transaction_type == 'wpłata':  # Wpłata do bankomatu
                new_transaction = SafeTransaction(date=date.today().strftime("%Y-%m-%d"), 
                                                  type="wpłata", 
                                                  amount=amount)
                db.session.add(new_transaction)
                db.session.commit()

            elif transaction_type == 'wypłata':  # Wypłata z bankomatu
                new_transaction = SafeTransaction(date=date.today().strftime("%Y-%m-%d"), 
                                                  type="wypłata", 
                                                  amount=amount)
                db.session.add(new_transaction)
                db.session.commit()

        return redirect(url_for('sejf_saldo'))

    # Pobranie ostatnich transakcji sejf <-> bankomat
    transactions = SafeTransaction.query.order_by(SafeTransaction.date.desc()).limit(10).all()

    return render_template('sejf_saldo.html', 
                           current_safe_balance=current_safe_balance, 
                           saldo_przelewow=saldo_przelewow, 
                           transactions=transactions)


    # Pobranie wszystkich wpłat i wypłat do/z bankomatu
    total_safe_transactions_in = db.session.query(db.func.sum(SafeTransaction.amount)
                                                  .filter(SafeTransaction.type == "wypłata")).scalar() or 0
    total_safe_transactions_out = db.session.query(db.func.sum(SafeTransaction.amount)
                                                   .filter(SafeTransaction.type == "wpłata")).scalar() or 0

    # Nowe saldo sejfu uwzględniające operacje wpłaty/wypłaty do bankomatu
    current_safe_balance = total_cash_in - total_cash_out + total_safe_transactions_in - total_safe_transactions_out

    # Obsługa formularza wpłat/wypłat do/z bankomatu
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        transaction_type = request.form.get('type')

        if amount > 0:  # Tylko jeśli kwota jest dodatnia
            new_transaction = SafeTransaction(date=date.today().strftime("%Y-%m-%d"), 
                                              type=transaction_type, 
                                              amount=amount)
            db.session.add(new_transaction)
            db.session.commit()

        return redirect(url_for('sejf_saldo'))

    # Pobranie ostatnich transakcji sejf <-> bankomat
    transactions = SafeTransaction.query.order_by(SafeTransaction.date.desc()).limit(10).all()

    return render_template('sejf_saldo.html', 
                           current_safe_balance=current_safe_balance, 
                           transactions=transactions)


@app.route('/sejf_saldo', methods=['GET', 'POST'])
@login_required
def sejf_saldo():
    # Obliczanie aktualnego salda sejfu (gotówki)
    total_cash_in = db.session.query(db.func.sum(Sale.gotowka)).scalar() or 0
    total_cash_out = db.session.query(db.func.sum(Cost.amount)
                                      .filter(Cost.payment_method == "Gotówka")).scalar() or 0

    # Pobranie wszystkich wpłat i wypłat do/z bankomatu
    total_safe_transactions_in = db.session.query(db.func.sum(SafeTransaction.amount)
                                                  .filter(SafeTransaction.type == "wypłata")).scalar() or 0
    total_safe_transactions_out = db.session.query(db.func.sum(SafeTransaction.amount)
                                                   .filter(SafeTransaction.type == "wpłata")).scalar() or 0

    # Nowe saldo sejfu uwzględniające operacje wpłaty/wypłaty do bankomatu
    current_safe_balance = total_cash_in - total_cash_out + total_safe_transactions_in - total_safe_transactions_out

    # Obsługa formularza wpłat/wypłat do/z bankomatu
    if request.method == 'POST':
        amount = float(request.form.get('amount', 0))
        transaction_type = request.form.get('type')

        if amount > 0:  # Tylko jeśli kwota jest dodatnia
            new_transaction = SafeTransaction(date=date.today().strftime("%Y-%m-%d"), 
                                              type=transaction_type, 
                                              amount=amount)
            db.session.add(new_transaction)
            db.session.commit()

        return redirect(url_for('sejf_saldo'))

    # Pobranie transakcji sejfu (sprzedaż i koszty gotówkowe)
    sales = Sale.query.filter(Sale.gotowka > 0).all()
    costs = Cost.query.filter(Cost.payment_method == "Gotówka").all()
    safe_transactions = SafeTransaction.query.all()

    # Połączenie danych w jedną listę transakcji
    transactions = []

    for sale in sales:
        transactions.append({
            "date": sale.date,
            "type": "Sprzedaż",
            "amount": sale.gotowka
        })

    for cost in costs:
        transactions.append({
            "date": cost.date,
            "type": "Wydatek",
            "amount": -cost.amount  # Koszty są ujemne
        })

    for transaction in safe_transactions:
        transactions.append({
            "date": transaction.date,
            "type": transaction.type,
            "amount": transaction.amount if transaction.type == "wypłata" else -transaction.amount
        })

    # Sortowanie transakcji według daty (najnowsze pierwsze)
    transactions = sorted(transactions, key=lambda x: x["date"], reverse=True)

    return render_template('sejf_saldo.html', 
                           current_safe_balance=current_safe_balance, 
                           transactions=transactions)
