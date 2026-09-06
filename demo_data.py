# -*- coding: utf-8 -*-
"""
بيانات تجريبية لعرض المنصة: مطاعم، أطباق بصور، سائقون، وزبائن.
لا تستورد app.py — تُستدعى منه بتمرير النماذج، فلا دور استيراد.
تشغيل محلي:  python seed_demo.py
من الخادم:   زر «تعبئة بيانات تجريبية» في لوحة الإدارة
"""

IMG = "/static/images/demo/"

# ── المطاعم ──────────────────────────────────────────────
RESTAURANTS = [
    dict(key="asala", name="Restaurant El Asala", name_ar="مطعم الأصالة",
         desc="مأكولات جزائرية أصيلة تُطهى يومياً على الطريقة التقليدية",
         cuisine="مأكولات جزائرية", wilaya="الجزائر", commune="باب الوادي",
         address="شارع ديدوش مراد، الجزائر الوسطى", phone="0540123456",
         lat=36.7853, lng=3.0603, img="rest-asala.jpg", rating=4.6, commission=10.0,
         owner=dict(username="مطعم الأصالة", email="restaurant@test.dz", phone="0540123456")),

    dict(key="wafa", name="Fast Food El Wafa", name_ar="فاست فود الوفاء",
         desc="وجبات سريعة طازجة: برغر، تاكوس، وشاورما",
         cuisine="فاست فود", wilaya="الجزائر", commune="حيدرة",
         address="حي حيدرة، الجزائر", phone="0550234567",
         lat=36.7538, lng=3.0300, img="rest-wafa.jpg", rating=4.2, commission=10.0,
         owner=dict(username="فاست فود الوفاء", email="fastfood@test.dz", phone="0550234567")),

    dict(key="amir", name="Grillades El Amir", name_ar="مشويات الأمير",
         desc="لحوم مشوية على الفحم، بروشيت ومرغاز وشواء مشكّل",
         cuisine="مشاوي", wilaya="وهران", commune="بئر الجير",
         address="شارع الأمير عبد القادر، بئر الجير", phone="0561345678",
         lat=35.7100, lng=-0.5800, img="rest-amir.jpg", rating=4.8, commission=12.0,
         owner=dict(username="مشويات الأمير", email="amir@test.dz", phone="0561345678")),

    dict(key="napoli", name="Pizza Napoli", name_ar="بيتزا نابولي",
         desc="بيتزا بعجينة إيطالية وباستا محضّرة في المكان",
         cuisine="بيتزا", wilaya="قسنطينة", commune="سيدي مبروك",
         address="حي سيدي مبروك، قسنطينة", phone="0554456789",
         lat=36.3650, lng=6.6147, img="rest-napoli.jpg", rating=4.4, commission=10.0,
         owner=dict(username="بيتزا نابولي", email="napoli@test.dz", phone="0554456789")),

    dict(key="yasmine", name="Patisserie El Yasmine", name_ar="حلويات الياسمين",
         desc="حلويات شرقية وغربية، بقلاوة وكريب ومثلجات",
         cuisine="حلويات ومرطبات", wilaya="سطيف", commune="سطيف",
         address="وسط مدينة سطيف", phone="0670567890",
         lat=36.1900, lng=5.4100, img="rest-yasmine.jpg", rating=4.7, commission=8.0,
         owner=dict(username="حلويات الياسمين", email="yasmine@test.dz", phone="0670567890")),

    dict(key="bahr", name="Restaurant El Bahr", name_ar="مطعم البحر الأبيض",
         desc="سمك طازج يومياً من ميناء عنابة، قمرون وكالامار",
         cuisine="مأكولات بحرية", wilaya="عنابة", commune="سيدي سالم",
         address="الواجهة البحرية، عنابة", phone="0552678901",
         lat=36.9000, lng=7.7667, img="rest-bahr.jpg", rating=4.5, commission=12.0,
         owner=dict(username="مطعم البحر الأبيض", email="bahr@test.dz", phone="0552678901")),
]

