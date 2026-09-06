from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from config import Config
from models import *
from datetime import datetime
from models import db, User, Restaurant, MenuItem, Order, OrderItem, Wallet  
from config import Config
import socket
import sys
import os
from flask_sqlalchemy import SQLAlchemy
import random
from flask import send_from_directory


# Add current directory to path FIRST
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)

# Create necessary directories immediately
os.makedirs(os.path.join(current_dir, 'database'), exist_ok=True)
os.makedirs(os.path.join(current_dir, 'static', 'images', 'uploads'), exist_ok=True)
os.makedirs(os.path.join(current_dir, 'templates', 'errors'), exist_ok=True)

# Load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except:
    pass



app = Flask(__name__)
app.config.from_object(Config)

# مفتاح الجلسات: لا نقبل القيمة الاحتياطية في الإنتاج
if os.environ.get('FLASK_ENV') == 'production' and not os.environ.get('SECRET_KEY'):
    raise RuntimeError('SECRET_KEY غير مضبوط — لا يمكن التشغيل في الإنتاج بمفتاح افتراضي')

db.init_app(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ── حدّ محاولات الدخول: خمس محاولات فاشلة لكل عنوان في خمس دقائق ──
_login_attempts = {}
LOGIN_MAX_TRIES = 5
LOGIN_WINDOW    = 300  # ثانية


def login_throttled(key):
    """هل تجاوز هذا العنوان عدد المحاولات المسموح؟"""
    import time
    now = time.time()
    tries = [t for t in _login_attempts.get(key, []) if now - t < LOGIN_WINDOW]
    _login_attempts[key] = tries
    return len(tries) >= LOGIN_MAX_TRIES


def record_login_failure(key):
    import time
    _login_attempts.setdefault(key, []).append(time.time())
    if len(_login_attempts) > 5000:      # تنظيف بسيط للذاكرة
        _login_attempts.clear()


def admin_required(f):
    """يمنع أي وصول لمسارات الإدارة من غير المشرف"""
    from functools import wraps

    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('سجّل الدخول أولاً', 'warning')
            return redirect(url_for('login'))
        if current_user.role != 'admin':
            flash('لا تملك صلاحية الوصول إلى هذه الصفحة', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return wrapper




# ============================================
# upload images  
# ============================================

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads', 'restaurants')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# ============================================
# images ROUTES
# ============================================

@app.route('/admin/restaurant/<int:restaurant_id>/upload-image', methods=['POST'])
@login_required
def upload_restaurant_image(restaurant_id):
    if current_user.role != 'admin':
        flash('ليس لديك صلاحية', 'danger')
        return redirect(url_for('index'))

    restaurant = Restaurant.query.get_or_404(restaurant_id)

    if 'image' not in request.files:
        flash('لا توجد صورة', 'danger')
        return redirect(url_for('admin_dashboard'))

    file = request.files['image']

    if file.filename == '':
        flash('اضف صورة', 'danger')
        return redirect(url_for('admin_dashboard'))

    ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}

    if file and '.' in file.filename and \
       file.filename.rsplit('.', 1)[1].lower() in ALLOWED:

        ext      = file.filename.rsplit('.', 1)[1].lower()
        filename = f"restaurant_{restaurant_id}.{ext}"
        folder   = os.path.join(app.root_path, 'static', 'uploads', 'restaurants')
        os.makedirs(folder, exist_ok=True)

        # delete old image
        for old_ext in ALLOWED:
            old = os.path.join(folder, f"restaurant_{restaurant_id}.{old_ext}")
            if os.path.exists(old):
                os.remove(old)

        # save new image
        file.save(os.path.join(folder, filename))
        restaurant.image_url = f"/static/uploads/restaurants/{filename}"
        db.session.commit()

        flash(f'✅ تم رفع صورة {restaurant.name_ar} بنجاح', 'success')
    else:
        flash('نوع الصورة غير مدعوم – استخدم PNG JPG WEBP', 'danger')

    return redirect(request.referrer or url_for('admin_panel'))





# ============================================
# DATABASE INITIALIZATION
# ============================================

# ============================================
# ولايات الجزائر الـ58 (المرسوم 2019) وتصنيفات المطاعم
# ============================================

WILAYAS = [
    ("01", "أدرار"), ("02", "الشلف"), ("03", "الأغواط"), ("04", "أم البواقي"),
    ("05", "باتنة"), ("06", "بجاية"), ("07", "بسكرة"), ("08", "بشار"),
    ("09", "البليدة"), ("10", "البويرة"), ("11", "تمنراست"), ("12", "تبسة"),
    ("13", "تلمسان"), ("14", "تيارت"), ("15", "تيزي وزو"), ("16", "الجزائر"),
    ("17", "الجلفة"), ("18", "جيجل"), ("19", "سطيف"), ("20", "سعيدة"),
    ("21", "سكيكدة"), ("22", "سيدي بلعباس"), ("23", "عنابة"), ("24", "قالمة"),
    ("25", "قسنطينة"), ("26", "المدية"), ("27", "مستغانم"), ("28", "المسيلة"),
    ("29", "معسكر"), ("30", "ورقلة"), ("31", "وهران"), ("32", "البيض"),
    ("33", "إليزي"), ("34", "برج بوعريريج"), ("35", "بومرداس"), ("36", "الطارف"),
    ("37", "تندوف"), ("38", "تيسمسيلت"), ("39", "الوادي"), ("40", "خنشلة"),
    ("41", "سوق أهراس"), ("42", "تيبازة"), ("43", "ميلة"), ("44", "عين الدفلى"),
    ("45", "النعامة"), ("46", "عين تموشنت"), ("47", "غرداية"), ("48", "غليزان"),
    ("49", "تيميمون"), ("50", "برج باجي مختار"), ("51", "أولاد جلال"),
    ("52", "بني عباس"), ("53", "عين صالح"), ("54", "عين قزام"), ("55", "تقرت"),
    ("56", "جانت"), ("57", "المغير"), ("58", "المنيعة"),
]

WILAYA_NAMES = [name for _, name in WILAYAS]

# تصنيفات المطاعم — تُستعمل في التسجيل وفي فلترة الصفحة الرئيسية
CUISINES = [
    "مأكولات جزائرية",
    "فاست فود",
    "بيتزا",
    "برغر وساندويتشات",
    "مشاوي",
    "مأكولات بحرية",
    "مأكولات شرقية",
    "مأكولات إيطالية",
    "مأكولات آسيوية",
    "حلويات ومرطبات",
    "مخبزة وفطائر",
    "مشروبات وعصائر",
    "أخرى",
]

DEFAULT_CUISINE = "أخرى"

# أسماء الحالات بالعربية — مصدر واحد لكل الواجهات
STATUS_AR = {
    'pending':    'بانتظار المطعم',
    'confirmed':  'قيد التحضير',
    'ready':      'جاهز',
    'assigned':   'سائق في الطريق للمطعم',
    'picked_up':  'في الطريق للزبون',
    'delivering': 'في الطريق للزبون',
    'delivered':  'تم التسليم',
    'completed':  'مكتمل',
    'cancelled':  'ملغى',
}


# ============================================
# محرّك التسعير الديناميكي (العرض والطلب)
# ============================================

def _haversine_km(lat1, lng1, lat2, lng2):
    """المسافة بالكيلومترات بين نقطتين"""
    from math import radians, sin, cos, asin, sqrt
    try:
        lat1, lng1, lat2, lng2 = map(float, (lat1, lng1, lat2, lng2))
    except (TypeError, ValueError):
        return 0.0
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng / 2) ** 2
    return 6371.0 * 2 * asin(min(1.0, sqrt(a)))


def demand_state():
    """حالة السوق الآن: كم طلب ينتظر مقابل كم سائق متاح"""
    waiting = Order.query.filter(
        Order.status.in_(['pending', 'confirmed', 'ready'])
    ).count()
    drivers = User.query.filter_by(role='driver', is_available=True, is_active=True).count()
    ratio = waiting / drivers if drivers else (float(waiting) if waiting else 0.0)
    return {'waiting_orders': waiting, 'available_drivers': drivers, 'ratio': round(ratio, 2)}


def surge_multiplier(settings=None, state=None):
    """مضاعف السعر حسب الضغط: كل درجة فوق العتبة تزيد نسبة ثابتة"""
    st = settings or PricingSetting.get()
    if not st.surge_enabled:
        return 1.0, (state or demand_state())
    state = state or demand_state()
    ratio = state['ratio']
    if ratio <= st.surge_threshold:
        return 1.0, state
    import math
    steps = math.ceil(ratio - st.surge_threshold)
    mult = 1.0 + (st.surge_step * steps)
    return round(min(mult, st.surge_max), 2), state


def quote_delivery(restaurant=None, dest_lat=None, dest_lng=None):
    """تسعيرة توصيل كاملة: الرسم، رسم الخدمة، المضاعف، وحصّة السائق"""
    st = PricingSetting.get()

    km = 0.0
    if restaurant is not None and dest_lat is not None and dest_lng is not None:
        km = _haversine_km(restaurant.latitude, restaurant.longitude, dest_lat, dest_lng)

    base = st.base_fee + (st.per_km * km)
    mult, state = surge_multiplier(st)
    fee = base * mult
    fee = max(st.min_fee, min(st.max_fee, fee))
    fee = round(fee / 10.0) * 10  # تقريب لأقرب 10 د.ج

    extra = max(0.0, fee - st.base_fee)
    driver_bonus = round(extra * (st.driver_share / 100.0))

    return {
        'delivery_fee': float(fee),
        'platform_fee': float(st.platform_fee),
        'commission': float(st.commission),
        'distance_km': round(km, 2),
        'multiplier': mult,
        'surge': mult > 1.0,
        'driver_bonus': driver_bonus,
        'waiting_orders': state['waiting_orders'],
        'available_drivers': state['available_drivers'],
        'ratio': state['ratio'],
    }


