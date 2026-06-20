from models import db, Order
from config import Config
from flask import Flask

app = Flask(__name__) 
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    orders = Order.query.all()
    print(f'Total orders: {len(orders)}')
    for o in orders:
        print(f'ID: {o.id}, User: {o.user_id}, Med: {o.medicine_id}, Status: {o.status}, Prescription: {o.prescription}')