# ── الأطباق ──────────────────────────────────────────────
DISHES = {
 "asala": [
   ("كسكسي بالدجاج", "كسكسي مفتول يدوياً مع دجاج بلدي وخضر الموسم", 800, "أطباق رئيسية", 35, "d-couscous.jpg"),
   ("شوربة فريك",    "شوربة الفريك التقليدية بلحم الغنم",            250, "شوربة",        20, "d-chorba.jpg"),
   ("رشتة قسنطينية", "رشتة منزلية بمرق أبيض ودجاج وحمّص",           700, "أطباق رئيسية", 30, "d-rechta.jpg"),
   ("محاجب",         "أربع قطع محاجب محشوة بالطماطم والبصل",         150, "مقبلات",       15, "d-mhajeb.jpg"),
   ("بوراك باللحم",  "ست قطع بوراك مقرمش محشو باللحم المفروم",       200, "مقبلات",       18, "d-bourek.jpg"),
   ("طاجين الزيتون", "طاجين دجاج بالزيتون والليمون المخلّل",         900, "أطباق رئيسية", 40, "d-tajine.jpg"),
 ],
 "wafa": [
   ("برغر كلاسيك",   "لحم بقري مشوي، جبن شيدر، خس وطماطم",           450, "برغر",          12, "d-burger.jpg"),
   ("بطاطا مقلية",   "بطاطا طازجة مقلية مع صلصة المنزل",             200, "مقبلات",         8, "d-fries.jpg"),
   ("تاكوس XL",      "تاكوس بثلاثة أنواع لحم وصلصة الجبن",           700, "ساندويتشات",    15, "d-tacos.jpg"),
   ("شاورما دجاج",   "شاورما دجاج بخبز عربي وثوم",                   500, "ساندويتشات",    12, "d-shawarma.jpg"),
   ("دجاج مقلي",     "ثماني قطع دجاج مقرمش مع البطاطا",              600, "أطباق رئيسية",  20, "d-chicken.jpg"),
   ("عصير طبيعي",    "عصير برتقال أو ليمون طازج",                    200, "مشروبات",        5, "d-juice.jpg"),
 ],
 "amir": [
   ("بروشيت لحم",    "ست أسياخ لحم غنم مشوية على الفحم",             900, "مشاوي",         25, "d-brochette.jpg"),
   ("شواء مشكّل",    "طبق لحم وكفتة ومرغاز مع الخبز والسلطة",       1600, "مشاوي",         35, "d-meat.jpg"),
   ("مرغاز",         "أربع قطع مرغاز حار مشوي",                      700, "مشاوي",         20, "d-merguez.jpg"),
   ("دجاج مشوي",     "نصف دجاجة متبّلة مشوية مع البطاطا",            850, "مشاوي",         30, "d-chicken.jpg"),
   ("سلطة مشوية",    "فلفل وطماطم مشوية بزيت الزيتون",               300, "سلطات",         12, "d-salad.jpg"),
 ],
 "napoli": [
   ("بيتزا مارغريتا","صلصة طماطم، موزاريلّا، وريحان طازج",           800, "بيتزا",         22, "d-pizza.jpg"),
   ("بيتزا مشكّلة",  "لحم، دجاج، فطر، فلفل وزيتون",                 1100, "بيتزا",         25, "d-pizza.jpg"),
   ("باستا بولونيز", "سباغيتي بصلصة اللحم المفروم",                  750, "معكرونة",       20, "d-pasta.jpg"),
   ("لازانيا",       "لازانيا باللحم وصلصة البشاميل",                850, "معكرونة",       25, "d-lasagna.jpg"),
   ("سلطة سيزر",     "خس، دجاج مشوي، بارميزان وصلصة سيزر",           450, "سلطات",         10, "d-salad.jpg"),
 ],
 "yasmine": [
   ("تشيز كيك",      "قطعة تشيز كيك بالفراولة",                      350, "حلويات",         5, "d-cake.jpg"),
   ("بقلاوة",        "علبة بقلاوة باللوز والعسل (12 قطعة)",          400, "حلويات",         5, "d-baklawa.jpg"),
   ("كريب نوتيلا",   "كريب ساخن بالنوتيلا والموز",                   400, "حلويات",        10, "d-crepe.jpg"),
   ("مثلجات",        "ثلاث كرات بنكهات مختارة",                      250, "حلويات",         5, "d-icecream.jpg"),
   ("قهوة",          "قهوة إسبريسو أو كابتشينو",                     120, "مشروبات",        5, "d-coffee.jpg"),
 ],
 "bahr": [
   ("سمك مشوي",      "سمك اليوم مشوي مع الليمون والأرز",            1400, "أطباق رئيسية",  35, "d-fish.jpg"),
   ("قمرون بالثوم",  "قمرون طازج مقلي بالثوم والبقدونس",            1800, "أطباق رئيسية",  30, "d-shrimp.jpg"),
   ("كالامار مقلي",  "حلقات كالامار مقرمشة مع صلصة التارتار",       1200, "مقبلات",        20, "d-calamari.jpg"),
   ("شوربة بحرية",   "شوربة بالسمك والقمرون",                        500, "شوربة",         18, "d-soup.jpg"),
 ],
}

