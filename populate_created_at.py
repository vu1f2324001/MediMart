from app import app, db
from models import User
from datetime import datetime

with app.app_context():
    # Get all users without created_at
    users = User.query.filter(User.created_at.is_(None)).all()
    print(f"Found {len(users)} users without created_at")

    # Set created_at to current time for existing users (or use a default date)
    default_date = datetime.utcnow()  # Or use a specific date like datetime(2023, 1, 1)

    for user in users:
        user.created_at = default_date

    db.session.commit()
    print(f"Updated {len(users)} users with created_at")

    # Verify
    total_users = User.query.count()
    users_with_created_at = User.query.filter(User.created_at.isnot(None)).count()
    print(f"Total users: {total_users}")
    print(f"Users with created_at: {users_with_created_at}")
