from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_login import UserMixin
from flask import url_for
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id              = db.Column(db.Integer, primary_key=True)
    first_name      = db.Column(db.String(100), nullable=False)
    last_name       = db.Column(db.String(100), nullable=False)
    email           = db.Column(db.String(100), unique=True, nullable=False)
    address         = db.Column(db.Text, nullable=True)
    password        = db.Column(db.String(200), nullable=True)
    credits         = db.Column(db.Integer, default=0)
    is_admin        = db.Column(db.Boolean, default=False)
    is_password_set = db.Column(db.Boolean, default=False)
    orders          = db.relationship('Order', backref='user', lazy=True)
    carts           = db.relationship('Cart', backref='user', lazy=True)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password, password)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)
    is_active = db.Column(db.Boolean, default=True)

    @property
    def image_url(self):
        if self.image_filename:
            return url_for('static', filename='uploads/' + self.image_filename)
        return url_for('static', filename='img/no-image.png')  # Fallback obrázek


class Shipping(db.Model):
    __tablename__ = 'shipping'
    id          = db.Column(db.Integer, primary_key=True)
    name        = db.Column(db.String(100), nullable=False)
    price       = db.Column(db.Integer, nullable=False)      # Cena v Kč
    description = db.Column(db.String(200), nullable=True)   # Popis dopravy
    active      = db.Column(db.Boolean, default=True)        # Je aktivní?
    orders      = db.relationship('Order', backref='shipping', lazy=True)


class Order(db.Model):
    id               = db.Column(db.Integer, primary_key=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    shipping_id      = db.Column(db.Integer, db.ForeignKey('shipping.id'), nullable=False)
    shipping_address = db.Column(db.String(200), nullable=True)
    total_price      = db.Column(db.Integer, nullable=False)  # Celková cena v Kč
    credits_used     = db.Column(db.Integer, default=0)
    final_price      = db.Column(db.Integer, nullable=False)  # Po odečtení kreditů
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)
    is_completed     = db.Column(db.Boolean, default=False)
    status           = db.Column(db.String(20), nullable=False, default='new')
    note             = db.Column(db.Text, nullable=True)          # poznámka od uživatele
    admin_note       = db.Column(db.Text, nullable=True)          # interní poznámka
    items            = db.relationship('OrderItem', backref='order', lazy=True)


class OrderItem(db.Model):
    id         = db.Column(db.Integer, primary_key=True)
    order_id   = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity   = db.Column(db.Integer, nullable=False)
    price      = db.Column(db.Integer, nullable=False)  # Jednotková cena v době objednávky
    # umožní v šabloně volat item.product.name
    product    = relationship('Product', backref='order_items', lazy=True)

class Cart(db.Model):
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    items   = db.relationship('CartItem', backref='cart', lazy=True)


class CartItem(db.Model):
    __tablename__ = 'cart_item'

    id         = db.Column(db.Integer, primary_key=True)
    cart_id    = db.Column(db.Integer, db.ForeignKey('cart.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)

    # ORM vztah na produkt
    product    = db.relationship(
        'Product',
        backref=db.backref('cart_items', lazy=True),
        lazy=True
    )

    # Jediná deklarace množství
    quantity   = db.Column(db.Integer, nullable=False)