import os
from app import app, db
from models import Admin, ContactInfo
from werkzeug.security import generate_password_hash
from flask_migrate import upgrade

with app.app_context():
    print("Running database migrations...")
    try:
        upgrade()
    except Exception as e:
        print(f"Migration warning: {e}")
    db.create_all()
    print("Migrations and schema verification complete.")
    
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

    if ContactInfo.query.count() == 0:
        default_contact = ContactInfo(
            address="Dakar, Senegal",
            email="Aeeegs@gmail.com",
            phone="+221 78 596 14 79",
            whatsapp_url="https://whatsapp.com/channel/0029VaycmEG9mrGYpZBjll2i",
            facebook_url="https://www.facebook.com/AEEEGS",
            instagram_url="https://www.instagram.com/aeeegs_tv/?hl=fr-fr"
        )
        db.session.add(default_contact)
        db.session.commit()
        print("Default contact info seeded.")