# أسماء الولايات القديمة باللاتينية → المقابل العربي (توحيد البيانات القديمة)
LEGACY_WILAYA_MAP = {
    "Alger": "الجزائر", "Oran": "وهران", "Constantine": "قسنطينة", "Annaba": "عنابة",
    "Blida": "البليدة", "Batna": "باتنة", "Djelfa": "الجلفة", "Sétif": "سطيف",
    "Setif": "سطيف", "Sidi Bel Abbès": "سيدي بلعباس", "Biskra": "بسكرة",
    "Tébessa": "تبسة", "El Oued": "الوادي", "Skikda": "سكيكدة", "Tiaret": "تيارت",
    "Béjaïa": "بجاية", "Tlemcen": "تلمسان", "Ouargla": "ورقلة", "Béchar": "بشار",
    "Mostaganem": "مستغانم", "Bordj Bou Arreridj": "برج بوعريريج", "Chlef": "الشلف",
    "Souk Ahras": "سوق أهراس", "El Tarf": "الطارف", "Jijel": "جيجل", "Saïda": "سعيدة",
    "Khenchela": "خنشلة", "Oum El Bouaghi": "أم البواقي", "Médéa": "المدية",
    "Mascara": "معسكر", "Ain Defla": "عين الدفلى", "Naâma": "النعامة",
    "Ain Témouchent": "عين تموشنت", "Ghardaïa": "غرداية", "Relizane": "غليزان",
    "Timimoun": "تيميمون", "Bordj Badji Mokhtar": "برج باجي مختار",
    "Ouled Djellal": "أولاد جلال", "Béni Abbès": "بني عباس", "In Salah": "عين صالح",
    "In Guezzam": "عين قزام", "Touggourt": "تقرت", "Djanet": "جانت",
    "El M'Ghair": "المغير", "El Meniaa": "المنيعة",
}


def ensure_schema():
    """ترحيل خفيف: يضيف الأعمدة الناقصة بلا ما يمسّ البيانات الموجودة.
    يخدم على SQLite (محلياً) و PostgreSQL (على الخادم)."""
    from sqlalchemy import inspect, text
    with app.app_context():
        try:
            insp = inspect(db.engine)
            if 'restaurants' not in insp.get_table_names():
                return
            db.create_all()          # ينشئ جدول pricing_settings إن لم يوجد
            PricingSetting.get()     # يضمن وجود صف الإعدادات
            # أعمدة ناقصة في جداول أخرى
            for table, col, ddl, default in [
                ('menu_items', 'rating',        'FLOAT',   '0'),
                ('menu_items', 'total_reviews', 'INTEGER', '0'),
                ('orders',     'cancelled_by',  'VARCHAR(20)',  'NULL'),
                ('orders',     'cancel_reason', 'VARCHAR(200)', 'NULL'),
                ('users',      'rating',        'FLOAT',        '0'),
                ('users',      'total_reviews', 'INTEGER',      '0'),
                ('restaurants','total_reviews', 'INTEGER',      '0'),
            ]:
                if table in insp.get_table_names():
                    existing = {c['name'] for c in insp.get_columns(table)}
                    if col not in existing:
                        with db.engine.begin() as conn:
                            conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))
                            if default != 'NULL':
                                conn.execute(text(f"UPDATE {table} SET {col} = {default} WHERE {col} IS NULL"))
                        print(f"✅ عمود {col} أُضيف إلى {table}")

            cols = {c['name'] for c in insp.get_columns('restaurants')}
            if 'cuisine' not in cols:
                with db.engine.begin() as conn:
                    conn.execute(text(
                        "ALTER TABLE restaurants ADD COLUMN cuisine VARCHAR(50)"
                    ))
                    conn.execute(text(
                        "UPDATE restaurants SET cuisine = :d WHERE cuisine IS NULL"
                    ), {"d": DEFAULT_CUISINE})
                print("✅ عمود cuisine أُضيف لجدول المطاعم")

            # توحيد أسماء الولايات القديمة (كانت باللاتينية) مع القائمة العربية
            with db.engine.begin() as conn:
                for old, new in LEGACY_WILAYA_MAP.items():
                    conn.execute(
                        text("UPDATE restaurants SET wilaya = :new WHERE wilaya = :old"),
                        {"new": new, "old": old}
                    )
                    conn.execute(
                        text("UPDATE users SET wilaya = :new WHERE wilaya = :old"),
                        {"new": new, "old": old}
                    )
                # البلديات والتصنيفات في البيانات التجريبية القديمة
                for old, new in {"Bab El Oued": "باب الوادي", "Hydra": "حيدرة"}.items():
                    conn.execute(
                        text("UPDATE restaurants SET commune = :new WHERE commune = :old"),
                        {"new": new, "old": old}
                    )
                for name_ar, c in {"مطعم الأصالة": "مأكولات جزائرية",
                                   "فاست فود الوفاء": "فاست فود"}.items():
                    conn.execute(
                        text("UPDATE restaurants SET cuisine = :c "
                             "WHERE name_ar = :n AND (cuisine IS NULL OR cuisine = :d)"),
                        {"c": c, "n": name_ar, "d": DEFAULT_CUISINE}
                    )
        except Exception as e:
            print(f"⚠️  ensure_schema: {e}")


def init_database():
    """Initialize database with Algerian sample data"""
    with app.app_context():
        db.create_all()
    ensure_schema()
    with app.app_context():
        
        # Create admin
        if not User.query.filter_by(email='admin@delivery.dz').first():
            admin = User(
                username='Admin',
                email='admin@delivery.dz',
                phone='0550123456',
                role='admin',
                wilaya='Alger'
            )
            admin.set_password('admin123')
            db.session.add(admin)
        
        # Create sample customer
        if not User.query.filter_by(email='client@test.dz').first():
            customer = User(
                username='أحمد  ',
                email='client@test.dz',
                phone='0770123456',
                role='customer',
                wilaya='Alger',
                commune='Bab El Oued'
            )
            customer.set_password('client123')
            db.session.add(customer)
        
        # Create sample driver
        if not User.query.filter_by(email='chauffeur@test.dz').first():
            driver = User(
                username='  محمد',
                email='chauffeur@test.dz',
                phone='0660123456',
                role='driver',
                is_available=True,
                current_lat=36.7538,
                current_lng=3.0588,
                vehicle_info='موتو  125',
                wilaya='Alger'
            )
            driver.set_password('chauffeur123')
            db.session.add(driver)
        
        # Create sample restaurants
        if not User.query.filter_by(email='restaurant@test.dz').first():
            rest_user = User(
                username='مطعم الأصالة',
                email='restaurant@test.dz',
                phone='0540123456',
                role='restaurant',
                wilaya='Alger'
            )
            rest_user.set_password('restaurant123')
            db.session.add(rest_user)
            db.session.commit()
            
            restaurant = Restaurant(
                user_id=rest_user.id,
                name='Restaurant El Asala',
                name_ar='مطعم الأصالة',
                description_ar='مأكولات جزائرية أصيلة',
                address='شارع ديدوش مراد، الجزائر العاصمة',
                wilaya='الجزائر',
                cuisine='مأكولات جزائرية',
                commune='باب الوادي',
                latitude=36.7538,
                longitude=3.0588,
                phone='0540123456',
                is_open=True
            )
            db.session.add(restaurant)
            db.session.commit()
            
            # Add Algerian menu items
            menu_items = [
                {'name_ar': 'كسكسي بالدجاج', 'price': 800.0, 'category_ar': 'أطباق رئيسية'},
                {'name_ar': 'شربة فريك', 'price': 300.0, 'category_ar': 'شوربة'},
                {'name_ar': 'طاجين زيتون', 'price': 900.0, 'category_ar': 'أطباق رئيسية'},
                {'name_ar': 'بوراك بالجبن', 'price': 400.0, 'category_ar': 'مقبلات'},
                {'name_ar': 'دولما', 'price': 700.0, 'category_ar': 'أطباق رئيسية'},
                {'name_ar': 'مثوم', 'price': 350.0, 'category_ar': 'مقبلات'},
                {'name_ar': 'حراقة', 'price': 250.0, 'category_ar': 'شوربة'},
                {'name_ar': 'شاورما', 'price': 500.0, 'category_ar': 'ساندويتشات'},
                {'name_ar': 'بيتزا مشكلة', 'price': 650.0, 'category_ar': 'بيتزا'},
                {'name_ar': 'طبق مشوي', 'price': 1200.0, 'category_ar': 'مشويات'},
            ]
            
            for item in menu_items:
                menu_item = MenuItem(
                    restaurant_id=restaurant.id,
                    name_ar=item['name_ar'],
                    price=item['price'],
                    category_ar=item['category_ar'],
                    description_ar=f'{item["name_ar"]} طازج وشهي',
                    is_available=True
                )
                db.session.add(menu_item)
        
        # Create second restaurant
        if not User.query.filter_by(email='fastfood@test.dz').first():
            rest_user2 = User(
                username='فاست فود الوفاء',
                email='fastfood@test.dz',
                phone='0550234567',
                role='restaurant',
                wilaya='Alger'
            )
            rest_user2.set_password('restaurant123')
            db.session.add(rest_user2)
            db.session.commit()
            
            restaurant2 = Restaurant(
                user_id=rest_user2.id,
                name='Fast Food El Wafa',
                name_ar='فاست فود الوفاء',
                description_ar='وجبات سريعة لذيذة',
                address='حيدرة، الجزائر',
                wilaya='الجزائر',
                cuisine='فاست فود',
                commune='حيدرة',
                latitude=36.7000,
                longitude=3.0500,
                phone='0550234567',
                is_open=True
            )
            db.session.add(restaurant2)
            db.session.commit()
            
            fastfood_items = [
                {'name_ar': 'برغر بالجبن', 'price': 450.0, 'category_ar': 'برغر'},
                {'name_ar': 'تاكوس دجاج', 'price': 400.0, 'category_ar': 'تاكوس'},
                {'name_ar': 'بيتزا 4 أجبان', 'price': 800.0, 'category_ar': 'بيتزا'},
                {'name_ar': 'سلطة سيزر', 'price': 350.0, 'category_ar': 'سلطات'},
                {'name_ar': 'عصير برتقال طبيعي', 'price': 200.0, 'category_ar': 'مشروبات'},
            ]
            
            for item in fastfood_items:
                menu_item = MenuItem(
                    restaurant_id=restaurant2.id,
                    name_ar=item['name_ar'],
                    price=item['price'],
                    category_ar=item['category_ar'],
                    is_available=True
                )
                db.session.add(menu_item)
        
        db.session.commit()
        
        print("\n" + "="*70)
        print("✅   database is ready   ")
        print("="*70)
        print("📧  accouts for test:")
        print("   👤 client:    client@test.dz / client123")
        print("   🚗 driver:    chauffeur@test.dz / chauffeur123")
        print("   🍽️  restaurant 1:  restaurant@test.dz / restaurant123")
        print("   🍽️  restaurant 2:  fastfood@test.dz / restaurant123")
        print("   👨‍💼 admin:  admin@delivery.dz / admin123")
        print("="*70 + "\n")


