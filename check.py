import sys
import os
current_dir = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, current_dir)

from app import app
from models import db, Restaurant, User

with app.app_context():
    print("\n" + "="*60)
    print("📊 Checking Restaurants in Database")
    print("="*60 + "\n")
    
    # Count restaurants
    total_restaurants = Restaurant.query.count()
    open_restaurants = Restaurant.query.filter_by(is_open=True).count()
    
    print(f"Total Restaurants: {total_restaurants}")
    print(f"Open Restaurants: {open_restaurants}")
    print("\n" + "-"*60 + "\n")
    
    # List all restaurants
    restaurants = Restaurant.query.all()
    
    if restaurants:
        for restaurant in restaurants:
            print(f"🍽️  {restaurant.name_ar}")
            print(f"   ID: {restaurant.id}")
            print(f"   English: {restaurant.name}")
            print(f"   Owner ID: {restaurant.user_id}")
            print(f"   Address: {restaurant.address}")
            print(f"   Wilaya: {restaurant.wilaya}")
            print(f"   Phone: {restaurant.phone}")
            print(f"   Status: {'✅ Open' if restaurant.is_open else '❌ Closed'}")
            print(f"   Menu Items: {restaurant.menu_items.count()}")
            print(f"   Image: {restaurant.image_url if restaurant.image_url else 'No image'}")
            print("-"*60 + "\n")
    else:
        print("❌ No restaurants found in database!")
        print("\nRun: python app.py")
        print("This will initialize the database with sample restaurants.")
    
    print("="*60)