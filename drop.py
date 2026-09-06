# recreate_db.py
import sys
import os
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)

from app import app
from models import db

with app.app_context():
    print("🗑️  Dropping all tables...")
    db.drop_all()
    
    print("📋 Creating all tables...")
    db.create_all()
    
    print("✅ Database recreated with image columns!")