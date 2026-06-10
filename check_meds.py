from models import db, Medicine
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    meds = Medicine.query.all()
    print(f'Total medicines: {len(meds)}')
    for m in meds:
        print(f'ID: {m.id}, Name: {m.name}, Image: {m.image}')
