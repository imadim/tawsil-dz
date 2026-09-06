# check_menuitem.py – run once: python check_menuitem.py
from app import app, MenuItem
with app.app_context():
    cols = [c.name for c in MenuItem.__table__.columns]
    print('MenuItem columns:', cols)