# ── السائقون ──────────────────────────────────────────────
DRIVERS = [
    dict(username="محمد بن عيسى", email="chauffeur@test.dz",  phone="0660123456",
         wilaya="الجزائر", commune="باب الوادي", vehicle="دراجة نارية 125",
         lat=36.7800, lng=3.0590, available=True),
    dict(username="ياسين حمادي",  email="driver2@test.dz",    phone="0661234567",
         wilaya="الجزائر", commune="حيدرة",     vehicle="دراجة نارية 150",
         lat=36.7500, lng=3.0350, available=True),
    dict(username="كريم زروقي",   email="driver3@test.dz",    phone="0662345678",
         wilaya="وهران",   commune="بئر الجير", vehicle="سيارة كليو",
         lat=35.7080, lng=-0.5820, available=True),
    dict(username="سفيان مرابط",  email="driver4@test.dz",    phone="0663456789",
         wilaya="قسنطينة", commune="سيدي مبروك", vehicle="دراجة نارية 125",
         lat=36.3630, lng=6.6120, available=False),
    dict(username="عبد الله شريف", email="driver5@test.dz",   phone="0664567890",
         wilaya="سطيف",    commune="سطيف",      vehicle="سيارة سيمبول",
         lat=36.1920, lng=5.4080, available=False),
]

# ── الزبائن ──────────────────────────────────────────────
CUSTOMERS = [
    dict(username="أحمد",   email="client@test.dz",   phone="0770123456", wilaya="الجزائر", commune="باب الوادي"),
    dict(username="سمية",   email="client2@test.dz",  phone="0771234567", wilaya="الجزائر", commune="حيدرة"),
    dict(username="رياض",   email="client3@test.dz",  phone="0772345678", wilaya="وهران",   commune="بئر الجير"),
    dict(username="نادية",  email="client4@test.dz",  phone="0773456789", wilaya="قسنطينة", commune="سيدي مبروك"),
    dict(username="بلال",   email="client5@test.dz",  phone="0774567890", wilaya="سطيف",    commune="سطيف"),
    dict(username="إيمان",  email="client6@test.dz",  phone="0775678901", wilaya="عنابة",   commune="سيدي سالم"),
]

DEFAULT_PASSWORDS = {"restaurant": "restaurant123", "driver": "chauffeur123", "customer": "client123"}


