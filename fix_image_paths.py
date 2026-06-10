from models import db, Medicine
from config import Config
from flask import Flask

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

with app.app_context():
    meds = Medicine.query.all()
    for m in meds:
        if m.image and '\\' in m.image:
            # Fix Windows path separator
            fixed_image = m.image.replace('\\', '/')
            m.image = fixed_image
            print(f"Fixed image for {m.name}: {m.image}")
    db.session.commit()
    print("All image paths fixed.")