# ============================================
# HELPER FUNCTIONS
# ============================================

def create_notification(user_id, title, message, order_id=None):
    """Create in-app notification"""
    notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        order_id=order_id
    )
    db.session.add(notif)
    db.session.commit()
    
    socketio.emit('new_notification', {
        'title': title,
        'message': message
    }, room=f'user_{user_id}')


def format_currency(amount):
    """Format amount in DZD"""
    return f"{amount:,.0f} د.ج"



# -------------------------------------------------------------
#    (Admin Dashboard)
# -------------------------------------------------------------

@app.route("/admin/dashboard")
@admin_required
def admin_grand_dashboard():
    # 1. إحصائيات المستخدمين حسب الرتبة
    total_clients = User.query.filter_by(role="customer").count()
    total_drivers = User.query.filter_by(role="driver").count()
    total_restaurants = Restaurant.query.count()
    
    # 2. حسابات توزيع المداخيل المالية المفصلة بالدينار الجزائري (دج)
    completed_orders = Order.query.filter_by(status="delivered").all()
    
    total_delivery_fees = sum(o.delivery_fee for o in completed_orders) # أرباح السائق الصافية
    total_platform_fees = sum(o.platform_fee for o in completed_orders) # عمولة التطبيق الصافية
    total_food_revenue = sum(o.total_amount for o in completed_orders)   # مداخيل الأكل الإجمالية
    
    # حساب عمولة التطبيق المفروضة على المطاعم (مثلاً 10% من قيمة الأكل)
    restaurant_commissions = sum(o.total_amount * (o.restaurant.commission_rate / 100.0) for o in completed_orders if o.restaurant)
    
    # صافي أرباح المنصة الإجمالية = عمولة المنصة الثابتة + النسبة المقتطعة من المطاعم
    net_platform_profit = total_platform_fees + restaurant_commissions
    
    # مستحقات المطاعم الصافية = مداخيل الأكل - النسبة المقتطعة للمنصة
    net_restaurant_earnings = total_food_revenue - restaurant_commissions
    
    # الحساب الإجمالي الذي دار في الشبكة
    grand_total_flow = total_food_revenue + total_delivery_fees + total_platform_fees

    # 3. قوائم الإدارة والتحكم
    all_users = User.query.all()
    all_restaurants = Restaurant.query.all()
    all_orders = Order.query.order_by(Order.created_at.desc()).all()

    return render_template(
        "admin/admin_dashboard.html",
        clients_count=total_clients,
        drivers_count=total_drivers,
        restaurants_count=total_restaurants,
        grand_total=grand_total_flow,
        platform_profit=net_platform_profit,
        driver_earnings=total_delivery_fees,
        restaurant_earnings=net_restaurant_earnings,
        users=all_users,
        restaurants=all_restaurants,
        orders=all_orders
    )

# -------------------------------------------------------------
# مسارات العمليات الإدارية  (تفعيل/تجميد/حذف)
# -------------------------------------------------------------

# تجميد أو تفعيل حساب مستخدم (زبون أو سائق)
@app.route("/admin/panel")
@admin_required
def admin_panel():
    """لوحة إدارة شاملة: الحسابات، المطاعم، الطلبات، والتسعير"""
    q     = (request.args.get('q') or '').strip()
    role  = request.args.get('role') or ''

    users_q = User.query
    if role in ('customer', 'driver', 'restaurant', 'admin'):
        users_q = users_q.filter_by(role=role)
    if q:
        like = f'%{q}%'
        users_q = users_q.filter(db.or_(
            User.username.ilike(like), User.email.ilike(like), User.phone.ilike(like)
        ))
    users = users_q.order_by(User.created_at.desc()).all()

    restaurants = Restaurant.query.order_by(Restaurant.is_open.desc(), Restaurant.name_ar).all()
    orders      = Order.query.order_by(Order.created_at.desc()).limit(60).all()

    counts = {
        'customer':   User.query.filter_by(role='customer').count(),
        'driver':     User.query.filter_by(role='driver').count(),
        'restaurant': Restaurant.query.count(),
        'orders':     Order.query.count(),
        'suspended':  User.query.filter_by(is_active=False).count(),
        'drivers_on': User.query.filter_by(role='driver', is_available=True, is_active=True).count(),
    }

    return render_template('admin/panel.html',
                           users=users, restaurants=restaurants, orders=orders,
                           counts=counts, pricing=PricingSetting.get(),
                           demand=demand_state(), quote=quote_delivery(),
                           q=q, role=role, cuisines=CUISINES)


@app.route("/admin/pricing", methods=['POST'])
@admin_required
def admin_save_pricing():
    """حفظ إعدادات التسعير"""
    st = PricingSetting.get()
    f = request.form

    def num(key, current, lo=0.0, hi=1e6):
        try:
            return max(lo, min(hi, float(f.get(key, current))))
        except (TypeError, ValueError):
            return current

    st.base_fee        = num('base_fee', st.base_fee)
    st.per_km          = num('per_km', st.per_km)
    st.platform_fee    = num('platform_fee', st.platform_fee)
    st.commission      = num('commission', st.commission, 0, 100)
    st.min_fee         = num('min_fee', st.min_fee)
    st.max_fee         = num('max_fee', st.max_fee)
    st.surge_threshold = num('surge_threshold', st.surge_threshold, 0.1)
    st.surge_step      = num('surge_step', st.surge_step, 0, 2)
    st.surge_max       = num('surge_max', st.surge_max, 1, 5)
    st.driver_share    = num('driver_share', st.driver_share, 0, 100)
    st.surge_enabled   = f.get('surge_enabled') == 'on'

    if st.min_fee > st.max_fee:
        st.min_fee, st.max_fee = st.max_fee, st.min_fee

    db.session.commit()
    flash('تم حفظ إعدادات التسعير', 'success')
    return redirect(url_for('admin_panel') + '#pricing')


@app.route("/admin/seed-demo", methods=['POST'])
@admin_required
def admin_seed_demo():
    """تعبئة بيانات العرض: مطاعم وأطباق بصور، سائقون وزبائن. آمنة للتكرار."""
    try:
        import demo_data
        rep = demo_data.seed(db, User, Restaurant, MenuItem, Wallet)
        flash(
            f"تمت التعبئة — مطاعم: {rep['restaurants']} جديد و{rep['updated']} محدَّث · "
            f"أطباق: {rep['dishes']} · سائقون: {rep['drivers']} · زبائن: {rep['customers']}",
            'success'
        )
    except Exception as e:
        db.session.rollback()
        flash(f'تعذّرت التعبئة: {e}', 'danger')
    return redirect(url_for('admin_panel'))


@app.route("/admin/restaurant/delete/<int:r_id>")
@admin_required
def admin_delete_restaurant(r_id):
    """حذف مطعم مع حساب صاحبه"""
    rest = Restaurant.query.get_or_404(r_id)
    name = rest.name_ar
    owner = User.query.get(rest.user_id)
    db.session.delete(rest)
    if owner and owner.role == 'restaurant':
        db.session.delete(owner)
    db.session.commit()
    flash(f'تم حذف مطعم {name}', 'success')
    return redirect(url_for('admin_panel'))


@app.route("/admin/user/toggle/<int:u_id>")
@admin_required
def admin_toggle_user(u_id):
    user = User.query.get_or_404(u_id)
    user.is_active = not user.is_active
    db.session.commit()
    flash(f"تم تغيير حالة حساب {user.username} بنجاح!", "success")
    return redirect(request.referrer or url_for('admin_panel'))

# حذف مستخدم نهائياً من المنصة
@app.route("/admin/user/delete/<int:u_id>")
@admin_required
def admin_delete_user(u_id):
    user = User.query.get_or_404(u_id)
    db.session.delete(user)
    db.session.commit()
    flash("تم حذف المستخدم نهائياً من قاعدة البيانات.", "danger")
    return redirect(request.referrer or url_for('admin_panel'))

# فتح أو غلق مطعم إدارياً
@app.route("/admin/restaurant/toggle/<int:r_id>")
@admin_required
def admin_toggle_restaurant(r_id):
    restaurant = Restaurant.query.get_or_404(r_id)
    restaurant.is_open = not restaurant.is_open
    db.session.commit()
    flash(f"تم تحديث حالة عمل مطعم {restaurant.name_ar}!", "success")
    return redirect(request.referrer or url_for('admin_panel'))


# ============================================
# AUTHENTICATION ROUTES
# ============================================

@app.context_processor
def inject_lists():
    """الولايات والتصنيفات متاحة في كل القوالب"""
    return dict(WILAYAS=WILAYAS, WILAYA_NAMES=WILAYA_NAMES, CUISINES=CUISINES,
                STATUS_AR=STATUS_AR)


