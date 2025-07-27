from app import app, db
from models import User

with app.app_context():
    users = User.query.all()
    print(f"Počet uživatelů v databázi: {len(users)}")
    
    for user in users:
        print(f"ID: {user.id}, Email: {user.email}")
        
    # Zkontrolujte konkrétního uživatele
    admin = User.query.filter_by(email='ondrej.klvac@smsreality.cz').first()
    if admin:
        print(f"\nAdmin uživatel existuje:")
        print(f"ID: {admin.id}")
        print(f"Email: {admin.email}")
        print(f"Heslo (hash): {admin.password}")
    else:
        print("\nAdmin uživatel neexistuje!")