def seed(db, User, Restaurant, MenuItem, Wallet=None):
    """يضيف ما ينقص فقط — التشغيل مرتين لا يُكرّر شيئاً"""
    report = {"restaurants": 0, "dishes": 0, "drivers": 0, "customers": 0, "updated": 0}

    def get_or_make_user(info, role, password):
        u = User.query.filter_by(email=info["email"]).first()
        created = False
        if not u:
            u = User(username=info["username"], email=info["email"], phone=info["phone"], role=role)
            u.set_password(password)
            db.session.add(u)
            created = True
        u.wilaya  = info.get("wilaya", u.wilaya)
        u.commune = info.get("commune", getattr(u, "commune", None))
        u.is_active = True
        return u, created

    # ── الزبائن ──
    for c in CUSTOMERS:
        _, new = get_or_make_user(c, "customer", DEFAULT_PASSWORDS["customer"])
        report["customers"] += 1 if new else 0
    db.session.commit()

    # ── السائقون ──
    for d in DRIVERS:
        u, new = get_or_make_user(d, "driver", DEFAULT_PASSWORDS["driver"])
        u.vehicle_info  = d["vehicle"]
        u.current_lat   = d["lat"]
        u.current_lng   = d["lng"]
        u.is_available  = d["available"]
        report["drivers"] += 1 if new else 0
    db.session.commit()

    # ── المطاعم وأطباقها ──
    for r in RESTAURANTS:
        owner, _ = get_or_make_user(
            dict(r["owner"], wilaya=r["wilaya"], commune=r["commune"]),
            "restaurant", DEFAULT_PASSWORDS["restaurant"]
        )
        db.session.commit()

        rest = Restaurant.query.filter_by(user_id=owner.id).first()
        if not rest:
            rest = Restaurant(user_id=owner.id, name=r["name"], name_ar=r["name_ar"],
                              address=r["address"], latitude=r["lat"], longitude=r["lng"])
            db.session.add(rest)
            report["restaurants"] += 1
        else:
            report["updated"] += 1

        rest.name            = r["name"]
        rest.name_ar         = r["name_ar"]
        rest.description_ar  = r["desc"]
        rest.cuisine         = r["cuisine"]
        rest.wilaya          = r["wilaya"]
        rest.commune         = r["commune"]
        rest.address         = r["address"]
        rest.phone           = r["phone"]
        rest.latitude        = r["lat"]
        rest.longitude       = r["lng"]
        rest.image_url       = IMG + r["img"]
        rest.rating          = r["rating"]
        rest.commission_rate = r["commission"]
        rest.is_open         = True
        db.session.commit()

        for name_ar, desc, price, cat, prep, img in DISHES.get(r["key"], []):
            item = MenuItem.query.filter_by(restaurant_id=rest.id, name_ar=name_ar).first()
            if not item:
                item = MenuItem(restaurant_id=rest.id, name_ar=name_ar, price=price)
                db.session.add(item)
                report["dishes"] += 1
            item.description_ar   = desc
            item.price            = price
            item.category_ar      = cat
            item.preparation_time = prep
            item.image_url        = IMG + img
            item.is_available     = True
        db.session.commit()

    # ── صورة افتراضية لأي طبق قديم بلا صورة، حسب تصنيفه ──
    BY_CATEGORY = {
        "مقبلات": "d-bourek.jpg",       "شوربة": "d-soup.jpg",
        "أطباق رئيسية": "d-tajine.jpg", "معكرونة": "d-pasta.jpg",
        "بيتزا": "d-pizza.jpg",         "برغر": "d-burger.jpg",
        "ساندويتشات": "d-shawarma.jpg", "سلطات": "d-salad.jpg",
        "حلويات": "d-cake.jpg",         "مشروبات": "d-juice.jpg",
        "مشاوي": "d-brochette.jpg",
    }
    for item in MenuItem.query.filter((MenuItem.image_url.is_(None)) | (MenuItem.image_url == '')).all():
        item.image_url = IMG + BY_CATEGORY.get(item.category_ar, "d-tajine.jpg")
        report["updated"] += 1
    db.session.commit()

    # ── محافظ فارغة للسائقين ──
    if Wallet is not None:
        for d in DRIVERS:
            u = User.query.filter_by(email=d["email"]).first()
            if u and not Wallet.query.filter_by(user_id=u.id).first():
                db.session.add(Wallet(user_id=u.id, balance=0.0, total_earned=0.0))
        db.session.commit()

    return report