@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'customer':
            return redirect(url_for('customer_dashboard'))
        elif current_user.role == 'driver':
            return redirect(url_for('driver_dashboard'))
        elif current_user.role == 'restaurant':
            return redirect(url_for('restaurant_dashboard'))
        elif current_user.role == 'admin':
            #return redirect(url_for('admin_dashboard'))
            return redirect(request.referrer or url_for('admin_panel')) 
    # نعرضو الكل — المفتوحة الأولى ثم حسب التقييم — والزبون يفلتر بنفسه
    restaurants = Restaurant.query.order_by(
        Restaurant.is_open.desc(),
        Restaurant.rating.desc()
    ).all()
    return render_template('index.html', restaurants=restaurants)

# ============================================
# LOGIN ROUTES
# ============================================

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        ip = request.headers.get('X-Forwarded-For', request.remote_addr or '?').split(',')[0].strip()
        if login_throttled(ip):
            flash('محاولات كثيرة. انتظر خمس دقائق ثم أعد المحاولة', 'danger')
            return render_template('login.html')

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            if not user.is_active:
                flash('حسابك معطل. راسل المدير', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=True)
            flash(f'مرحبا، {user.username}!', 'success')
            
            if user.role == 'customer':
                return redirect(url_for('customer_dashboard'))
            elif user.role == 'driver':
                return redirect(url_for('driver_dashboard'))
            elif user.role == 'restaurant':
                return redirect(url_for('restaurant_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_panel'))
        else:
            record_login_failure(ip)
            flash('البريد الإلكتروني أو كلمة السر غير صحيحة', 'danger')

    return render_template('login.html')

# ============================================
# REGISTER ROUTES
# ============================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        role = request.form.get('role', 'customer')
        wilaya = request.form.get('wilaya', 'Alger')
        
        # 1. Check if Username is already in use
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم هذا محجوز بالفعل! يرجى اختيار اسم آخر.', 'danger')
            return redirect(url_for('register'))

        # 2. Check if Email is already in use
        if User.query.filter_by(email=email).first():
            flash('هذا البريد الإلكتروني مستعمل بالفعل!', 'danger')
            return redirect(url_for('register'))
        
        # Instantiate and validate base User
        user = User(
            username=username,
            email=email,
            phone=phone,
            role=role,
            wilaya=wilaya
        )
        user.set_password(password)
        
        # Check if driver and initialize default availability values
        if role == 'driver':
            user.is_available = True
            user.current_lat = 36.7538
            user.current_lng = 3.0588
        
        db.session.add(user)
        
        try:
            db.session.commit()  # Committing generates the user.id
        except Exception as e:
            db.session.rollback()
            flash('حدث خطأ غير متوقع أثناء حفظ الحساب.', 'danger')
            return redirect(url_for('register'))

        # If user is a restaurant owner, extract profile fields and build database entry
        if role == 'restaurant':
            try:
                restaurant = Restaurant(
                    user_id=user.id,
                    name=request.form.get('restaurant_name'),
                    name_ar=request.form.get('restaurant_name_ar'),
                    description_ar=request.form.get('description_ar'),
                    address=request.form.get('address'),
                    wilaya=wilaya,
                    cuisine=request.form.get('cuisine') or DEFAULT_CUISINE,
                    commune=request.form.get('commune'),
                    latitude=float(request.form.get('latitude', 36.7538)),
                    longitude=float(request.form.get('longitude', 3.0588)),
                    phone=phone,
                    is_open=True
                )
                db.session.add(restaurant)
                db.session.commit()  # Commit restaurant profile to database
                
                # Seed basic starter dishes for the newly registered restaurant
                starter_dishes = [
                    {'name_ar': 'شاورما دجاج', 'price': 350.0, 'category_ar': 'ساندويتشات'},
                    {'name_ar': 'بيتزا مارغريتا', 'price': 500.0, 'category_ar': 'بيتزا'},
                    {'name_ar': 'فريت أومليت', 'price': 250.0, 'category_ar': 'مقبلات'},
                ]
                for dish in starter_dishes:
                    menu_item = MenuItem(
                        restaurant_id=restaurant.id,
                        name_ar=dish['name_ar'],
                        price=dish['price'],
                        category_ar=dish['category_ar'],
                        description_ar=f'{dish["name_ar"]} طازج ولذيذ',
                        is_available=True
                    )
                    db.session.add(menu_item)
                db.session.commit()
                
            except Exception as e:
                db.session.rollback()
                # Clean up dangling orphaned user so they can try again
                db.session.delete(user)
                db.session.commit()
                flash(f'لم يتم إنشاءالمطعم: {str(e)}', 'danger')
                return redirect(url_for('register'))
        
        # Initialize default user wallet
        try:
            wallet = Wallet(user_id=user.id, balance=0.0, total_earned=0.0)
            db.session.add(wallet)
            db.session.commit()
        except:
            db.session.rollback() # Non-blocking wallet save fallback

        flash('تم تسجيلك بنجاح! أدخل الآن للبدء.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', wilayas=WILAYAS)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('خرجت بنجاح', 'info')
    return redirect(url_for('index'))

# ============================================
# /restaurant/register ROUTES
# ============================================


