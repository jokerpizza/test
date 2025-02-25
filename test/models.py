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

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='sales')

class CostCategory(db.Model):
    __tablename__ = 'cost_category'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    # Relacja do podkategorii
    subcategories = db.relationship('CostSubcategory', backref='category', cascade="all, delete-orphan")

class CostSubcategory(db.Model):
    __tablename__ = 'cost_subcategory'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    # Każda podkategoria należy do jednej kategorii
    category_id = db.Column(db.Integer, db.ForeignKey('cost_category.id'), nullable=False)

class Cost(db.Model):
    __tablename__ = 'cost'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))
    description = db.Column(db.String(255))
    amount = db.Column(db.Float, default=0.0)
    payment_method = db.Column(db.String(50))  # "Gotówka" / "Przelew"

    # Podkategoria (powiązana z tabelą cost_subcategory)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('cost_subcategory.id'))
    subcategory = db.relationship('CostSubcategory')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='costs')

class RolePermissions(db.Model):
    __tablename__ = 'role_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    role = db.Column(db.String(64), nullable=True)
    permission = db.Column(db.String(64), nullable=False)
    user_id = db.Column(db.Integer, nullable=True)

class SafeTransaction(db.Model):
    __tablename__ = 'safe_transaction'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10))       
    type = db.Column(db.String(50))       # "wpłata" / "wypłata"
    amount = db.Column(db.Float, default=0.0)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db
