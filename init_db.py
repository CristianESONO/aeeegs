import os
from app import app, db
from models import Admin
from werkzeug.security import generate_password_hash
from flask_migrate import upgrade

with app.app_context():
    print("Running database migrations...")
    upgrade()
    print("Migrations complete.")
    
    if Admin.query.count() == 0:
        username = os.environ.get('ADMIN_USERNAME', 'admin')
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        default_admin = Admin(
            username=username,
            password=generate_password_hash(password)
        )
        db.session.add(default_admin)
        db.session.commit()
        print(f"Default admin created: username='{username}'")
    else:
        print("Admin user(s) already exist.")