@app.route('/restaurant/register', methods=['GET', 'POST'])
def restaurant_register():
    if request.method == 'POST':
        username       = request.form.get('username', '').strip()
        phone          = request.form.get('phone', '').strip()
        password       = request.form.get('password', '').strip()
        confirm_pass   = request.form.get('confirm_password', '').strip()
        email          = request.form.get('email', '').strip()
        name_ar        = request.form.get('name_ar', '').strip()
        name           = request.form.get('name', '').strip()
        description_ar = request.form.get('description_ar', '').strip()
        address        = request.form.get('address', '').strip()
        wilaya         = request.form.get('wilaya', '').strip()
        commune        = request.form.get('commune', '').strip()
        rest_phone     = request.form.get('rest_phone', '').strip()
        latitude       = request.form.get('latitude', '0').strip()
        longitude      = request.form.get('longitude', '0').strip()
        commission     = request.form.get('commission_rate', '10').strip()
        cuisine        = request.form.get('cuisine', '').strip() or DEFAULT_CUISINE

        # ── auto generate email if empty ──
        if not email:
            email = f"{username}_{phone}@restaurant.dz"

        # ── fix name: use name_ar if name is empty ──
        if not name:
            name = name_ar          # ← KEY FIX

        # ── fix address: use wilaya if address is empty ──
        if not address:
            address = wilaya        # ← KEY FIX

        # ── validate passwords ──
        if password != confirm_pass:
            flash('كلمتا المرور غير متطابقتان', 'danger')
            return redirect(url_for('restaurant_register'))

        # ── validate required fields ──
        if not name_ar:
            flash('اسم المطعم مطلوب', 'danger')
            return redirect(url_for('restaurant_register'))

        if not wilaya:
            flash('الولاية مطلوبة', 'danger')
            return redirect(url_for('restaurant_register'))

        # ── check duplicates ──
        if User.query.filter_by(username=username).first():
            flash('اسم المستخدم موجود بالفعل', 'danger')
            return redirect(url_for('restaurant_register'))

        if User.query.filter_by(phone=phone).first():
            flash('رقم الهاتف موجود بالفعل', 'danger')
            return redirect(url_for('restaurant_register'))

        if User.query.filter_by(email=email).first():
            flash('البريد الإلكتروني موجود بالفعل', 'danger')
            return redirect(url_for('restaurant_register'))

        try:
            # ── create user ──
            user = User(
                username  = username,
                email     = email,
                phone     = phone,
                role      = 'restaurant',
                is_active = True
            )
            user.set_password(password)
            db.session.add(user)
            db.session.flush()

            # ── safe lat/lng conversion ──
            try:
                lat = float(latitude) if latitude else 0.0
                lng = float(longitude) if longitude else 0.0
            except ValueError:
                lat = 0.0
                lng = 0.0

            # ── create restaurant ──
            # check your Restaurant model for correct column names
            restaurant = Restaurant(
                user_id         = user.id,       # ← use user_id not owner_id
                name            = name,           # ← never None now
                name_ar         = name_ar,
                description_ar  = description_ar or '',
                address         = address,        # ← never None now
                wilaya          = wilaya,
                    cuisine=cuisine,
                commune         = commune or '',
                phone           = rest_phone or phone,
                latitude        = lat,
                longitude       = lng,
                commission_rate = float(commission) if commission else 10.0,
                is_open         = True,
                rating          = 0.0
            )
            db.session.add(restaurant)
            db.session.flush()

            # ── handle image ──
            if 'image' in request.files:
                file = request.files['image']
                ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}
                if file and file.filename and '.' in file.filename and \
                   file.filename.rsplit('.', 1)[1].lower() in ALLOWED:
                    ext      = file.filename.rsplit('.', 1)[1].lower()
                    filename = f"restaurant_{restaurant.id}.{ext}"
                    folder   = os.path.join(
                        app.root_path, 'static', 'uploads', 'restaurants'
                    )
                    os.makedirs(folder, exist_ok=True)
                    file.save(os.path.join(folder, filename))
                    restaurant.image_url = f"/static/uploads/restaurants/{filename}"

            db.session.commit()
            flash(f'✅ تم تسجيل مطعم {name_ar} بنجاح! يمكنك الآن تسجيل الدخول', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            db.session.rollback()
            print(f'❌ Error: {e}')
            flash(f'لم يتم إنشاء المطعم: {str(e)}', 'danger')
            return redirect(url_for('restaurant_register'))

    return render_template('restaurant_register.html')


@app.route('/restaurant/<int:restaurant_id>/profile')
def restaurant_profile(restaurant_id):
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    menu_items = MenuItem.query.filter_by(
        restaurant_id=restaurant_id,
        is_available=True
    ).all()
    reviews = Review.query.filter_by(target_type='restaurant', target_id=restaurant_id)\
                          .order_by(Review.created_at.desc()).limit(20).all()
    breakdown = {n: Review.query.filter_by(target_type='restaurant',
                                           target_id=restaurant_id, stars=n).count()
                 for n in range(5, 0, -1)}
    return render_template(
        'restaurant_profile.html',
        restaurant=restaurant,
        menu_items=menu_items,
        reviews=reviews,
        breakdown=breakdown,
        reviews_count=sum(breakdown.values())
    )







# ============================================
# CUSTOMER ROUTES
# ============================================

@app.route('/customer/dashboard')
@login_required
def customer_dashboard():
    if current_user.role != 'customer':
        return redirect(url_for('index'))
    
    restaurants = Restaurant.query.filter_by(is_open=True).all()
    orders = Order.query.filter_by(customer_id=current_user.id).order_by(Order.created_at.desc()).all()
    
    return render_template('customer/dashboard.html', restaurants=restaurants, orders=orders)


ACTIVE_STATUSES = ('pending', 'confirmed', 'ready', 'assigned', 'picked_up', 'delivering')


@app.route('/my-orders')
@login_required
def my_orders():
    """كل طلبات الزبون: الجارية والسابقة"""
    if current_user.role != 'customer':
        return redirect(url_for('index'))

    all_orders = Order.query.filter_by(customer_id=current_user.id)\
                            .order_by(Order.created_at.desc()).all()
    active = [o for o in all_orders if o.status in ACTIVE_STATUSES]
    past   = [o for o in all_orders if o.status not in ACTIVE_STATUSES]

    spent = sum((o.final_amount or 0) for o in past if o.status == 'delivered')

    return render_template('customer/orders.html',
                           active_orders=active, past_orders=past,
                           total_spent=spent,
                           delivered_count=len([o for o in past if o.status == 'delivered']))


def refresh_rating(target_type, target_id):
    """يعيد حساب متوسط النجوم وعدد التقييمات للهدف"""
    rows = Review.query.filter_by(target_type=target_type, target_id=target_id).all()
    n = len(rows)
    avg = round(sum(r.stars for r in rows) / n, 1) if n else 0.0
    obj = Restaurant.query.get(target_id) if target_type == 'restaurant' else User.query.get(target_id)
    if obj:
        obj.rating = avg
        if hasattr(obj, 'total_reviews'):
            obj.total_reviews = n
        db.session.commit()
    return avg, n


@app.route('/order/<int:order_id>/review', methods=['GET', 'POST'])
@login_required
def review_order(order_id):
    """تقييم المطعم والسائق بعد التسليم"""
    order = Order.query.get_or_404(order_id)

    if order.customer_id != current_user.id:
        flash('لا تملك صلاحية تقييم هذا الطلب', 'danger')
        return redirect(url_for('my_orders'))

    if order.status != 'delivered':
        flash('يمكن التقييم بعد تسليم الطلب فقط', 'warning')
        return redirect(url_for('my_orders'))

    existing = {r.target_type: r for r in order.reviews}

    if request.method == 'POST':
        saved = 0

        def upsert(kind, target_id, stars_key, comment_key):
            nonlocal saved
            if not target_id:
                return
            try:
                stars = int(request.form.get(stars_key, 0))
            except (TypeError, ValueError):
                return
            if stars < 1 or stars > 5:
                return
            comment = (request.form.get(comment_key) or '').strip()[:400]
            rv = existing.get(kind)
            if rv:
                rv.stars, rv.comment = stars, comment
            else:
                db.session.add(Review(order_id=order.id, customer_id=current_user.id,
                                      target_type=kind, target_id=target_id,
                                      stars=stars, comment=comment))
            saved += 1

        upsert('restaurant', order.restaurant_id, 'restaurant_stars', 'restaurant_comment')
        upsert('driver',     order.driver_id,     'driver_stars',     'driver_comment')
        db.session.commit()

        if order.restaurant_id:
            refresh_rating('restaurant', order.restaurant_id)
        if order.driver_id:
            refresh_rating('driver', order.driver_id)

        if saved:
            if order.restaurant and order.restaurant.user_id:
                create_notification(order.restaurant.user_id, '⭐ تقييم جديد',
                                    f'قيّم {current_user.username} طلبه من مطعمك', order.id)
            if order.driver_id:
                create_notification(order.driver_id, '⭐ تقييم جديد',
                                    f'قيّم {current_user.username} توصيلتك', order.id)
            flash('شكراً لك — سُجّل تقييمك', 'success')
        else:
            flash('لم تختر أي نجوم', 'warning')
        return redirect(url_for('my_orders'))

    return render_template('customer/review.html', order=order, existing=existing)


@app.route('/restaurant/orders')
@login_required
def restaurant_orders():
    """كل طلبات المطعم مع تصفية بالحالة"""
    if current_user.role != 'restaurant':
        return redirect(url_for('index'))
    rest = Restaurant.query.filter_by(user_id=current_user.id).first()
    if not rest:
        flash('أكمل بيانات مطعمك أولاً', 'warning')
        return redirect(url_for('index'))

    status = request.args.get('status') or ''
    q = Order.query.filter_by(restaurant_id=rest.id)
    if status == 'active':
        q = q.filter(Order.status.in_(ACTIVE_STATUSES))
    elif status in ('delivered', 'cancelled'):
        q = q.filter_by(status=status)
    orders = q.order_by(Order.created_at.desc()).limit(200).all()

    return render_template('restaurant/orders.html',
                           restaurant=rest, orders=orders, status=status,
                           counts={
                               'all':       Order.query.filter_by(restaurant_id=rest.id).count(),
                               'active':    Order.query.filter_by(restaurant_id=rest.id)
                                                 .filter(Order.status.in_(ACTIVE_STATUSES)).count(),
                               'delivered': Order.query.filter_by(restaurant_id=rest.id, status='delivered').count(),
                               'cancelled': Order.query.filter_by(restaurant_id=rest.id, status='cancelled').count(),
                           })


@app.route('/restaurant/reports')
@login_required
def restaurant_reports():
    """أرباح المطعم، زبائنه الأوفياء، والسائقون الأكثر توصيلاً له"""
    if current_user.role != 'restaurant':
        return redirect(url_for('index'))
    rest = Restaurant.query.filter_by(user_id=current_user.id).first()
    if not rest:
        flash('أكمل بيانات مطعمك أولاً', 'warning')
        return redirect(url_for('index'))

    from datetime import timedelta
    now        = datetime.utcnow()
    day_start  = now.replace(hour=0, minute=0, second=0, microsecond=0)
    month_start= now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    rate       = (rest.commission_rate or 10.0) / 100.0

    delivered = Order.query.filter_by(restaurant_id=rest.id, status='delivered').all()

    def money(rows):
        gross = sum((o.total_amount or 0) for o in rows)
        return {'orders': len(rows), 'gross': gross,
                'commission': gross * rate, 'net': gross * (1 - rate)}

    today_rows = [o for o in delivered if o.delivered_at and o.delivered_at >= day_start]
    month_rows = [o for o in delivered if o.delivered_at and o.delivered_at >= month_start]

    # ── مبيعات آخر 14 يوماً للرسم البياني ──
    daily = []
    for i in range(13, -1, -1):
        d0 = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
        d1 = d0 + timedelta(days=1)
        rows = [o for o in delivered if o.delivered_at and d0 <= o.delivered_at < d1]
        daily.append({'label': d0.strftime('%d/%m'),
                      'gross': sum((o.total_amount or 0) for o in rows),
                      'orders': len(rows)})

    # ── الزبائن الأوفياء ──
    by_customer = {}
    for o in delivered:
        e = by_customer.setdefault(o.customer_id, {'orders': 0, 'spent': 0.0, 'last': None, 'user': o.customer})
        e['orders'] += 1
        e['spent']  += (o.total_amount or 0)
        if not e['last'] or (o.delivered_at and o.delivered_at > e['last']):
            e['last'] = o.delivered_at
    loyal = sorted(by_customer.values(), key=lambda x: (-x['orders'], -x['spent']))[:8]

    # ── السائقون الموثوقون ──
    by_driver = {}
    for o in delivered:
        if not o.driver_id:
            continue
        e = by_driver.setdefault(o.driver_id, {'orders': 0, 'fees': 0.0, 'last': None, 'user': o.driver})
        e['orders'] += 1
        e['fees']   += (o.delivery_fee or 0)
        if not e['last'] or (o.delivered_at and o.delivered_at > e['last']):
            e['last'] = o.delivered_at
    # نسبة الإتمام: كم طلباً قبله السائق من هذا المطعم مقابل ما أتمّه
    for did, e in by_driver.items():
        taken = Order.query.filter_by(restaurant_id=rest.id, driver_id=did)\
                           .filter(Order.status != 'cancelled').count()
        e['rate'] = round(100.0 * e['orders'] / taken) if taken else 100
        e['stars'] = (e['user'].rating or 0) if e['user'] else 0
    trusted = sorted(by_driver.values(), key=lambda x: (-x['orders'], -x['rate']))[:8]

    return render_template('restaurant/reports.html',
                           restaurant=rest,
                           today=money(today_rows), month=money(month_rows), total=money(delivered),
                           daily=daily, loyal=loyal, trusted=trusted,
                           commission_rate=rest.commission_rate or 10.0)


@app.route('/restaurant/<int:restaurant_id>/menu')
@login_required
def restaurant_menu(restaurant_id):
    if current_user.role != 'customer':
        return redirect(url_for('index'))
    
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id, is_available=True).all()
    
    return render_template('customer/menu.html', restaurant=restaurant, menu_items=menu_items)


