import sqlite3
from flask_bcrypt import Bcrypt

conn = sqlite3.connect('pharma.db')
c = conn.cursor()

bcrypt = Bcrypt() 
hashed = bcrypt.generate_password_hash('adminpass').decode('utf-8')

c.execute("""INSERT OR IGNORE INTO user 
             (email, phone, password, is_admin, is_verified) 
             VALUES (?, ?, ?, ?, ?)""",
          ('admin@pharma.com', '1234567890', hashed, 1, 1))

conn.commit()
conn.close()

print("Admin user created if not exists: admin@pharma.com / adminpass")
