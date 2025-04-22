# models.py

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(64), default='Pracownik')  # np. Pracownik / Manager / Administrator
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Sale(db.Model):
    __tablename__ = 'sale'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))  # Format YYYY-MM-DD
    gotowka = db.Column(db.Float, default=0.0)
    przelew = db.Column(db.Float, default=0.0)
    zaplacono = db.Column(db.Float, default=0.0)

    # Który użytkownik dodał sprzedaż
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='sales')

class Cost(db.Model):
    __tablename__ = 'cost'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    category = db.Column(db.String(100))
    description = db.Column(db.String(255))
    amount = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(50))  # "Gotówka" / "Przelew"

    # Który użytkownik dodał koszt
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='costs')

class RolePermissions(db.Model):
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(64), nullable=True)        # np. "Administrator", "Manager"
    permission = db.Column(db.String(64), nullable=False) # np. "add_cost", "manage_users"
    user_id = db.Column(db.Integer, nullable=True)        # user-specific permission

class CostCategory(db.Model):
    __tablename__ = 'cost_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=False, nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('cost_category.id'), nullable=True)
    parent = db.relationship('CostCategory', remote_side=[id], backref=db.backref('subcategories', cascade='all, delete-orphan'))
    parent_id = db.Column(db.Integer, db.ForeignKey('cost_category.id'), nullable=True)
    parent = db.relationship('CostCategory', remote_side=[id], backref=db.backref('subcategories', cascade='all, delete-orphan'))

class SafeTransaction(db.Model):
    __tablename__ = 'safe_transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))       # Format YYYY-MM-DD
    type = db.Column(db.String(50))       # "wpłata" / "wypłata"
    amount = db.Column(db.Float, default=0.0)
    # description = db.Column(db.String(200))  # <- Możesz dodać opis, jeśli potrzebujesz

    # Który użytkownik wykonał operację sejfu
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='safe_transactions')

class AuditLog(db.Model):
    __tablename__ = 'audit_log'
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, nullable=False, default=db.func.now())
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    user = db.relationship('User', backref='audit_logs')
    action = db.Column(db.String(20), nullable=False)
    object_type = db.Column(db.String(50), nullable=False)
    object_id = db.Column(db.Integer, nullable=True)
    details = db.Column(db.Text, nullable=True)

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price_per_kg = db.Column(db.Float, nullable=False)

class Dish(db.Model):
    __tablename__ = 'dish'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    sale_price = db.Column(db.Float, nullable=False)
    recipe_items = db.relationship('RecipeItem', backref='dish', cascade='all, delete-orphan')

class RecipeItem(db.Model):
    __tablename__ = 'recipe_item'
    id = db.Column(db.Integer, primary_key=True)
    dish_id = db.Column(db.Integer, db.ForeignKey('dish.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    weight_kg = db.Column(db.Float, nullable=False)
    product = db.relationship('Product')