@app.route('/order/create', methods=['POST'])
@login_required
def create_order():
    if current_user.role != 'customer':
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    data = request.json

    # تسعيرة لحظية حسب المسافة وحالة العرض والطلب
    _rest = Restaurant.query.get(data['restaurant_id'])
    quote = quote_delivery(
        _rest,
        data.get('delivery_lat', 36.7538),
        data.get('delivery_lng', 3.0588)
    )

    order = Order(
        order_number=generate_order_number(),
        customer_id=current_user.id,
        restaurant_id=data['restaurant_id'],
        delivery_address=data['delivery_address'],
        delivery_wilaya=current_user.wilaya,
        delivery_lat=data.get('delivery_lat', 36.7538),
        delivery_lng=data.get('delivery_lng', 3.0588),
        payment_method=data['payment_method'],
        customer_notes=data.get('notes', ''),
        total_amount=0,
        delivery_fee=quote['delivery_fee'],
        platform_fee=quote['platform_fee']
    )
    
    total = 0
    for item in data['items']:
        menu_item = MenuItem.query.get(item['id'])
        if menu_item:
            order_item = OrderItem(
                menu_item_id=menu_item.id,
                quantity=item['quantity'],
                price=menu_item.price
            )
            order.items.append(order_item)
            total += menu_item.price * item['quantity']
    
    order.total_amount = total
    order.calculate_final_amount()
    
    verification_code = order.generate_verification_code()
    
    db.session.add(order)
    db.session.commit()
    
    create_notification(
        order.restaurant.user_id,
        '🔔 طلبية جديدة',
        f'طلبية رقم {order.order_number} بـ {format_currency(total)}',
        order.id
    )
    
    socketio.emit('new_order', {
        'order_id': order.id,
        'order_number': order.order_number,
        'total': total
    }, room=f'restaurant_{order.restaurant_id}')
    
    return jsonify({
        'success': True,
        'order_id': order.id,
        'order_number': order.order_number,
        'verification_code': verification_code,
        'message': f'تم تسجيل طلبك بنجاح. كود الاستلام: {verification_code}'
    })

# ============================================
# order track ROUTES
# ============================================
#@app.route("/track/<order_id>")
#return render_template('customer/track.html', order=order)
@app.route('/order/<int:order_id>/track')
@login_required
def track_order(order_id):
    order = Order.query.get_or_404(order_id)
    
    # security check
    if current_user.role == 'customer' and order.customer_id != current_user.id:
        flash('لا تملك الصلاحية لرؤية الطلبية', 'danger')
        return redirect(url_for('customer_dashboard'))
    
    # ── always build driver_coords to avoid UndefinedError ──
    driver_coords = {
        'lat': float(order.restaurant.latitude),   # default = restaurant location
        'lng': float(order.restaurant.longitude)
    }

    if order.driver:
        if order.driver.current_lat and order.driver.current_lng:
            # driver has real GPS position
            driver_coords = {
                'lat': float(order.driver.current_lat),
                'lng': float(order.driver.current_lng)
            }
        else:
            # driver assigned but no GPS yet → start at restaurant
            driver_coords = {
                'lat': float(order.restaurant.latitude),
                'lng': float(order.restaurant.longitude)
            }

    return render_template(
        'customer/track.html',
        order=order,
        driver_coords=driver_coords    # ← pass it always
    )

# ============================================
# DRIVER ROUTES
# ============================================

@app.route('/driver/dashboard')
@login_required
def driver_dashboard():
    if current_user.role != 'driver':
        return redirect(url_for('index'))
    
    available_orders = Order.query.filter_by(status='ready', driver_id=None).all()
    active_orders = Order.query.filter_by(driver_id=current_user.id).filter(
        Order.status.in_(['assigned', 'picked_up', 'delivering'])
    ).all()
    
    completed_orders = Order.query.filter_by(driver_id=current_user.id, status='delivered').all()
    wallet = Wallet.query.filter_by(user_id=current_user.id).first()
    # الرصيد المسجَّل هو المرجع، والحساب اللحظي احتياط للطلبات السابقة لتفعيل المحفظة
    total_earnings = max(
        (wallet.total_earned or 0.0) if wallet else 0.0,
        sum(o.delivery_fee for o in completed_orders)
    )
    
    my_reviews = Review.query.filter_by(target_type='driver', target_id=current_user.id)\
                             .order_by(Review.created_at.desc()).limit(5).all()

    return render_template('driver/dashboard.html',
                         available_orders=available_orders,
                         active_orders=active_orders,
                         total_earnings=total_earnings,
                         completed_count=len(completed_orders),
                         my_reviews=my_reviews)


@app.route('/driver/toggle_availability', methods=['POST'])
@login_required
def toggle_availability():
    if current_user.role != 'driver':
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    current_user.is_available = not current_user.is_available
    db.session.commit()
    
    return jsonify({
        'success': True,
        'is_available': current_user.is_available,
        'message': 'انت نشط الان' if current_user.is_available else 'انت غير نشط'
    })


@app.route('/driver/accept_order/<int:order_id>', methods=['POST'])
@login_required
def accept_order(order_id):
    if current_user.role != 'driver':
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    order = Order.query.get_or_404(order_id)

    if order.status != 'ready':
        return jsonify({'error': 'الطلب غير متاح للقبول'}), 400

    # إسناد ذرّي: يمنع سائقَين من أخذ الطلب نفسه في اللحظة ذاتها
    updated = Order.query.filter(
        Order.id == order_id,
        Order.driver_id.is_(None),
        Order.status == 'ready'
    ).update(
        {'driver_id': current_user.id, 'status': 'assigned'},
        synchronize_session=False
    )
    db.session.commit()

    if not updated:
        return jsonify({'error': 'سبقك سائق آخر إلى هذا الطلب'}), 409

    db.session.refresh(order)

    create_notification(
        order.customer_id,
        '🛵 سائق قبل طلبك',
        f'السائق {current_user.username} في طريقه إلى المطعم لاستلام طلبك',
        order.id
    )
    
    socketio.emit('order_update', {
        'order_id': order.id,
        'status': 'assigned',
        'driver_name': current_user.username
    }, room=f'order_{order.id}')

    return jsonify({'success': True, 'message': 'قبلت الطلب — توجّه إلى المطعم'})


@app.route('/driver/start_delivery/<int:order_id>', methods=['POST'])
@login_required
def start_delivery(order_id):
    """السائق استلم الطلب من المطعم وانطلق إلى الزبون"""
    order = Order.query.get_or_404(order_id)

    if order.driver_id != current_user.id:
        return jsonify({'error': 'لا تملك الصلاحية'}), 403

    if order.status != 'assigned':
        return jsonify({'error': 'لا يمكن بدء التوصيل في هذه الحالة'}), 400

    order.status = 'picked_up'
    db.session.commit()

    create_notification(
        order.customer_id,
        '🚗 طلبك في الطريق إليك',
        f'السائق {current_user.username} استلم طلبك من المطعم',
        order.id
    )

    socketio.emit('order_update', {
        'order_id': order.id,
        'status': 'picked_up',
        'driver_name': current_user.username
    }, room=f'order_{order.id}')

    return jsonify({'success': True, 'message': 'انطلقت — الزبون يتابعك على الخريطة'})


@app.route('/driver/complete_delivery/<int:order_id>', methods=['POST'])
@login_required
def complete_delivery(order_id):
    order = Order.query.get_or_404(order_id)
    data = request.json
    
    if order.driver_id != current_user.id:
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    if data.get('code') != order.verification_code:
        return jsonify({'error': 'كود الاستلام غير صحيح'}), 400
    
    order.is_verified = True
    order.status = 'delivered'
    order.delivered_at = datetime.utcnow()
    order.payment_status = 'completed'
    
    db.session.commit()

    # قيد أرباح السائق في محفظته
    wallet = Wallet.query.filter_by(user_id=current_user.id).first()
    if not wallet:
        wallet = Wallet(user_id=current_user.id, balance=0.0, total_earned=0.0)
        db.session.add(wallet)
    wallet.balance = (wallet.balance or 0.0) + (order.delivery_fee or 0.0)
    wallet.total_earned = (wallet.total_earned or 0.0) + (order.delivery_fee or 0.0)
    db.session.commit()
    
    create_notification(
        order.customer_id,
        '✅ وصل طلبك',
        'تم تسليم طلبك. بالهناء والشفاء',
        order.id
    )
    
    return jsonify({
        'success': True,
        'message': f'تم التسليم — أُضيف {format_currency(order.delivery_fee)} إلى رصيدك'
    })


@app.route('/driver/update_location', methods=['POST'])
@login_required
def update_location():
    if current_user.role != 'driver':
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    data = request.json
    current_user.current_lat = data['lat']
    current_user.current_lng = data['lng']
    db.session.commit()
    
    active_orders = Order.query.filter_by(driver_id=current_user.id, status='delivering').all()
    
    for order in active_orders:
        socketio.emit('driver_location', {
            'lat': data['lat'],
            'lng': data['lng']
        }, room=f'order_{order.id}')
    
    return jsonify({'success': True})


# ============================================
# RESTAURANT ROUTES
# ============================================

@app.route('/restaurant/dashboard')
@login_required
def restaurant_dashboard():
    if current_user.role != 'restaurant':
        return redirect(url_for('index'))
    
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first()
    
    if not restaurant:
        flash('أكمل بيانات مطعمك أولاً', 'warning')
        return redirect(url_for('index'))
    
    pending_orders = Order.query.filter_by(
        restaurant_id=restaurant.id,
        status='pending'
    ).order_by(Order.created_at.desc()).all()
    
    active_orders = Order.query.filter_by(restaurant_id=restaurant.id).filter(
        Order.status.in_(['confirmed', 'ready', 'assigned', 'picked_up', 'delivering'])
    ).all()
    
    completed_orders = Order.query.filter_by(
        restaurant_id=restaurant.id,
        status='delivered'
    ).all()
    
    total_revenue = sum(o.total_amount for o in completed_orders)
    
    return render_template('restaurant/dashboard.html',
                         restaurant=restaurant,
                         pending_orders=pending_orders,
                         active_orders=active_orders,
                         total_revenue=total_revenue,
                         completed_count=len(completed_orders))


@app.route('/restaurant/confirm_order/<int:order_id>', methods=['POST'])
@login_required
def confirm_order(order_id):
    order = Order.query.get_or_404(order_id)
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first()
    
    if order.restaurant_id != restaurant.id:
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    order.status = 'confirmed'
    order.confirmed_at = datetime.utcnow()
    db.session.commit()
    
    create_notification(
        order.customer_id,
        '✅ تم تأكيد الطلبية',
        f'{restaurant.name_ar}  الطلبية قيد التحضير',
        order.id
    )
    
    return jsonify({'success': True, 'message': 'تم تأكيد الطلبية'})


