# -*- coding: utf-8 -*-
"""تعبئة بيانات تجريبية محلياً:  python seed_demo.py"""
from app import app, db, User, Restaurant, MenuItem, Wallet, ensure_schema
import demo_data

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    ensure_schema()
    with app.app_context():
        rep = demo_data.seed(db, User, Restaurant, MenuItem, Wallet)
    print("\n✅ اكتملت التعبئة")
    print(f"   مطاعم جديدة: {rep['restaurants']}  (مُحدَّثة: {rep['updated']})")
    print(f"   أطباق جديدة: {rep['dishes']}")
    print(f"   سائقون جدد: {rep['drivers']}")
    print(f"   زبائن جدد:  {rep['customers']}")
    print("\n   كلمات السر: زبون client123 · سائق chauffeur123 · مطعم restaurant123\n")
