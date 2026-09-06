from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import string

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """User model"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20), nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_active = db.Column(db.Boolean, default=True, index=True)
    is_verified = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    
    # Driver specific
    is_available = db.Column(db.Boolean, default=False, index=True)
    current_lat = db.Column(db.Float)
    current_lng = db.Column(db.Float)
    vehicle_info = db.Column(db.String(200))
    license_number = db.Column(db.String(50))
    
    # Restaurant specific
    restaurant_name = db.Column(db.String(100))
    restaurant_address = db.Column(db.Text)
    restaurant_lat = db.Column(db.Float)
    restaurant_lng = db.Column(db.Float)
    
    # Wilaya (State in Algeria)
    wilaya = db.Column(db.String(50))
    commune = db.Column(db.String(50))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Restaurant(db.Model):
    """Restaurant model"""
    __tablename__ = 'restaurants'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    name = db.Column(db.String(100), nullable=False)
    name_ar = db.Column(db.String(100), nullable=False, index=True)
    description_ar = db.Column(db.Text)
    
    address = db.Column(db.Text, nullable=False)
    wilaya = db.Column(db.String(50), nullable=False, index=True)
    commune = db.Column(db.String(50))
    
    latitude = db.Column(db.Float, nullable=False, index=True)
    longitude = db.Column(db.Float, nullable=False, index=True)
    
    phone = db.Column(db.String(20))
    image_url = db.Column(db.String(500), nullable=True, default=None)
    cuisine = db.Column(db.String(50), index=True, default='أخرى')
    is_open = db.Column(db.Boolean, default=True, index=True)
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    
    commission_rate = db.Column(db.Float, default=10.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('restaurant_profile', uselist=False))
    menu_items = db.relationship('MenuItem', backref='restaurant', lazy='dynamic', cascade='all, delete-orphan')
    orders = db.relationship('Order', backref='restaurant', lazy='dynamic')

    def __repr__(self):
        return f'<Restaurant {self.name_ar}>'


class MenuItem(db.Model):
    """Menu item model"""
    __tablename__ = 'menu_items'
    
    id = db.Column(db.Integer, primary_key=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    
    name_ar = db.Column(db.String(100), nullable=False)
    description_ar = db.Column(db.Text)
    
    price = db.Column(db.Float, nullable=False)
    
    category_ar = db.Column(db.String(50), index=True)
    
    # Image fields
    image_url = db.Column(db.String(255))  # Add this line
    image_thumbnail = db.Column(db.String(255))  # Add this line
    
    is_available = db.Column(db.Boolean, default=True, index=True)
    rating = db.Column(db.Float, default=0.0)
    total_reviews = db.Column(db.Integer, default=0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<MenuItem {self.name_ar}>'

class Order(db.Model):
    """Order model"""
    __tablename__ = 'orders'
    
    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(20), unique=True, nullable=False, index=True)
    
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    restaurant_id = db.Column(db.Integer, db.ForeignKey('restaurants.id'), nullable=False, index=True)
    
    total_amount = db.Column(db.Float, nullable=False)
    delivery_fee = db.Column(db.Float, default=100.0)
    platform_fee = db.Column(db.Float, default=50.0)
    final_amount = db.Column(db.Float, nullable=False)
    
    delivery_address = db.Column(db.Text, nullable=False)
    delivery_wilaya = db.Column(db.String(50))
    delivery_commune = db.Column(db.String(50))
    delivery_lat = db.Column(db.Float, nullable=False)
    delivery_lng = db.Column(db.Float, nullable=False)
    
    status = db.Column(db.String(20), default='pending', index=True)
    
    payment_method = db.Column(db.String(20), nullable=False, index=True)
    payment_status = db.Column(db.String(20), default='pending', index=True)
    cancelled_by = db.Column(db.String(20))
    cancel_reason = db.Column(db.String(200))
    
    verification_code = db.Column(db.String(6), index=True)
    is_verified = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    confirmed_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    
    customer_notes = db.Column(db.Text)
    
    customer = db.relationship('User', foreign_keys=[customer_id], backref='customer_orders')
    driver = db.relationship('User', foreign_keys=[driver_id], backref='driver_orders')
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    def generate_verification_code(self):
        self.verification_code = ''.join(random.choices(string.digits, k=6))
        return self.verification_code
    
    def calculate_final_amount(self):
        self.final_amount = self.total_amount + self.delivery_fee + self.platform_fee
        return self.final_amount

    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    """Order item model"""
    __tablename__ = 'order_items'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey('menu_items.id'), nullable=False)
    
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    
    menu_item = db.relationship('MenuItem')

    def __repr__(self):
        return f'<OrderItem {self.id}>'


class Notification(db.Model):
    """Notification model"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id',ondelete='CASCADE'), nullable=True, index=True)
    
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    
    is_read = db.Column(db.Boolean, default=False, index=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    user = db.relationship('User', backref='notifications')

    def __repr__(self):
        return f'<Notification {self.id}>'


class Wallet(db.Model):
    """Wallet model"""
    __tablename__ = 'wallets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    
    balance = db.Column(db.Float, default=0.0)
    total_earned = db.Column(db.Float, default=0.0)
    
    user = db.relationship('User', backref=db.backref('wallet', uselist=False))

    def __repr__(self):
        return f'<Wallet User:{self.user_id} Balance:{self.balance} DZD>'


class PricingSetting(db.Model):
    """إعدادات التسعير — صف واحد يتحكّم فيه المشرف من لوحة الإدارة"""
    __tablename__ = 'pricing_settings'

    id = db.Column(db.Integer, primary_key=True)

    # الرسوم الأساسية
    base_fee       = db.Column(db.Float, default=200.0)   # رسم التوصيل الثابت
    per_km         = db.Column(db.Float, default=0.0)     # زيادة عن كل كيلومتر
    platform_fee   = db.Column(db.Float, default=50.0)    # رسم خدمة المنصة
    commission     = db.Column(db.Float, default=10.0)    # عمولة المنصة على المطعم (٪)

    # حدود رسم التوصيل بعد كل الحسابات
    min_fee        = db.Column(db.Float, default=150.0)
    max_fee        = db.Column(db.Float, default=600.0)

    # سياسة العرض والطلب
    surge_enabled  = db.Column(db.Boolean, default=True)
    surge_threshold= db.Column(db.Float, default=1.5)   # طلبات لكل سائق متاح
    surge_step     = db.Column(db.Float, default=0.20)  # نسبة الزيادة عن كل درجة
    surge_max      = db.Column(db.Float, default=2.0)   # أقصى مضاعف

    # مكافأة السائق عند ندرة السائقين (تُضاف لحصّته من الزيادة)
    driver_share   = db.Column(db.Float, default=100.0)  # ٪ من الزيادة تذهب للسائق

    updated_at     = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @staticmethod
    def get():
        """يُرجع صف الإعدادات، وينشئه بالقيم الافتراضية إن لم يوجد"""
        st = PricingSetting.query.get(1)
        if not st:
            st = PricingSetting(id=1)
            db.session.add(st)
            db.session.commit()
        return st

    def __repr__(self):
        return f'<PricingSetting base={self.base_fee} surge={self.surge_enabled}>'


class Review(db.Model):
    """تقييم بنجوم وتعليق — للمطعم أو للسائق، مرتبط بطلب مسلَّم"""
    __tablename__ = 'reviews'

    id          = db.Column(db.Integer, primary_key=True)
    order_id    = db.Column(db.Integer, db.ForeignKey('orders.id'), nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)

    target_type = db.Column(db.String(12), nullable=False, index=True)   # restaurant | driver
    target_id   = db.Column(db.Integer, nullable=False, index=True)

    stars       = db.Column(db.Integer, nullable=False)                  # من 1 إلى 5
    comment     = db.Column(db.String(400))
    created_at  = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    order    = db.relationship('Order', backref=db.backref('reviews', lazy='dynamic'))
    customer = db.relationship('User', foreign_keys=[customer_id])

    __table_args__ = (
        db.UniqueConstraint('order_id', 'target_type', name='uq_review_order_target'),
    )

    def __repr__(self):
        return f'<Review {self.target_type}#{self.target_id} {self.stars}★>'