@app.route('/restaurant/ready_order/<int:order_id>', methods=['POST'])
@login_required
def ready_order(order_id):
    order = Order.query.get_or_404(order_id)
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first()
    
    if order.restaurant_id != restaurant.id:
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    order.status = 'ready'
    db.session.commit()
    
    socketio.emit('order_ready', {
        'order_id': order.id,
        'restaurant_name': restaurant.name_ar,
        'delivery_fee': order.delivery_fee
    }, room='drivers')
    
    return jsonify({'success': True, 'message': 'الطلبية جاهزة'})


@app.route('/restaurant/reject_order/<int:order_id>', methods=['POST'])
@login_required
def reject_order(order_id):
    order = Order.query.get_or_404(order_id)
    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first()
    
    if order.restaurant_id != restaurant.id:
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    db.session.delete(order)
    db.session.commit()
    
    create_notification(
        order.customer_id,
        '❌ تم الغاء الطلبية',
        f'آسف ، {restaurant.name_ar}  لم تقبل طلبيتك '
    )
    
    return jsonify({'success': True, 'message': 'رفضت الطلبية'})




@app.route('/restaurant/menu')
@login_required
def restaurant_menu_management():
    """صفحة إدارة قائمة أطباق المطعم"""
    if current_user.role != 'restaurant':
        flash('لا تملك الصلاحية', 'danger')
        return redirect(url_for('index'))

    restaurant = Restaurant.query.filter_by(user_id=current_user.id).first()
    if not restaurant:
        flash('أكمل بيانات مطعمك أولاً', 'warning')
        return redirect(url_for('index'))

    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant.id)\
                               .order_by(MenuItem.category_ar, MenuItem.name_ar).all()

    return render_template('restaurant/menu_management.html',
                           restaurant=restaurant,
                           menu_items=menu_items)


@app.route('/restaurant/menu/add', defaults={'restaurant_id': None}, methods=['GET', 'POST'])
@app.route('/restaurant/menu/add/<int:restaurant_id>', methods=['GET', 'POST'])
@login_required
def add_menu_item(restaurant_id):
    if current_user.role != 'restaurant':
        flash('لا تملك الصلاحية', 'danger')
        return redirect(url_for('index'))

    if restaurant_id is None:
        restaurant = Restaurant.query.filter_by(user_id=current_user.id).first()
        if not restaurant:
            flash('أكمل بيانات مطعمك أولاً', 'warning')
            return redirect(url_for('index'))
    else:
        restaurant = Restaurant.query.get_or_404(restaurant_id)
    
    if restaurant.user_id != current_user.id:
        flash('لا تملك الصلاحية', 'danger')
        return redirect(url_for('restaurant_dashboard'))
    
    if request.method == 'POST':
        from services import save_image
        
        name_ar = request.form.get('name_ar')
        description_ar = request.form.get('description_ar')
        price = float(request.form.get('price'))
        category_ar = request.form.get('category_ar')
        
        # Handle image upload
        image_url = None
        image_thumbnail = None
        
        if 'item_image' in request.files:
            file = request.files['item_image']
            if file and file.filename:
                images = save_image(file, folder='menu_items')
                if images:
                    image_url = images['original']
                    image_thumbnail = images['thumbnail']
        
        menu_item = MenuItem(
            restaurant_id=restaurant_id,
            name_ar=name_ar,
            description_ar=description_ar,
            price=price,
            category_ar=category_ar,
            image_url=image_url,
            image_thumbnail=image_thumbnail,
            is_available=True
        )
        
        db.session.add(menu_item)
        db.session.commit()
        
        flash(f'تمت إضافة {name_ar} بنجاح!', 'success')
        return redirect(url_for('restaurant_menu_management'))
    
    return render_template('restaurant/add_dish.html', restaurant=restaurant)

# ============================================
# ADM MENU ITEMS IN ROUTES
# ============================================

@app.route('/restaurant/menu/edit/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_menu_item(item_id):
    menu_item = MenuItem.query.get_or_404(item_id)
    restaurant = menu_item.restaurant
    
    if restaurant.user_id != current_user.id:
        flash('لا تملك الصلاحية', 'danger')
        return redirect(url_for('restaurant_dashboard'))
    
    if request.method == 'POST':
        from services import save_image
        
        menu_item.name_ar = request.form.get('name_ar')
        menu_item.description_ar = request.form.get('description_ar')
        menu_item.price = float(request.form.get('price'))
        menu_item.category_ar = request.form.get('category_ar')
        menu_item.is_available = request.form.get('is_available') == 'on'
        
        # Handle image upload
        if 'item_image' in request.files:
            file = request.files['item_image']
            if file and file.filename:
                images = save_image(file, folder='menu_items')
                if images:
                    menu_item.image_url = images['original']
                    menu_item.image_thumbnail = images['thumbnail']
        
        db.session.commit()
        flash('تم التحديث بنجاح!', 'success')
        return redirect(url_for('restaurant_menu_management'))
    
    return render_template('restaurant/edit_dish.html', 
                         menu_item=menu_item, 
                         restaurant=restaurant)


@app.route('/restaurant/menu/delete/<int:item_id>', methods=['POST'])
@login_required
def delete_menu_item(item_id):
    menu_item = MenuItem.query.get_or_404(item_id)
    restaurant = menu_item.restaurant
    
    if restaurant.user_id != current_user.id:
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    db.session.delete(menu_item)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'تم الحذف'})

# ============================================
# images ROUTES
# ============================================

# app.py  – add this temporary test route
@app.route('/test')
def test_map():
    """Temporary page to test map visuals without real order data"""
    return render_template('test_map.html')


