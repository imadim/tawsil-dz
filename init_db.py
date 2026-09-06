"""
تهيئة قاعدة البيانات على الخادم (إنشاء الجداول + البيانات التجريبية).
شغّله مرة واحدة بعد أول نشر:
    python init_db.py
"""
from app import init_database

if __name__ == '__main__':
    init_database()
    print("✅ قاعدة البيانات جاهزة")