# ============================================
# ADMIN ROUTES
# ============================================
@app.route('/admin/restaurant/<int:restaurant_id>/menu')
@login_required
def admin_menu(restaurant_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    restaurant = Restaurant.query.get_or_404(restaurant_id)
    menu_items = MenuItem.query.filter_by(restaurant_id=restaurant_id).all()
    return render_template(
        'admin/menu_manager.html',
        restaurant=restaurant,
        menu_items=menu_items
    )

@app.route('/admin/restaurant/<int:restaurant_id>/menu/add', methods=['POST'])
@login_required
def admin_add_menu_item(restaurant_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    restaurant = Restaurant.query.get_or_404(restaurant_id)

    name_ar     = request.form.get('name_ar', '').strip()
    name        = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()
    price       = request.form.get('price', 0)
    category    = request.form.get('category', '').strip()

    if not name_ar or not price:
        flash('اسم الطبق والسعر مطلوبان', 'danger')
        return redirect(url_for('admin_menu', restaurant_id=restaurant_id))

    item = MenuItem(
        restaurant_id  = restaurant_id,
        name_ar        = name_ar,
        #name           = name or name_ar,
        description_ar = description,
        price          = float(price),
        category_ar       = category,
        is_available   = True
    )
    db.session.add(item)
    db.session.flush()  # get item.id before commit

    # handle image upload
    if 'image' in request.files:
        file = request.files['image']
        ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}
        if file and file.filename and '.' in file.filename and \
           file.filename.rsplit('.', 1)[1].lower() in ALLOWED:
            ext      = file.filename.rsplit('.', 1)[1].lower()
            filename = f"menu_item_{item.id}.{ext}"
            folder   = os.path.join(app.root_path, 'static', 'uploads', 'menu')
            os.makedirs(folder, exist_ok=True)
            file.save(os.path.join(folder, filename))
            item.image_url = f"/static/uploads/menu/{filename}"

    db.session.commit()
    flash(f'✅ تم إضافة {name_ar} بنجاح', 'success')
    return redirect(url_for('admin_menu', restaurant_id=restaurant_id))


@app.route('/admin/menu-item/<int:item_id>/delete')
@login_required
def admin_delete_menu_item(item_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    item = MenuItem.query.get_or_404(item_id)
    restaurant_id = item.restaurant_id
    db.session.delete(item)
    db.session.commit()
    flash('تم حذف الطبق', 'success')
    return redirect(url_for('admin_menu', restaurant_id=restaurant_id))


@app.route('/admin/menu-item/<int:item_id>/toggle')
@login_required
def admin_toggle_menu_item(item_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))
    item = MenuItem.query.get_or_404(item_id)
    item.is_available = not item.is_available
    db.session.commit()
    return redirect(url_for('admin_menu', restaurant_id=item.restaurant_id))


@app.route('/admin/menu-item/<int:item_id>/upload-image', methods=['POST'])
@login_required
def admin_upload_menu_image(item_id):
    if current_user.role != 'admin':
        return redirect(url_for('index'))

    item = MenuItem.query.get_or_404(item_id)
    ALLOWED = {'png', 'jpg', 'jpeg', 'webp'}

    if 'image' in request.files:
        file = request.files['image']
        if file and file.filename and '.' in file.filename and \
           file.filename.rsplit('.', 1)[1].lower() in ALLOWED:
            ext      = file.filename.rsplit('.', 1)[1].lower()
            filename = f"menu_item_{item_id}.{ext}"
            folder   = os.path.join(app.root_path, 'static', 'uploads', 'menu')
            os.makedirs(folder, exist_ok=True)

            # delete old
            for old_ext in ALLOWED:
                old = os.path.join(folder, f"menu_item_{item_id}.{old_ext}")
                if os.path.exists(old):
                    os.remove(old)

            file.save(os.path.join(folder, filename))
            item.image_url = f"/static/uploads/menu/{filename}"
            db.session.commit()
            flash('✅ تم رفع صورة الطبق', 'success')

    return redirect(url_for('admin_menu', restaurant_id=item.restaurant_id))

# ============================================
# location tracking routes
# ============================================

@app.route('/firebase-messaging-sw.js')
def firebase_sw():
    return send_from_directory(
        os.path.join(app.root_path, 'static'),
        'firebase-messaging-sw.js',
        mimetype='application/javascript'
    )



# ============================================
# API ROUTES
# ============================================

@app.route('/api/order/<int:order_id>/info')
@login_required
def api_order_info(order_id):
    order = Order.query.filter((Order.id == order_id) | (Order.order_number == order_id)).first_or_404()

    # لا يقرأ الطلب إلا أطرافه: الزبون، صاحب المطعم، السائق المسنَد، أو المشرف
    if not user_may_see_order(order):
        return jsonify({'error': 'لا تملك صلاحية الاطلاع على هذا الطلب'}), 403
    
    driver_location = None
    if order.driver:
        driver_location = {
            'lat': order.driver.current_lat,
            'lng': order.driver.current_lng
        }
    
    return jsonify({
        'success': True,
        'order_number': order.order_number,
        'status': order.status,
        'verification_code': order.verification_code if current_user.id == order.customer_id else None,
        'total': order.final_amount,
        'driver_location': driver_location,
        'driver_name': order.driver.username if order.driver else None,
        'driver_phone': order.driver.phone if order.driver else None,
        'restaurant': {
            'name': order.restaurant.name_ar,
            'lat': order.restaurant.latitude,
            'lng': order.restaurant.longitude,
            'phone': order.restaurant.phone
        },
        'delivery': {
            'address': order.delivery_address,
            'lat': order.delivery_lat,
            'lng': order.delivery_lng
        }
    })


@app.route('/api/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(20).all()
    
    return jsonify([{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'order_id': n.order_id,
        'is_read': n.is_read,
        'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')
    } for n in notifications])


@app.route('/api/notifications/<int:notif_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notif_id):
    notif = Notification.query.get_or_404(notif_id)
    
    if notif.user_id != current_user.id:
        return jsonify({'error': 'لا تملك الصلاحية'}), 403
    
    notif.is_read = True
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/api/notifications/mark_all_read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return jsonify({'success': True})


# ============================================
# WEBSOCKET EVENTS
# ============================================

@socketio.on('connect')
def handle_connect():
    if current_user.is_authenticated:
        join_room(f'user_{current_user.id}')
        
        if current_user.role == 'driver':
            join_room('drivers')
        elif current_user.role == 'restaurant':
            restaurant = Restaurant.query.filter_by(user_id=current_user.id).first()
            if restaurant:
                join_room(f'restaurant_{restaurant.id}')
        
        emit('connected', {
            'message': 'متصل بالخادم',
            'user': current_user.username,
            'role': current_user.role
        })
        
        print(f"✅ {current_user.username} ({current_user.role}) connected")


@socketio.on('disconnect')
def handle_disconnect():
    if current_user.is_authenticated:
        print(f"❌ {current_user.username} disconnected")


@socketio.on('join_order')
def handle_join_order(data):
    if current_user.is_authenticated:
        order_id = data['order_id']
        order = Order.query.get(order_id)
        
        if order and (
            current_user.id == order.customer_id or
            current_user.id == order.driver_id or
            current_user.role == 'admin'
        ):
            join_room(f'order_{order_id}')
            emit('joined_order', {
                'order_id': order_id,
                'status': order.status
            })


# ============================================
# TEMPLATE FILTERS
# ============================================

@app.template_filter('currency')
def currency_filter(amount):
    """Format currency in DZD"""
    return format_currency(amount)


@app.context_processor
def utility_processor():
    """Add utility functions to templates"""
    return dict(
        format_currency=format_currency,
        CURRENCY_SYMBOL=Config.CURRENCY_SYMBOL
    )


# ============================================
# RUN APPLICATION
# ============================================


# ============================================
# PWA — تطبيق قابل للتثبيت على الهاتف
# ============================================
# الـ service worker لازم يُقدَّم من جذر الموقع حتى يغطّي كل الصفحات،
# لذلك نمرّره من / بدل /static/ .

@app.route('/sw.js')
def service_worker():
    response = send_from_directory('static', 'sw.js')
    response.headers['Content-Type'] = 'application/javascript; charset=utf-8'
    response.headers['Service-Worker-Allowed'] = '/'
    response.headers['Cache-Control'] = 'no-cache'
    return response


@app.route('/manifest.json')
def pwa_manifest():
    response = send_from_directory('static', 'manifest.json')
    response.headers['Content-Type'] = 'application/manifest+json; charset=utf-8'
    return response


def generate_order_number():
    """رقم طلب فريد — الدقة بالثانية وحدها كانت تُسقط أي طلبين في اللحظة نفسها"""
    import secrets
    stamp = datetime.now().strftime('%y%m%d%H%M%S')
    for _ in range(6):
        num = f"DZ{stamp}{secrets.randbelow(9000) + 1000}"
        if not Order.query.filter_by(order_number=num).first():
            return num
    return f"DZ{stamp}{secrets.token_hex(3).upper()}"


def user_may_see_order(order):
    """هل يحقّ للمستخدم الحالي الاطلاع على هذا الطلب؟"""
    if not current_user.is_authenticated:
        return False
    if current_user.role == 'admin':
        return True
    if order.customer_id == current_user.id:
        return True
    if order.driver_id and order.driver_id == current_user.id:
        return True
    if current_user.role == 'restaurant':
        rest = Restaurant.query.filter_by(user_id=current_user.id).first()
        if rest and order.restaurant_id == rest.id:
            return True
    return False


# الحالات التي يجوز فيها الإلغاء لكل دور
CANCELLABLE = {
    'customer':   ('pending', 'confirmed'),
    'restaurant': ('pending', 'confirmed', 'ready'),
    'admin':      ('pending', 'confirmed', 'ready', 'assigned'),
}


@app.route('/order/<int:order_id>/cancel', methods=['POST'])
@login_required
def cancel_order(order_id):
    """إلغاء طلب — للزبون قبل التحضير، وللمطعم قبل خروجه، وللمشرف في أي حالة قبل الاستلام"""
    order = Order.query.get_or_404(order_id)

    if not user_may_see_order(order):
        return jsonify({'error': 'لا تملك الصلاحية'}), 403

    role = current_user.role
    if role == 'driver':
        return jsonify({'error': 'السائق لا يلغي الطلب — تواصل مع الإدارة'}), 403

    allowed = CANCELLABLE.get(role, ())
    if order.status not in allowed:
        msg = {
            'pending':   'الطلب قيد المراجعة',
            'confirmed': 'المطعم بدأ التحضير',
            'ready':     'الطلب جاهز وينتظر سائقاً',
            'assigned':  'السائق في طريقه إلى المطعم',
            'picked_up': 'الطلب في الطريق إليك',
            'delivering':'الطلب في الطريق إليك',
            'delivered': 'الطلب سُلّم بالفعل',
            'cancelled': 'الطلب ملغى بالفعل',
        }.get(order.status, order.status)
        return jsonify({'error': f'لا يمكن الإلغاء الآن — {msg}'}), 400

    reason = (request.json or {}).get('reason', '') if request.is_json else request.form.get('reason', '')
    order.status = 'cancelled'
    order.cancelled_by = role
    order.cancel_reason = (reason or '')[:200]
    db.session.commit()

    who = {'customer': 'الزبون', 'restaurant': 'المطعم', 'admin': 'الإدارة'}.get(role, role)

    # إبلاغ كل الأطراف المعنية
    targets = {order.customer_id}
    if order.restaurant and order.restaurant.user_id:
        targets.add(order.restaurant.user_id)
    if order.driver_id:
        targets.add(order.driver_id)
    targets.discard(current_user.id)

    for uid in targets:
        create_notification(
            uid,
            '❌ أُلغي الطلب',
            f'الطلب {order.order_number} أُلغي من طرف {who}' + (f' — {reason}' if reason else ''),
            order.id
        )

    socketio.emit('order_update', {
        'order_id': order.id, 'status': 'cancelled', 'by': role
    }, room=f'order_{order.id}')

    return jsonify({'success': True, 'message': 'تم إلغاء الطلب'})


@app.route('/api/pricing/quote')
def api_pricing_quote():
    """تسعيرة لحظية — تستدعيها صفحة السلة قبل تأكيد الطلب"""
    rid = request.args.get('restaurant_id', type=int)
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    rest = Restaurant.query.get(rid) if rid else None
    return jsonify(quote_delivery(rest, lat, lng))


@app.route('/guide')
def guide():
    """صفحة أدلة الاستعمال (PDF لكل دور)"""
    return render_template('guide.html')


@app.route('/guide/<role>')
def guide_download(role):
    """تحميل دليل دور معيّن"""
    files = {
        'customer':   'دليل-الزبون.pdf',
        'restaurant': 'دليل-صاحب-المطعم.pdf',
        'driver':     'دليل-السائق.pdf',
    }
    if role not in files:
        return redirect(url_for('guide'))
    return send_from_directory(
        os.path.join(current_dir, 'static', 'docs'),
        files[role],
        as_attachment=False
    )


@app.route('/offline')
def offline_page():
    """تُعرض عند انقطاع الاتصال (يخزّنها الـ service worker)"""
    return render_template('offline.html')


# ============================================
# AUTO-INIT ON SERVER (Render / Railway / gunicorn)
# ============================================
# عند التشغيل عبر gunicorn لا يُنفَّذ بلوك __main__، لذا ننشئ الجداول هنا.
# العملية آمنة ومتكررة: init_database تتحقق من وجود البيانات قبل إضافتها.

if os.environ.get('DATABASE_URL') and os.environ.get('AUTO_INIT_DB', '1') == '1':
    try:
        init_database()
        print("✅ Database initialized on startup")
    except Exception as _e:
        print(f"⚠️  Database init skipped: {_e}")


if __name__ == '__main__':
    init_database()
    
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
    except:
        local_ip = '127.0.0.1'
    
    print("\n" + "="*70)
    print("🚀 server is ready...")
    print("="*70)
    print(f"📱  from phone: http://{local_ip}:5000")
    print(f"💻  from laptop: http://localhost:5000")
    print("="*70)
    print("⚡ WebSocket ready")
    print("💰 currency:   (DZD)")
    print("="*70 + "\n")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
